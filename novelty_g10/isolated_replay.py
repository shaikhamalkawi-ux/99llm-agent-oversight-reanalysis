#!/usr/bin/env python3
"""Inside offline disposable benchmark container. No transcript command execution."""
import hashlib,json,os,re,subprocess,sys,tempfile,xml.etree.ElementTree as ET
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
    with tempfile.TemporaryDirectory() as td:
        xml=Path(td)/'test.xml'
        try:p=run([sys.executable,'-m','pytest','-q','--disable-warnings','--junitxml='+str(xml),*nodes],100)
        except subprocess.TimeoutExpired:fail('HOLD_TEST_TIMEOUT')
        if not xml.is_file():fail('HOLD_NO_JUNIT_REPORT')
        try:
            root=ET.parse(xml).getroot();cases=root.findall('.//testcase')
        except ET.ParseError:fail('HOLD_JUNIT_PARSE')
        n=len(cases);errors=sum(x.find('error') is not None for x in cases);failed=sum(x.find('failure') is not None for x in cases);skipped=sum(x.find('skipped') is not None for x in cases);passed=n-errors-failed-skipped
        if n!=len(nodes) or errors or skipped or p.returncode not in (0,1):verdict='HOLD'
        elif p.returncode==0 and passed==n:verdict='PASS'
        elif p.returncode==1 and failed>0:verdict='FAIL'
        else:verdict='HOLD'
        result={'status':'EXECUTED','pytest_verdict':verdict,'pytest_returncode':p.returncode,'collected':n,'passed':passed,'failed':failed,'errors':errors,'skipped':skipped,'non_test_tree_digest':digest,'exact_base_restored_offline':base_restored}
        print('G10_CELL '+json.dumps(result,sort_keys=True))
if __name__=='__main__':
    try:main(sys.argv[1])
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):fail('HOLD_RUNTIME_OR_SETUP')
