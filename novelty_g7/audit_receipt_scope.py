#!/usr/bin/env python3
"""G7 sensitivity: repeated local markers and within-patch discordance.
Post-primary exploratory challenge; no transcript text or commands exported.
"""
import argparse,json,collections,re,shlex
from pathlib import Path
from audit_patch_receipts import (RUNS,REPO,REV,fetch,command_kind,receipt,state_at,stable3,PYTEST_SUMMARY,NUM,EXIT,exit_codes)
C=collections.Counter
def cmd_identity(step):
    x=step['tool_calls'][0]['arguments']
    a=json.loads(x) if isinstance(x,str) else x
    # Literal tokenized command including explicit cwd. Different command strings
    # do not imply distinct test sets; same strings need not run the same tests.
    return tuple(shlex.split(a['command']))
def strict_summary(kind,obs):
    if receipt(kind,obs)!='pass':return False
    if kind=='unittest':return True
    m=list(PYTEST_SUMMARY.finditer(obs))
    if len(m)!=1:return False
    n=C()
    for k,v in NUM.findall(m[0]['summary']):n[v.lower()]+=int(k)
    return not any(n[x] for x in ('skipped','deselected','xfailed','xpassed'))
def run(T,P,n):
    patch={(p['instance_id'],p['patch_id']):p['resolved'] for p in P}
    assert len(patch)==len(P) and len(T)==n and len({q['instance_id'] for q in T})==n
    totals=C();checks=C();scope=C();patchscope=C()
    for row in T:
        iid=row['instance_id'];ids=row['step_patch_ids'] or [];final=row['final_patch_id']
        assert all((iid,p) in patch for p in ids if p)
        assert (bool(final) and patch[(iid,final)])==row['resolved']
        totals['all']+=1
        if not row['trajectory_complete'] or not row['trajectory']:continue
        steps=json.loads(row['trajectory'])
        if len(steps)!=row['stop'] or [q.get('step') for q in steps]!=list(range(1,len(steps)+1)):continue
        totals['aligned_complete']+=1
        linked=collections.defaultdict(list)
        for s in steps:
            kind,o=command_kind(s);r=receipt(kind,o)
            if not r:continue
            p=state_at(ids,s['step'])
            if not p:continue
            cid=cmd_identity(s)
            triple=bool(stable3(ids,s['step']))
            clean=strict_summary(kind,o)
            linked[p].append((r,cid,triple,clean))
            checks['linked_'+r]+=1
            if exit_codes(o):checks['parsed_exit_mentioned_'+r]+=1
            # Observe marker syntax only; no claims about missing process status.
            for label,pattern in [('exit_code_underscore',r'\bexit_code\b'),('exitcode',r'\bexitcode\b'),('exited_with_code',r'\bexited with (?:status |code )?\d+'),('xml_exit_code',r'<exit_code>'),('xml_returncode',r'<returncode>')]:
                if re.search(pattern,o,re.I):checks[label+'_'+r]+=1
        def flags(records):
            pos=[x for x in records if x[0]=='pass'];neg=[x for x in records if x[0]=='fail']
            pc={x[1] for x in pos};nc={x[1] for x in neg}
            pt=[x for x in pos if x[2]];nt=[x for x in neg if x[2]]
            clean=[x for x in pos if x[3]]
            return {'pass':bool(pos),'fail':bool(neg),'both':bool(pos and neg),
                    'both_same_literal_command':bool(pc&nc),
                    'both_distinct_literal_commands':any(a!=b for a in pc for b in nc),
                    'two_pass_events':len(pos)>=2,'two_distinct_pass_commands':len(pc)>=2,
                    'three_distinct_pass_commands':len(pc)>=3,
                    'two_triple_pass_events':len(pt)>=2,'two_distinct_triple_pass_commands':len({x[1] for x in pt})>=2,
                    'both_triple':bool(pt and nt),'clean_summary_pass':bool(clean),
                    'two_distinct_clean_pass_commands':len({x[1] for x in clean})>=2}
        any_flags=C()
        for p,rs in linked.items():
            ok=patch[(iid,p)]
            for name,on in flags(rs).items():
                if on:
                    patchscope[name+'_patches']+=1;patchscope[name+'_benchmark_fail_patches']+=not ok
                    any_flags[name]=1
        for name,on in any_flags.items():totals['any_patch_'+name+'_runs']+=on
        if final and final in linked:
            for name,on in flags(linked[final]).items():
                if on:
                    scope[name+'_runs']+=1;scope[name+'_benchmark_fail_runs']+=not row['resolved']
    return {'cohort':dict(totals),'receipt_syntax':dict(checks),'all_linked_patch_units':dict(patchscope),'final_patch_run_units':dict(scope)}
def selftest():
    assert strict_summary('pytest','2 passed in 0.1s')
    assert not strict_summary('pytest','2 passed, 1 skipped in 0.1s')
    assert not strict_summary('pytest','2 passed, 1 deselected in 0.1s')
    assert strict_summary('unittest','Ran 2 tests in 0.01s\n\nOK')
    s={'tool_calls':[{'arguments':'{"command":"python -m pytest tests/a.py"}'}]}
    assert cmd_identity(s)==('python','-m','pytest','tests/a.py')
    print('G7 scope synthetic checks PASS')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--selftest',action='store_true');a.add_argument('--input-dir');a.add_argument('--out');o=a.parse_args()
    if o.selftest:selftest()
    if o.input_dir:
        root=Path(o.input_dir);out={'repo':REPO,'revision':REV,'runs':{},'source_hashes':{}}
        allc=collections.defaultdict(C)
        for name,n in RUNS.items():
            T,th=fetch(root,name,'trajectories');P,ph=fetch(root,name,'patches')
            z=run(T,P,n);out['runs'][name]=z;out['source_hashes'][name]={'trajectories':th,'patches':ph}
            for k,v in z.items():allc[k].update(v)
            print('G7_SCOPE_RUN',name,json.dumps(z,sort_keys=True),flush=True)
            del T,P
        out['totals']={k:dict(v) for k,v in allc.items()}
        out['qualification']='Exploratory after initial G7 results. Different command identities are not independent or disjoint test suites; same command can differ in environment or selection. Recorded local text markers are not independently rerun tests. Benchmark grades are source-provided. Patch IDs do not capture all runtime state. Settings repeat task IDs; counts are descriptive run or setting-task-patch units.'
        assert out['totals']['cohort']['all']==2400 and out['totals']['cohort']['aligned_complete']==2275
        assert out['totals']['final_patch_run_units']['pass_runs']<=142
        assert out['totals']['final_patch_run_units']['pass_benchmark_fail_runs']<=87
        Path(o.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print('G7_SCOPE_TOTAL',json.dumps(out['totals'],sort_keys=True),flush=True)
        print('G7_SOURCE_HASHES',json.dumps(out['source_hashes'],sort_keys=True),flush=True)
        print('G7 WITHIN-PATCH SCOPE SOURCE-LOCKED PASS')
