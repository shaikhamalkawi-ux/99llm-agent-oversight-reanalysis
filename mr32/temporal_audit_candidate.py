#!/usr/bin/env python3
"""MR32P2 conservatively tests time order of EXPLICIT editor tool receipts
and local passing-test receipts. Inference gate only; not a final-code oracle.
No rules are adapted based on observed results.
"""
import argparse, json, re
from pathlib import Path
from collections import Counter

PREFIX="evaluation/python/verified/20250329_OpenHands_Claude-3.5-Sonnet(Oct)"
UPSTREAM_COMMIT="2b8d930540ddaf0ae1290e718f1bd0741c70005e"
EDITOR_RESULT=re.compile(
    r"^EXECUTION RESULT of \[str_replace_editor\]:\s*(?:\n)?"
    r"(?:The file ([^\n]+?) has been edited\.|File created successfully at:\s*([^\n]+))",
    re.I
)
PASSED=re.compile(r"\b\d+\s+passed\b|\bRan\s+\d+\s+tests?\s+in[\s\S]{0,160}?\bOK\b",re.I)
EXTS=(".py",".js",".ts",".tsx",".jsx",".java",".go",".rs",".cpp",".c",".h",".rb",".php")
SKIP_SEGMENTS={"test","tests","testing","docs","doc","examples","example","fixtures","fixture","scripts"}
SKIP_PREFIXES=("test_","conftest","reproduce","check_","example_","setup_","scratch_")
def source_code_path(path):
    s=path.strip().strip("'\"")
    if not s.startswith("/workspace/"):
        return False
    seg=s.split("/workspace/",1)[1].split("/")
    if len(seg)<3 or not s.lower().endswith(EXTS):
        return False
    fn=seg[-1].lower()
    return (not any(p in SKIP_SEGMENTS for p in (x.lower() for x in seg[1:-1]))
        and not fn.startswith(SKIP_PREFIXES) and "test" not in fn.lower())

def flags(trajectory):
    msgs=trajectory.get("messages") or []
    edits=[]
    local_test_pass=[]
    for i,m in enumerate(msgs):
        if m.get("role")!="user": continue
        txt=str(m.get("content") or "")
        e=EDITOR_RESULT.search(txt)
        if e and source_code_path(e.group(1) or e.group(2)):
            edits.append(i)
        if txt.startswith("EXECUTION RESULT of [") and PASSED.search(txt):
            local_test_pass.append(i)
    return {
        "explicit_source_edits": len(edits),
        "local_pass_receipts": len(local_test_pass),
        "has_source_edit":bool(edits),
        "passing_receipt_after_last_explicit_source_edit":bool(edits and
             any(k>edits[-1] for k in local_test_pass)),
        "passing_receipt_before_or_on_last_explicit_source_edit":bool(edits and
             any(k<=edits[-1] for k in local_test_pass)),
        "no_verified_tool_edit":not bool(edits)
    }

def run(root):
    root=Path(root)
    metadata=json.loads((root/"results"/"results.json").read_text(encoding="utf8"))
    groups={"resolved":metadata["resolved"],"unresolved":metadata["unresolved_ids"],
           "no_patch_or_error":metadata["empty_error_patch_ids"]}
    all_ids=[a for arr in groups.values() for a in arr]
    if len(all_ids)!=500 or len(set(all_ids))!=500:
        raise ValueError("500 distinct IDs required before analysis")
    idx={}
    for f in (root/"trajs").glob("*/*.json"):
        if f.parent.name in idx:raise ValueError("multiple traces for "+f.parent.name)
        idx[f.parent.name]=f
    if set(idx)!=set(all_ids):raise ValueError("trace identity mismatch")
    rows=[]
    for label,ids in groups.items():
        for ident in sorted(ids):
            raw=json.loads(idx[ident].read_text(encoding="utf8"))
            ff=flags(raw)
            rows.append({"id":ident,"status":label,**ff})
    c={}
    for label in groups:
        sub=[x for x in rows if x["status"]==label]
        c[label]={"denominator":len(sub),"any_explicit_source_edit":sum(x["has_source_edit"] for x in sub),
          "local_pass_after_last_explicit_source_edit":sum(x["passing_receipt_after_last_explicit_source_edit"] for x in sub),
          "local_pass_before_last_explicit_source_edit":sum(x["passing_receipt_before_or_on_last_explicit_source_edit"] for x in sub),
          "no_recognized_editor_receipt":sum(x["no_verified_tool_edit"] for x in sub)}
    a,b=c["resolved"]["local_pass_after_last_explicit_source_edit"],c["unresolved"]["local_pass_after_last_explicit_source_edit"]
    return {
       "title":"MR32P2 conservative observed-editor temporal gate",
       "source_commit":UPSTREAM_COMMIT,
       "scope":"last acknowledged str_replace_editor SOURCE-file edit versus later tool output pass; no shell-write completeness",
       "population":len(all_ids),
       "status_counts":{k:len(v) for k,v in groups.items()},
       "counts":c,
       "unresolved_among_observed_edit_then_local_pass":b/(a+b) if a+b else None,
       "no_per_case_data_redistributed":True,
       "limitations":[
          "This is a lower-coverage time-order diagnostic, not a guarantee that tests ran after the LAST code edit.",
          "Unobserved shell-based edits, failed edit operations, and test-generated file writes can change timing.",
          "Local pass patterns may reflect only partial tests and do not represent independently run hidden tests.",
          "No human-coded labels, no manual case adjudication, no proof of deception.",
          "The verifier has documented task/test validity risks and the cohort is one agent/model run."
       ]
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--source",required=True)
    a.add_argument("--out",required=True)
    args=a.parse_args()
    z=run(args.source)
    p=Path(args.out);p.mkdir(parents=True,exist_ok=True)
    (p/"TEMPORAL_GATE.json").write_text(json.dumps(z,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps(z,indent=2))
if __name__=="__main__":
    main()
