#!/usr/bin/env python3
"""G6: original validation-stage scope and within-session resolver transport.
Aggregate only; no reannotation, endpoint adjudication or original row export.
"""
import argparse, hashlib, json, sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'novelty_g5'))
from verify_release_context import read, sk, ek, unique, features, SCALE, DEN, L, U, W

VPIN=('cf11774099860ae1c36fb2eebc5dab58aead3da0',16387277)
STRICT={'invisible_agent_action','session_terminated_before_completion'}
BROAD=STRICT|{'invisible_project_context','truncation'}
def read_validation(p):
    b=Path(p).read_bytes()
    blob=hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
    assert (blob,len(b))==VPIN
    return json.loads(b),{'sha256':hashlib.sha256(b).hexdigest(),'blob':blob,'bytes':len(b)}
def add(d, rows):
    d['sessions']+=1
    for r,w in rows:
        d['episodes']+=1
        if r['resolution_status']=='RS2':
            d['unknowns']+=1;d['unknown_weight_units']+=w
        else:
            d['RS1']+=1
            d['RS1_signed_units']+=w if r['damage_severity']=='DS2' else -w
            if r['resolver']=='RV2':d['RV2_signed_units']+=w if r['damage_severity']=='DS2' else -w
def pair_summary(rs):
    c=Counter()
    for a,b in combinations(rs,2):
        c['pairs']+=1
        c['cross_severity']+=a['damage_severity']!=b['damage_severity']
        c['distinct_resolver']+=a['resolver']!=b['resolver']
        c['RV2_vs_other']+=(a['resolver']=='RV2')!=(b['resolver']=='RV2')
    return c
def analyze(a,r,v):
    A,R,V=unique(a,ek),unique(r,ek),unique(v,ek)
    assert R.keys()<=A.keys()
    assert all(all(q[k]==x for k,x in A[i].items()) for i,q in R.items())
    assert set(q['label'] for q in v)=={'VALID','INVALID'}
    valid={k for k,q in V.items() if q['label']=='VALID'}
    assert A.keys()<=valid,'Annotated row absent from source VALID gate'
    shared=Counter()
    for i,q in A.items():
        z=V[i]
        for k in set(q)&set(z):
            assert q[k]==z[k],f'Shared annotation/validation metadata mismatch: {k}'
            shared[k]+=1
    reasons=Counter(q['invalid_category'] for q in v if q['label']=='INVALID')
    invalid=defaultdict(list)
    for q in v:
        if q['label']=='INVALID':invalid[sk(q)].append(q['invalid_category'])
    grouped=defaultdict(list)
    for q in a:
        if q['damage_severity'] in ('DS1','DS2'):grouped[sk(q)].append(q)
    counts=defaultdict(Counter);strata=defaultdict(Counter)
    resolver=Counter();transport=Counter();transport_strata=defaultdict(Counter)
    packet=Counter();pstrata=defaultdict(Counter);gate=Counter()
    for s,qs in grouped.items():
        ns=Counter(q['damage_severity'] for q in qs)
        if len(ns)!=2:continue
        assert all(SCALE%n==0 for n in ns.values())
        rows=[(q,SCALE//ns[q['damage_severity']]) for q in qs]
        assert all(q['resolution_status'] in ('RS1','RS2') for q in qs)
        known=[q for q in qs if q['resolution_status']=='RS1']
        assert all(q['resolver'] in ('RV1','RV2','RV3') for q in known)
        assert all(q['resolver'] is None for q in qs if q['resolution_status']=='RS2')
        unknown=[(q,w) for q,w in rows if q['resolution_status']=='RS2']
        ispub=[ek(q) in R for q in qs];assert all(ispub) or not any(ispub)
        rel='released' if all(ispub) else 'absent'
        flags={'all':True,'any_rejection':s in invalid,
               'strict_endpoint_visibility_rejection':bool(set(invalid[s])&STRICT),
               'broad_evidence_rejection':bool(set(invalid[s])&BROAD),
               'invisible_agent_action': 'invisible_agent_action' in invalid[s],
               'session_terminated_before_completion':'session_terminated_before_completion' in invalid[s]}
        for k,on in flags.items():
            if on:
                add(counts[k],rows);add(strata[(s[0],rel,k)],rows)
                counts[k]['invalid_records']+=len(invalid[s])
                counts[k]['strict_rejected_records']+=sum(x in STRICT for x in invalid[s])
                counts[k]['RS1_and_RS2_sessions']+=bool(known and unknown)
                counts[k]['RS1_sessions']+=bool(known)
        strict=flags['strict_endpoint_visibility_rejection']
        if strict:
            gate['strict_and_RS1_sessions']+=bool(known)
            gate['strict_and_RS2_sessions']+=bool(unknown)
            gate['strict_and_both_sessions']+=bool(known and unknown)
        # Known-resolver labels are episode-level, not transportable by session identity.
        kinds={q['resolver']=='RV2' for q in known}
        resolver['sessions_with_RS1']+=bool(known)
        resolver['sessions_with_two_or_more_RS1']+=len(known)>=2
        resolver['sessions_with_RV2_and_other']+=len(kinds)==2
        resolver.update(pair_summary(known))
        for q,w in unknown:
            g=transport_strata[(s[0],rel,q['damage_severity'])]
            for d in [g,transport]:
                d['unknowns']+=1;d['weight_units']+=w
                for name,val in [('any_RS1_sibling',bool(known)),('RV2_sibling',True in kinds),
                                 ('other_resolver_sibling',False in kinds),('both_resolver_types',len(kinds)==2)]:
                    if val:d[name]+=1;d[name+'_weight_units']+=w
        # Full literal nonempty quote sets, not merely a shared turn or one quote.
        if rel=='released':
            F={ek(q):features(R[ek(q)],Counter()) for q in qs}
            for x,y in combinations(qs,2):
                f,g=F[ek(x)],F[ek(y)]
                status_diff=x['resolution_status']!=y['resolution_status']
                rv_diff=x['resolution_status']==y['resolution_status']=='RS1' and ((x['resolver']=='RV2')!=(y['resolver']=='RV2'))
                exact=f['literal_quotes']==g['literal_quotes']
                last={z for z in f['literal_quotes'] if z[0]==f['last']} & {z for z in g['literal_quotes'] if z[0]==g['last']}
                shared_quote=bool(f['literal_quotes']&g['literal_quotes'])
                for d in [packet,pstrata[s[0]]]:
                    d['pairs']+=1
                    d['status_discordant_pairs']+=status_diff
                    d['RV2_vs_other_pairs']+=rv_diff
                    for name,ok in [('shared_literal_quote',shared_quote),('shared_latest_literal_quote',bool(last)),('identical_literal_quote_set',exact)]:
                        d[name]+=ok
                        d[name+'_status_discordant']+=ok and status_diff
                        d[name+'_RV2_vs_other']+=ok and rv_diff
    assert (counts['all']['sessions'],counts['all']['episodes'],counts['all']['unknowns'],counts['all']['unknown_weight_units'])==(853,2775,2352,W)
    assert transport['unknowns']==2352 and transport['weight_units']==W
    assert counts['all']['RV2_signed_units']==251805 and counts['all']['RS1_signed_units']==300105
    def ceiling(z):
        w=z['unknown_weight_units']
        return {'fraction_width_pct':100*w/W,'residual_width_pp':100*(W-w)/DEN,
                'greatest_lower_pp':100*(L+w)/DEN,'smallest_upper_pp':100*(U-w)/DEN,
                'either_sign_possible_after_favorable_completion':bool(L+w>0 or U-w<0)}
    return {'source_rows':{'annotated':len(a),'released':len(r),'validation':len(v),
                          'valid':len(valid),'invalid':len(v)-len(valid),
                          'valid_not_annotated':len(valid-A.keys()),'annotated_not_valid':0,
                          'shared_fields_checked':len(shared),'per_field_matches':dict(shared)},
            'all_original_invalid_categories':dict(reasons),
            'matched_gate_counts':{k:dict(z)|{'hypothetical_perfect_ascertainment':ceiling(z)} for k,z in counts.items()},
            'matched_gate_strata':{'/'.join(k):dict(z) for k,z in strata.items() if k in strata and k[-1] in ('all','strict_endpoint_visibility_rejection')},
            'strict_gate_coexistence':dict(gate),'known_resolver_pairs':dict(resolver),
            'unknown_sibling_transport':dict(transport),'unknown_sibling_transport_strata':{'/'.join(k):dict(z) for k,z in transport_strata.items()},
            'released_literal_packet_pairs':dict(packet),'released_literal_packet_by_source':{k:dict(z) for k,z in pstrata.items()},
            'qualification':'Original validator labels concern support for misalignment, not final repair. Rejected records remain excluded; same-session and shared-quote links do not adjudicate a focal outcome. Counterfactual ceilings do not measure retrieval, legal entitlement, or verified repairs.'}
def test():
    assert pair_summary([{'damage_severity':'DS1','resolver':'RV2'},{'damage_severity':'DS2','resolver':'RV1'}])==Counter(pairs=1,cross_severity=1,distinct_resolver=1,RV2_vs_other=1)
    assert pair_summary([{'damage_severity':'DS1','resolver':'RV2'},{'damage_severity':'DS1','resolver':'RV2'}])['RV2_vs_other']==0
    assert STRICT<BROAD
    print('G6 synthetic checks PASS')
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('annotations','excerpts','validation','out'):p.add_argument('--'+n)
    p.add_argument('--selftest',action='store_true');args=p.parse_args()
    if args.selftest:test()
    if args.annotations:
        a,ah=read(args.annotations,'annotations');r,rh=read(args.excerpts,'excerpts');v,vh=read_validation(args.validation)
        result=analyze(a,r,v);result['source_hashes']={'annotations':ah,'excerpts':rh,'validation':vh}
        Path(args.out).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        # Only aggregates, never source rows, in public logs.
        for k in ('source_rows','all_original_invalid_categories','matched_gate_counts','strict_gate_coexistence','known_resolver_pairs','unknown_sibling_transport','released_literal_packet_pairs','matched_gate_strata'):
            print(k,json.dumps(result[k],sort_keys=True))
        print('G6 PINNED SOURCE AGGREGATE PASS')
