import json
import unittest


class CardConditionsTest(unittest.TestCase):
    def test_only_cards_with_findings_are_shipped_with_their_conditions(self):
        from capraz_pipeline.narratives import _card_conditions
        core = {"BG": {"events": [{"supported": [], "uncertain": [{"id": "framing-effect"}]}]},
                "BGM": {"events": [], "pending": {"events": [{"supported": [{"id": "labeling"}], "uncertain": []}]}}}
        got = _card_conditions(core)
        self.assertEqual(sorted(got), ["framing-effect", "labeling"])
        self.assertTrue(got["framing-effect"]["c"] and got["labeling"]["n"])

    def test_merge_ships_blind_packets_without_the_key(self):
        from capraz_pipeline.config import REPO
        from capraz_pipeline.narratives import merge
        core = {}
        merge(core)
        self.assertEqual(core.get("BLIND"), json.loads((REPO / "data/reference/blind-packets.json").read_text(encoding="utf-8")))
        self.assertNotIn("ai_shown", json.dumps(core["BLIND"]))


if __name__ == "__main__":
    unittest.main()
