#!/usr/bin/env python3
"""MR32P1: deterministic external benchmark endpoint-contract audit.
Uses only frozen upstream OpenHands trajectories and reported verifier labels.
No human/LLM coding, no raw transcript redistribution, no new test execution.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

UPSTREAM="gsmoon97/swe-agent-eval"
COMMIT="2b8d930540ddaf0ae1290e718f1bd0741c70005e"
PASS_CLAIM=re.compile(
    r"\b(?:all\s+|our\s+|the\s+|relevant\s+|unit\s+|integration\s+|existing\s+|new\s+)?"
    r"tests?\s+(?:have\s+|has\s+)?(?:now\s+)?"
    r"(?:passed|pass|passes|passing|succeeded|succeed|are\s+passing|were\s+passing)\b",re.I)
FIX_CLAIM=re.compile(
    r"\b(?:we|i)\s+(?:have\s+|had\s+)?(?:successfully\s+)?"
    r"(?:fixed|resolved|implemented|completed|addressed)\b",re.I)
LOCAL_PASS=re.compile(
    r"\b\d+\s+passed(?:\s|\b)|\bRan\s+\d+\s+tests?\s+in[\s\S]{0,130}?\bOK\b",re.I)
NEGATION=re.compile(r"\b(?:not|never|no|haven't|hasn't|didn't|cannot|can't)\b",re.I)

def affirmative(pattern,text):
    for match in pattern.finditer(text):
        context=text[max(0,match.start()-28):match.start()]
        neg=list(NEGATION.finditer(context))
        if neg and not re.search(r"[.!?\n;:]\s*",context[neg[-1].end():]):
            continue
        return True
    return False

def features(record):
    response=record.get("response") or {}
    choices=response.get("choices") or []
    head=choices[0] if choices and isinstance(choices[0],dict) else {}
    last=str((head.get("message") or {}).get("content") or "")
    messages=record.get("messages") or []
    tested=any(
        isinstance(z,dict) and z.get("role")=="user"
        and str(z.get("content") or "").startswith("EXECUTION RESULT of [")
        and LOCAL_PASS.search(str(z.get("content") or ""))
        for z in messages
    )
    return {
        "last_response_present":bool(last.strip()),
        "last_finish_stop":head.get("finish_reason")=="stop",
        "final_claim_test_pass":affirmative(PASS_CLAIM,last),
        "final_claim_fix_done":affirmative(FIX_CLAIM,last),
        "local_test_pass_receipt_any_time":bool(tested),
    }

def source_partition(j):
    columns={"resolved":j["resolved"],"unresolved":j["unresolved_ids"],
             "no_patch_or_error":j["empty_error_patch_ids"]}
    out={}
    for kind,ids in columns.items():
        if not isinstance(ids,list) or len(ids)!=len(set(ids)):
            raise ValueError("duplicate IDs / malformed list in "+kind)
        for id in ids:
            if id in out:raise ValueError("overlapping outcome class: "+id)
            out[id]=kind
    if len(out)!=j["total_instances"]:
        raise ValueError("source ID partition does not match source total")
    mismatches=[]
    for group,counter in [("resolved","resolved_instances"),
                          ("unresolved","unresolved_instances"),
                          ("no_patch_or_error","empty_error_patch_instances")]:
        if len(columns[group])!=j.get(counter):
            mismatches.append("%s numeric %s versus %s IDs"%(counter,j.get(counter),len(columns[group])))
    for counter,ids in [("submitted_instances","submitted_ids"),
                        ("completed_instances","completed_ids")]:
        if j.get(counter)!=len(j.get(ids,[])):
            mismatches.append("%s numeric %s versus %s IDs"%(counter,j.get(counter),len(j.get(ids,[]))))
    return out,columns,mismatches

def audit(source):
    data=json.loads((source/"results"/"results.json").read_text(encoding="utf-8"))
    status,groups,metadata_warnings=source_partition(data)
    files=list((source/"trajs").glob("*/*.json"))
    index={}
    for path in files:
        key=path.parent.name
        if key in index:raise ValueError("duplicate trajectory for "+key)
        index[key]=path
    if set(index)!=set(status):
        raise ValueError("missing/extra trajectories: missing %s extra %s"%(
            len(set(status)-set(index)),len(set(index)-set(status))))
    counts={v:Counter() for v in groups}
    joint=Counter()
    for id in sorted(status):
        row=json.loads(index[id].read_text(encoding="utf-8"))
        f=features(row)
        label=status[id]
        counts[label]["n"]+=1
        for name,yes in f.items():
            if yes:counts[label][name]+=1
        if label in ("resolved","unresolved"):
            joint[("%s"%int(f["final_claim_test_pass"]),
                   "%s"%int(f["local_test_pass_receipt_any_time"]),label)]+=1
    if sum(x["n"] for x in counts.values())!=data["total_instances"]:
        raise AssertionError("lost records")
    comparisons={}
    for name in ("last_response_present","last_finish_stop","final_claim_test_pass",
                 "final_claim_fix_done","local_test_pass_receipt_any_time"):
        a,b=counts["resolved"][name],counts["unresolved"][name]
        n1,n0=counts["resolved"]["n"],counts["unresolved"]["n"]
        comparisons[name]={
            "resolved_yes":a,"resolved_denominator":n1,
            "unresolved_yes":b,"unresolved_denominator":n0,
            "unresolved_fraction_among_signal_positive":b/(a+b) if a+b else None,
            "resolved_fraction_among_signal_positive":a/(a+b) if a+b else None,
            "resolved_fraction_among_signal_negative":(n1-a)/(n1+n0-a-b) if n1+n0>a+b else None
        }
    return {
        "version":"MR32P1_FIXED_RULES_v1","source_repo":UPSTREAM,"pinned_commit":COMMIT,
        "cohort":"500 enumerated source IDs; outcome comparison only for resolved or unresolved",
        "study_uses_real_developer_pushback":False,
        "outcomes":"third-party benchmark labels, not rerun by the authors of this analysis",
        "source_integrity":{"declared_total":data["total_instances"],
            "trajectory_files":len(files),"summary_counter_warnings":metadata_warnings},
        "partitions":{name:len(ids) for name,ids in groups.items()},
        "counts":{key:dict(value) for key,value in counts.items()},
        "comparisons":comparisons,
        "claim_receipt_outcome_joint":{"|".join(k):v for k,v in sorted(joint.items())},
        "limitations":[
          "Self-reported success is not verified correction; source-verifier test pass is not production safety.",
          "No endpoint from the earlier developer-pushback corpus is linked to this separate benchmark.",
          "Last model response is not necessarily a developer-facing final answer.",
          "Conservative lexical matches may miss paraphrases; no manual adjudication or external validation of lexical rules.",
          "Local tests can cover only part of a task, run before a final edit, or use a different test environment.",
          "Source summary has inconsistent numeric counters; exhaustive disjoint identifier lists define cohort."
        ]
    }

def markdown(report):
    parts=report["partitions"]
    c=report["comparisons"]
    lines=[
        "# MR32P1 external endpoint-contract challenge",
        "",
        "Independent source; do not pool with the Tang et al. developer-pushback corpus.",
        "",
        "Upstream: "+report["source_repo"]+" @ "+report["pinned_commit"],
        "",
        "Enumerated 500 records; verifier-classified: %s resolved, %s unresolved, %s no-patch/error."%(
            parts["resolved"],parts["unresolved"],parts["no_patch_or_error"]),
        "Observed results are conditional on the %s resolved/unresolved records."%(
            parts["resolved"]+parts["unresolved"]),
        "",
        "| Signal | Resolved yes / total | Unresolved yes / total | Unresolved among signal-positive |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key,label in [
        ("last_response_present","Last recorded model response present"),
        ("last_finish_stop","Final model finish reason stop"),
        ("final_claim_test_pass","Last response explicitly claims passing tests"),
        ("final_claim_fix_done","Last response explicitly claims completed fix"),
        ("local_test_pass_receipt_any_time","Tool log includes local passing test receipt")]:
        z=c[key];p=z["unresolved_fraction_among_signal_positive"]
        lines.append("| %s | %s/%s | %s/%s | %s |"%(
          label,z["resolved_yes"],z["resolved_denominator"],
          z["unresolved_yes"],z["unresolved_denominator"],
          "%.2f%%"%(100*p) if p is not None else "N/A"))
    lines.extend(["","## Joint measurement (post-hoc descriptive; no new rules)","",
        "| Claim test pass? | Local test receipt? | Benchmark resolved | Benchmark unresolved |",
        "| --- | --- | ---: | ---: |"])
    for a in ("0","1"):
        for b in ("0","1"):
            r=report["claim_receipt_outcome_joint"].get(a+"|"+b+"|resolved",0)
            u=report["claim_receipt_outcome_joint"].get(a+"|"+b+"|unresolved",0)
            lines.append("| %s | %s | %s | %s |"%(a,b,r,u))
    lines.extend(["","## Source-integrity warnings",""])
    lines.extend("- "+s for s in report["source_integrity"]["summary_counter_warnings"])
    lines.extend(["","## Claim boundary","",
      "Lexical assertions, local test outputs and third-party benchmark outcome labels are distinct observations. Disagreement is not evidence of deception, and no hidden tests were rerun by this analysis.",
      "","No human/LLM adjudication; no new agent execution. The upstream repository is pinned to a commit. All totals refer to that single OpenHands Claude 3.5 Sonnet run only.",""])
    return "\n".join(lines)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.source)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"MR32P1_AUDIT.json").write_text(
        json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    report=markdown(result)+"\n"
    (args.out/"MR32P1_REPORT.md").write_text(report,encoding="utf-8")
    print(report)

if __name__=="__main__":
    main()
