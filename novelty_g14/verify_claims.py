#!/usr/bin/env python3
"""G14 aggregate-level evidence lock: verifies inherited results, not raw data or new tests."""
import argparse, collections, hashlib, json
from fractions import Fraction
from pathlib import Path
C=collections.Counter
ROOT=Path(__file__).resolve().parents[1]
FILES={6:"novelty_g6/G6_verified_summary.json",7:"novelty_g7/G7_verified_summary.json",9:"novelty_g9/G9_verified_summary.json",10:"novelty_g10/G10_full_cohort_summary.json",11:"novelty_g11/G11_verified_summary.json",12:"novelty_g12/G12_verified_summary.json",13:"novelty_g13/G13_verified_summary.json"}
def require(x,msg):
    if not x:raise ValueError(msg)
def cell(x):
    v=x.get("pytest_verdict")
    # EXECUTED/COMPLETED_PILOT alone is never an outcome certificate.
    if x.get("status")!="EXECUTED" or v not in ("PASS","FAIL"):return "HOLD"
    if x.get("errors",0) or x.get("collection_errors",0) or x.get("skipped",0) or x.get("held",0):return "HOLD"
    if v=="PASS" and x.get("pytest_returncode")==0 and x.get("passed",0)>0 and not x.get("failed",0):return "PASS"
    if v=="FAIL" and x.get("pytest_returncode")==1 and x.get("failed",0)>0:return "FAIL"
    return "HOLD"
def invariant(a,b):
    return bool(a.get("non_test_tree_digest")) and a.get("non_test_tree_digest")==b.get("non_test_tree_digest")
def key(r):return r["setting"],r["source_verdict"],r["rank"]
def pct(x,y):return round(100*x/y,6)
def audit(root):
    docs={};hashes={}
    for k,p in FILES.items():
        raw=(root/p).read_bytes();docs[k]=json.loads(raw)
        hashes[p]=hashlib.sha256(raw).hexdigest()
    a,b,d,e,f,g,h=(docs[k] for k in (6,7,9,10,11,12,13))
    m=a["matched_gate_counts"]["all"];t=a["G6_TARGETING"]
    require((m["sessions"],m["episodes"],m["unknowns"])==(853,2775,2352),"G6 cohort")
    require((t["released_unknowns"],t["strict_target_unknowns"],t["strict_target_sessions"])==(936,271,97),"G6 targets")
    require(t["union_unknowns"]==t["released_unknowns"]+t["strict_target_unknowns"]==1207,"G6 disjoint unknowns")
    W=m["unknown_weight_units"];u=t["released_unknown_weight_units"];v=t["strict_target_weight_units"]
    require(W==3544605 and u+v==t["union_weight_units"]==1911879,"G6 exact weights")
    require(abs(100*(u+v)/W-t["union_width_reduction_pct"])<1e-10,"G6 percent")
    p=b["primary_total"]["cohort"]
    for k in ("all","aligned_complete","any_pass_linked_to_final_patch","final_patch_linked_pass_benchmark_fail","triple_pass_linked_to_final_patch","triple_final_patch_linked_pass_benchmark_fail"):
        require(p[k]==sum(s["cohort"].get(k,0) for s in b["primary_by_setting"].values()),"G7 sum "+k)
    require(tuple(p[k] for k in ("all","aligned_complete","any_pass_linked_to_final_patch","final_patch_linked_pass_benchmark_fail","triple_pass_linked_to_final_patch","triple_final_patch_linked_pass_benchmark_fail"))==(2400,2275,142,87,113,70),"G7 anchors")
    require(b["revision"]==g["source_revision"]==d["static"]["source_revision"],"release revision")
    require(b["source_hashes"]==g["source_hashes"],"G7/G12 identical source manifests")
    for k,vv in d["static"]["source_hashes"].items():
        require(vv==g["source_hashes"][k],"G9/G12 source manifest "+k)
    s=d["static"]["groups"]["all/all"]
    require((s["runs"],s["ftp_count"],s["gold_node_found"],s["reported_pass_node_AST_differs_from_gold"],s["reported_pass_node_AST_matches_gold"])==(13,15,15,14,1),"G9 identity")
    require(d["static"]["distinct_selected_tasks"]==13,"G9 task count")
    ex=d["external"]; exn=sum(x["cohort"]["admitted"] for x in ex.values())
    require(exn==1375,"G9 external admitted")
    ep=sum(x["local_reference_scope"].get("positive_runs",0) for x in ex.values())
    en=sum(x["local_reference_scope"].get("positive_benchmark_nonpass",0) for x in ex.values())
    splits=[sum(x["local_reference_scope"].get("positive_"+k+"_failure_runs",0) for x in ex.values()) for k in ("ftp_only","ptp_only","both")]
    require((ep,en,splits)==(242,65,[56,1,8]) and sum(splits)==en,"G9 external endpoint partition")
    rows=e["rows"];require(len(rows)==len({key(r) for r in rows})==len({r["task_id_sha256"] for r in rows})==13,"G10 frozen cohort")
    lookup={r["task_id_sha256"]:r for r in rows}
    table={key(r):r for r in e["table"]};require(len(table)==13,"G10 table")
    pairs=C();baseflip=controls=discrimination=witness=0
    pair_by_source=collections.defaultdict(C)
    for r in rows:
        cc=r["cells"];names=("base_local","base_reference","candidate_local","candidate_reference","gold_reference")
        v0,v1,v2,v3,v4=[cell(cc[x]) for x in names]
        bi=invariant(cc[names[0]],cc[names[1]]);ci=invariant(cc[names[2]],cc[names[3]])
        tr=table[key(r)]
        require([tr[x] for x in names]==[v0,v1,v2,v3,v4],"G10 table vs actual verdict")
        require(tr["base_tree_invariant"]==bi and tr["candidate_tree_invariant"]==ci,"G10 digest comparison")
        label=v2+"/"+v3 if ci else "HOLD/HOLD"
        pairs[label]+=1;pair_by_source[r["source_verdict"]][label]+=1
        baseflip+=bi and (v0,v1)==("PASS","FAIL")
        controls+=(v1,v4)==("FAIL","PASS")
        discrimination+=bi and ci and (v0,v1,v2,v3,v4)==("PASS","FAIL","PASS","PASS","PASS")
        witness+=bi and ci and (v0,v1,v2,v3,v4)==("PASS","FAIL","PASS","FAIL","PASS")
        for name,x in r["selection"]["source_hashes"].items():
            if name in ("trajectories","patches"):require(x==g["source_hashes"][r["setting"]][name],"G10 source manifest")
    require(dict(pairs)=={"PASS/HOLD":1,"PASS/PASS":9,"PASS/FAIL":1,"HOLD/HOLD":2},"G10 pairs")
    require((baseflip,controls,discrimination,witness)==(10,12,7,1),"G10 controls")
    require(sum(pair_by_source["pass"].values())==7 and sum(pair_by_source["nonpass"].values())==6,"G10 source strata")
    require(pair_by_source["nonpass"]["PASS/PASS"]==2,"G10 historical nonpasses")
    rep=e["replication_record"]; rr=lookup[rep["task_id_sha256"]]
    require(rep["cells"]==rr["cells"] and rep["image_id"]==rr["image_id"] and rep["candidate_patch_sha256"]==rr["candidate_patch_sha256"],"G10 exact witness repetition")
    for rset in f["verified_runs"].values():
        for r in rset.values():
            orig=lookup[r["task_id_sha256"]]
            for k in ("candidate_patch_sha256","reference_test_patch_sha256","gold_patch_sha256","image_id"):
                require(r[k]==orig[k],"G11 source binding "+k)
    a11=f["verified_runs"]["45551510016"]["sphinx_a"]
    b11=f["verified_runs"]["45551510130"]["sphinx_b"]
    require(a11["reference_controls_valid"] and a11["candidate_ftp_pass"] and a11["candidate_ptp_pass"] and not a11["ptp_only_nonpass_witness"],"G11 case A")
    cb=b11["cells"]["candidate"]
    require(cb["collected_count"]==42 and cb["ptp"]=={"n":25,"pass":12,"fail":0,"hold":13} and not cb["fully_determinate"],"G11 case B remains HOLD")
    require(cb["identifier_representation_diagnostics"]["legacy_first_token"]["unique_unused_mapping"]==11,"G11 diagnostic only")
    pp=g["patch_rows"];fp=g["final_runs"]
    require(pp["rows"]==pp["raw_id_match"]+pp["raw_id_mismatch"]==26666,"G12 row balance")
    require(pp["raw_id_mismatch"]==pp["removed_positive_mismatch"]+pp["removed_zero_mismatch"]==218,"G12 mismatch balance")
    require((pp["raw_id_match"],pp["removed_positive_mismatch"],pp["removed_zero_mismatch"])==(26448,211,7),"G12 anchors")
    require(fp["rows"]+fp["empty_final_patch_id"]==2400 and fp["raw_id_match"]+fp["raw_id_mismatch"]==fp["rows"],"G12 final run balance")
    require(g["frozen_13"]["rows"]==g["frozen_13"]["raw_id_match"]==g["frozen_13"]["removed_zero"]==13,"G12 frozen provenance")
    require(g["frozen_13"]["git_numstat_parse"]==12,"G12 syntax")
    require(set(key(r) for r in g["frozen_13_diagnostics"])==set(table),"G12/G10 cohort parity")
    same=g["same_task_same_released_bytes_patch_groups"]
    require((same["multirow_groups"],same["mixed_grade_groups"])==(149,0),"G12 positive consistency")
    r=lookup[h["task_id_sha256"]]
    for k in ("candidate_patch_sha256","reference_test_patch_sha256","gold_patch_sha256","image_id"):
        require(h[k]==r[k],"G13 source binding "+k)
    require(tuple(cell(h["cells"][x]) for x in names)==("PASS","HOLD","PASS","HOLD","HOLD"),"G13 no outcome escalation")
    require(h["cells"]["candidate_reference"]["required_collected"]==0 and h["cells"]["candidate_reference"]["collection_error_categories"]=={"module_not_found":1},"G13 collection cause category")
    require(invariant(h["cells"]["base_local"],h["cells"]["base_reference"]) and invariant(h["cells"]["candidate_local"],h["cells"]["candidate_reference"]) and not h["controlled_witness"],"G13 controlled HOLD")
    H=3
    return {"status":"AGGREGATE_LOCK_PASS","scope":"Offline aggregate consistency; not fresh raw-source replay, new tests, full historical reproduction, or submission approval.","source_file_sha256":hashes,
      "G6":{"matched_sessions":853,"unknown_episodes":2352,"released_unknowns":936,"additional_unknowns":271,"additional_sessions":97,"released_width_fraction_exact":str(Fraction(u,W)),"released_width_pct":pct(u,W),"hypothetical_union_width_fraction_exact":str(Fraction(u+v,W)),"hypothetical_union_width_pct":pct(u+v,W)},
      "G7":{"run_units":2400,"aligned":2275,"final_positive":142,"source_nonpass":87,"triple_positive":113,"triple_nonpass":70},
      "G9":{"selected":13,"definitions":15,"AST_different":14,"external_admitted":exn,"external_positive":ep,"external_nonpass":en,"external_nonpass_partitions":splits},
      "G10":{"fixed_runs":13,"source_pass":7,"source_nonpass":6,"candidate_pairs":dict(pairs),"determinate_pairs":10,"controlled_witnesses":witness,"unresolved_pairs":H,"logical_witness_count_range":[witness,witness+H],"logical_witness_fraction_range":[str(Fraction(witness,13)),str(Fraction(witness+H,13))],"base_version_reversals":baseflip,"base_gold_controls":controls,"reference_discrimination_witnesses":discrimination,"source_nonpass_both_test_versions_pass":2,"qualification":"Count range over selected frame under arbitrary completions of unresolved outcomes; not confidence interval or population prevalence."},
      "G11":{"case_A_candidate_named_pass":6,"case_B_required_PTP_pass":12,"case_B_required_PTP_hold":13,"case_B_collected":42,"exact_application_HOLD":2},
      "G12":{"patch_rows":26666,"digest_convention_matches":26448,"declared_projection_mismatch":211,"unexplained_mismatch":7,"same_bytes_duplicate_groups":149,"mixed_grades_in_these_groups":0,"frozen_candidates_digest_match":13,"frozen_candidates_parseable":12},
      "G13":{"candidate_local":"PASS","candidate_reference":"HOLD","gold_reference":"HOLD","additional_witnesses":0},
      "publication":{"baseline":"MR31R9-EP2","native_source_parity":"HOLD","article_revision":"NOT_GENERATED","candidate_text":"MANUSCRIPT_INSERTION.md"}}
def selftest():
    require(cell({"status":"COMPLETED_PILOT"})=="HOLD","status is not a grade")
    require(cell({"status":"EXECUTED","pytest_verdict":"FAIL","pytest_returncode":2,"failed":1})=="HOLD","collection exit")
    require(cell({"status":"EXECUTED","pytest_verdict":"PASS","pytest_returncode":0,"passed":1,"held":1})=="HOLD","missing node")
    require(cell({"status":"EXECUTED","pytest_verdict":"PASS","pytest_returncode":0,"passed":1})=="PASS","positive control")
    require(cell({"status":"EXECUTED","pytest_verdict":"FAIL","pytest_returncode":1,"failed":1})=="FAIL","negative control")
    require(not invariant({},{}),"missing digests")
    require(not invariant({"non_test_tree_digest":"a"},{"non_test_tree_digest":"b"}),"different tree")
    print("G14 synthetic fail-closed checks: PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);o=p.parse_args()
    selftest();z=audit(ROOT);o.out.parent.mkdir(parents=True,exist_ok=True);o.out.write_text(json.dumps(z,indent=2,sort_keys=True)+"\n")
    print("G14_EVIDENCE_LOCK",json.dumps(z,sort_keys=True));print("G14 AGGREGATE LOCK PASS")
