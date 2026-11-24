#!/usr/bin/env python3
"""G9 external: report-level FTP/PTP decomposition and local named evidence.
No execution of third-party code, no transcript/identifier export.
"""
import argparse,collections,concurrent.futures,hashlib,json,re,sys,urllib.request,urllib.parse,xml.etree.ElementTree as ET,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g8'))
from audit_test_scope_transition import command_kind,receipt,PYID
from audit_test_identity import read_meta,audit_case
C=collections.Counter
OFFICIAL='40f164d5b8f1d249bf95a6df8b74b577fd8e519d'
GEMINI_REV='2f6637a2557da1f7b5f2b583ab7090a077bbeed2'
GEMINI_REPO='SWE-bench/20260901_mini-v2.4.2_gemini-3-5-flash'
S3='https://swe-bench-submissions.s3.amazonaws.com/'
RUNS={'gemini':'20260901_mini-v2.4.2_gemini-3-5-flash','gpt5mini':'20250807_mini-v1.7.0_gpt-5-mini','devstral':'20251209_mini-v1.17.2_devstral-small-2512'}
WRAPPER=re.compile(r'\s*<returncode>\s*(-?\d+)\s*</returncode>\s*<output>([\s\S]*)</output>\s*')
def fetch(url,limit=30*1024*1024):
    req=urllib.request.Request(url,headers={'User-Agent':'99llm-aggregate-research/1.0'})
    with urllib.request.urlopen(req,timeout=50) as r:b=r.read(limit+1)
    if len(b)>limit:raise ValueError('oversize')
    return b
def sha(b):return hashlib.sha256(b).hexdigest()
def norm_patch(p):
    if isinstance(p,bytes):
        try:p=p.decode('utf-8')
        except UnicodeDecodeError:return None
    if not isinstance(p,str):return None
    # Permit final newline convention only; never strip spaces or alter file content.
    return p.replace('\r\n','\n').rstrip('\n')
def list_s3(prefix):
    keys=[];token=None
    while True:
        p={'list-type':'2','prefix':prefix,'max-keys':1000}
        if token:p['continuation-token']=token
        doc=ET.fromstring(fetch(S3+'?'+urllib.parse.urlencode(p)))
        keys.extend(x.text for x in doc.findall('.//{*}Key'))
        token=doc.findtext('.//{*}NextContinuationToken')
        if not token:break
    return keys
def read_report(raw,iid,m):
    z=json.loads(raw)
    if iid not in z or len(z)!=1:return None,'wrong_report_key'
    v=z[iid]
    if not isinstance(v.get('resolved'),bool):return None,'missing_resolved'
    if not v.get('patch_successfully_applied'):return v,'not_applied_or_no_report'
    s=v.get('tests_status')
    if not isinstance(s,dict):return v,'no_test_breakdown'
    try:
        result={}
        for k,want in [('FAIL_TO_PASS',m['ftp']),('PASS_TO_PASS',m['ptp'])]:
            a=s[k]['success'];b=s[k]['failure'];A=set(a);B=set(b)
            if len(A)!=len(a) or len(B)!=len(b) or A&B or A|B!=want:return v,'test_name_partition_mismatch'
            result[k]=(A,B)
    except (TypeError,KeyError,ValueError):return v,'no_test_breakdown'
    if bool(v['resolved'])!=(not result['FAIL_TO_PASS'][1] and not result['PASS_TO_PASS'][1]):return v,'verdict_partition_mismatch'
    return (v,result),'admitted'
def calls(messages):
    """Use exact adjacent single call/result links; older explicit fenced bash only."""
    for i,(a,b) in enumerate(zip(messages,messages[1:])):
        if a.get('role')!='assistant':continue
        cs=a.get('tool_calls') or []
        mode=None;cmd=None
        if len(cs)==1 and b.get('role')=='tool':
            c=cs[0];f=c.get('function') or {}
            if c.get('id')!=b.get('tool_call_id') or not c.get('id') or f.get('name') not in ('bash','terminal'):continue
            args=f.get('arguments')
            try:args=json.loads(args) if isinstance(args,str) else args
            except (ValueError,TypeError):continue
            if isinstance(args,dict):cmd=args.get('command');mode='structured'
        elif not cs and b.get('role')=='user' and isinstance(a.get('content'),str):
            matches=re.findall(r'\x60\x60\x60(?:bash|sh)\s*\n([\s\S]*?)\x60\x60\x60',a['content'])
            if len(matches)!=1 or a['content'].count('\x60\x60\x60')!=2:continue
            cmd=matches[0];mode='legacy_single_fence'
        if not isinstance(cmd,str) or not isinstance(b.get('content'),str):continue
        m=WRAPPER.fullmatch(b['content'])
        if not m:continue
        rc=int(m[1]);out=m[2]
        yield i,cmd.strip(),rc,out,mode
def positive(cmd,rc,out):
    if rc!=0:return None
    kind,o=command_kind({'tool_calls':[{'tool':'bash','arguments':{'command':cmd}}],'observations':[out]})
    if receipt(kind,o)!='pass':return None
    return {m[1].removeprefix('./') for m in PYID.finditer(o)} if kind=='pytest' else set()
def add_condition(z,label,on,report,parts,ids,m):
    if not on:return
    f,p=parts['FAIL_TO_PASS'],parts['PASS_TO_PASS']
    z[label+'_runs']+=1;z[label+'_benchmark_nonpass']+=not report['resolved']
    z[label+'_ftp_failure_runs']+=bool(f[1]);z[label+'_ptp_failure_runs']+=bool(p[1])
    z[label+'_ftp_only_failure_runs']+=bool(f[1]) and not p[1]
    z[label+'_ptp_only_failure_runs']+=not f[1] and bool(p[1])
    z[label+'_both_failure_runs']+=bool(f[1] and p[1])
    z[label+'_local_reported_ftp_names_failed_in_report_runs']+=bool(ids&f[1])
    z[label+'_local_reported_ptp_names_failed_in_report_runs']+=bool(ids&p[1])
def analyze_one(iid,raws,official,meta,detail):
    c=C();z=C();static=None
    c['official_frame_member']=1
    required={'report','patch','traj'}
    if not required.issubset(set(raws.keys())):
        c['missing_any_required_artifact']=1
        for k in ('report','patch','traj'):c['missing_'+k]+=k not in raws
        return c,z,None
    c['all_three_artifacts']=1
    try:
        t=json.loads(raws['traj']);report=json.loads(raws['report'])
    except (ValueError,TypeError):c['invalid_json']=1;return c,z,None
    if t.get('instance_id') not in (None,iid):c['trajectory_id_mismatch']=1;return c,z,None
    patch=norm_patch(raws['patch'])
    if patch is None or not patch:c['empty_or_unreadable_patch']=1;return c,z,None
    if norm_patch((t.get('info') or {}).get('submission'))!=patch:
        c['submission_patch_mismatch_or_missing']=1;return c,z,None
    c['submission_equals_evaluated_patch']=1
    if detail is None or not isinstance(detail.get('resolved'),bool):
        c['no_official_row_verdict']=1;return c,z,None
    if iid not in report or report[iid].get('resolved')!=detail['resolved']:
        c['official_report_verdict_mismatch']=1;return c,z,None
    c['official_report_verdict_agrees']=1
    rep,state=read_report(raws['report'],iid,meta)
    c[state]+=1
    if state!='admitted':return c,z,None
    r,parts=rep
    c['admitted_benchmark_pass']+=r['resolved']
    f=parts['FAIL_TO_PASS'][1];p=parts['PASS_TO_PASS'][1]
    c['admitted_ftp_only_nonpass']+=bool(f) and not p
    c['admitted_ptp_only_nonpass']+=not f and bool(p)
    c['admitted_both_nonpass']+=bool(f and p)
    messages=t.get('messages')
    if not isinstance(messages,list):c['missing_messages']=1;return c,z,None
    rec=list(calls(messages))
    c['runs_with_recognized_tool_pair']+=bool(rec)
    local=[];snap=set();modes=set()
    for i,cmd,rc,out,mode in rec:
        modes.add(mode)
        # Exact full unstaged diff snapshot only. Does not include untracked state.
        if rc==0 and cmd in ('git diff','git --no-pager diff','git diff --no-color','git --no-pager diff --no-color') and norm_patch(out)==patch:
            snap.add(i)
        ids=positive(cmd,rc,out)
        if ids is not None:local.append((i,ids))
    c['structured_runs']+='structured' in modes;c['legacy_runs']+='legacy_single_fence' in modes
    c['any_local_positive']=bool(local)
    c['any_local_named_positive']=any(ids for _,ids in local)
    c['exact_final_diff_snapshot_runs']=bool(snap)
    union=set().union(*(ids for _,ids in local)) if local else set()
    m=meta
    full=[(i,ids) for i,ids in local if m['ftp']<=ids]
    full_both=[(i,ids) for i,ids in full if m['ptp']<=ids]
    # Strongest conservative adjacency: one complete local command pair
    # immediately between two exact final-diff command pairs in message list.
    bracket=[(i,ids) for i,ids in local if i-2 in snap and i+2 in snap]
    lastdiff=[(i,ids) for i,ids in local if i+2 in snap]
    predicates=[('positive',bool(local),union),('named_positive',bool(union),union),
        ('any_ftp_name',bool(union&m['ftp']),union),
        ('full_ftp_union',bool(local) and m['ftp']<=union,union),
        ('full_ftp_single',bool(full),set().union(*(ids for _,ids in full)) if full else set()),
        ('full_ftp_ptp_single',bool(full_both),set().union(*(ids for _,ids in full_both)) if full_both else set()),
        ('full_ftp_ptp_union',bool(local) and (m['ftp']|m['ptp'])<=union,union),
        ('positive_immediately_before_final_diff',bool(lastdiff),set().union(*(ids for _,ids in lastdiff)) if lastdiff else set()),
        ('positive_bracketed_final_diff',bool(bracket),set().union(*(ids for _,ids in bracket)) if bracket else set())]
    for name,on,ids in predicates:add_condition(z,name,on,r,parts,ids,m)
    # Static final tracked test identity for full-FTP single-receipt subset;
    # not necessarily the local test's historical state.
    if full:
        pick=max((ids for _,ids in full),key=lambda ids:len(ids&m['ptp']))
        static=(r['resolved'],pick,union,patch)
    return c,z,static
def selftest():
    m={'ftp':{'tests/a.py::test_a'},'ptp':{'tests/a.py::test_b'}}
    j={'i':{'resolved':False,'patch_successfully_applied':True,'tests_status':{'FAIL_TO_PASS':{'success':[],'failure':['tests/a.py::test_a']},'PASS_TO_PASS':{'success':['tests/a.py::test_b'],'failure':[]}}}}
    v,s=read_report(json.dumps(j).encode(),'i',m);assert s=='admitted'
    j['i']['tests_status']['FAIL_TO_PASS']['failure']=['other']
    assert read_report(json.dumps(j).encode(),'i',m)[1]=='test_name_partition_mismatch'
    a={'role':'assistant','tool_calls':[{'id':'x','function':{'name':'bash','arguments':'{"command":"pytest -v tests/a.py"}'}}]}
    b={'role':'tool','tool_call_id':'x','content':'<returncode>0</returncode>\n<output>\ntests/a.py::test_a PASSED [100%]\n1 passed in 0.1s\n</output>'}
    rec=list(calls([a,b]));assert len(rec)==1
    assert positive(rec[0][1],rec[0][2],rec[0][3])=={'tests/a.py::test_a'}
    assert positive('pytest',1,'1 passed in 0.1s') is None
    assert norm_patch('a\n')==norm_patch('a') and norm_patch('a ' )!=norm_patch('a')
    # Full end-to-end fixture: identical nonempty submission and evaluation patch,
    # report contains all required names, explicit positive local receipt.
    j['i']['tests_status']['FAIL_TO_PASS']['failure']=['tests/a.py::test_a']
    t={'instance_id':'i','info':{'submission':'diff --git a/a b/a\n'},'messages':[a,b]}
    raw={'report':json.dumps(j).encode(),'patch':b'diff --git a/a b/a\n','traj':json.dumps(t).encode()}
    q,z,st=analyze_one('i',raw,{'i':{'resolved':False}},m,{'resolved':False})
    assert q['all_three_artifacts']==1 and q['admitted']==1
    assert z['full_ftp_single_runs']==1 and z['full_ftp_single_ftp_failure_runs']==1
    assert st is not None
    print('G9 external partition, receipt and full admission fixture PASS')
def main(root,run):
    meta,mh=read_meta(root)
    runid=RUNS[run]
    official_raw=fetch(f'https://raw.githubusercontent.com/SWE-bench/experiments/{OFFICIAL}/evaluation/verified/{runid}/per_instance_details.json')
    official=json.loads(official_raw);assert set(official)<=set(meta)
    all_paths={};clone=None;unknown_keys=C()
    if run=='gemini':
        clone=root/'external'
        subprocess.run(['git','clone','--quiet','--depth','1','https://github.com/'+GEMINI_REPO+'.git',str(clone)],check=True)
        assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=clone,text=True).strip()==GEMINI_REV
        for iid in meta:
            for k,path in [('report',clone/'logs'/iid/'report.json'),('patch',clone/'logs'/iid/'patch.diff'),('traj',clone/'trajs'/(iid+'.traj.json'))]:
                if path.is_file() and not path.is_symlink():all_paths[iid,k]=str(path)
        preds=[json.loads(l) for l in (clone/'all_preds.jsonl').read_text().splitlines() if l.strip()]
        pred={p['instance_id']:p['model_patch'] for p in preds};assert len(pred)==len(preds)
        for iid in pred:
            if (iid,'patch') in all_paths:assert norm_patch(Path(all_paths[iid,'patch']).read_bytes())==norm_patch(pred[iid])
    else:
        for folder in ('logs','trajs'):
            pref=f'bash-only/{runid}/{folder}/'
            for key in list_s3(pref):
                rel=key[len(pref):];pieces=rel.split('/')
                iid=next((x for x in pieces if x in meta),None)
                if iid is None:
                    iid=next((x for x in meta if pieces[-1]==x+'.traj.json' or pieces[-1]==x+'.json' or pieces[-1]==x+'.traj'),None)
                if iid is None:unknown_keys[folder]+=1;continue
                kind=None
                if folder=='logs' and pieces[-1]=='report.json':kind='report'
                elif folder=='logs' and pieces[-1]=='patch.diff':kind='patch'
                elif folder=='trajs' and (pieces[-1].endswith('.traj.json') or pieces[-1] in (iid+'.json',iid+'.traj')):kind='traj'
                if not kind:continue
                k=(iid,kind)
                if k in all_paths:raise ValueError('duplicate archive object per task/kind')
                all_paths[k]=key
    print('G9_EXTERNAL_INVENTORY',run,json.dumps({'official_rows':len(official),'artifact_paths':dict(C(k for _,k in all_paths)),'unknown_keys':dict(unknown_keys)},sort_keys=True),flush=True)
    independently_loaded=C();tally=C();counts=C();static_counts=collections.defaultdict(C);static_runs=collections.defaultdict(C);hash_rows=[];base_cache={};base_hashes=C();errors=C()
    def load(iid):
        raw={};e=C()
        for kind in ('report','patch','traj'):
            k=iid,kind
            if k not in all_paths:continue
            try:
                source=all_paths[k]
                raw[k]=Path(source).read_bytes() if clone else fetch(S3+urllib.parse.quote(source,safe='/'))
            except Exception as ex:e[k+'_fetch_'+type(ex).__name__]+=1
        return iid,raw,e
    # Full 500-task frame, no replacing unavailable cases.
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for iid,raw,errs in ex.map(load,sorted(meta)):
            errors.update(errs)
            independently_loaded['triples']+=set(raw)=={'report','patch','traj'}
            for k,b in raw.items():hash_rows.append((iid,k,sha(b)));independently_loaded[k]+=1
            c,z,s=analyze_one(iid,dict(raw),official,meta[iid],official.get(iid))
            assert c['all_three_artifacts']==int(set(raw)=={'report','patch','traj'})
            tally.update(c);counts.update(z)
            if s is not None:
                ok,ids,union,patch=s
                a=audit_case(meta[iid],patch,ids,union,base_cache,base_hashes)
                for tag in ('all','benchmark_pass' if ok else 'benchmark_nonpass'):
                    static_counts[tag].update(a);static_counts[tag]['runs']+=1
                    for k,v in a.items():static_runs[tag][k+'_positive_runs']+=bool(v)
    assert tally['official_frame_member']==500
    assert tally['all_three_artifacts']==independently_loaded['triples']
    for kind in ('report','patch','traj'):assert tally['missing_'+kind]<=500-independently_loaded[kind]
    assert tally['all_three_artifacts']+tally['missing_any_required_artifact']==500
    assert tally['all_three_artifacts']>0,'No complete artifacts: external result is not admitted'
    assert tally['admitted']==tally['admitted_benchmark_pass']+tally['admitted_ftp_only_nonpass']+tally['admitted_ptp_only_nonpass']+tally['admitted_both_nonpass']
    assert counts['full_ftp_single_runs']==static_counts['all']['runs']
    out={'run':run,'official_revision':OFFICIAL,'official_details_sha256':sha(official_raw),'official_rows':len(official),'official_passes':sum(bool(x.get('resolved')) for x in official.values()),
         'artifact_path_counts':dict(C(k for _,k in all_paths)),'metadata_hash':mh,'source_bundle_manifest_sha256':sha(json.dumps(sorted(hash_rows),separators=(',',':')).encode()),
         'independent_read_counts':dict(independently_loaded),'artifact_bytes_read_count':len(hash_rows),'fetch_errors':dict(errors),'cohort':dict(tally),'local_reference_scope':dict(counts),
         'static_final_test_identity':{k:dict(v) for k,v in static_counts.items()},'static_run_flags':{k:dict(v) for k,v in static_runs.items()},
         'static_base_files':len(base_cache),'static_base_file_status':dict(C(x[0] for x in base_cache.values())),
         'qualification':'Separate archived submission cohorts. Final patch equality to trajectory submission does not bind earlier local receipts to final patch; report-level grade is source-reported. Same test names may have different code, runtime or selection. Adjacent equal recorded git diff is a narrow screen, not full environment identity. Static final test AST does not identify executed local AST. Unavailable artifacts retained in 500-task frame, not failures. No data or source identifiers exported; S3 snapshot manifest is a digest, not an immutable origin guarantee.'}
    return out
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--selftest',action='store_true');a.add_argument('--run',choices=list(RUNS));a.add_argument('--root');a.add_argument('--out');o=a.parse_args()
    if o.selftest:selftest()
    if o.run:
        root=Path(o.root);root.mkdir(parents=True,exist_ok=True);z=main(root,o.run)
        Path(o.out).write_text(json.dumps(z,indent=2,sort_keys=True)+'\n')
        print('G9_EXTERNAL_RESULT',o.run,json.dumps(z,sort_keys=True),flush=True)
        print('G9 EXTERNAL ARCHIVE AUDIT PASS')
