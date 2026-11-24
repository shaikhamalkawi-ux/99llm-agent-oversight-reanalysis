#!/usr/bin/env python3
"""G3: source-pinned, license-METADATA-gated exact RV2 ascertainment counterfactual.

Not a legal-access ruling, outcome audit, new statistical method, or terminal
code repair test. Exports aggregate counts only. Original author rows never
leave the ephemeral CI process.
"""
from __future__ import annotations
import argparse, hashlib, json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

PIN="7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57"
SCALE=2520
M=853
DEN=M*SCALE
FULL_WIDTH=3544605
LOWER=-1670550
UPPER=1874055

def examine(path):
    b=Path(path).read_bytes()
    if hashlib.sha256(b).hexdigest()!=PIN:
        raise ValueError("Pinned upstream SHA-256 mismatch")
    rows=json.loads(b)
    if len(rows)!=16118:raise ValueError("Unexpected original source rows")
    sessions=defaultdict(lambda: {"DS1":[0,0,0,0],"DS2":[0,0,0,0],"license":set(),"source":set()})
    two_class=0
    repo_license=defaultdict(set)
    for a in rows:
        g=a.get("damage_severity")
        if g not in ("DS1","DS2"):continue
        two_class+=1
        key=(str(a["source"]),str(a["repository_id"]),str(a["session_id"]))
        repo_license[key[:2]].add(str(a.get("license_type")))
        p=sessions[key]
        p["license"].add(str(a.get("license_type")))
        p["source"].add(str(a["source"]))
        z=p[g]
        z[0]+=1
        z[1]+=int(a.get("resolution_status")=="RS2")
        z[2]+=int(a.get("resolution_status")=="RS1")
        z[3]+=int(a.get("resolution_status")=="RS1" and a.get("resolver")=="RV2")
        if z[1]+z[2]!=z[0]:raise ValueError("Unexpected status")
    if (two_class,len(sessions))!=(15948,8590):raise ValueError("Source admission frame shifted")
    if len(repo_license)!=1229 or any(len(x)!=1 for x in repo_license.values()):
        raise ValueError("Repository-level licence metadata was not stable")
    bins={c:{"matched_sessions":0,"size_hist":Counter(),"n":0,"weight":0} for c in ("NO_LICENSE","OTHER")}
    rv2=rs1=u1=u2=matched=episodes=0
    no_license_swe=0
    matched_repo={"NO_LICENSE":set(),"OTHER":set()}
    for key,p in sessions.items():
        if len(p["license"])!=1 or len(p["source"])!=1:
            raise ValueError("Inconsistent source metadata within session")
        a,b=p["DS1"],p["DS2"]
        if not(a[0] and b[0]):continue
        matched+=1
        episodes+=a[0]+b[0]
        group="NO_LICENSE" if "NO_LICENSE" in p["license"] else "OTHER"
        v=bins[group]
        matched_repo[group].add(key[:2])
        v["matched_sessions"]+=1
        if group=="NO_LICENSE" and key[0]=="swe":no_license_swe+=1
        for z in (a,b):
            n=z[0]
            if SCALE % n:raise ValueError("Unexpected severity-group size")
            v["size_hist"][n]+=z[1]
            v["n"]+=z[1]
            v["weight"]+=z[1]*(SCALE//n)
        rs1+=b[2]*(SCALE//b[0])-a[2]*(SCALE//a[0])
        rv2+=b[3]*(SCALE//b[0])-a[3]*(SCALE//a[0])
        u1+=a[1]*(SCALE//a[0]);u2+=b[1]*(SCALE//b[0])
    if (matched,episodes,rs1,rv2,u1,u2,no_license_swe)!=(853,2775,300105,251805,1922355,1622250,0):
        raise AssertionError("Original result numerical lock mismatch")
    assert (len(matched_repo["NO_LICENSE"]),len(matched_repo["OTHER"]))==(215,137)
    assert bins["NO_LICENSE"]["n"]==1347 and bins["NO_LICENSE"]["matched_sessions"]==451
    assert bins["NO_LICENSE"]["weight"]==1942518 and bins["NO_LICENSE"]["size_hist"][1]==441
    assert bins["OTHER"]["n"]==1005 and bins["OTHER"]["matched_sessions"]==402
    assert bins["OTHER"]["weight"]==1602087 and bins["OTHER"]["size_hist"][1]==412
    assert FULL_WIDTH==bins["NO_LICENSE"]["weight"]+bins["OTHER"]["weight"]
    assert LOWER+bins["OTHER"]["weight"]==-68463
    assert UPPER-bins["OTHER"]["weight"]==271968
    weights={}
    for g in ("NO_LICENSE","OTHER"):
        weights[g]=sorted([SCALE//n for n,c in bins[g]["size_hist"].items() for _ in range(c)],reverse=True)
    def prefix(w,k):return sum(w[:k])
    best=sorted(weights["NO_LICENSE"]+weights["OTHER"],reverse=True)
    def first_crossing(w,threshold):
        total=0
        for i,x in enumerate(w):
            pre=total;total+=x
            if total>=threshold:return i+1,pre,total
        return None
    unrestricted=first_crossing(best,Fraction(FULL_WIDTH,2))
    minimum_no=None
    for n in range(705):
        k_other=704-n
        if n>len(weights["NO_LICENSE"]) or k_other>len(weights["OTHER"]):continue
        gain=prefix(weights["NO_LICENSE"],n)+prefix(weights["OTHER"],k_other)
        if gain>=Fraction(FULL_WIDTH,2):
            minimum_no=(n,k_other,gain)
            break
    need_more=Fraction(FULL_WIDTH,2)-sum(weights["OTHER"])
    minimal_unlicensed=first_crossing(weights["NO_LICENSE"],need_more)
    assert unrestricted==(704,1771560,1774080)
    assert minimum_no==(291,413,1772820)
    assert minimal_unlicensed==(68,168840,171360)
    return {
        "version":"G3_exact_license_metadata_eligibility_candidate_NOT_IN_MANUSCRIPT",
        "original_author_sha256":PIN,
        "matched_sessions":matched,
        "unknown_episode_statuses":2352,
        "denominator_exact":DEN,
        "no_license_metadata":{"unknown":1347,"matched_sessions":451,"matched_repositories":215,"all_specstory":True,
            "width_units":1942518,"n1_unknown":441},
        "other_metadata":{"unknown":1005,"matched_sessions":402,"matched_repositories":137,
            "width_units":1602087,"n1_unknown":412},
        "width_pp_initial":100*FULL_WIDTH/DEN,
        "max_shrink_pct_excluding_no_license":100*1602087/FULL_WIDTH,
        "residual_width_pp_excluding_no_license":100*1942518/DEN,
        "max_possible_lower_bound_pp":100*(-68463)/DEN,
        "min_possible_upper_bound_pp":100*271968/DEN,
        "exact_minimum_unknown_episodes_unrestricted_half_width":unrestricted[0],
        "exact_minimum_no_license_at_total_704":{"no_license":minimum_no[0],
            "other":minimum_no[1],"attained_units":minimum_no[2]},
        "min_no_license_if_all_other_ascertained":minimal_unlicensed[0],
        "sha_pinned_full_source_replay":True,
        "original_rows_or_identifiers_exported":False,
        "critical_boundary":"NO_LICENSE is a repository metadata value, not legal adjudication. Excluding it is a declared hypothetical evidence-admission policy. All other metadata records may still be unobservable, and RV2 does not independently certify code-state repair."
    }

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--annotations",required=True)
    parser.add_argument("--output")
    args=parser.parse_args()
    result=examine(args.annotations)
    s=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:Path(args.output).write_text(s)
    else:print(s)
    print("PINNED SOURCE G3: exact numeric gates PASS; identities suppressed")
