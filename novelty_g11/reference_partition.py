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
    rc=int(pytest.main(['-q','--disable-warnings',*nodes],plugins=[receipt]))
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
    exact=(len(receipt.collected)==len(nodes) and actual==set(nodes) and not receipt.collection_errors)
    determinate=exact and not a['hold'] and not b['hold'] and rc in (0,1)
    consistent=(rc==0)==(a['fail']+b['fail']==0)
    emit({'status':'EXECUTED','ftp':a,'ptp':b,'pytest_returncode':rc,'exact_collection':exact,'collected_count':len(receipt.collected),'collection_errors':receipt.collection_errors,'fully_determinate':determinate and consistent,'tree_digest':full_digest})
if __name__=='__main__':
    try:main(sys.argv[1])
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired):stop('HOLD_RUNTIME')
