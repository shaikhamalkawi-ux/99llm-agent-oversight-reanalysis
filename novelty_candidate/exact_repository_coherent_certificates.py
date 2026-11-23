#!/usr/bin/env python3
"""Novelty candidate: exact repository-coherent perturbation certificates.

Input: immutable upstream public 16,118-episode categorical source. Output:
aggregate-only exact finite-frame sensitivity diagnostics. No user/session/
repository IDs or original episode rows are written to the outputs.

Two DIFFERENT hypothetical operations on source-qualified repositories:
 (A) swap every DS1/DS2 severity label in a repository, keeping RS1 fixed;
 (B) delete the repository from the matched-session statistic.
Neither operation is observed misclassification, causal treatment,
probabilistic uncertainty, or a prediction of later recovery.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

PIN = "7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57"
SCIENTIFIC_LOCK = Fraction(6669, 56)    # Sum, not mean, over 853 paired sessions
M = 853

def thresholds(total, sorted_records):
    """Prove both cardinality minima by greedy maximal k-gain certificate.

    Each source-qualified repository's gain is additive; the maximum gain
    obtainable with k repositories is the sum of the k largest gains.
    Therefore the first k that crosses a target is globally minimal.
    """
    if not isinstance(total, Fraction) or total <= 0:
        raise ValueError("Positive exact total required")
    ranking = sorted(sorted_records, key=lambda z: (-z["gain"], z["key"]))
    thresholds_out = {}
    for operation, required in (
        ("swap_entire_repository_DS1_DS2", total/2),
        ("delete_entire_repository", total),
    ):
        pref=Fraction(0)
        winner=[]
        for item in ranking:
            pref += item["gain"]
            winner.append(item)
            if pref >= required:
                break
        else:
            raise ValueError("No sign-reversal certificate under "+operation)
        n=len(winner)
        before=pref-winner[-1]["gain"]
        assert before < required <= pref
        removed_sessions=sum(v["matched_sessions"] for v in winner)
        if operation=="delete_entire_repository":
            assert M-removed_sessions>0
            new_difference=(total-pref)/(M-removed_sessions)
            prev_difference=(total-before)/(M-removed_sessions+winner[-1]["matched_sessions"])
        else:
            new_difference=(total-2*pref)/M
            prev_difference=(total-2*before)/M
        assert prev_difference>0 and new_difference<=0
        thresholds_out[operation]={
            "minimum_number_of_source_qualified_repositories":n,
            "matched_repository_frame":len(ranking),
            "threshold_exact":str(required),
            "optimal_prefix_gain_exact":str(pref),
            "before_prefix_gain_exact":str(before),
            "mean_before_last_repository_exact":str(prev_difference),
            "mean_after_last_repository_exact":str(new_difference),
            "mean_before_last_repository_pp":100*float(prev_difference),
            "mean_after_last_repository_pp":100*float(new_difference),
            "witness_aggregate_only":{
                "matched_sessions_touched":removed_sessions,
                "matched_episodes_touched":sum(z["matched_episodes"] for z in winner),
                "DS1_DS2_records_in_selected_repositories":sum(z["all_records"] for z in winner),
                "all_two_class_sessions_in_selected_repositories":sum(z["all_sessions"] for z in winner),
                "repositories_by_original_source":dict(sorted(Counter(z["source"] for z in winner).items())),
            },
            "optimality_proof":"For any k, the k-largest source-qualified repository contributions maximize removable/swappable sum. At k-1 their exact sum is below the target, while at k the target is attained.",
            "hypothetical_not_observed":True,
            "witness_ids_disclosed":False
        }
    return thresholds_out

def run(path):
    b=Path(path).read_bytes()
    observed=hashlib.sha256(b).hexdigest()
    if observed!=PIN:raise ValueError("Refused unpinned source: "+observed)
    rows=json.loads(b)
    if len(rows)!=16118:raise ValueError("Unexpected row count")
    sessions=defaultdict(lambda: {"DS1":[0,0],"DS2":[0,0]})
    repos=defaultdict(lambda:{
        "all_records":0,"all_sessions":set(),"matched_sessions":0,
        "matched_episodes":0,"gain":Fraction(0)})
    nrecords=0
    for r in rows:
        g=r.get("damage_severity")
        if g not in ("DS1","DS2"):continue
        nrecords+=1
        k=(r["source"],str(r["repository_id"]),str(r["session_id"]))
        rkey=k[:2]
        target=sessions[k][g]
        target[0]+=1
        target[1]+=int(r["resolution_status"]=="RS1")
        repos[rkey]["all_records"]+=1
        repos[rkey]["all_sessions"].add(k)
    if nrecords!=15948 or len(sessions)!=8590 or len(repos)!=1229:
        raise ValueError("Source-frame gate mismatch")
    positive=negative=tied=0
    matched_n=matched_eps=0
    for k,groups in sessions.items():
        a,b=groups["DS1"],groups["DS2"]
        if not (a[0] and b[0]):continue
        matched_n+=1
        matched_eps+=a[0]+b[0]
        d=Fraction(b[1],b[0])-Fraction(a[1],a[0])
        positive+=int(d>0);negative+=int(d<0);tied+=int(d==0)
        z=repos[k[:2]]
        z["matched_sessions"]+=1
        z["matched_episodes"]+=a[0]+b[0]
        z["gain"]+=d
    records=[]
    for key,z in repos.items():
        if not z["matched_sessions"]:continue
        records.append({
            "key":key,
            "source":key[0],
            "gain":z["gain"],
            "matched_sessions":z["matched_sessions"],
            "matched_episodes":z["matched_episodes"],
            "all_records":z["all_records"],
            "all_sessions":len(z["all_sessions"]),
        })
    total=sum((r["gain"] for r in records), Fraction(0))
    assert (matched_n,matched_eps,len(records))==(853,2775,352)
    assert (positive,negative,tied)==(201,99,553)
    assert total==SCIENTIFIC_LOCK and total/M==Fraction(6669,47768)
    polarity=Counter("positive" if r["gain"]>0 else "negative" if r["gain"]<0 else "zero"
                     for r in records)
    assert dict(polarity)=={"positive":119,"negative":48,"zero":185}
    return {
        "claim":"Two exact finite-dataset sensitivity thresholds for repository-coherent *hypothetical* disturbances",
        "source":"Tang et al. 2026 frozen original-author categorical release",
        "sha256":PIN,
        "source_rows":len(rows),"two_class_rows":nrecords,
        "all_two_class_sessions":len(sessions),
        "all_two_class_repositories":len(repos),
        "matched_sessions":matched_n,
        "matched_episodes":matched_eps,
        "matched_repositories":len(records),
        "matched_session_original_sum_exact":str(total),
        "matched_session_original_mean_exact":str(total/M),
        "matched_session_original_mean_pp":100*float(total/M),
        "repository_contribution_signs":dict(polarity),
        "exact_certificates":thresholds(total,records),
        "limitations":[
            "This is a conditional adversarial sensitivity exercise, not an empirical label-error estimate.",
            "Repo-coherent DS1/DS2 swaps are not an established plausible misclassification process.",
            "Repo deletion is an extreme selection stress, not new evidence about missing outcomes.",
            "Conclusions remain confined to original annotation labels in 853 matched sessions.",
            "No estimate of verified terminal repair, causal human oversight benefit, or population-wide safety.",
            "It does not establish a new statistical procedure; it is a source-specific sharp certificate."
        ],
        "raw_row_or_identifier_export_count":0
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--annotations",required=True)
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    result=run(args.annotations)
    target=Path(args.out)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "validation":"PASS", "source_sha256":PIN,
        "original_matched_mean_pp":result["matched_session_original_mean_pp"],
        "swap":result["exact_certificates"]["swap_entire_repository_DS1_DS2"],
        "delete":result["exact_certificates"]["delete_entire_repository"]
    },indent=2))
if __name__=="__main__":
    main()
