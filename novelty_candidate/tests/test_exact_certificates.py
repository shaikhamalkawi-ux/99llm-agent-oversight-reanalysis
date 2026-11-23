"""Purely synthetic checks for the exact additive-cluster threshold proof."""
from fractions import Fraction
from pathlib import Path
import importlib.util
import unittest

P=Path(__file__).resolve().parent.parent/"exact_repository_coherent_certificates.py"
s=importlib.util.spec_from_file_location("certificate",P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def item(name,gain,sessions=1):
    return {"key":("synthetic",name),"source":"synthetic","gain":Fraction(gain),
            "matched_sessions":sessions,"matched_episodes":2*sessions,
            "all_records":2*sessions,"all_sessions":sessions}

class TestExactCertificate(unittest.TestCase):
    def setUp(self):
        # Total 4.5 positive, with three contributors 3, 2, -0.5.
        self.rows=[item("a",3),item("b",2),item("c",Fraction(-1,2))]
        self.total=Fraction(9,2)

    def test_global_minimality(self):
        x=m.thresholds(self.total,self.rows)
        s=x["swap_entire_repository_DS1_DS2"]
        d=x["delete_entire_repository"]
        self.assertEqual(s["minimum_number_of_source_qualified_repositories"],1)
        self.assertEqual(d["minimum_number_of_source_qualified_repositories"],2)
        self.assertLessEqual(Fraction(s["mean_after_last_repository_exact"]),0)
        self.assertGreater(Fraction(s["mean_before_last_repository_exact"]),0)
        self.assertTrue(s["optimality_proof"].startswith("For any k"))

    def test_tie_stable(self):
        seq=[item("z",1),item("a",1),item("n",Fraction(-1,2))]
        tot=Fraction(3,2)
        q=m.thresholds(tot,seq)
        self.assertEqual(q["swap_entire_repository_DS1_DS2"]["minimum_number_of_source_qualified_repositories"],1)
        self.assertEqual(q["delete_entire_repository"]["minimum_number_of_source_qualified_repositories"],2)

    def test_not_attributable_to_source_individual_errors(self):
        vals=m.thresholds(self.total,self.rows)
        for key in vals:
            self.assertTrue(vals[key]["hypothetical_not_observed"])
            self.assertFalse(vals[key]["witness_ids_disclosed"])

if __name__=="__main__":unittest.main()
