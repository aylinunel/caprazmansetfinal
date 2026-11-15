import unittest
from pathlib import Path

from validation.feedback.labels import Label
from validation.learning.errors import clusters, confusion, joined, next_move, report, stuck_conditions

RUN = Path(__file__).resolve().parents[2] / "runs" / "bg"


def row(event, card="framing-effect", tier="ai_confident", pack="p1", text="t", bloc="sol", status="needs_context"):
    return {"event": event, "card_id": card, "tier": tier, "pack_version": pack, "text_sha256": text, "bloc_mix": bloc,
            "status": status, "catalog": "behavioural", "month": "2026-10", "event_size": "5–9", "audit": False}


def label(event, outcome, card="framing-effect", pack="p1", text="t"):
    return Label(event, card, pack, text, outcome, "", "ai_confident", False, False, "2026-11-14T00:00:00Z")


class ErrorsTest(unittest.TestCase):
    def test_join_ignores_labels_from_another_pack_or_text(self):
        j = joined([row("e1"), row("e2"), row("e3")],
                   [label("e1", "rejected"), label("e2", "rejected", pack="p0"), label("e3", "rejected", text="x")])
        self.assertEqual([r["outcome"] for r in j], ["rejected", None, None])

    def test_confusion_counts_unreviewed_separately(self):
        j = joined([row("e1"), row("e2"), row("e3", tier="needs_human"), row("e4", card=None, tier=None, status="analysis_incomplete")],
                   [label("e1", "verified"), label("e3", "rejected")])
        c = confusion(j)
        self.assertEqual(c["ai_confident"], {"kept": 1, "rejected": 0, "unreviewed": 1})
        self.assertEqual(c["needs_human"], {"kept": 0, "rejected": 1, "unreviewed": 0})
        self.assertEqual(c["system_failures"], 1)

    def test_small_slices_are_reported_as_too_few(self):
        rs = [row(f"e{i}") for i in range(3)]
        out = clusters(joined(rs, [label(f"e{i}", "rejected") for i in range(3)]), by=["card_id"])
        self.assertEqual(out["clusters"], [])
        self.assertEqual(out["too_few"], [{"slice": {"card_id": "framing-effect"}, "reviewed": 3, "rejected": 3}])

    def test_clusters_sorted_by_lower_bound_of_reject_rate(self):
        rs = [row(f"a{i}", card="a") for i in range(10)] + [row(f"b{i}", card="b") for i in range(10)]
        ls = ([label(f"a{i}", "rejected" if i < 2 else "verified", card="a") for i in range(10)]
              + [label(f"b{i}", "rejected" if i < 8 else "verified", card="b") for i in range(10)])
        out = clusters(joined(rs, ls), by=["card_id"])["clusters"]
        self.assertEqual([c["slice"]["card_id"] for c in out], ["b", "a"])
        self.assertEqual((out[0]["reviewed"], out[0]["rejected"], out[0]["reject_rate"]), (10, 8, 0.8))
        self.assertLess(out[0]["lower"], 0.8)
        self.assertGreater(out[0]["upper"], 0.8)

    def test_clusters_by_two_fields(self):
        rs = [row(f"e{i}", bloc="sağ") for i in range(6)]
        out = clusters(joined(rs, [label(f"e{i}", "rejected") for i in range(6)]), by=["card_id", "bloc_mix"])
        self.assertEqual(out["clusters"][0]["slice"], {"card_id": "framing-effect", "bloc_mix": "sağ"})

    def test_next_move_rules(self):
        self.assertEqual(next_move({"slice": {"card_id": "x"}}, [], 0.0), "better card wording")
        self.assertEqual(next_move({"slice": {"card_id": "x"}}, [{"card_id": "x", "stuck_share": 0.7}], 0.0),
                         "better evidence (context the input lacks)")
        self.assertEqual(next_move({"slice": {"bloc_mix": "sol"}}, [], 0.0), "better threshold/config")
        self.assertEqual(next_move({"slice": {"bloc_mix": "sol"}}, [], 0.2), "better product fallback")

    def test_stuck_conditions_on_the_recorded_run(self):
        stuck = stuck_conditions(RUN)
        framing = next(s for s in stuck if s["card_id"] == "framing-effect")
        self.assertGreater(framing["assessments"], 100)
        self.assertEqual(len(framing["conditions"]), 3)
        self.assertTrue(all(set(c) == {"index", "satisfied", "unknown", "contradicted"} for c in framing["conditions"]))
        self.assertTrue(0 <= framing["stuck_share"] <= 1)

    def test_report_shows_counts_beside_every_rate(self):
        rs = [row(f"b{i}", card="b") for i in range(10)]
        j = joined(rs, [label(f"b{i}", "rejected" if i < 8 else "verified", card="b") for i in range(10)])
        text = report("snap", j, [])
        self.assertIn("8/10", text)
        self.assertIn("verify-pass", text)
        self.assertNotRegex(text, r"\d+%(?! interval)")   # rates are given as counts, never as a bare percentage

    def test_report_with_no_reviews_says_so(self):
        self.assertIn("No finding has been reviewed yet", report("snap", joined([row("e1")], []), []))


if __name__ == "__main__":
    unittest.main()
