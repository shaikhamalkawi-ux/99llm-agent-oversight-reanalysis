#!/usr/bin/env python3
"""Inside offline disposable benchmark container. No transcript command execution."""
import hashlib,json,os,re,subprocess,sys,tempfile,collections
from pathlib import Path
def run(a,timeout=90):
    return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def fail(status):
    print('G10_CELL '+json.dumps({'status':status},sort_keys=True));sys.exit(0)
def git(*a):
    p=run(['git','-c','safe.directory=/testbed',*a])
    if p.returncode:fail('HOLD_GIT_OPERATION')
    return p.stdout
def apply(path):
    for opts in (['--check'],[]):
        p=run(['git','-c','safe.directory=/testbed','apply','--whitespace=nowarn',*opts,path])
        if p.returncode:fail('HOLD_EXACT_PATCH_APPLICATION')
def main(cell):
    if cell not in ('base_local','base_reference','candidate_local','candidate_reference','gold_reference'):fail('HOLD_BAD_CELL')
    os.chdir('/testbed');m=json.loads(Path('/audit/meta.json').read_text())
    initial_head=git('rev-parse','HEAD').decode().strip()
    if git('status','--porcelain','--untracked-files=all'):fail('HOLD_DIRTY_BASE')
    # Published images may use a setup commit. Check out the exact requested
    # commit only if the object is already present offline; never fetch inside.
    if initial_head!=m['base_commit']:
        if run(['git','-c','safe.directory=/testbed','cat-file','-e',m['base_commit']+'^{commit}']).returncode:fail('HOLD_BASE_COMMIT_NOT_IN_IMAGE')
        git('checkout','--detach',m['base_commit'])
    if git('rev-parse','HEAD').decode().strip()!=m['base_commit']:fail('HOLD_BASE_COMMIT_MISMATCH')
    if git('status','--porcelain','--untracked-files=all'):fail('HOLD_DIRTY_BASE')
    base_restored=initial_head!=m['base_commit']
    # Apply the fixed production/candidate patch, then change only reference test paths.
    if cell.startswith('candidate_'):apply('/audit/candidate.diff')
    if cell.startswith('gold_'):apply('/audit/gold.diff')
    if cell.endswith('_reference'):
        for p in m['test_paths']:
            if p.startswith('/') or '..' in Path(p).parts or not p:fail('HOLD_PATH')
            target=Path(p)
            if any(x.is_symlink() for x in [target,*target.parents] if str(x)!='.'):fail('HOLD_SYMLINK')
            has=run(['git','-c','safe.directory=/testbed','cat-file','-e',m['base_commit']+':'+p]).returncode==0
            if has:git('restore','--source='+m['base_commit'],'--worktree','--staged','--',p)
            elif target.exists():
                if not target.is_file():fail('HOLD_PATH_TYPE')
                target.unlink()
        apply('/audit/reference_tests.diff')
    git('add','-A')
    # Bind the non-test tree, including all tracked and newly staged paths,
    # by path and blob IDs. Exclude only the exact intervention paths.
    tree=git('ls-files','--stage','-z').split(b'\0')
    excluded=set(m['test_paths']);keep=[]
    for line in tree:
        if not line:continue
        header,path=line.split(b'\t',1)
        if path.decode('utf-8') not in excluded:keep.append(line)
    digest=hashlib.sha256(b'\0'.join(sorted(keep))).hexdigest()
    nodes=m['nodes']
    if not nodes or not all(isinstance(x,str) and x and not x.startswith('-') and '\x00' not in x for x in nodes):fail('HOLD_NODES')
    if any('::' not in x or not x.split('::',1)[0].endswith('.py') or '..' in Path(x.split('::',1)[0]).parts or x.startswith('/') for x in nodes):fail('HOLD_UNSUPPORTED_NODE_SYNTAX')
    files=sorted({x.split('::',1)[0] for x in nodes})
    if any(not Path(p).is_file() for p in files):fail('HOLD_FILE_MISSING')
    # Match python -m pytest's initial repository import path.
    sys.path.insert(0,os.getcwd())
    import pytest
    class Receipt:
        def __init__(self):
            self.all=[];self.kept=[];self.reports=collections.defaultdict(list);self.collection_errors=0;self.collection_error_categories=collections.Counter()
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self,session,config,items):
            self.all=[i.nodeid for i in items]
            selected=[i for i in items if i.nodeid in nodes]
            self.kept=[i.nodeid for i in selected]
            # If identity incomplete, never treat a subset as complete.
            dropped=[i for i in items if i.nodeid not in nodes]
            items[:]=selected
            config.hook.pytest_deselected(items=dropped)
        def pytest_collectreport(self,report):
            if report.failed:
                self.collection_errors+=1
                # No original messages, source paths or test text are emitted.
                s=str(report.longrepr)
                k=('module_not_found' if 'ModuleNotFoundError' in s else 'import_error' if 'ImportError' in s else 'syntax_error' if 'SyntaxError' in s else 'attribute_error' if 'AttributeError' in s else 'type_error' if 'TypeError' in s else 'other')
                self.collection_error_categories[k]+=1
        def pytest_runtest_logreport(self,r):
            self.reports[r.nodeid].append((r.when,r.outcome,bool(getattr(r,'wasxfail',False))))
    p=Receipt()
    rc=int(pytest.main(['-q','--disable-warnings',*files],plugins=[p]))
    def verdict(n):
        a=p.reports[n]
        if len(a)!=3 or {x[0] for x in a}!={'setup','call','teardown'} or any(x[2] for x in a):return 'HOLD'
        q={x[0]:x[1] for x in a}
        if q['setup']!='passed' or q['teardown']!='passed':return 'HOLD'
        return {'passed':'PASS','failed':'FAIL'}.get(q['call'],'HOLD')
    counts=collections.Counter(verdict(n) for n in nodes)
    exact=(len(p.kept)==len(nodes) and set(p.kept)==set(nodes) and len(p.all)==len(set(p.all)) and not p.collection_errors)
    complete=exact and not counts['HOLD'] and rc in (0,1)
    result='HOLD'
    if complete and rc==0 and counts['PASS']==len(nodes):result='PASS'
    elif complete and rc==1 and counts['FAIL']>0:result='FAIL'
    d={'status':'EXECUTED','pytest_verdict':result,'pytest_returncode':rc,'all_file_collected':len(p.all),'required_collected':len(p.kept),'required_missing':len(set(nodes)-set(p.all)),'passed':counts['PASS'],'failed':counts['FAIL'],'held':counts['HOLD'],'collection_errors':p.collection_errors,'collection_error_categories':dict(p.collection_error_categories),'non_test_tree_digest':digest,'exact_base_restored_offline':base_restored}
    print('G10_CELL '+json.dumps(d,sort_keys=True),flush=True)

if __name__=='__main__':
    try:main(sys.argv[1])
    except Exception as exc:
        import traceback
        # Own script line locations and exception class only, no source output.
        lines=[f.lineno for f in traceback.extract_tb(exc.__traceback__) if f.filename==__file__]
        print('G10_CELL '+json.dumps({'status':'HOLD_RUNTIME_OR_SETUP','exception_type':type(exc).__name__,'audit_lines':lines},sort_keys=True),flush=True)
