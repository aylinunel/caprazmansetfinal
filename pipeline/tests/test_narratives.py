import unittest


class CardConditionsTest(unittest.TestCase):
    def test_only_cards_with_findings_are_shipped_with_their_conditions(self):
        from capraz_pipeline.narratives import _card_conditions
        core = {"BG": {"events": [{"supported": [], "uncertain": [{"id": "framing-effect"}]}]},
                "BGM": {"events": [], "pending": {"events": [{"supported": [{"id": "labeling"}], "uncertain": []}]}}}
        got = _card_conditions(core)
        self.assertEqual(sorted(got), ["framing-effect", "labeling"])
        self.assertTrue(got["framing-effect"]["c"] and got["labeling"]["n"])


if __name__ == "__main__":
    unittest.main()
