import unittest

from validation.feedback.labels import Label
from validation.learning.insights import co_occurrence, drift, new_pattern_notes, proposals, report, tier_shift


def snap(pack, n_events, card_counts, version="v1", tier="ai_confident"):
    rows = []
    for card, k in card_counts.items():
        rows += [{"event": f"{pack}-e{i}", "card_id": card, "tier": tier, "pack_version": pack,
                  "detector_version": version, "bloc_mix": "sol"} for i in range(k)]
    rows += [{"event": f"{pack}-e{i}", "card_id": "filler", "tier": None, "pack_version": pack,
              "detector_version": version, "bloc_mix": "yok"} for i in range(n_events)]
    return rows


def note(text, i=0, new=True):
    return Label(f"e{i}", "framing-effect", "p1", "t", "corrected", text, "ai_confident", False, new, f"2026-11-{10 + i:02d}")


class InsightsTest(unittest.TestCase):
    def test_drift_needs_four_earlier_packs(self):
        d = drift([snap(f"p{i}", 100, {"a": 10}) for i in range(3)])
        self.assertEqual(d[0]["flag"], "too little history")

    def test_spike_with_unchanged_detector_is_flagged_as_data_drift(self):
        history = [snap(f"p{i}", 100, {"a": 10 + i % 2}) for i in range(5)] + [snap("p9", 100, {"a": 60})]
        d = next(x for x in drift(history) if x["card_id"] == "a")
        self.assertEqual(d["flag"], "outside usual range")
        self.assertFalse(d["detector_version_changed"])
        self.assertEqual(d["latest"], "60/100")

    def test_stable_card_is_not_flagged(self):
        history = [snap(f"p{i}", 100, {"a": 10 + i % 2}) for i in range(6)]
        self.assertEqual(next(x for x in drift(history) if x["card_id"] == "a")["flag"], "within usual range")

    def test_detector_change_is_marked(self):
        history = [snap(f"p{i}", 100, {"a": 10 + i % 2}) for i in range(5)] + [snap("p9", 100, {"a": 60}, version="v2")]
        self.assertTrue(next(x for x in drift(history) if x["card_id"] == "a")["detector_version_changed"])

    def test_tier_shift_counts_per_pack(self):
        t = tier_shift([snap("p1", 10, {"a": 4}), snap("p2", 10, {"a": 2}, tier="needs_human")])
        self.assertEqual(t, [{"pack": "p1", "ai_confident": 4, "needs_human": 0},
                             {"pack": "p2", "ai_confident": 0, "needs_human": 2}])

    def test_pairs_below_min_events_are_not_reported(self):
        rows = [{"event": f"e{i}", "card_id": c, "tier": "ai_confident"} for i in range(4) for c in ("a", "b")]
        self.assertEqual(co_occurrence(rows, min_events=10), [])
        self.assertEqual(co_occurrence(rows, min_events=4)[0]["pair"], ["a", "b"])

    def test_lift_is_reported_with_counts(self):
        rows = ([{"event": f"e{i}", "card_id": c, "tier": "x"} for i in range(10) for c in ("a", "b")]
                + [{"event": f"z{i}", "card_id": "c", "tier": "x"} for i in range(10)])
        pair = co_occurrence(rows, min_events=10)[0]
        self.assertEqual((pair["together"], pair["events"]), (10, 20))
        self.assertAlmostEqual(pair["lift"], 2.0)

    def test_new_pattern_notes_group_turkish_variants(self):
        groups = new_pattern_notes([note("başlıkta soru işareti", 0), note("Başlıkta soru isareti", 1),
                                    note("başka bir şey", 2), note("sayılmaz", 3, new=False)])
        self.assertEqual(groups[0]["count"], 2)
        self.assertEqual(len(groups), 2)

    def test_proposal_requires_minimum_support_else_watching(self):
        few = [{"text": "x", "count": 4, "examples": []}]
        many = [{"text": "y", "count": 5, "examples": []}]
        self.assertEqual(proposals([], few, [])["proposals"], [])
        self.assertEqual(proposals([], few, [])["watching"][0]["kind"], "new_card")
        self.assertEqual(proposals([], many, [])["proposals"][0]["kind"], "new_card")

    def test_cooccurring_pair_and_rejected_cluster_become_proposals(self):
        out = proposals([{"pair": ["a", "b"], "together": 12, "events": 100, "lift": 3.0}], [],
                        [{"slice": {"card_id": "a"}, "reviewed": 20, "rejected": 12, "reject_rate": 0.6}])
        self.assertEqual({p["kind"] for p in out["proposals"]}, {"merge_or_split_cards", "reword_card"})
        self.assertTrue(all(p["next"] == "write it as a lab candidate and pass the promotion gate" for p in out["proposals"]))

    def test_report_states_nothing_is_added_automatically(self):
        text = report("p1", [], [], [], {"proposals": [], "watching": []})
        self.assertIn("Nothing in this report changes a catalogue", text)
        self.assertIn("No proposals yet", text)


if __name__ == "__main__":
    unittest.main()
