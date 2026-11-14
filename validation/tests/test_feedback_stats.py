import unittest

from validation.feedback.labels import Label
from validation.feedback.stats import card_stats, card_status, wilson_lower

GATES = {"agreed": True, "min_run_completion": 0.95, "min_reviews_to_judge": 15, "min_precision_lower_bound": 0.70,
         "hide_min_reviews": 10, "hide_below_precision": 0.50, "audit_rate": 0.05}


def labels(card, kept, rejected, corrected=0, tier="ai_confident", audit=False):
    def one(i, outcome):
        return Label(f"e{card}{outcome}{tier}{audit}{i}", card, "p1", "t" * 64, outcome, "", tier, audit, False, "2026-11-14T00:00:00Z")
    return ([one(i, "verified") for i in range(kept)] + [one(i, "rejected") for i in range(rejected)]
            + [one(i, "corrected") for i in range(corrected)])


class StatsTest(unittest.TestCase):
    def test_wilson_known_values(self):
        self.assertIsNone(wilson_lower(0, 0))
        self.assertAlmostEqual(wilson_lower(15, 15), 0.8472, places=3)
        self.assertLess(wilson_lower(13, 15), 0.70)
        self.assertGreater(wilson_lower(14, 15), 0.70)

    def test_card_with_no_reviews_is_unjudged_with_none_precision(self):
        status = card_status({"x": card_stats([])["x"]} if "x" in card_stats([]) else {}, GATES)
        self.assertEqual(status, {})
        s = card_stats(labels("a", 0, 0))
        self.assertEqual(s, {})

    def test_few_reviews_are_unjudged(self):
        st = card_status(card_stats(labels("a", 0, 3)), GATES)["a"]
        self.assertEqual(st["status"], "unjudged")
        self.assertTrue(st["reasons"])

    def test_corrected_counts_as_kept(self):
        s = card_stats(labels("a", 10, 0, corrected=5))["a"]
        self.assertEqual((s["reviewed"], s["kept"], s["precision"]), (15, 15, 1.0))

    def test_14_of_15_is_eligible_and_13_of_15_is_demoted(self):
        self.assertEqual(card_status(card_stats(labels("a", 14, 1)), GATES)["a"]["status"], "eligible")
        self.assertEqual(card_status(card_stats(labels("a", 13, 2)), GATES)["a"]["status"], "demoted")

    def test_4_of_10_is_hidden(self):
        self.assertEqual(card_status(card_stats(labels("a", 4, 6)), GATES)["a"]["status"], "hidden")

    def test_between_ten_and_fifteen_reviews_above_half_is_unjudged(self):
        self.assertEqual(card_status(card_stats(labels("a", 9, 3)), GATES)["a"]["status"], "unjudged")

    def test_nothing_is_applied_while_not_agreed(self):
        out = card_status(card_stats(labels("a", 4, 6)), {**GATES, "agreed": False})
        self.assertFalse(any(c["applied"] for c in out.values()))
        self.assertEqual(out["a"]["status"], "hidden")

    def test_everything_is_applied_once_agreed(self):
        self.assertTrue(all(c["applied"] for c in card_status(card_stats(labels("a", 4, 6)), GATES).values()))

    def test_audit_precision_uses_only_audit_sampled_ai_confident_findings(self):
        ls = (labels("a", 5, 5, audit=False) + labels("a", 3, 1, audit=True)
              + [l for l in labels("a", 2, 0, tier="needs_human", audit=True)])
        s = card_stats(ls)["a"]
        self.assertEqual((s["audit_reviewed"], s["audit_kept"], s["audit_precision"]), (4, 3, 0.75))

    def test_stats_split_by_tier(self):
        s = card_stats(labels("a", 2, 1) + labels("a", 1, 3, tier="needs_human"))["a"]
        self.assertEqual(s["by_tier"]["ai_confident"], {"reviewed": 3, "kept": 2})
        self.assertEqual(s["by_tier"]["needs_human"], {"reviewed": 4, "kept": 1})

    def test_every_status_has_a_reason(self):
        out = card_status(card_stats(labels("a", 14, 1) + labels("b", 4, 6) + labels("c", 1, 0)), GATES)
        self.assertTrue(all(c["reasons"] for c in out.values()))


if __name__ == "__main__":
    unittest.main()
