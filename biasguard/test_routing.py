"""Offline checks for finding tiers, the audit sample and the review queue.

    python -m unittest biasguard.test_routing -v
"""
import json
import tempfile
import unittest
from pathlib import Path

from biasguard.news import apply
from biasguard.routing import in_audit_sample, review_queue, tier

RUN = Path(__file__).resolve().parents[1] / "runs" / "bg"
REJECTED = "sorgulayan inceleme reddetti ve hiçbir koşulu doğrulamadı"
DEMOTED = "insan incelemeleri bu kavramda yetersiz buldu"


def a(verdict, satisfied=0, total=3):
    return {"verdict": verdict, "necessary_conditions": [
        {"condition_index": i, "status": "satisfied" if i < satisfied else "unknown"} for i in range(total)]}


def findings(out):
    return [f for e in out["events"] for k in ("supported", "uncertain", "effects") for f in e.get(k, [])]


class TierTest(unittest.TestCase):
    def test_both_uncertain_is_ai_confident_as_not_dismissed(self):
        self.assertEqual(tier(a("uncertain"), a("uncertain"), None), ("ai_confident", [], "not_dismissed"))

    def test_both_supported_is_ai_confident(self):
        self.assertEqual(tier(a("supported", 3), a("supported", 3), None), ("ai_confident", [], "both"))

    def test_skeptic_rejects_but_confirms_one_condition_is_ai_confident(self):
        self.assertEqual(tier(a("uncertain"), a("not_supported", 1), None),
                         ("ai_confident", [], "skeptic_partly_confirmed"))

    def test_skeptic_rejects_and_confirms_nothing_is_needs_human(self):
        self.assertEqual(tier(a("uncertain"), a("not_supported", 0), None), ("needs_human", [REJECTED], None))

    def test_advocate_condition_alone_does_not_confirm(self):
        self.assertEqual(tier(a("uncertain", 2), a("not_supported", 0), None)[0], "needs_human")

    def test_demoted_card_is_needs_human_even_when_not_dismissed(self):
        self.assertEqual(tier(a("uncertain"), a("uncertain"), "demoted"), ("needs_human", [DEMOTED], "not_dismissed"))

    def test_reasons_accumulate_in_fixed_order(self):
        self.assertEqual(tier(a("uncertain"), a("not_supported", 0), "demoted")[1], [REJECTED, DEMOTED])

    def test_eligible_or_unjudged_status_changes_nothing(self):
        for status in ("eligible", "unjudged", None):
            self.assertEqual(tier(a("uncertain"), a("uncertain"), status)[0], "ai_confident")


class AuditTest(unittest.TestCase):
    def test_audit_sample_is_stable_for_a_pack(self):
        self.assertEqual(in_audit_sample("e1", "c1", "p1"), in_audit_sample("e1", "c1", "p1"))

    def test_audit_sample_changes_with_pack_version(self):
        keys = [(f"e{i}", "c") for i in range(400)]
        self.assertNotEqual([in_audit_sample(e, c, "p1") for e, c in keys],
                            [in_audit_sample(e, c, "p2") for e, c in keys])

    def test_audit_rate_is_close_to_five_percent_over_many_keys(self):
        hits = sum(in_audit_sample(f"e{i}", "card", "p") for i in range(10000))
        self.assertTrue(400 <= hits <= 600, hits)

    def test_rate_zero_and_one(self):
        self.assertFalse(in_audit_sample("e", "c", "p", rate=0.0))
        self.assertTrue(in_audit_sample("e", "c", "p", rate=1.0))


def ev(event, outlets, *fs):
    return {"event": event, "outlets": outlets, "status": "review_complete", "supported": [], "effects": [],
            "uncertain": [{"id": c, "tier": t, "audit": au} for c, t, au in fs]}


class QueueTest(unittest.TestCase):
    def test_queue_puts_least_reviewed_cards_first(self):
        q = review_queue([ev("e1", 5, ("often", "needs_human", False), ("rare", "needs_human", False))],
                         {"often": 9, "rare": 0})
        self.assertEqual([x["card_id"] for x in q], ["rare", "often"])

    def test_ties_break_on_event_size_then_id(self):
        q = review_queue([ev("small", 5, ("c", "needs_human", False)), ev("big", 20, ("c", "needs_human", False))], {})
        self.assertEqual([x["event"] for x in q], ["big", "small"])

    def test_queue_contains_every_needs_human_finding_once(self):
        q = review_queue([ev("e1", 5, ("a", "needs_human", False), ("b", "needs_human", False))], {})
        self.assertEqual(sorted((x["event"], x["card_id"]) for x in q), [("e1", "a"), ("e1", "b")])

    def test_ai_confident_outside_sample_is_not_queued(self):
        self.assertEqual(review_queue([ev("e1", 5, ("a", "ai_confident", False))], {}), [])

    def test_audited_ai_confident_is_queued_as_audit(self):
        q = review_queue([ev("e1", 5, ("a", "ai_confident", True))], {})
        self.assertEqual(q[0]["why"], "audit")


class ApplyOnRecordedRunTest(unittest.TestCase):
    """The 8.1 reviewer run that is checked into runs/bg."""

    @classmethod
    def setUpClass(cls):
        cls.out = apply(RUN)

    def test_owner_rule_gives_257_ai_confident_and_182_needs_human(self):
        s = self.out["summary"]
        self.assertEqual((s["aiConfident"], s["needsHuman"]), (257, 182))
        self.assertEqual((s["supported"], s["uncertain"], s["completed"]), (0, 439, 150))

    def test_apply_stamps_every_finding_and_counts_tiers(self):
        fs = findings(self.out)
        self.assertTrue(all(f["tier"] in ("ai_confident", "needs_human") for f in fs))
        self.assertTrue(all(isinstance(f["tier_reasons"], list) and "audit" in f for f in fs))
        s = self.out["summary"]
        self.assertEqual(s["aiConfident"] + s["needsHuman"], len(fs))

    def test_tier_basis_split_is_220_plus_37(self):
        basis = [f["tier_basis"] for f in findings(self.out) if f["tier"] == "ai_confident"]
        self.assertEqual(sum(b in ("not_dismissed", "both") for b in basis), 220)
        self.assertEqual(basis.count("skeptic_partly_confirmed"), 37)

    def test_only_ai_confident_findings_are_audit_sampled(self):
        fs = findings(self.out)
        self.assertFalse(any(f["audit"] for f in fs if f["tier"] == "needs_human"))
        self.assertEqual(self.out["summary"]["auditSample"], sum(f["audit"] for f in fs))

    def test_queue_holds_needs_human_and_audit_findings(self):
        s = self.out["summary"]
        self.assertEqual(len(self.out["reviewQueue"]), s["needsHuman"] + s["auditSample"])

    def test_events_carry_text_hash_and_summary_names_the_detector(self):
        self.assertRegex(self.out["events"][0]["text"], r"^[0-9a-f]{64}$")
        self.assertEqual(set(self.out["summary"]["detector"]), {"card_hash", "prompts_version", "max_candidates"})

    def _status(self, status, applied=True):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = Path(d.name) / "card_status.json"
        path.write_text(json.dumps({"cards": {"framing-effect": {"status": status, "applied": applied}}}))
        return apply(RUN, card_status_path=path)

    def test_apply_drops_findings_of_hidden_cards_and_counts_them(self):
        out = self._status("hidden")
        self.assertEqual(out["summary"]["hiddenByGate"], 119)
        self.assertFalse(any(f["id"] == "framing-effect" for f in findings(out)))

    def test_demoted_card_findings_all_need_human(self):
        out = self._status("demoted")
        self.assertEqual({f["tier"] for f in findings(out) if f["id"] == "framing-effect"}, {"needs_human"})

    def test_status_that_is_not_applied_changes_nothing(self):
        out = self._status("hidden", applied=False)
        self.assertEqual(out["summary"]["hiddenByGate"], 0)
        self.assertEqual(out["summary"]["aiConfident"], 257)


if __name__ == "__main__":
    unittest.main()
