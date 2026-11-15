import json
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from biasguard.catalog import load_cards
from validation.biaslab import crosswalk
from validation.biaslab.crosswalk import coverage, load, resolve

MESA = Path(__file__).resolve().parents[1] / "mesa_bias_expanded"


def mesa_ids():
    return [c["id"] for c in json.loads((MESA / "missing_concepts.json").read_text(encoding="utf-8"))]


class CrosswalkTest(unittest.TestCase):
    def test_one_entry_per_mesa_concept(self):
        self.assertEqual(set(load()), set(mesa_ids()))

    def test_counts(self):
        c = coverage()
        self.assertEqual(c["relationship"]["candidate_same_id"], 112)
        self.assertEqual(c["relationship"]["unsupported_in_current_taxonomy"], 9)   # need full articles, images or layout
        self.assertEqual(c["relationship"]["equivalent_within_task"], 17)           # media cards, lab candidates
        self.assertEqual(c["resolvable"], 18)

    def test_every_detector_id_is_a_real_card(self):
        from validation.biaslab.configs import catalog
        cards = {c["id"] for c in catalog("candidate")}
        self.assertTrue(all(e.detector_id in cards for e in load().values() if e.detector_id))
        production = {c["id"] for c in load_cards()}
        self.assertTrue(all(e.detector_id in production for e in load().values()
                            if e.detector_id and e.relationship == "candidate_same_id"))

    def test_unreviewed_same_id_match_does_not_resolve(self):
        self.assertIsNone(resolve("the_sunk_cost_fallacy"))

    def test_pilot_entry_resolves(self):
        self.assertEqual(resolve("illusory_truth_effect"), "illusory-truth-effect")

    def test_media_technique_needing_full_articles_has_no_detector_id(self):
        self.assertIsNone(resolve("source_selection"))
        self.assertEqual(load()["source_selection"].evidence_tier, "full_article")

    def test_headline_media_technique_resolves_to_its_candidate_card(self):
        self.assertEqual(resolve("selective_statistics"), "selective-statistics")
        self.assertEqual(load()["spin"].policy, "effect_context_only")

    def test_selective_statistics_lists_required_evidence(self):
        self.assertEqual(len(load()["selective_statistics"].required_evidence), 3)

    def test_tier_above_available_does_not_resolve(self):
        entries = dict(load())
        entries["illusory_truth_effect"] = replace(entries["illusory_truth_effect"], evidence_tier="full_article")
        with mock.patch.object(crosswalk, "load", return_value=entries):
            self.assertIsNone(resolve("illusory_truth_effect"))
            self.assertEqual(resolve("illusory_truth_effect", "full_article"), "illusory-truth-effect")

    def test_unknown_id_raises_keyerror(self):
        with self.assertRaises(KeyError):
            resolve("no_such_concept")

    def test_invalid_enum_in_file_raises_valueerror(self):
        bad = [{"simulation_id": "x", "detector_id": None, "relationship": "made_up", "evidence_tier": "headline_lede",
                "policy": "p", "review_status": "pilot", "required_evidence": []}]
        with self.assertRaises(ValueError):
            crosswalk.parse(bad)


if __name__ == "__main__":
    unittest.main()
