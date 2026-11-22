import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("audit",ROOT/"code"/"audit_endpoint_contract.py")
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class MR32SyntheticOnly(unittest.TestCase):
    def test_claim_vs_negation(self):
        self.assertTrue(audit.affirmative(audit.PASS_CLAIM,"All tests have passed."))
        self.assertFalse(audit.affirmative(audit.PASS_CLAIM,"All tests have not passed."))
        self.assertTrue(audit.affirmative(audit.FIX_CLAIM,"We fixed the issue."))
        self.assertFalse(audit.affirmative(audit.FIX_CLAIM,"We have not fixed the issue."))

    def test_trace_evidence_only(self):
        record={"response":{"choices":[{"finish_reason":"stop",
             "message":{"content":"All tests passed. We have fixed the issue."}}]},
             "messages":[
                 {"role":"user","content":"EXAMPLE: 4 passed"},
                 {"role":"user","content":"EXECUTION RESULT of [execute_bash]:\n4 passed in 0.1s"}]}
        v=audit.features(record)
        self.assertTrue(v["final_claim_test_pass"])
        self.assertTrue(v["final_claim_fix_done"])
        self.assertTrue(v["local_test_pass_receipt_any_time"])
        record["messages"]=record["messages"][:1]
        self.assertFalse(audit.features(record)["local_test_pass_receipt_any_time"])

    def test_partition_warning_preserved(self):
        x={"total_instances":3,"resolved":["a"],"unresolved_ids":["b"],
           "empty_error_patch_ids":["c"],"resolved_instances":1,"unresolved_instances":1,
           "empty_error_patch_instances":0,"submitted_ids":["a","b"],"submitted_instances":3,
           "completed_ids":["a","b"],"completed_instances":3}
        membership,groups,warn=audit.source_partition(x)
        self.assertEqual(membership["b"],"unresolved")
        self.assertEqual(len(warn),3)

    def test_toy_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/"results").mkdir()
            header={"total_instances":3,"resolved":["a"],"unresolved_ids":["b"],
             "empty_error_patch_ids":["c"],"resolved_instances":1,"unresolved_instances":1,
             "empty_error_patch_instances":1,"submitted_ids":["a","b"],"submitted_instances":2,
             "completed_ids":["a","b"],"completed_instances":2}
            (root/"results"/"results.json").write_text(json.dumps(header))
            for name,text in (("a","All tests passed."),("b","All tests passed."),
                              ("c","No final message.")):
                f=root/"trajs"/name;f.mkdir(parents=True)
                (f/"x.json").write_text(json.dumps({"response":{"choices":[
                  {"finish_reason":"stop","message":{"content":text}}]},"messages":[]}))
            z=audit.audit(root)
            self.assertEqual(z["partitions"],{"resolved":1,"unresolved":1,"no_patch_or_error":1})
            self.assertEqual(z["comparisons"]["final_claim_test_pass"]["unresolved_yes"],1)
            self.assertEqual(z["comparisons"]["final_claim_test_pass"]["unresolved_fraction_among_signal_positive"],0.5)
