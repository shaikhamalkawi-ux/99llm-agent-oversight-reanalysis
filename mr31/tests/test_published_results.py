#!/usr/bin/env python3
"""Offline checks on already published MR31 aggregates (not source-label validation)."""
import json
import unittest
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
FIG=ROOT/'figures'
read=lambda name:json.loads((DATA/name).read_text(encoding='utf8'))

class MR31PublishedChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=read('aggregate_results.json')
        cls.cover=read('matched_coverage_results.json')
        cls.elig=read('matched_RV2_eligibility.json')
        cls.sens=read('exact_label_sensitivity.json')
        cls.new=read('new_result_values.json')

    def test_source_identity(self):
        self.assertEqual(self.a['source_sha256'],'7e0693675242a625bdb586bcd8cef23f5da76c65cf840108c3c24b6b479b9f57')
        for row in [self.cover,self.elig['RV2_partial_identification'],self.sens]:
            self.assertEqual(row.get('original_source_sha256',row.get('source_sha256')),self.a['source_sha256'])
        self.assertEqual(self.a['source_episode_count'],16118)
        self.assertEqual(self.a['excluded_other_severity_episodes'],170)

    def test_visibility_source_counts(self):
        s=self.a['all_severity']
        self.assertEqual((s['DS1']['episodes'],s['DS1']['visibly_resolved']), (14587,1174))
        self.assertEqual((s['DS2']['episodes'],s['DS2']['visibly_resolved']), (1361,330))
        self.assertEqual(s['DS1']['episodes']+s['DS2']['episodes'],15948)
        self.assertAlmostEqual(self.a['visible_risk_difference_ds2_minus_ds1'],330/1361-1174/14587,places=13)

    def test_matched_session_scope_and_ties(self):
        cov=self.cover
        self.assertEqual(cov['matched_session_count'],853)
        self.assertEqual(cov['matched_session_episode_count'],2775)
        self.assertEqual(cov['two_class_distinct_source_sessions'],8590)
        self.assertEqual(cov['matched_session_sign_counts'],{'positive':201,'negative':99,'tie':553})
        self.assertEqual(sum(cov['matched_session_sign_counts'].values()),853)
        self.assertEqual(self.a['session_matched']['signs'],cov['matched_session_sign_counts'])
        comp=cov['matched_session_tie_components']
        self.assertEqual(sum(v for v in comp.values() if isinstance(v,int)),553)

    def test_exact_sensitivity_119_120(self):
        rows=self.sens['complete_exact_budget_frontier_to_first_nonpositive']
        self.assertEqual(len(rows),121)
        for k,row in enumerate(rows):
            self.assertEqual(row['budget_k'],k)
            self.assertTrue(row['attains_analytic_bound'])
            self.assertEqual(Fraction(row['minimum_attainable_equal_session_difference']['exact']),Fraction(6669-56*k,47768))
        self.assertGreater(Fraction(rows[119]['minimum_attainable_equal_session_difference']['exact']),0)
        self.assertLess(Fraction(rows[120]['minimum_attainable_equal_session_difference']['exact']),0)
        self.assertEqual(self.sens['minimal_number_of_severity_switches_to_nonpositive_contrast'],120)

    def test_figures_and_reproduction_inputs(self):
        names=('F1_Completion_Frontier_Clear','F2_Eligibility_And_Bounds_Clear',
               'N1_Visibility_And_Unknown','N2_Matched_Session_Ties','N3_Repository_Resampling',
               'S1_Exact_Budget_Clear_119_120')
        for n in names:
            self.assertTrue((FIG/(n+'.pdf')).stat().st_size>1000)
            self.assertTrue((FIG/(n+'.svg')).stat().st_size>1000)
        self.assertEqual(self.new['figures']['N1_Visibility_And_Unknown']['source_total'],16118)
        self.assertEqual(self.new['figures']['N1_Visibility_And_Unknown']['other_severity_excluded'],170)

if __name__=='__main__':
    unittest.main()
