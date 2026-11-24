#!/usr/bin/env python3
"""G9: frozen G8 all-FTP local markers: static test identity and coverage audit.
Do not execute source, tests or transcript commands. Only aggregate data leave runner.
"""
import argparse,ast,collections,hashlib,json,re,sys,tempfile,subprocess,urllib.request,urllib.error
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g8'))
from audit_test_scope_transition import (VREPO,VREV,VRUNS,RUNS,REV,REPO,download,load_source,parse_diff,stable,scope_flags,PYID,command_kind,receipt)
C=collections.Counter
def digest(b):return hashlib.sha256(b).hexdigest()
def read_meta(root):
    import pyarrow.parquet as pq
    p=root/'verified_task_metadata.parquet'
    h=download(f'https://huggingface.co/datasets/{VREPO}/resolve/{VREV}/data/test-00000-of-00001.parquet',p)
    assert h['sha256']=='a45b1fe4e2f0c8390b2b2938ac83e92ed5979000856808f3679c07812e9e6dcd'
    rows=pq.read_table(p,columns=['instance_id','repo','base_commit','test_patch','FAIL_TO_PASS','PASS_TO_PASS']).to_pylist()
    assert len(rows)==500 and len({r['instance_id'] for r in rows})==500
    out={}
    for r in rows:
        f=r['FAIL_TO_PASS'];p=r['PASS_TO_PASS']
        if isinstance(f,str):f=json.loads(f)
        if isinstance(p,str):p=json.loads(p)
        assert isinstance(f,list) and f and isinstance(p,list)
        dm=parse_diff(r['test_patch'])
        out[r['instance_id']]=dict(r,ftp=set(f),ptp=set(p),testpaths=set(dm) if dm is not None else None)
    return out,h
def node_parts(node):
    # Pytest node IDs only, exact path; strip parametrization, not aliases.
    x=node.split('::')
    if len(x)<2 or not x[0].endswith('.py'):return None
    path=x[0].removeprefix('./')
    names=x[1:];names[-1]=names[-1].split('[',1)[0]
    if not all(s.isidentifier() for s in names):return None
    return path,tuple(names)
def get_ast(raw,names):
    if raw is None:return ('file_missing',None)
    try:t=ast.parse(raw)
    except (SyntaxError,ValueError,TypeError):return ('parse_error',None)
    for i,name in enumerate(names):
        expected=(ast.FunctionDef,ast.AsyncFunctionDef) if i==len(names)-1 else (ast.ClassDef,)
        found=[n for n in getattr(t,'body',[]) if isinstance(n,expected) and n.name==name]
        if len(found)!=1:return ('function_missing_or_ambiguous',None)
        t=found[0]
    return ('found',ast.dump(t,include_attributes=False))
def safe(p):
    q=PurePosixPath(p)
    return bool(p and not q.is_absolute() and '..' not in q.parts and '\\' not in p and '\x00' not in p and not any(x.startswith('.') for x in q.parts))
def base_file(meta,path,cache,hashes):
    key=(meta['repo'],meta['base_commit'],path)
    if key in cache:return cache[key]
    if not safe(path) or not re.fullmatch(r'[\w.-]+/[\w.-]+',meta['repo']) or not re.fullmatch(r'[a-f0-9]{40}',meta['base_commit']):
        return ('unsafe_path',None)
    from urllib.parse import quote
    url=f"https://raw.githubusercontent.com/{meta['repo']}/{meta['base_commit']}/{quote(path,safe='/')}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'99llm-static-audit/1.0'}),timeout=30) as r:
            b=r.read(8*1024*1024+1)
        if len(b)>8*1024*1024:result=('oversize',None)
        else:result=('present',b);hashes[digest(b)]+=1
    except urllib.error.HTTPError as e:
        result=('absent',None) if e.code==404 else ('fetch_error',None)
    except Exception:result=('fetch_error',None)
    cache[key]=result;return result
def apply_block(base,block,path):
    if block is None:return ('unchanged',base)
    if not safe(path):return ('unsafe_path',None)
    # Strict header and exact application, no fuzzy application or code execution.
    if not block.startswith(f'diff --git a/{path} b/{path}\n'):return ('unparseable',None)
    if re.search(r'^(?:rename |copy |GIT binary patch|Binary files|new file mode 120000|old mode 120000|new mode 120000)',block,re.M):return ('unsupported',None)
    if re.search(r'^(?:---|\+\+\+) ',block,re.M):
        allowed={f'--- a/{path}',f'+++ b/{path}','--- /dev/null','+++ /dev/null'}
        headers=[x for x in block.splitlines() if x.startswith(('--- ','+++ '))]
        # Changed content can begin with "-- " etc.; strict rejection is safe.
        if any(x not in allowed for x in headers):return ('unparseable',None)
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);target=root/path
        if base is not None:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(base)
        b=block.encode('utf-8')
        res=subprocess.run(['git','apply','--check','--whitespace=nowarn','-'],cwd=d,input=b,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if res.returncode:return ('apply_failed',None)
        res=subprocess.run(['git','apply','--whitespace=nowarn','-'],cwd=d,input=b,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if res.returncode:return ('apply_failed',None)
        if target.is_symlink():return ('unsupported',None)
        return ('applied',target.read_bytes() if target.is_file() else None)
def audit_case(meta,agentdiff,receipt_ids,all_ids,cache,hashes):
    gold=parse_diff(meta['test_patch']);agent=parse_diff(agentdiff)
    row=C()
    row['ftp_count']=len(meta['ftp']);row['ptp_count']=len(meta['ptp'])
    row['ptp_in_single_all_ftp_receipt']=len(meta['ptp']&receipt_ids)
    row['ptp_in_union_final_positive_receipts']=len(meta['ptp']&all_ids)
    row['full_ptp_single']=meta['ptp']<=receipt_ids;row['full_ptp_union']=meta['ptp']<=all_ids
    row['ptp_empty']=not meta['ptp'];row['agent_diff_parseable']=agent is not None
    row['gold_diff_parseable']=gold is not None
    if gold is None or agent is None:return row
    row['agent_touches_any_gold_test_file']=bool(agent.keys()&gold.keys())
    row['agent_touches_any_FTP_node_file']=bool(agent.keys()&{x[0] for f in meta['ftp'] if (x:=node_parts(f))})
    row['agent_exact_gold_test_file_blocks']=sum(agent.get(p)==b for p,b in gold.items())
    row['gold_test_files']=len(gold)
    for f in sorted(meta['ftp']):
        n=node_parts(f)
        if n is None:row['node_id_unparseable']+=1;continue
        path,names=n
        status,raw=base_file(meta,path,cache,hashes)
        if status not in ('present','absent'):row['base_file_unavailable']+=1;continue
        bs,ba=get_ast(raw,names)
        gs,graw=apply_block(raw,gold.get(path),path)
        ass,araw=apply_block(raw,agent.get(path),path)
        if gs not in ('unchanged','applied') or ass not in ('unchanged','applied'):
            row['diff_application_unavailable']+=1;continue
        gstat,ga=get_ast(graw,names);astat,aa=get_ast(araw,names)
        if gstat!='found':row['gold_node_not_found']+=1;continue
        row['gold_node_found']+=1
        if bs!='found':row['gold_node_not_found_in_base']+=1
        elif ba!=ga:row['gold_node_changed_from_base']+=1
        else:row['gold_node_same_as_base']+=1
        if astat!='found':row['reported_pass_node_not_found_in_reconstructed_agent_file']+=1
        elif aa!=ga:row['reported_pass_node_AST_differs_from_gold']+=1
        else:row['reported_pass_node_AST_matches_gold']+=1
        # File-byte agreement is stricter than one AST; imported code/runtime not checked.
        if araw is not None and araw==graw:row['agent_file_bytes_equal_gold']+=1
        if araw is not None and raw is not None and araw==raw and raw!=graw:row['agent_file_unchanged_but_gold_file_differs']+=1
        if path in gold:row['FTP_node_in_gold_changed_file']+=1
    return row
def selftest():
    raw=b'def test_x():\n    assert True\n'
    patch='diff --git a/tests/a.py b/tests/a.py\n--- a/tests/a.py\n+++ b/tests/a.py\n@@ -1,2 +1,2 @@\n def test_x():\n-    assert True\n+    assert False\n'
    status,new=apply_block(raw,patch,'tests/a.py')
    assert status=='applied' and get_ast(raw,('test_x',))!=get_ast(new,('test_x',))
    assert node_parts('tests/a.py::TestA::test_x[p]')==('tests/a.py',('TestA','test_x'))
    assert not safe('../x.py') and get_ast(None,('x',))[0]=='file_missing'
    print('G9 static identity synthetic tests PASS')
def run(root):
    meta,mh=read_meta(root);cache={};hashes=C();groups=collections.defaultdict(C);cases=collections.defaultdict(C);source={};selected=[]
    for name in sorted(VRUNS):
        T,th=load_source(root,name,'trajectories');P,ph=load_source(root,name,'patches')
        # dependency_files_removed: audit release projection explicitly
        import pyarrow.parquet as pq
        drows=pq.read_table(root/f'{name}_patches.parquet',columns=['instance_id','patch_id','dependency_files_removed']).to_pylist()
        removed={(q['instance_id'],q['patch_id']):q['dependency_files_removed'] for q in drows}
        pm={(q['instance_id'],q['patch_id']):q for q in P};assert len(pm)==len(P)
        assert {q['instance_id'] for q in T}==set(meta)
        source[name]={'trajectories':th,'patches':ph}
        for r in T:
            if not r['trajectory_complete'] or not r['trajectory']:continue
            iid=r['instance_id'];fin=r['final_patch_id'];ids=r['step_patch_ids'] or [];ok=r['resolved']
            if not fin:continue
            assert pm[iid,fin]['resolved']==ok
            steps=json.loads(r['trajectory'])
            if len(steps)!=r['stop'] or [q.get('step') for q in steps]!=list(range(1,len(steps)+1)):continue
            allpass=set();full=[]
            for st in steps:
                kind,obs=command_kind(st)
                if receipt(kind,obs)!='pass':continue
                s,p=stable(ids,st['step'])
                if not s or p!=fin:continue
                nodeids={m[1].removeprefix('./') for m in PYID.finditer(obs)} if kind=='pytest' else set()
                allpass|=nodeids
                if meta[iid]['ftp']<=nodeids:full.append(nodeids)
            if not full:continue
            # Representative single receipt: maximum PTP coverage among all-FTP receipts.
            pick=max(full,key=lambda x:len(x&meta[iid]['ptp']))
            z=audit_case(meta[iid],pm[iid,fin]['patch'],pick,allpass,cache,hashes)
            z['dependency_files_removed']=removed[iid,fin] or 0
            label='benchmark_pass' if ok else 'benchmark_nonpass'
            key=(name,label)
            for k in [key,('all',label),('all','all')]:
                groups[k].update(z);groups[k]['runs']+=1
                for n,v in z.items():
                    if v:cases[k][n+'_positive_runs']+=1
            # Private task IDs not emitted; collect distinct task count only.
            selected.append((iid,ok))
        del T,P
    assert len(selected)==13 and sum(not ok for _,ok in selected)==6
    return {'source_revision':REV,'metadata_hash':mh,'source_hashes':source,'distinct_selected_tasks':len({x for x,_ in selected}),
            'groups':{'/'.join(k):dict(v) for k,v in groups.items()},'run_flags':{'/'.join(k):dict(v) for k,v in cases.items()},
            'base_file_fetch_count':len(cache),'base_file_fetch_status':dict(C(x[0] for x in cache.values())),
            'base_file_sha256_counts':dict(hashes),'qualification':'Static reconstruction of released tracked diffs against base commit; no test execution or runtime coverage proof. AST comparison excludes formatting but does not compare imported helpers or fixture semantics. Binary benchmark verdict cannot identify FTP vs PTP vs infrastructure failure. Local name matches are reported strings, not independently verified test execution.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selftest',action='store_true');p.add_argument('--input-dir');p.add_argument('--out');o=p.parse_args()
    if o.selftest:selftest()
    if o.input_dir:
        root=Path(o.input_dir);root.mkdir(parents=True,exist_ok=True);z=run(root)
        Path(o.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        print('G9_AGGREGATE',json.dumps(z,sort_keys=True),flush=True)
        print('G9 STATIC SOURCE AUDIT PASS')
