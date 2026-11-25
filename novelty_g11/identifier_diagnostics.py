#!/usr/bin/env python3
"""G11: exact named reference FTP+PTP tests, with independent collection receipt.
Run only in disposable network-isolated official task container.
"""
import collections,hashlib,json,os,subprocess,sys
from pathlib import Path
def emit(d): print('G11_CELL '+json.dumps(d,sort_keys=True),flush=True)
def stop(s,**k):emit({'status':s,**k});sys.exit(0)
def proc(a,timeout=90):return subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
def git(*a):
    p=proc(['git','-c','safe.directory=/testbed',*a])
    if p.returncode:stop('HOLD_GIT')
    return p.stdout
def diag(p):
    # Fixed aggregate categories, never publish source paths or patch contents.
    e=p.stderr.lower()
    return ('corrupt_patch' if b'corrupt patch' in e else
            'patch_context_mismatch' if b'patch does not apply' in e or b'patch failed' in e else
            'path_missing' if b'no such file' in e or b'does not exist' in e else
            'path_already_exists' if b'already exists' in e else
            'binary_patch' if b'binary' in e else 'other')
def apply(p):
    for opts in (['--check'],[]):
        r=proc(['git','-c','safe.directory=/testbed','apply','--whitespace=nowarn',*opts,p])
        if r.returncode:stop('HOLD_EXACT_PATCH_APPLICATION',patch_role=Path(p).stem,reason=diag(r))
def main(cell):
    os.chdir('/testbed');m=json.loads(Path('/audit/meta.json').read_text())
    if git('status','--porcelain','--untracked-files=all'):stop('HOLD_DIRTY_IMAGE')
    b=m['base_commit']
    if git('rev-parse','HEAD').decode().strip()!=b:
        if proc(['git','-c','safe.directory=/testbed','cat-file','-e',b+'^{commit}']).returncode:stop('HOLD_BASE_NOT_IN_IMAGE')
        git('checkout','--detach',b)
    if git('rev-parse','HEAD').decode().strip()!=b or git('status','--porcelain','--untracked-files=all'):stop('HOLD_BASE')
    if cell=='candidate':apply('/audit/candidate.diff')
    elif cell=='gold':apply('/audit/gold.diff')
    elif cell!='base':stop('HOLD_CELL')
    # Same intervention as G10: restore only official test paths then apply test patch.
    for p in m['test_paths']:
        if p.startswith('/') or '..' in Path(p).parts or not p:stop('HOLD_TEST_PATH')
        path=Path(p)
        if any(x.is_symlink() for x in [path,*path.parents] if str(x)!='.'):stop('HOLD_SYMLINK')
        has=proc(['git','-c','safe.directory=/testbed','cat-file','-e',b+':'+p]).returncode==0
        if has:git('restore','--source='+b,'--worktree','--staged','--',p)
        elif path.exists():
            if not path.is_file():stop('HOLD_PATH_TYPE')
            path.unlink()
    apply('/audit/reference_tests.diff')
    git('add','-A')
    full_digest=hashlib.sha256(git('ls-files','--stage','-z')).hexdigest()
    F=set(m['ftp']);P=set(m['ptp'])
    if F&P:stop('HOLD_OVERLAPPING_REFERENCE_GROUPS')
    nodes=sorted(F|P)
    if not nodes or any(not x or x.startswith('-') or '\x00' in x or '::' not in x or not x.split('::')[0].endswith('.py') or '..' in Path(x.split('::')[0]).parts or x.startswith('/') for x in nodes):
        stop('HOLD_UNSUPPORTED_NODE_SYNTAX',ftp_count=len(F),ptp_count=len(P))
    import pytest
    class Receipt:
        def __init__(self):self.collected=[];self.reports=collections.defaultdict(list);self.collection_errors=0
        def pytest_collection_finish(self,session):self.collected=[x.nodeid for x in session.items]
        def pytest_collectreport(self,report):
            self.collection_errors+=report.failed
        def pytest_runtest_logreport(self,report):
            self.reports[report.nodeid].append((report.when,report.outcome,bool(getattr(report,'wasxfail',False))))
    receipt=Receipt()
    # Do not print original test stdout: host retains only the structured marker.
    # Follow file-level collection, preserving required-node membership.
    # Extra tests are counted separately rather than silently treated as required.
    files=sorted({x.split('::',1)[0] for x in nodes})
    if any(not Path(p).is_file() for p in files):stop('HOLD_REQUIRED_TEST_FILE_MISSING',ftp_count=len(F),ptp_count=len(P))
    rc=int(pytest.main(['-q','--disable-warnings',*files],plugins=[receipt]))
    actual=set(receipt.collected)
    def status(n):
        rs=receipt.reports[n]
        if len(rs)!=3 or {x[0] for x in rs}!={'setup','call','teardown'} or any(x[2] for x in rs):return 'HOLD'
        d={a:b for a,b,_ in rs}
        if d['setup']!='passed' or d['teardown']!='passed':return 'HOLD'
        return {'passed':'PASS','failed':'FAIL'}.get(d['call'],'HOLD')
    def group(names):
        counts=collections.Counter(status(n) for n in names)
        return {'n':len(names),'pass':counts['PASS'],'fail':counts['FAIL'],'hold':counts['HOLD']}
    a,b=group(F),group(P)
    exact=(len(receipt.collected)==len(actual) and set(nodes)<=actual and not receipt.collection_errors)
    extra=group(actual-set(nodes))
    determinate=exact and not a['hold'] and not b['hold'] and rc in (0,1)

    # Diagnostic only: map missing exact metadata names to otherwise unassigned
    # collected items under explicit parser representations. No outcome recoding.
    missing=set(nodes)-actual
    unused=actual-set(nodes)
    def whitespace(x):return ' '.join(x.split())
    def token(x):return x.split()[0] if x.split() else ''
    def noansi(x):
        import re
        x=re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]','',x)
        return ''.join(c for c in x if ord(c)>=32)
    # Do not treat the broad parameter-family rule as a match:
    # count only how many have a possible same-function family.
    def family(x):return x.split('[',1)[0]
    diag={}
    for name,rule in [('whitespace_normalization',whitespace),('legacy_first_token',token),('current_log_control_whitespace',lambda x:whitespace(noansi(x)))]:
        d=collections.Counter();reverse=collections.defaultdict(list)
        for x in actual:reverse[rule(x)].append(x)
        mapped={}
        for q in sorted(missing):
            z=reverse.get(rule(q),[])
            if len(z)!=1:d['none_or_ambiguous']+=1;continue
            if z[0] not in unused:d['collides_with_exact_required']+=1;continue
            mapped[q]=z[0]
        collision=collections.Counter(mapped.values())
        for q,x in mapped.items():
            if collision[x]!=1:d['many_to_one']+=1;continue
            d['unique_unused_mapping']+=1
            d['unique_mapped_PASS']+=status(x)=='PASS'
            d['unique_mapped_FAIL']+=status(x)=='FAIL'
            d['unique_mapped_HOLD']+=status(x)=='HOLD'
        d['missing_total']=len(missing)
        assert sum(d[k] for k in ('none_or_ambiguous','collides_with_exact_required','many_to_one','unique_unused_mapping'))==len(missing)
        diag[name]=dict(d)
    fam=collections.Counter()
    for q in missing:
        n=sum(family(q)==family(x) for x in unused)
        fam['same_parameter_family_candidates']+=n>0
        fam['single_family_candidate']+=n==1
        fam['multiple_family_candidates']+=n>1
        fam['missing_with_whitespace']+=any(c.isspace() for c in q)
        fam['missing_with_open_bracket']+='[' in q
    fam['missing_total']=len(missing)

    # Additional tests may fail, so global exit status cannot be attributed
    # to just FTP/PTP. Report required-group and extra-group results separately.
    emit({'status':'EXECUTED','ftp':a,'ptp':b,'extra':extra,'pytest_returncode':rc,'required_collection_complete':exact,'collected_count':len(receipt.collected),'collection_errors':receipt.collection_errors,'required_not_collected':len(set(nodes)-actual),'fully_determinate':determinate,'identifier_representation_diagnostics':diag,'parameter_family_diagnostics':dict(fam),'tree_digest':full_digest})
if __name__=='__main__':
    try:main(sys.argv[1])
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):stop('HOLD_RUNTIME')
