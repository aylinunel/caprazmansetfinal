import json
import tempfile
import unittest
from pathlib import Path


class CardConditionsTest(unittest.TestCase):
    def test_only_cards_with_findings_are_shipped_with_their_conditions(self):
        from capraz_pipeline.narratives import _card_conditions
        core = {"BG": {"events": [{"supported": [], "uncertain": [{"id": "framing-effect"}]}]},
                "BGM": {"events": [], "pending": {"events": [{"supported": [{"id": "labeling"}], "uncertain": []}]}}}
        got = _card_conditions(core)
        self.assertEqual(sorted(got), ["framing-effect", "labeling"])
        self.assertTrue(got["framing-effect"]["c"] and got["labeling"]["n"])

    def test_merge_ships_blind_packets_without_the_key_and_narrative_quality(self):
        from capraz_pipeline.config import REPO
        from capraz_pipeline.narratives import merge
        core = {}
        merge(core)
        self.assertEqual(core.get("BLIND"), json.loads((REPO / "data/reference/blind-packets.json").read_text(encoding="utf-8")))
        self.assertNotIn("ai_shown", json.dumps(core["BLIND"]))
        self.assertEqual(core.get("NQ"), json.loads((REPO / "data/reference/narrative-quality.json").read_text(encoding="utf-8")))

    def test_examples_never_include_an_event_of_the_batch(self):
        from capraz_pipeline.narratives import tasks
        gold = [{"key": k, "q": {}, "rows": [{"s": "a", "hl": "H"}], "score": s} for k, s in (("g1", 3.0), ("g2", 2.0), ("g3", 1.0))]
        items = [{"event": "g1", "week": "w1", "title": "t", "headlines": []}]
        with tempfile.TemporaryDirectory() as d:
            b = json.loads(tasks(items, gold, Path(d), batch=12, n_examples=2)[0].read_text())
        self.assertEqual([x["key"] for x in b["examples"]], ["g2", "g3"])
        self.assertEqual(b["events"][0]["event"], "g1")
        self.assertIn("frame", b["dimensions"])

    def test_example_without_headlines_is_never_chosen(self):
        from capraz_pipeline.narratives import tasks
        row = {"s": "a", "hl": "H", "frame": "F"}
        gold = [{"key": "nohl", "q": {}, "rows": [{"s": "a", "frame": "F"}], "score": 9.0},
                {"key": "empty", "q": {}, "rows": [], "score": 8.0},
                {"key": "ok", "q": {}, "rows": [row], "score": 1.0}]
        items = [{"event": "x", "week": "w1", "title": "t", "headlines": []}]
        with tempfile.TemporaryDirectory() as d:
            b = json.loads(tasks(items, gold, Path(d))[0].read_text())
        self.assertEqual([x["key"] for x in b["examples"]], ["ok"])

    def test_tasks_split_events_into_batches(self):
        from capraz_pipeline.narratives import tasks
        items = [{"event": f"e{i}", "week": "w1", "title": "t", "headlines": []} for i in range(5)]
        with tempfile.TemporaryDirectory() as d:
            files = tasks(items, [], Path(d), batch=2)
        self.assertEqual([f.name for f in files], ["batch-1.json", "batch-2.json", "batch-3.json"])


if __name__ == "__main__":
    unittest.main()
