#!/usr/bin/env python3
"""G8: scope attribution and same-command fail-to-pass transitions.

Post-G7 exploratory study, with definitions committed before G8 source outcomes.
No execution of transcript commands; no original rows, IDs, paths or text exported.
"""
import argparse, collections, hashlib, json, re, shlex, sys, urllib.request
from pathlib import Path, PurePosixPath
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g7'))
from audit_patch_receipts import RUNS,REPO,REV,command_kind,receipt,stable3,state_at,exit_codes
from audit_receipt_scope import cmd_identity,strict_summary
C=collections.Counter
VREPO='princeton-nlp/SWE-bench_Verified'
VREV='c104f840cc67f8b6eec6f759ebc8b2693d585d4a'
VRUNS={r for r in RUNS if 'verified' in r}
TESTPATH=re.compile(r'(^|/)(tests?|testing|spec|__tests__|test_?data|fixtures)/|(^|/)test_[^/]*$|_test\.[a-z]+$|[._-](test|spec)\.[a-z]+$|Tests?\.java$')
PROD_EXT={'.py','.pyx','.pxd','.c','.cc','.cpp','.h','.hpp','.js','.ts','.tsx','.jsx','.java','.go','.rs','.rb','.php','.cs','.swift','.kt'}
HEADER=re.compile(r'^diff --git a/([^\s"]+) b/([^\s"]+)$',re.M)
# No basename-only matches; only exact root-relative paths or unique suffixes
# containing at least two path components. Matching is textual, not execution.
PYPATH=re.compile(r'^(?:[A-Za-z0-9_./+-]+/)?[A-Za-z0-9_.+-]+\.py(?:::.+)?$')
PYID=re.compile(r'^([A-Za-z0-9_./+-]+\.py::\S+)\s+PASSED(?:\s+\[\s*\d+%\])?\s*$',re.M)
PYFLAGS={'-q','-qq','-v','-vv','-s','-x','-ra','-rA','--verbose','--quiet','--disable-warnings','--showlocals','--tb=short','--tb=long','--tb=no','--tb=auto','--strict-markers','--strict-config','--no-header','--no-summary','--color=no','--color=yes','--color=auto'}
def download(url,path):
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'99llm-scope-audit/1.0'})
        with urllib.request.urlopen(req,timeout=120) as src,path.open('wb') as dst:
            while True:
                b=src.read(1024*1024)
                if not b:break
                dst.write(b)
    return {'url':url,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def load_source(root,run,kind):
    import pyarrow.parquet as pq
    p=root/f'{run}_{kind}.parquet'
    h=download(f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/data/{run}/{kind}.parquet',p)
    cols=['instance_id','patch_id','resolved','patch'] if kind=='patches' else ['instance_id','resolved','first_correct','stop','trajectory_complete','trajectory','step_patch_ids','final_patch_id']
    return pq.read_table(p,columns=cols).to_pylist(),h
def parse_diff(diff):
    if diff is None or diff=='':return {}
    if not isinstance(diff,str):return None
    starts=[m.start() for m in re.finditer(r'^diff --git ',diff,re.M)]
    ms=list(HEADER.finditer(diff))
    if not starts or starts[0]!=0 or starts!=[m.start() for m in ms]:return None
    d={}
    for i,m in enumerate(ms):
        a,b=m[1],m[2]
        if a!=b or a in d:return None # keep rename/ambiguous paths out of exact map comparisons
        chunk=diff[m.start():ms[i+1].start() if i+1<len(ms) else len(diff)]
        d[a]=chunk
    return d
def read_verified(root):
    import pyarrow.parquet as pq
    p=root/'verified_task_metadata.parquet'
    h=download(f'https://huggingface.co/datasets/{VREPO}/resolve/{VREV}/data/test-00000-of-00001.parquet',p)
    rows=pq.read_table(p,columns=['instance_id','repo','test_patch','FAIL_TO_PASS','PASS_TO_PASS']).to_pylist()
    assert len(rows)==500 and len({r['instance_id'] for r in rows})==500
    out={}
    for r in rows:
        f=r['FAIL_TO_PASS'];p=r['PASS_TO_PASS']
        if isinstance(f,str):f=json.loads(f)
        if isinstance(p,str):p=json.loads(p)
        assert isinstance(f,list) and f and isinstance(p,list)
        assert all(isinstance(x,str) for x in f+p)
        testmap=parse_diff(r['test_patch'])
        out[r['instance_id']]={'repo':r['repo'],'ftp':set(f),'ptp':set(p),'testpaths':set(testmap) if testmap is not None else None}
    return out,h
def stable(ids,s):
    # Empty patch is explicitly null in the dataset schema; keep separate
    # from absent indices or unequal snapshots.
    if not 2<=s<=len(ids) or ids[s-1]!=ids[s-2]:return False,None
    return True,ids[s-1]
def path_category(p,official):
    if (official is not None and p in official) or TESTPATH.search(p):return 'test_path'
    if PurePosixPath(p).suffix.lower() in PROD_EXT:return 'non_test_source_extension'
    return 'other'
def transition(a,b,official,ida,idb):
    if ida==idb:return 'identical_recorded_patch'
    if a is None or b is None:return 'unparseable_diff'
    diff={k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
    if not diff:return 'different_id_equal_file_blocks'
    categories={path_category(k,official) for k in diff}
    if categories=={'test_path'}:return 'test_paths_only'
    if categories=={'non_test_source_extension'}:return 'non_test_source_extensions_only'
    if categories=={'other'}:return 'other_paths_only'
    return 'mixed_paths'
def selectors(st):
    # Parse only narrow pytest invocations; unknown options may change scope,
    # so retain the receipt but mark its selected file scope unclassified.
    try:tok=list(cmd_identity(st))
    except (ValueError,TypeError,KeyError):return None
    if tok[:1]==['cd']:
        if len(tok)<4 or tok[2]!='&&':return None
        tok=tok[3:]
    if tok[:1] in (['pytest'],['py.test']):tok=tok[1:]
    elif len(tok)>=3 and re.fullmatch(r'python(?:[0-9]+(?:\.[0-9]+)*)?',tok[0]) and tok[1:3]==['-m','pytest']:tok=tok[3:]
    else:return None
    paths=[]
    for t in tok:
        if t in PYFLAGS:continue
        if t.startswith('-') or not PYPATH.fullmatch(t):return None
        path=t.split('::',1)[0]
        if '..' in PurePosixPath(path).parts:return None
        paths.append(t.removeprefix('./'))
    return paths or None
def match_path(path,targets):
    if targets is None:return None
    path=path.removeprefix('./')
    if path in targets:return path
    if len(PurePosixPath(path).parts)<2:return None
    hit=[x for x in targets if path.endswith('/'+x) or x.endswith('/'+path)]
    return hit[0] if len(hit)==1 else None
def scope_flags(st,kind,obs,meta):
    if not meta:return {}
    s=selectors(st);official=meta['testpaths']
    matched=set()
    exact_path=set()
    if s and official is not None:
        for v in s:
            p=v.split('::',1)[0]
            if p in official:exact_path.add(p)
            m=match_path(p,official)
            if m:matched.add(m)
    ids={m[1].removeprefix('./') for m in PYID.finditer(obs)} if kind=='pytest' else set()
    f=meta['ftp'];p=meta['ptp']
    return {'gold_test_patch_path_parseable':official is not None,
            'explicit_pytest_file_scope':bool(s),
            'explicit_gold_test_path_match':bool(matched),
            'explicit_exact_gold_test_path_match':bool(exact_path),
            'explicit_gold_FTP_selector_match':bool(set(s or [])&f),
            'explicit_gold_PTP_selector_match':bool(set(s or [])&p),
            'named_local_PASSED_line':bool(ids),
            'exact_reported_gold_FTP_PASS':bool(ids&f),
            'exact_reported_gold_PTP_PASS':bool(ids&p),
            'all_gold_FTP_names_reported_PASS':f<=ids}
def add_flags(c,flags,ok):
    for k,on in flags.items():
        if on:
            c[k]+=1;c[k+'_benchmark_nonpass']+=not ok
def analyze(T,P,expected,meta):
    patches={}
    for x in P:
        k=(x['instance_id'],x['patch_id'])
        assert k not in patches and isinstance(x['resolved'],bool)
        patches[k]=x
    assert len(T)==expected and len({x['instance_id'] for x in T})==expected
    if meta is not None:assert {x['instance_id'] for x in T}==set(meta)
    total=C();scope=C();scope_events=C();transition_runs=C();transition_events=C()
    first_pair=C();final_flags=C();trans_by_setting_repo=collections.defaultdict(C)
    for r in T:
        iid=r['instance_id'];ids=r['step_patch_ids'] or [];fin=r['final_patch_id'];ok=r['resolved']
        assert all((iid,p) in patches for p in ids if p)
        assert (bool(fin) and patches[iid,fin]['resolved'])==ok
        total['runs']+=1;total['final_benchmark_pass']+=ok
        if not r['trajectory_complete'] or not r['trajectory']:continue
        steps=json.loads(r['trajectory'])
        if len(steps)!=r['stop'] or [x.get('step') for x in steps]!=list(range(1,len(steps)+1)):continue
        total['aligned_complete']+=1
        metadata=meta[iid] if meta else None
        official=metadata['testpaths'] if metadata else None
        maps={}
        def dmap(p):
            if not p:return {}
            if p not in maps:maps[p]=parse_diff(patches[iid,p]['patch'])
            return maps[p]
        def grade(p):return bool(p) and patches[iid,p]['resolved']
        last_fail={};anypairs=set();paired_final=set();pair_records=[];runflags=C();run_event_flags=C()
        local_positive_final=False;local_positive_final_clean=False
        for st in steps:
            kind,obs=command_kind(st);status=receipt(kind,obs)
            if not status:continue
            valid,p=stable(ids,st['step'])
            if not valid:continue
            key=cmd_identity(st)
            # Last observed failure under the same literal tokenized command.
            # Any intervening PASS consumes that failure: do not repeatedly pair.
            if status=='fail':
                last_fail[key]=(st['step'],p);continue
            final=(p==fin and bool(p))
            if final:
                local_positive_final=True
                local_positive_final_clean|=strict_summary(kind,obs)
                flags=scope_flags(st,kind,obs,metadata)
                add_flags(scope_events,flags,ok)
                for name,v in flags.items():runflags[name]|=bool(v)
            if key in last_fail:
                fstep,fp=last_fail.pop(key)
                if not p:continue # final/after patch must be nonempty for comparison
                cat=transition(dmap(fp),dmap(p),official,fp,p)
                pair_records.append((cat,fp,p,fstep,st['step']))
                anypairs.add(cat)
                for d in (transition_events,):
                    d['pairs']+=1;d[cat]+=1
                    d[cat+'_after_benchmark_nonpass']+=not grade(p)
                    d[cat+'_before_benchmark_pass']+=grade(fp)
                    d[cat+'_before_nonpass_after_pass']+=not grade(fp) and grade(p)
                    d[cat+'_before_pass_after_nonpass']+=grade(fp) and not grade(p)
                if final:
                    paired_final.add(cat)
                    transition_events['final_linked_pairs']+=1
                    transition_events['final_'+cat]+=1
                    transition_events['final_'+cat+'_benchmark_nonpass']+=not ok
        if local_positive_final:
            total['final_positive_runs']+=1;total['final_positive_benchmark_nonpass']+=not ok
            total['final_clean_positive_runs']+=local_positive_final_clean
            if metadata:
                add_flags(scope,runflags,ok)
                for name in ('explicit_pytest_file_scope','explicit_gold_test_path_match','explicit_exact_gold_test_path_match','explicit_gold_FTP_selector_match','exact_reported_gold_FTP_PASS','exact_reported_gold_PTP_PASS'):
                    if runflags[name]:trans_by_setting_repo[metadata['repo']][name]+=1;trans_by_setting_repo[metadata['repo']][name+'_nonpass']+=not ok
                trans_by_setting_repo[metadata['repo']]['final_positive_runs']+=1
                trans_by_setting_repo[metadata['repo']]['final_positive_nonpass']+=not ok
            final_flags['with_same_command_fail_predecessor']+=bool(paired_final)
            final_flags['with_same_command_fail_predecessor_benchmark_nonpass']+=bool(paired_final) and not ok
            final_flags['without_same_command_fail_predecessor']+=not paired_final
            final_flags['without_same_command_fail_predecessor_benchmark_nonpass']+=(not paired_final) and not ok
            for k in paired_final:
                final_flags[k]+=1;final_flags[k+'_benchmark_nonpass']+=not ok
        if pair_records:
            transition_runs['any_paired_run']+=1
            for k in anypairs:transition_runs[k]+=1
            cat,a,b,s,t=pair_records[0]
            first_pair[cat]+=1;first_pair[cat+'_after_nonpass']+=not grade(b)
            first_pair['all']+=1;first_pair['all_after_nonpass']+=not grade(b)
            first_pair['before_empty_patch']+=not a
    return {'cohort':dict(total),'scope_final_run_units':dict(scope),'scope_final_event_units':dict(scope_events),
            'same_command_transition_events':dict(transition_events),'same_command_transition_runs':dict(transition_runs),
            'first_transition_per_run':dict(first_pair),'final_run_pair_flags':dict(final_flags),
            'verified_scope_by_repo':{k:dict(v) for k,v in trans_by_setting_repo.items()}}
def selftest():
    a='diff --git a/pkg/a.py b/pkg/a.py\n@@ -1 +1 @@\n-a\n+b\n'
    b='diff --git a/tests/test_a.py b/tests/test_a.py\n@@ -1 +1 @@\n-x\n+y\n'
    assert transition(parse_diff(a),parse_diff(a+b),None,'1','2')=='test_paths_only'
    assert transition({},parse_diff(a),None,None,'2')=='non_test_source_extensions_only'
    assert transition(parse_diff(a),parse_diff(a),None,'1','1')=='identical_recorded_patch'
    assert transition(parse_diff(a),parse_diff(b),None,'1','2')=='mixed_paths'
    assert parse_diff('diff --git a/a.py b/b.py\n') is None
    assert stable([None,None,'a','a'],2)==(True,None)
    assert stable([None,None,'a','a'],3)==(False,None)
    assert stable([None,None,'a','a'],4)==(True,'a')
    s={'tool_calls':[{'arguments':'{"command":"cd /repo && python -m pytest -q tests/test_a.py::test_x"}'}]}
    assert selectors(s)==['tests/test_a.py::test_x']
    assert match_path('tests/test_a.py',{'pkg/tests/test_a.py'})=='pkg/tests/test_a.py'
    assert match_path('test_a.py',{'pkg/tests/test_a.py'}) is None
    assert match_path('tests/test_a.py',{'p/tests/test_a.py','q/tests/test_a.py'}) is None
    m={'testpaths':{'tests/test_a.py'},'ftp':{'tests/test_a.py::test_x'},'ptp':set()}
    f=scope_flags(s,'pytest','tests/test_a.py::test_x PASSED [100%]',m)
    assert f['explicit_gold_FTP_selector_match'] and f['exact_reported_gold_FTP_PASS']
    print('G8 synthetic transition and scope tests PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--selftest',action='store_true');p.add_argument('--input-dir');p.add_argument('--out');a=p.parse_args()
    if a.selftest:selftest()
    if a.input_dir:
        root=Path(a.input_dir);root.mkdir(parents=True,exist_ok=True)
        meta,mh=read_verified(root);out={'version':'G8','source_revision':REV,'verified_revision':VREV,'verified_metadata_hash':mh,'runs':{},'hashes':{}}
        sums=collections.defaultdict(C);vsums=collections.defaultdict(C)
        for name,n in RUNS.items():
            T,th=load_source(root,name,'trajectories');P,ph=load_source(root,name,'patches')
            z=analyze(T,P,n,meta if name in VRUNS else None)
            out['runs'][name]=z;out['hashes'][name]={'trajectories':th,'patches':ph}
            for k,v in z.items():
                if k=='verified_scope_by_repo':continue
                sums[k].update(v)
                if name in VRUNS:vsums[k].update(v)
            print('G8_RUN',name,json.dumps(z,sort_keys=True),flush=True)
            del T,P
        out['all_setting_sums']={k:dict(v) for k,v in sums.items()}
        out['verified_setting_sums']={k:dict(v) for k,v in vsums.items()}
        assert out['all_setting_sums']['cohort']['runs']==2400
        assert out['all_setting_sums']['cohort']['aligned_complete']==2275
        assert out['all_setting_sums']['cohort']['final_positive_runs']==142
        assert out['all_setting_sums']['cohort']['final_positive_benchmark_nonpass']==87
        assert out['verified_setting_sums']['cohort']['runs']==1500
        out['qualification']='Post hoc exploratory secondary analysis. Same tokenized command is not proof of same environment, test selection or test semantics. Test-file designation is an explicit path rule, not semantic verification. Matching a gold test path or identifier does not establish hidden test body identity; absence of a match is not proof of irrelevance. Grade is source-provided, not a new test. Repeated task IDs across settings; sums descriptive only.'
        Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print('G8_TOTAL',json.dumps(out['all_setting_sums'],sort_keys=True),flush=True)
        print('G8_VERIFIED',json.dumps(out['verified_setting_sums'],sort_keys=True),flush=True)
        print('G8_HASHES',json.dumps({'verified':mh,'trajectory_sources':out['hashes']},sort_keys=True),flush=True)
        print('G8 SOURCE-LOCKED SCOPE AND TRANSITION PASS',flush=True)
