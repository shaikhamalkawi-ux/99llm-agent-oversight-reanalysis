import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import p9_decide as d
import p9_reveal as r


def fixture():
    return json.loads((ROOT/'examples/SYNTHETIC_decision_only.jsonl').read_text().splitlines()[0])

def oracle():
    return json.loads((ROOT/'examples/SYNTHETIC_oracle_AFTER_SEAL.jsonl').read_text().splitlines()[0])

class TestP9(unittest.TestCase):
    def test_fixture_admitted_by_source(self):
        self.assertEqual(d.decide_one(fixture())['decisions']['source_linked'],'ACCEPT')
    def test_no_local_tests(self):
        x=fixture();x['receipts']=[]
        a=d.decide_one(x)['decisions'];self.assertEqual(a['source_linked'],'HOLD');self.assertEqual(a['local_pass'],'HOLD');self.assertEqual(a['self_report'],'ACCEPT')
    def test_future_receipt_rejected(self):
        x=fixture();x['receipts'][0]['completed_at']='2026-11-16T10:01:00Z'
        with self.assertRaises(ValueError):d.decide_one(x)
    def test_wrong_sha_source_hold(self):
        x=fixture();x['receipts'][0]['head_sha']='b'*40
        self.assertEqual(d.decide_one(x)['decisions']['source_linked'],'HOLD')
    def test_wrong_sha_local_baseline_still_accepts(self):
        x=fixture();x['receipts'][0]['head_sha']='b'*40
        self.assertEqual(d.decide_one(x)['decisions']['local_pass'],'ACCEPT')
    def test_zero_test_no_evidence(self):
        x=fixture();x['receipts'][0]['test_count']=0
        self.assertEqual(d.decide_one(x)['decisions']['source_linked'],'HOLD')
    def test_missing_manifest_hold(self):
        x=fixture();x['receipts'][0]['test_scope_prespecified']=False
        self.assertEqual(d.decide_one(x)['decisions']['source_linked'],'HOLD')
    def test_actor_attribution_boundary(self):
        x=fixture();x['target_agent_is_commit_author']=False
        self.assertEqual(d.decide_one(x)['decisions']['source_linked'],'HOLD')
    def test_human_edit_boundary(self):
        x=fixture();x['unrelated_intervening_edit']=True
        self.assertEqual(d.decide_one(x)['decisions']['source_linked'],'HOLD')
    def test_oracle_field_rejected(self):
        x=fixture();x['resolved']=True
        with self.assertRaises(ValueError):d.decide_one(x)
    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'i.jsonl';p.write_text(json.dumps(fixture())+'\n'+json.dumps(fixture())+'\n')
            with self.assertRaises(ValueError):d.run(p,Path(td)/'out')
    def test_seal_prevents_overwrite_and_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            p=ROOT/'examples/SYNTHETIC_decision_only.jsonl';o=Path(td)/'out'
            d.run(p,o)
            with self.assertRaises(ValueError):d.run(p,o)
            oraclep=ROOT/'examples/SYNTHETIC_oracle_AFTER_SEAL.jsonl'
            self.assertEqual(r.run(o,oraclep,Path(td)/'s.json')['oracle_admitted'],2)
            with (o/'P9_DECISIONS_SEALED.jsonl').open('ab') as fh:fh.write(b'\n')
            with self.assertRaises(ValueError):r.run(o,oraclep,Path(td)/'s2.json')
    def test_post_oracle_required(self):
        x=fixture();z=oracle();z['started_at']=x['t_decision']
        self.assertEqual(r.oracle_label(d.decide_one(x),z)[0],None)
    def test_no_same_tests_as_oracle(self):
        x=fixture();z=oracle();z['oracle_independent_of_visible_receipts']=False
        self.assertIsNone(r.oracle_label(d.decide_one(x),z)[0])
    def test_no_agent_modified_oracle(self):
        x=fixture();z=oracle();z['oracle_unmodified_by_agent']=False
        self.assertIsNone(r.oracle_label(d.decide_one(x),z)[0])
    def test_oracle_mismatched_sha(self):
        x=fixture();z=oracle();z['head_sha']='c'*40
        self.assertIsNone(r.oracle_label(d.decide_one(x),z)[0])
    def test_oracle_zero_tests(self):
        x=fixture();z=oracle();z['tests_executed']=0
        self.assertIsNone(r.oracle_label(d.decide_one(x),z)[0])
    def test_oracle_failed_f2p(self):
        x=fixture();z=oracle();z['f2p_passed']=9
        self.assertEqual(r.oracle_label(d.decide_one(x),z)[0],0)
    def test_oracle_failed_p2p(self):
        x=fixture();z=oracle();z['p2p_failed']=1
        self.assertEqual(r.oracle_label(d.decide_one(x),z)[0],0)
    def test_outcome_unavailable_not_failure(self):
        with tempfile.TemporaryDirectory() as td:
            path=ROOT/'examples/SYNTHETIC_decision_only.jsonl';o=Path(td)/'seal';d.run(path,o)
            oraclefile=Path(td)/'empty.jsonl';oraclefile.write_text('')
            scores=r.run(o,oraclefile,Path(td)/'score.json')
            self.assertEqual(scores['status'],'HOLD_NO_ADMISSIBLE_ORACLE')
            self.assertEqual(scores['oracle_admitted'],0)
            self.assertEqual(scores['oracle_unadmitted'],2)
    def test_one_true_one_false(self):
        with tempfile.TemporaryDirectory() as td:
            p=ROOT/'examples/SYNTHETIC_decision_only.jsonl';o=Path(td)/'out';d.run(p,o)
            q=r.run(o,ROOT/'examples/SYNTHETIC_oracle_AFTER_SEAL.jsonl',Path(td)/'s.json')
            self.assertEqual(q['oracle_admitted'],2)
            self.assertEqual(q['oracle_pass'],1)
            self.assertEqual(q['oracle_fail'],1)
            self.assertEqual(q['policies']['self_report']['false_accept'],1)
            self.assertEqual(q['policies']['source_linked']['false_accept'],0)
            self.assertEqual(q['policies']['source_linked']['evaluated_accept'],1)

if __name__=='__main__':unittest.main()
