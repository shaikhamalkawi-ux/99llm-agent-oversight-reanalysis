#!/usr/bin/env python3
"""Exact outcome-ascertainment frontier; source-pinned, aggregate output only.

All effects are conditional on the original 853 matched sessions, existing
DS1/DS2 severity labels, and fixed observed RS1 resolver labels.  An RS2
unknown could hypothetically later be adjudicated as RV2 or non-RV2; the
analysis does not validate code repair and includes no performed follow-up.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import argparse, hashlib, itertools, json

SOURCE_SHA = "7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57"
M, SCALE = 853, 2520
DEN = M * SCALE

def certificate(weights, threshold, strict=False):
    prefix = 0
    for k, w in enumerate(sorted(weights, reverse=True), start=1):
        prior = prefix
        prefix += w
        if (prefix > threshold) if strict else (prefix >= threshold):
            return {"k": k, "previous_scaled_sum": prior, "attained_scaled_sum": prefix}
    raise ValueError("Certificate not attainable")

def run(source_path):
    b=Path(source_path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=SOURCE_SHA:
        raise ValueError("Original-source SHA-256 mismatch; refusing analysis")
    rows=json.loads(b)
    if len(rows)!=16118: raise ValueError("Unexpected original episode count")
    sessions=defaultdict(lambda: {"DS1":[0,0,0,0], "DS2":[0,0,0,0]})
    two_class=0
    for row in rows:
        g=row.get("damage_severity")
        if g not in ("DS1","DS2"): continue
        two_class+=1
        key=(str(row["source"]),str(row["repository_id"]),str(row["session_id"]))
        c=sessions[key][g]
        c[0]+=1
        c[1]+=int(row.get("resolution_status")=="RS1")
        c[2]+=int(row.get("resolution_status")=="RS1" and row.get("resolver")=="RV2")
        c[3]+=int(row.get("resolution_status")=="RS2")
        if c[1]+c[3]!=c[0]: raise ValueError("Unexpected status")
    if (two_class,len(sessions))!=(15948,8590): raise ValueError("Source-frame mismatch")
    d0=u1=u2=rs1=0
    matched=episodes=0
    weights=[]
    session_weights=[]
    repository=defaultdict(int)
    histogram={"DS1":Counter(),"DS2":Counter()}
    for key,x in sessions.items():
        a,b=x["DS1"],x["DS2"]
        if not a[0] or not b[0]:continue
        matched+=1
        episodes+=a[0]+b[0]
        if SCALE%a[0] or SCALE%b[0]:raise ValueError("Unexpected group size")
        v1,v2=SCALE//a[0],SCALE//b[0]
        rs1+=b[1]*v2-a[1]*v1
        d0+=b[2]*v2-a[2]*v1
        u1+=a[3]*v1;u2+=b[3]*v2
        weights.extend([v1]*a[3])
        weights.extend([v2]*b[3])
        histogram["DS1"][a[0]]+=a[3];histogram["DS2"][b[0]]+=b[3]
        sw=a[3]*v1+b[3]*v2
        session_weights.append(sw)
        repository[key[:2]]+=sw
    if (matched,episodes,len(repository),len(weights),rs1,d0,u1,u2)!=(853,2775,352,2352,300105,251805,1922355,1622250):
        raise AssertionError("Frozen matched-frame numerical gate failed")
    lower=d0-u1;upper=d0+u2;width=u1+u2
    frac={name:certificate(weights,Fraction(width*num,den)) for name,num,den
          in (("25pct",1,4),("50pct",1,2),("75pct",3,4),("90pct",9,10))}
    abs_targets={str(t):certificate(weights,width-Fraction(t*DEN,100))
                 for t in (100,50,25,10)}
    sign={
        "positive_best_case":certificate(weights,-lower,True),
        "negative_best_case":certificate(weights,upper,True),
        "complete_sessions_positive_best_case":certificate(session_weights,-lower,True),
        "complete_sessions_negative_best_case":certificate(session_weights,upper,True),
        "complete_repositories_positive_best_case":certificate(list(repository.values()),-lower,True),
        "complete_repositories_negative_best_case":certificate(list(repository.values()),upper,True),
    }
    if ([frac[k]["k"] for k in ("25pct","50pct","75pct","90pct")],
        [sign[k]["k"] for k in sign])!=([352,704,1257,1773],[663,744,332,372,49,63]):
        raise AssertionError("Frontier gate failed")
    return {
        "result_status":"verified_source_specific_potential_information_gain_not_performed",
        "source_sha256":SOURCE_SHA,"source_episodes":len(rows),
        "two_class_episodes":two_class,"matched_sessions":matched,
        "matched_episodes":episodes,"matched_repositories":len(repository),
        "unknown_episodes":len(weights),"source_resolver_labels_fixed":True,
        "unit":"1/(853*2520)","initial_bound_scaled":[lower,upper],
        "initial_width_scaled":width,
        "initial_width_pp":100*width/DEN,
        "fractional_width_reduction_certificates":frac,
        "absolute_width_target_pp_certificates":abs_targets,
        "best_case_sign_certificates":sign,
        "uniform_random_expected_width_at_704_pp":100*width*(1-704/len(weights))/DEN,
        "optimal_width_at_704_pp":100*(width-frac["50pct"]["attained_scaled_sum"])/DEN,
        "unknown_weight_histogram":{g:{str(n):num for n,num in sorted(v.items())} for g,v in histogram.items()},
        "raw_rows_or_source_ids_exported":False,
        "qualification":"Hypothetical perfect ascertainment of eventual RV2 status only; not terminal repair, observed improvement, causal benefit or a new general method."
    }

def selftest():
    for ws in ([1,2,3],[3,3,1,1],[5,3,2,1]):
        for t in range(1,sum(ws)+1):
            for strict in (False,True):
                possible=[k for k in range(1,len(ws)+1)
                          if any((sum(z)>t if strict else sum(z)>=t)
                                 for z in itertools.combinations(ws,k))]
                if not possible:continue
                assert certificate(ws,t,strict)["k"]==min(possible)
    print("Synthetic exact-cardinality tests: PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--annotations")
    parser.add_argument("--output")
    parser.add_argument("--selftest",action="store_true")
    args=parser.parse_args()
    if args.selftest:selftest()
    if args.annotations:
        result=run(args.annotations)
        payload=json.dumps(result,sort_keys=True,indent=2)+"\n"
        if args.output:Path(args.output).write_text(payload)
        else:print(payload)
    elif not args.selftest:
        parser.error("--annotations is needed unless --selftest")
