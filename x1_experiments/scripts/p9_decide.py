#!/usr/bin/env python3
"""X1 P9: produce source-time-locked, oracle-blind ACCEPT/HOLD decisions.
This is a prospective protocol implementation, NOT evidence of efficacy.
Standard library only. All inputs must exclude future oracle results.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

POLICY_VERSION = 'X1-P9-alpha-1-20261116'
POLICIES = ['self_report', 'local_pass', 'source_linked']
HEX40 = re.compile(r'^[a-f0-9]{40}$')


def iso(s):
    if not isinstance(s, str) or not s.endswith('Z'):
        raise ValueError('Timestamps must be UTC ISO8601 ending in Z')
    v = datetime.fromisoformat(s[:-1] + '+00:00')
    if v.tzinfo is None: raise ValueError('Naive timestamp')
    return v


def read_jsonl(file):
    txt = Path(file).read_text(encoding='utf8')
    return [json.loads(s) for s in txt.splitlines() if s.strip()]


def is_valid_receipt(x, rec, t):
    # Used only for gate; never evaluates future oracle, held-out tests or hidden patches.
    if not isinstance(x, dict): raise ValueError('Invalid receipt')
    if x.get('kind') != 'local_test': raise ValueError('Only visible local tests permitted as gate features')
    complete = iso(x['completed_at'])
    if complete > t: raise ValueError('Future local evidence leakage')
    if x.get('source_url','') == '': raise ValueError('Local receipt needs provenance URL/path')
    if not isinstance(x.get('test_count'), int) or isinstance(x.get('test_count'),bool):
        raise ValueError('test_count must be an integer')
    if x['test_count'] < 0: raise ValueError('Negative test count')
    if x.get('status') not in ['success','failure','skipped','error']:
        raise ValueError('Unexpected receipt status')
    if 'test_scope_prespecified' not in x or type(x['test_scope_prespecified']) != bool:
        raise ValueError('test_scope_prespecified must be boolean')
    sha = x.get('head_sha', '')
    if not HEX40.fullmatch(sha): raise ValueError('Invalid receipt SHA')
    return x['status'] == 'success' and x['test_count'] > 0


def decide_one(rec):
    forbidden = {'oracle','oracle_status','oracle_result','future_ci','future_test','heldout_result','label','resolved','task_outcome','test_patch','FAIL_TO_PASS','PASS_TO_PASS'}
    if any(k in rec for k in forbidden):
        raise ValueError('Decision file contains oracle/outcome field(s)')
    required = ['episode_id','task_family','repo','head_sha','t_decision',
                'patch_applied','agent_claimed_fixed','target_agent_is_commit_author',
                'unrelated_intervening_edit','receipts']
    for k in required:
        if k not in rec: raise ValueError('Missing '+k)
    sha = rec['head_sha']
    if not isinstance(sha,str) or not HEX40.fullmatch(sha):
        raise ValueError('Head SHA must be 40 lowercase hex characters')
    t=iso(rec['t_decision'])
    if not isinstance(rec['receipts'], list): raise ValueError('receipts must be a list')
    for k in ['patch_applied','agent_claimed_fixed','target_agent_is_commit_author','unrelated_intervening_edit']:
        if type(rec[k]) != bool: raise ValueError(k+' must be boolean')
    rows=[(x,is_valid_receipt(x,rec,t)) for x in rec['receipts']]
    any_local=any(p for x,p in rows)
    exact_scoped=any(p and x['head_sha']==sha and x['test_scope_prespecified'] for x,p in rows)
    patch=rec['patch_applied']
    decision={
        'self_report':'ACCEPT' if patch and rec['agent_claimed_fixed'] else 'HOLD',
        'local_pass':'ACCEPT' if patch and any_local else 'HOLD',
        'source_linked':'ACCEPT' if patch and exact_scoped and rec['target_agent_is_commit_author'] and not rec['unrelated_intervening_edit'] else 'HOLD'
    }
    return { 'episode_id':rec['episode_id'],'task_family':rec['task_family'],
      'repo':rec['repo'],'head_sha':sha,'t_decision':rec['t_decision'],
      'policy_version':POLICY_VERSION,'decisions':decision,
      'decision_features':{'patch_applied':patch,'has_local_success_receipt':any_local,
      'has_exact_scoped_local_receipt':exact_scoped},
    }


def canonical(data):return (json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf8')

def run(inp,out):
    rows=read_jsonl(inp)
    if not rows: raise ValueError('Empty decision records')
    ids=[x.get('episode_id') for x in rows]
    if any(not isinstance(i,str) or not i.strip() for i in ids) or len(ids)!=len(set(ids)):
        raise ValueError('Invalid or duplicate episode ID')
    decisions=[decide_one(x) for x in rows]
    data=b''.join(canonical(d) for d in sorted(decisions,key=lambda x:x['episode_id']))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    de=out/'P9_DECISIONS_SEALED.jsonl'
    if de.exists() or (out/'P9_DECISION_SEAL.json').exists():
        raise ValueError('Output already sealed; refuse overwrite')
    de.write_bytes(data)
    script_path=Path(__file__)
    seal={'policy_version':POLICY_VERSION,'episode_count':len(decisions),
      'input_sha256':hashlib.sha256(Path(inp).read_bytes()).hexdigest(),
      'script_sha256':hashlib.sha256(script_path.read_bytes()).hexdigest(),
      'decisions_sha256':hashlib.sha256(data).hexdigest(),
      'files':{'decisions':'P9_DECISIONS_SEALED.jsonl'},
      'note':'No future oracle accessed. Keep independent test labels separate until sealed.'}
    (out/'P9_DECISION_SEAL.json').write_bytes(canonical(seal))
    print(json.dumps({'sealed':True,'episodes':len(decisions),'sha256':seal['decisions_sha256']},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True)
    args=p.parse_args()
    try:run(args.input,args.out)
    except (ValueError,KeyError,TypeError) as exc: print('BLOCK:',exc,file=sys.stderr);sys.exit(2)
