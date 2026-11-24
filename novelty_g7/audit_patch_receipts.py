#!/usr/bin/env python3
"""G7: local test markers bound to independently graded recorded patch IDs."""
import argparse, collections, hashlib, json, re, shlex, urllib.request
from pathlib import Path
REPO='musacim/termination-lag-trajectories'
REV='15b2cea1f2bbf8c9945dea1f6311613ccb0b9ebe'
RUNS={'qwen3coder_verified':500,'qwen3coder_multilingual':300,'laguna_verified':500,'laguna_multilingual':300,'seedoss_pro300':300,'qwen3coder_verified_minisweagent':500}
ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')
SHELL=re.compile(r'[\n\r;&|<>\x60$]')
PYTHON=re.compile(r'^python(?:[0-9]+(?:\.[0-9]+)*)?$')
EXIT=re.compile(r'\b(?:exit code|return code|returncode)\s*(?:[:=]|is)?\s*(-?\d+)\b',re.I)
PYTEST_SUMMARY=re.compile(r'^\s*=*\s*(?P<summary>(?:\d+\s+(?:passed|failed|errors?|skipped|deselected|xfailed|xpassed|warnings?)(?:,\s*)?)+)\s+in\s+\d+(?:\.\d+)?s(?:\s+\([^)]*\))?\s*=*\s*$',re.I|re.M)
UN_RUN=re.compile(r'^\s*Ran\s+(\d+)\s+tests?\s+in\s+\d+(?:\.\d+)?s\s*$',re.I|re.M)
UN_OK=re.compile(r'^\s*OK(?:\s+\(([^)]*)\))?\s*$',re.M)
UN_FAIL=re.compile(r'^\s*FAILED(?:\s+\([^)]*\))?\s*$',re.M)
NUM=re.compile(r'(\d+)\s+(passed|failed|errors?|skipped|deselected|xfailed|xpassed|warnings?)',re.I)
def command_kind(step):
    calls=step.get('tool_calls') or [];obs=step.get('observations') or []
    if len(calls)!=1 or len(obs)!=1:return None,None
    call=calls[0]
    if call.get('tool') not in ('terminal','bash'):return None,None
    a=call.get('arguments')
    try:a=json.loads(a) if isinstance(a,str) else a
    except (ValueError,TypeError):return None,None
    if not isinstance(a,dict):return None,None
    cmd=a.get('command')
    if not isinstance(cmd,str):return None,None
    cmd=cmd.strip()
    if cmd.startswith('cd ') and '&&' in cmd:
        prefix,cmd=cmd.split('&&',1)
        if SHELL.search(prefix.strip()):return None,None
        cmd=cmd.strip()
    if SHELL.search(cmd):return None,None
    try:tokens=shlex.split(cmd)
    except ValueError:return None,None
    if not tokens:return None,None
    if tokens[0] in ('pytest','py.test'):kind='pytest'
    elif len(tokens)>=3 and PYTHON.fullmatch(tokens[0]) and tokens[1]=='-m' and tokens[2] in ('pytest','unittest'):kind=tokens[2]
    else:return None,None
    o=obs[0]
    if not isinstance(o,str):return kind,None
    return kind,ANSI.sub('',o).replace('\r\n','\n').replace('\r','\n')
def receipt(kind,o):
    if not kind or o is None:return None
    codes=[int(c) for c in EXIT.findall(o)];nonzero=any(c!=0 for c in codes)
    if kind=='pytest':
        m=list(PYTEST_SUMMARY.finditer(o))
        if len(m)!=1:return None
        counts=collections.Counter()
        for num,label in NUM.findall(m[0]['summary']):counts[label.lower()]+=int(num)
        bad=counts['failed']+counts['error']+counts['errors']+counts['xpassed']
        if counts['passed']>0 and not bad and not nonzero:return 'pass'
        if counts['failed']+counts['error']+counts['errors']>0:return 'fail'
    if kind=='unittest':
        n=list(UN_RUN.finditer(o));good=list(UN_OK.finditer(o));bad=list(UN_FAIL.finditer(o))
        if len(n)!=1:return None
        if len(good)==1 and not bad and not nonzero:
            if int(n[0][1])>0 and not good[0][1]:return 'pass'
        if len(bad)==1 and not good:return 'fail'
    return None
def state_at(ids,s):
    if not (2<=s<=len(ids)):return None
    p=ids[s-1]
    return p if p and p==ids[s-2] else None
def stable3(ids,s):
    p=state_at(ids,s)
    return p if p and s<len(ids) and ids[s]==p else None
def summarize(trajectories,patches,expected):
    patch={}
    for q in patches:
        k=(q['instance_id'],q['patch_id'])
        assert k not in patch and isinstance(q['resolved'],bool)
        patch[k]=q['resolved']
    assert len(trajectories)==expected
    assert len({q['instance_id'] for q in trajectories})==expected
    count=collections.Counter();receipt_counts=collections.Counter();tables=collections.defaultdict(collections.Counter)
    for row in trajectories:
        iid=row['instance_id'];ids=row['step_patch_ids'] or [];final=row['final_patch_id']
        assert all((iid,p) in patch for p in ids if p)
        assert not final or (iid,final) in patch
        assert (bool(final) and patch[(iid,final)])==row['resolved']
        correct=[s for s,p in enumerate(ids,1) if p and patch[(iid,p)]]
        assert (min(correct) if correct else None)==row['first_correct']
        count['all']+=1;count['all_final_resolved']+=row['resolved']
        if not row['trajectory_complete'] or not row['trajectory']:continue
        steps=json.loads(row['trajectory'])
        if not isinstance(steps,list) or len(steps)!=row['stop'] or [q.get('step') for q in steps]!=list(range(1,len(steps)+1)):
            count['complete_metadata_but_step_alignment_failed']+=1;continue
        count['aligned_complete']+=1;count['aligned_complete_final_resolved']+=row['resolved']
        pos=[];neg=[];triple=[];narrow_pos=[];observed_pos=0;observed_neg=0
        for st in steps:
            kind,o=command_kind(st)
            if kind:receipt_counts['eligible_single_test_commands']+=1
            x=receipt(kind,o)
            if not x:continue
            s=st['step'];p=state_at(ids,s);receipt_counts[x+'_marker']+=1
            if x=='pass':observed_pos+=1
            if x=='fail':observed_neg+=1
            if not p:
                receipt_counts[x+'_no_stable_nonempty_patch']+=1;continue
            ok=patch[(iid,p)];q=(s,p,ok)
            (pos if x=='pass' else neg).append(q)
            receipt_counts[x+'_stable_patch']+=1;receipt_counts[x+'_stable_benchmark_pass']+=ok
            if x=='pass':
                if stable3(ids,s):triple.append(q)
                if EXIT.findall(o) and all(int(z)==0 for z in EXIT.findall(o)):narrow_pos.append(q)
        count['any_pass_marker']+=bool(observed_pos);count['any_fail_marker']+=bool(observed_neg)
        count['any_patch_linked_pass']+=bool(pos);count['any_patch_linked_fail']+=bool(neg)
        count['any_triple_linked_pass']+=bool(triple);count['any_explicit_zero_exit_linked_pass']+=bool(narrow_pos)
        for label,records in [('first_pass',pos),('first_fail',neg),('first_triple_pass',triple),('first_zero_exit_pass',narrow_pos),('last_pass',pos[-1:])]:
            if not records:continue
            s,p,ok=records[0];t=tables[label]
            t['n']+=1;t['benchmark_pass_at_receipt']+=ok;t['final_resolved']+=row['resolved']
            t['receipt_pass_final_fail']+=ok and not row['resolved'];t['receipt_fail_final_pass']+=not ok and row['resolved']
            t['same_final_patch_id']+=p==final;t['same_final_patch_benchmark_fail']+=p==final and not ok
            t['changed_final_patch_id']+=p!=final;t['changed_final_patch_benchmark_fail']+=p!=final and not row['resolved']
            t['steps_after_receipt']+=row['stop']-s
        final_matches=[q for q in pos if q[1]==final]
        if final_matches:
            count['any_pass_linked_to_final_patch']+=1
            count['final_patch_linked_pass_benchmark_fail']+=not row['resolved']
        if pos and not final_matches:
            count['pass_linked_only_to_nonfinal_patches']+=1
            count['nonfinal_only_pass_final_benchmark_fail']+=not row['resolved']
        if any(p==final for s,p,ok in triple):
            count['triple_pass_linked_to_final_patch']+=1
            count['triple_final_patch_linked_pass_benchmark_fail']+=not row['resolved']
        if any(p==final for s,p,ok in narrow_pos):
            count['zero_exit_pass_linked_to_final_patch']+=1
            count['zero_exit_final_patch_linked_pass_benchmark_fail']+=not row['resolved']
    return {'cohort':dict(count),'receipt_events':dict(receipt_counts),'tables':{k:dict(v) for k,v in tables.items()},'patch_rows':len(patch)}
def selftest():
    assert receipt('pytest','===== 3 passed, 1 skipped in 0.21s =====')=='pass'
    assert receipt('pytest','=== 2 failed, 3 passed in 1.0s ===')=='fail'
    assert receipt('pytest','3 passed in 0.20s\nExit code: 1') is None
    assert receipt('pytest','0 passed in 0.0s') is None
    assert receipt('pytest','3 passed') is None
    assert receipt('unittest','Ran 2 tests in 0.02s\n\nOK')=='pass'
    assert receipt('unittest','Ran 2 tests in 0.02s\n\nOK (skipped=2)') is None
    assert receipt('unittest','Ran 2 tests in 0.02s\n\nFAILED (failures=1)')=='fail'
    assert state_at([None,'a','a','b'],3)=='a'
    assert stable3([None,'a','a','b'],3) is None
    assert stable3(['a','a','a'],2)=='a'
    s={'tool_calls':[{'tool':'terminal','arguments':'{"command":"cd /repo && python -m pytest tests"}'}],'observations':['3 passed in 0.1s']}
    assert command_kind(s)[0]=='pytest'
    s['tool_calls'][0]['arguments']='{"command":"pytest; echo OK"}'
    assert command_kind(s)==(None,None)
    print('G7 synthetic receipt and patch-alignment checks PASS')
def fetch(root,run,kind):
    import pyarrow.parquet as pq
    path=root/f'{run}_{kind}.parquet'
    url=f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/data/{run}/{kind}.parquet'
    if not path.exists():
        req=urllib.request.Request(url,headers={'User-Agent':'99llm-source-audit/1.0'})
        with urllib.request.urlopen(req,timeout=120) as response,path.open('wb') as out:
            while True:
                b=response.read(1024*1024)
                if not b:break
                out.write(b)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    cols=['instance_id','patch_id','resolved'] if kind=='patches' else ['instance_id','resolved','first_correct','stop','trajectory_complete','trajectory','step_patch_ids','final_patch_id']
    return pq.read_table(path,columns=cols).to_pylist(),{'sha256':digest,'bytes':path.stat().st_size,'url':url}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--selftest',action='store_true');a.add_argument('--input-dir');a.add_argument('--out');a.add_argument('--runs',nargs='*',choices=list(RUNS));o=a.parse_args()
    if o.selftest:selftest()
    if o.input_dir:
        root=Path(o.input_dir);root.mkdir(parents=True,exist_ok=True)
        selected=o.runs or list(RUNS);out={'dataset':REPO,'revision':REV,'runs':{},'source_hashes':{}}
        pooled=collections.defaultdict(collections.Counter);ct=collections.Counter();events=collections.Counter()
        for run in selected:
            T,th=fetch(root,run,'trajectories');P,ph=fetch(root,run,'patches')
            z=summarize(T,P,RUNS[run]);out['runs'][run]=z;out['source_hashes'][run]={'trajectories':th,'patches':ph}
            ct.update(z['cohort']);events.update(z['receipt_events'])
            for k,v in z['tables'].items():pooled[k].update(v)
            print('G7_RUN',run,json.dumps(z,sort_keys=True),flush=True)
            del T,P
        out['run_level_sums']={'cohort':dict(ct),'receipt_events':dict(events),'tables':{k:dict(v) for k,v in pooled.items()}}
        out['qualification']='Benchmark grades are original offline test outcomes, not newly executed tests or objective truth. Text markers are conservative recorded receipts, not proof of test execution. Bracketed identical nonempty patch IDs bind a receipt to the same recorded diff, not all environment state. Six settings can repeat task IDs; summed counts are run-level descriptive, not independent tasks. Retrospective first-receipt patch selection is not a causal rollout.'
        Path(o.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print('G7_TOTAL',json.dumps(out['run_level_sums'],sort_keys=True),flush=True)
        print('G7 SOURCE-REVISION AND FULL-COHORT CHECK PASS',flush=True)
