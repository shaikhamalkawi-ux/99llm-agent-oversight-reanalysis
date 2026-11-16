#!/usr/bin/env python3
"""X1 P9 post-seal oracle evaluation; unknown or compromised labels remain HOLD.
Standard library only. Never confuses code-unit tests with task-oracle execution.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from p9_decide import read_jsonl, POLICIES, POLICY_VERSION, iso


def oracle_label(dec,oracle):
    # Source independent of gate's local-test features and immutable before observation.
    if oracle.get('episode_id')!=dec['episode_id'] or oracle.get('head_sha')!=dec['head_sha']:
        return None,'mismatched_episode_or_head_sha'
    if oracle.get('oracle_type') not in ['heldout_harness','immutable_independent_ci']:
        return None,'oracle_type_not_admitted'
    if not oracle.get('oracle_test_manifest_frozen_before_decision'):
        return None,'verifier_was_not_frozen'
    if not oracle.get('oracle_independent_of_visible_receipts'):
        return None,'same_tests_as_decision_receipts'
    if not oracle.get('oracle_unmodified_by_agent'):
        return None,'oracle_agent_modification_not_ruled_out'
    if not oracle.get('source_url') or not oracle.get('oracle_code_sha256'):
        return None,'missing_oracle_provenance'
    try:
        if iso(oracle['started_at'])<=iso(dec['t_decision']):
            return None,'oracle_not_strictly_after_decision'
    except (ValueError,TypeError,KeyError):return None,'invalid_time'
    if oracle.get('status') not in ['complete','error','not_run']:
        return None,'invalid_oracle_status'
    if oracle['status']!='complete':return None,'oracle_not_completed'
    f2p=oracle.get('f2p_total');passed=oracle.get('f2p_passed');reg=oracle.get('p2p_failed');cnt=oracle.get('tests_executed')
    if any(type(v)!=int for v in [f2p,passed,reg,cnt]):return None,'invalid_oracle_counts'
    if f2p<=0 or passed<0 or passed>f2p or reg<0 or cnt<=0:return None,'invalid_oracle_counts'
    return int(passed==f2p and reg==0),'admitted'


def run(path,oracle_file,out):
    path=Path(path);data=(path/'P9_DECISIONS_SEALED.jsonl').read_bytes()
    seal=json.loads((path/'P9_DECISION_SEAL.json').read_text())
    if hashlib.sha256(data).hexdigest()!=seal['decisions_sha256'] or seal['policy_version']!=POLICY_VERSION:
        raise ValueError('Seal mismatch or policy version changed')
    decisions=read_jsonl(path/'P9_DECISIONS_SEALED.jsonl')
    oracles=read_jsonl(oracle_file)
    omap={}
    for o in oracles:
        key=o.get('episode_id')
        if key in omap: raise ValueError('Duplicate oracle row')
        omap[key]=o
    by={p:{'all_accept':0,'all_hold':0,'evaluated_accept':0,'evaluated_hold':0,'false_accept':0,'unnecessary_hold':0} for p in POLICIES}
    admitted=0;pass_n=0;failed_n=0;reasons={};details=[]
    for d in decisions:
        o=omap.get(d['episode_id'])
        outcome,reason=oracle_label(d,o) if o else (None,'missing_oracle_record')
        reasons[reason]=reasons.get(reason,0)+1
        if outcome is not None:
            admitted+=1;pass_n+=outcome;failed_n+=1-outcome
        for p in POLICIES:
            action=d['decisions'][p]
            stat=by[p];stat['all_accept' if action=='ACCEPT' else 'all_hold']+=1
            if outcome is not None:
                stat['evaluated_accept' if action=='ACCEPT' else 'evaluated_hold']+=1
                stat['false_accept']+=int(action=='ACCEPT' and outcome==0)
                stat['unnecessary_hold']+=int(action=='HOLD' and outcome==1)
        details.append({'episode_id':d['episode_id'],'admitted':outcome is not None,'reason':reason,'outcome':outcome})
    for stat in by.values():
        n=stat['evaluated_accept'];stat['false_accept_among_accepted']=stat['false_accept']/n if n>0 else None
        stat['unnecessary_hold_among_true_pass']=stat['unnecessary_hold']/pass_n if pass_n>0 else None
    result={ 'status':'MEASURED_DESCRIPTIVE_NOT_CAUSAL' if admitted else 'HOLD_NO_ADMISSIBLE_ORACLE',
      'policy_version':POLICY_VERSION,'total_decisions':len(decisions),'oracle_admitted':admitted,
      'oracle_unadmitted':len(decisions)-admitted,'oracle_pass':pass_n,'oracle_fail':failed_n,
      'nonadmission_reasons':reasons,'policies':by,
      'note':'Associational paired policy comparison on evaluated episodes only. Not causal efficacy; missing oracles are NOT counted as failure.'}
    Path(out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sealed-dir',required=True);p.add_argument('--oracle',required=True);p.add_argument('--out',required=True)
    v=p.parse_args()
    try:print(json.dumps(run(v.sealed_dir,v.oracle,v.out),indent=2))
    except (ValueError,KeyError,TypeError,FileNotFoundError) as e:print('BLOCK:',str(e),file=sys.stderr);sys.exit(2)
