"""Tests exercise fabricated cases only; cannot substitute for original-source replay."""
import sys, unittest, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reproduce_nested_robustness import analyze_sessions,relabeling_certificate
from verify_replay import verify

class SyntheticMath(unittest.TestCase):
    def test_matched_session_estimator(self):
        # Two completely artificial sessions in distinct repositories.
        recs=[]
        for repo,ds1rs,ds2rs in [('A','RS2','RS1'),('B','RS1','RS2')]:
            recs.extend([{'source':'fake','repository_id':repo,'session_id':'s',
                          'damage_severity':'DS1','resolution_status':ds1rs},
                         {'source':'fake','repository_id':repo,'session_id':'s',
                          'damage_severity':'DS2','resolution_status':ds2rs}])
        res=analyze_sessions(recs,seed=42)
        self.assertEqual(res['matched_sessions'],2)
        self.assertEqual(res['matched_repositories'],2)
        self.assertEqual(res['matched_episodes'],4)
        self.assertEqual(res['equal_session_mean_difference'],0.)
        self.assertEqual(res['equal_repository_mean_of_session_differences'],0.)
    def test_worst_case_reclassification_certificate_small(self):
        res=relabeling_certificate(1,10,3,5)
        self.assertEqual(res['minimum_reclassifications'],3)
        self.assertGreaterEqual(res['relabelled_fraction_ds1'],res['relabelled_fraction_ds2'])
        self.assertTrue(res['strictly_smaller_k_certified_impossible_by_exhaustive_integer_search'])
    def test_full_published_integer_certificate_uses_only_aggregates(self):
        res=relabeling_certificate(1174,14587,330,1361)
        self.assertEqual(res['minimum_reclassifications'],223)
        self.assertEqual(res['optimal_DS2_RS1_to_DS1_RS1'],223)
        self.assertEqual(res['optimal_DS1_RS2_to_DS2_RS2'],0)
    def test_aggregate_public_release_has_no_episode_identifiers(self):
        obj=json.loads((ROOT/'results'/'aggregate_results.json').read_text())
        self.assertEqual(obj['source_episode_count'],16118)
        self.assertEqual(obj['third_party_rows_exported'],0)
        raw=json.dumps(obj)
        for unsafe in ['session_sha','session_timestamp','user_turns','misalignment_id','session_001','repository_id']:
            self.assertNotIn('"'+unsafe+'"',raw)
    def test_committed_replay_hash(self):
        file=ROOT/'results'/'aggregate_results.json'
        self.assertTrue(verify(file,file))

if __name__=='__main__':unittest.main()
