import json
import tempfile
import unittest
from pathlib import Path

from validation.learning.promotion import (PROMOTION_GATES, assert_promotion_ready, decide, metrics_from, record,
                                            slice_regressions)

GOOD = {"replay_reintroduced_absent": 0, "replay_still_shown_absent_delta": 0, "replay_lost_present_rate": 0.0,
        "replay_error_rate": 0.0, "lab_forbidden_rate": 0.0, "run_completion": 1.0}


def replay(kept=10, lost=0, by_card=None, **extra):
    base = {"kept_present": kept, "lost_present": lost, "kept_absent": 2, "still_shown_absent": 1,
            "reintroduced_absent": 0, "errors": 0, "scored": kept + lost + 3,
            "by_card": by_card or {"a": {"kept_present": kept, "lost_present": lost}}}
    return {**base, **extra}


class PromotionTest(unittest.TestCase):
    def test_good_metrics_pass(self):
        assert_promotion_ready(GOOD)

    def test_missing_metric_fails_closed(self):
        m = dict(GOOD); del m["lab_forbidden_rate"]
        with self.assertRaisesRegex(ValueError, "lab_forbidden_rate"):
            assert_promotion_ready(m)

    def test_none_metric_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "run_completion"):
            assert_promotion_ready({**GOOD, "run_completion": None})

    def test_one_reintroduced_rejection_blocks_promotion(self):
        with self.assertRaisesRegex(ValueError, "replay_reintroduced_absent"):
            assert_promotion_ready({**GOOD, "replay_reintroduced_absent": 1})

    def test_gates_cover_every_metric_in_the_spec(self):
        self.assertEqual(set(PROMOTION_GATES), set(GOOD))

    def test_metrics_from_replay_and_lab(self):
        m = metrics_from(replay(), replay(kept=9, lost=1, still_shown_absent=1), {"forbidden_rate": {"value": 0.0}}, 1.0)
        self.assertEqual(m["replay_lost_present_rate"], 0.1)
        self.assertEqual(m["replay_still_shown_absent_delta"], 0)
        self.assertEqual(m["lab_forbidden_rate"], 0.0)

    def test_metrics_from_empty_replay_set_is_not_estimable(self):
        empty = replay(kept=0, lost=0, scored=0, by_card={})
        self.assertIsNone(metrics_from(empty, empty, {"forbidden_rate": {"value": 0.0}}, 1.0)["replay_lost_present_rate"])

    def test_overall_gain_with_one_card_regression_is_refused_and_names_the_card(self):
        base = replay(by_card={"a": {"kept_present": 10, "lost_present": 10}, "b": {"kept_present": 12, "lost_present": 0}})
        cand = replay(by_card={"a": {"kept_present": 20, "lost_present": 0}, "b": {"kept_present": 9, "lost_present": 3}})
        regs = slice_regressions(base, cand)
        self.assertEqual([r["slice"] for r in regs], ["b"])
        d = decide(GOOD, regs)
        self.assertFalse(d["promote"])
        self.assertTrue(any("b" in r for r in d["reasons"]))

    def test_small_slice_change_is_not_a_regression(self):
        base = replay(by_card={"a": {"kept_present": 3, "lost_present": 0}})
        cand = replay(by_card={"a": {"kept_present": 2, "lost_present": 1}})
        self.assertEqual(slice_regressions(base, cand), [])

    def test_clean_candidate_is_promoted_and_recorded(self):
        d = decide(GOOD, [])
        self.assertEqual(d, {"promote": True, "reasons": ["all gates met; no slice regressed"]})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "versions.jsonl"
            record(path, "v1", d, Path("report.md"))
            record(path, "v2", decide({**GOOD, "run_completion": 0.5}, []), Path("r2.md"))
            rows = [json.loads(l) for l in path.read_text().splitlines()]
        self.assertEqual([(r["version"], r["promote"]) for r in rows], [("v1", True), ("v2", False)])

    def test_failed_gate_is_a_refusal_not_an_exception_in_decide(self):
        d = decide({**GOOD, "replay_error_rate": 0.5}, [])
        self.assertFalse(d["promote"])
        self.assertIn("replay_error_rate", d["reasons"][0])


if __name__ == "__main__":
    unittest.main()
