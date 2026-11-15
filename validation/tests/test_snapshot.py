import gzip
import json
import tempfile
import unittest
from pathlib import Path

from validation.learning.snapshot import detector_version, load_core, rows, snapshot_id, write

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "public" / "data" / "core.bin"


def results(card_hash="h1"):
    return {"pack": "p1", "summary": {"detector": {"card_hash": card_hash, "prompts_version": "v1", "max_candidates": 6}},
            "events": [
                {"event": "e1", "outlets": 12, "status": "review_complete", "text": "t" * 64,
                 "selected": ["framing-effect", "halo-effect"], "supported": [], "effects": [],
                 "uncertain": [{"id": "framing-effect", "status": "needs_context", "tier": "ai_confident",
                                "tier_reasons": [], "audit": False,
                                "evidence": [{"o": ["sol1"]}, {"o": ["sag1"]}]}]},
                {"event": "e2", "outlets": 6, "status": "analysis_incomplete", "selected": None}]}


CORE_STUB = {"S": [{"s": "sol1", "lean": 20}, {"s": "sag1", "lean": 80}, {"s": "orta1", "lean": 50}],
             "E": [{"i": "e1", "f": "2026-10-03T10:00"}, {"i": "e2", "f": "2026-11-01T10:00"}]}


class SnapshotTest(unittest.TestCase):
    def test_changed_card_hash_changes_detector_version(self):
        self.assertNotEqual(detector_version(results("h1")), detector_version(results("h2")))
        self.assertRegex(detector_version(results()), r"^[0-9a-f]{12}$")

    def test_finding_row_fields(self):
        r = rows(results(), CORE_STUB, "behavioural")[0]
        self.assertEqual((r["event"], r["card_id"], r["tier"], r["status"]), ("e1", "framing-effect", "ai_confident", "needs_context"))
        self.assertEqual((r["month"], r["event_size"], r["bloc_mix"]), ("2026-10", "10–19", "karışık"))
        self.assertEqual((r["pack_version"], r["catalog"], r["text_sha256"]), ("p1", "behavioural", "t" * 64))

    def test_selected_but_unflagged_cards_get_a_row(self):
        rs = rows(results(), CORE_STUB, "behavioural")
        self.assertEqual([(r["card_id"], r["status"], r["tier"]) for r in rs if r["event"] == "e1"][1],
                         ("halo-effect", "suppressed", None))

    def test_incomplete_event_gets_one_failure_row(self):
        rs = [r for r in rows(results(), CORE_STUB, "behavioural") if r["event"] == "e2"]
        self.assertEqual([(r["card_id"], r["status"]) for r in rs], [(None, "analysis_incomplete")])

    def test_bloc_mix_from_quoted_outlets(self):
        res = results()
        res["events"][0]["uncertain"][0]["evidence"] = [{"o": ["sol1"]}]
        self.assertEqual(rows(res, CORE_STUB, "behavioural")[0]["bloc_mix"], "sol")
        res["events"][0]["uncertain"][0]["evidence"] = [{"o": []}]
        self.assertEqual(rows(res, CORE_STUB, "behavioural")[0]["bloc_mix"], "yok")

    def test_row_has_no_field_derived_from_reviews(self):
        keys = set(rows(results(), CORE_STUB, "behavioural")[0])
        self.assertFalse(keys & {"outcome", "note", "reviewed_at", "kept"})

    def test_same_inputs_give_same_snapshot_id_and_no_second_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            a = write(results(), CORE_STUB, "behavioural", out)
            b = write(results(), CORE_STUB, "behavioural", out)
            self.assertEqual(a, b)
            self.assertEqual(len(list(out.glob("*.jsonl.gz"))), 1)
            self.assertEqual(a.name, snapshot_id("p1", "behavioural", detector_version(results())) + ".jsonl.gz")
            self.assertEqual(len(gzip.decompress(a.read_bytes()).decode().splitlines()), 3)

    def test_same_id_with_different_content_raises(self):
        with tempfile.TemporaryDirectory() as d:
            write(results(), CORE_STUB, "behavioural", Path(d))
            changed = results()
            changed["events"][0]["uncertain"][0]["tier"] = "needs_human"
            with self.assertRaises(ValueError):
                write(changed, CORE_STUB, "behavioural", Path(d))

    def test_real_pack_produces_439_finding_rows(self):
        core = load_core(CORE)
        rs = rows(core["BG"], core, "behavioural")
        self.assertEqual(sum(r["tier"] is not None for r in rs), 439)
        self.assertEqual(sum(r["tier"] == "ai_confident" for r in rs), 257)
        self.assertEqual(len({r["event"] for r in rs}), 150)


if __name__ == "__main__":
    unittest.main()
