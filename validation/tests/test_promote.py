import json
import tempfile
import unittest
from pathlib import Path

from validation.biaslab.promote import promotable, promote

CLEAN = {"positive": ["supported", "supported"], "boundary_control": ["not_supported"], "quoted_control": ["uncertain"]}
REPO = Path(__file__).resolve().parents[2]


class PromoteTest(unittest.TestCase):
    def test_clean_approved_card_is_promotable(self):
        self.assertEqual(promotable(CLEAN, True), (True, []))

    def test_card_with_a_forbidden_control_is_refused_with_reason(self):
        ok, why = promotable({**CLEAN, "quoted_control": ["supported"]}, True)
        self.assertFalse(ok)
        self.assertIn("quoted_control", why[0])

    def test_card_with_no_supported_positive_is_refused(self):
        ok, why = promotable({**CLEAN, "positive": ["uncertain", "uncertain"]}, True)
        self.assertFalse(ok)
        self.assertIn("no positive case was supported", why[0])

    def test_contextual_effect_counts_as_a_supported_positive(self):
        self.assertTrue(promotable({**CLEAN, "positive": ["contextual_effect"]}, True)[0])

    def test_unapproved_card_is_refused_even_if_clean(self):
        self.assertEqual(promotable(CLEAN, False), (False, ["not approved by the owner"]))

    def test_incomplete_cases_block_promotion(self):
        ok, why = promotable({**CLEAN, "boundary_control": ["error"]}, True)
        self.assertFalse(ok)
        self.assertIn("did not complete", why[0])

    def test_unassessed_cases_block_promotion(self):
        self.assertFalse(promotable({**CLEAN, "positive": ["supported", "unassessed"]}, True)[0])

    def test_no_cases_at_all_blocks_promotion(self):
        self.assertEqual(promotable({}, True), (False, ["no lab cases were scored for this card"]))

    def test_promote_writes_only_promotable_cards_sorted_and_reports_refusals(self):
        outcomes = {"word-choice": CLEAN, "labeling": CLEAN, "fear-appeal": {**CLEAN, "quoted_control": ["supported"]}}
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "media_cards.json"
            dest.write_text("[]\n")
            refused = promote(outcomes, ["word-choice", "labeling", "fear-appeal"], "lab-run-1", dest)
            cards = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual([c["id"] for c in cards], ["labeling", "word-choice"])
        self.assertEqual(list(refused), ["fear-appeal"])
        self.assertTrue(all("lab-run-1" in c["provenance"] and not c["provenance"].startswith("LAB-ONLY") for c in cards))

    def test_promote_keeps_cards_already_promoted(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "media_cards.json"
            dest.write_text("[]\n")
            promote({"labeling": CLEAN}, ["labeling"], "run-1", dest)
            promote({"word-choice": CLEAN}, ["word-choice"], "run-2", dest)
            self.assertEqual([c["id"] for c in json.loads(dest.read_text(encoding="utf-8"))], ["labeling", "word-choice"])

    def test_promote_never_touches_cards_json(self):
        before = (REPO / "biasguard/data/cards.json").read_bytes()
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "media_cards.json"
            dest.write_text("[]\n")
            promote({"labeling": CLEAN}, ["labeling"], "run-1", dest)
        self.assertEqual((REPO / "biasguard/data/cards.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
