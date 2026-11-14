import json
import unittest
from pathlib import Path

from biasguard.engine import BiasGuard
from validation.biaslab.configs import PROPOSED_DIR, catalog, manifest, target

REPO = Path(__file__).resolve().parents[2]


class ConfigsTest(unittest.TestCase):
    def test_baseline_is_the_stock_catalog(self):
        stock = BiasGuard().analyze("x", mode="offline")["audit"]["card_hash_sha256"]
        self.assertEqual(manifest("baseline")["card_hash"], stock)
        self.assertEqual(manifest("baseline")["proposed_card_ids"], [])

    def test_candidate_adds_exactly_the_proposed_cards(self):
        self.assertEqual(manifest("candidate")["card_count"], 117)
        self.assertEqual(manifest("candidate")["proposed_card_ids"], ["selective-statistics"])
        self.assertNotEqual(manifest("candidate")["card_hash"], manifest("baseline")["card_hash"])

    def test_candidate_catalog_is_accepted_by_the_engine(self):
        self.assertEqual(len(BiasGuard(cards=catalog("candidate")).cards), 117)

    def test_production_catalog_file_does_not_contain_the_proposal(self):
        self.assertNotIn('"selective-statistics"', (REPO / "biasguard/data/cards.json").read_text(encoding="utf-8"))

    def test_targets(self):
        self.assertIsNone(target("selective_statistics", "baseline"))
        self.assertEqual(target("selective_statistics", "candidate"), "selective-statistics")
        self.assertEqual(target("illusory_truth_effect", "baseline"), "illusory-truth-effect")
        self.assertEqual(target("illusory_truth_effect", "candidate"), "illusory-truth-effect")

    def test_proposed_card_has_three_conditions_and_lab_only_provenance(self):
        card = json.loads((PROPOSED_DIR / "selective-statistics.json").read_text(encoding="utf-8"))
        self.assertEqual(len(card["necessary_conditions"]), 3)
        self.assertTrue(card["provenance"].startswith("LAB-ONLY PROPOSAL, not reviewed, not in production"))
        self.assertGreaterEqual(len(card["non_examples"]), 3)

    def test_unknown_config_raises(self):
        with self.assertRaises(ValueError):
            catalog("production")


if __name__ == "__main__":
    unittest.main()
