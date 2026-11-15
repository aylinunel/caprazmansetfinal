"""Offline checks for the media-technique catalogue ("Medyanın oyunları").

    python -m unittest biasguard.test_catalog_media -v
"""
import unittest

from biasguard.catalog import CatalogError, load_cards, load_media_cards, validate_cards
from biasguard.engine import BiasGuard

TEXT = "[A · 09:00] Bakan: kriz yok — Açıklama tekrarlandı\n[B · 09:05] Krizi herkes görüyor, bakan inkâr etti"
QUOTE = "Krizi herkes görüyor, bakan inkâr etti"
MEDIA = {**load_cards()[0], "id": "test-media-card", "name": "Test", "entry_type": "media_practice",
         "review_policy": "media_pattern_review"}


class Reviewer:
    def review(self, text, context, cards, role):
        c = cards[0]
        return {"role": role, "assessments": [{
            "card_id": c["id"], "verdict": "supported", "evidence": [{"source": "text", "quote": QUOTE, "kind": "behavioral"}],
            "necessary_conditions": [{"condition_index": i, "status": "satisfied", "evidence_indices": [0]}
                                     for i in range(len(c["necessary_conditions"]))],
            "mechanism": "m", "alternative_explanation": "a", "missing_context": []}]}

    def provider_info(self):
        return {"provider": "stub"}


class MediaCatalogTest(unittest.TestCase):
    def test_behavioural_catalogue_is_unchanged(self):
        self.assertEqual(len(load_cards()), 116)
        self.assertFalse(any(c.get("entry_type") == "media_practice" for c in load_cards()))

    def test_media_catalogue_loads_as_a_list_of_media_cards(self):
        cards = load_media_cards()
        self.assertIsInstance(cards, list)
        self.assertTrue(all(c["entry_type"] == "media_practice" for c in cards))
        self.assertFalse({c["id"] for c in cards} & {c["id"] for c in load_cards()})

    def test_media_card_validates_with_new_entry_type_and_policy(self):
        self.assertEqual(validate_cards([MEDIA])[0]["review_policy"], "media_pattern_review")

    def test_unknown_entry_type_still_rejected(self):
        with self.assertRaises(CatalogError):
            validate_cards([{**MEDIA, "entry_type": "made_up"}])

    def test_media_finding_is_supported_and_carries_entry_type(self):
        r = BiasGuard(cards=[MEDIA], reviewer=Reviewer()).analyze(TEXT, "", mode="ai")
        self.assertEqual(r["status"], "review_complete")
        f = r["supported_findings"][0]
        self.assertEqual((f["entry_type"], f["review_policy"], f["not_necessarily_an_error"]),
                         ("media_practice", "media_pattern_review", False))


if __name__ == "__main__":
    unittest.main()
