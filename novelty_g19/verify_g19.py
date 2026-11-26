#!/usr/bin/env python3
"""Verify G19 aggregate record against frozen G10 input; no raw data or benchmark execution."""
import argparse, collections,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def key(r):return (r['setting'],r['source_verdict'],r['rank'])
NAMES=('base_local','base_reference','candidate_local','candidate_reference','gold_reference')
def classify(x,n):
    if x.get('status')!='EXECUTED' or x.get('pytest_verdict') not in ('PASS','FAIL'):return 'HOLD'
    assert x['exact_node_identity'] and x['required_ids_sha256']==x['collected_ids_sha256']
    assert x['required_collected']==x['all_collected']==n and x['unexpected_collected']==x['required_missing']==x['collection_errors']==x['held']==0
    assert x['passed']+x['failed']==n
    v=x['pytest_verdict']
    assert (v=='PASS' and x['pytest_returncode']==0 and x['failed']==0) or (v=='FAIL' and x['pytest_returncode']==1 and x['failed']>=1)
    return v
def invariant(a,b):return bool(a.get('non_test_tree_digest')) and a.get('non_test_tree_digest')==b.get('non_test_tree_digest')
def main():
    old=json.loads((ROOT/'novelty_g10/G10_full_cohort_summary.json').read_text())
    new=json.loads((ROOT/'novelty_g19/G19_verified_summary.json').read_text())
    p={key(r):r for r in old['rows']}; t={key(r):r for r in old['table']}
    assert len(p)==len(t)==len(new['rows'])==len({key(r) for r in new['rows']})==13
    assert len({r['task_id_sha256'] for r in new['rows']})==13
    counts=collections.Counter();strata=collections.defaultdict(collections.Counter); changes=[]
    exact=flip=disc=controls=witness=det=agree=0
    for r in new['rows']:
        k=key(r); o=p[k]; tr=t[k]; c=r['cells']
        for fld in ('task_id_sha256','image_id','candidate_patch_sha256','reference_test_patch_sha256','gold_patch_sha256','ftp_count'):assert r[fld]==o[fld]
        assert r['selection']['source_hashes']==o['selection']['source_hashes']
        v=tuple(classify(c[n],r['ftp_count']) for n in NAMES)
        bi=invariant(c['base_local'],c['base_reference']); ci=invariant(c['candidate_local'],c['candidate_reference'])
        flip+=bi and v[:2]==('PASS','FAIL')
        controls+=v[1]=='FAIL' and v[4]=='PASS'
        disc+=bi and ci and v==('PASS','FAIL','PASS','PASS','PASS')
        witness+=bi and ci and v==('PASS','FAIL','PASS','FAIL','PASS')
        pair='/'.join(v[2:4]) if ci else 'HOLD/HOLD'; counts[pair]+=1;strata[r['source_verdict']][pair]+=1
        det+=ci and 'HOLD' not in v[2:4]
        if v==tuple(tr[n] for n in NAMES) and bi==tr['base_tree_invariant'] and ci==tr['candidate_tree_invariant']:agree+=1
        else:changes.append('/'.join(map(str,k)))
        for n,s in zip(NAMES,v):
            if s!='HOLD':exact+=1;assert c[n]['non_test_tree_digest']==o['cells'][n]['non_test_tree_digest']
    out={'candidate_pairs':dict(counts),'candidate_pairs_by_source':{k:dict(v) for k,v in strata.items()},'determinate_cells':exact,'all_cells':65,'determinate_candidate_pairs':det,'base_version_reversals':flip,'base_gold_controls':controls,'discrimination_witnesses':disc,'controlled_pass_fail_witnesses':witness,'complete_task_cell_and_tree_agreement':agree,'changed_tasks':changes}
    assert out==new['aggregate'],(out,new['aggregate'])
    print('G19 AGGREGATE EXACT NODE REPLAY CHECK PASS',json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
