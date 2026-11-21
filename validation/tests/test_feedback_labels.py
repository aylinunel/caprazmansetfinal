import json
import tempfile
import unittest
from pathlib import Path

from validation.feedback.labels import append, import_export, read

CARDS = {"framing-effect", "salience-bias"}
RESULTS = {"pack": "p1", "events": [{
    "event": "ev1", "text": "t" * 64, "status": "review_complete", "supported": [], "effects": [],
    "uncertain": [{"id": "framing-effect", "tier": "ai_confident", "audit": True},
                  {"id": "salience-bias", "tier": "needs_human", "audit": False}]}]}


def export(*reviews, pack="p1"):
    return {"pack": pack, "exported_at": "2026-11-14T10:00:00Z", "reviews": list(reviews)}


def rev(key, status="verified", note="", pack="p1", text="t" * 64, **extra):
    return {"key": key, "status": status, "note": note, "at": "2026-11-14T09:00:00Z", "pack": pack, "text": text, **extra}


class LabelsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "labels.jsonl"

    def tearDown(self):
        self.dir.cleanup()

    def test_blind_packet_reviews_are_skipped_like_narrative_ones(self):
        ls = import_export(export(rev("ev1__framing-effect"),
                                  rev("blind__behaviour-A1__ev1__framing-effect", "coded", answers={"present": "yes"}),
                                  rev("narr__k1", "coded")), RESULTS, CARDS)
        self.assertEqual([l.card_id for l in ls], ["framing-effect"])

    def test_import_round_trip(self):
        ls = import_export(export(rev("ev1__framing-effect"), rev("ev1__salience-bias", "rejected", "değil")),
                           RESULTS, CARDS)
        self.assertEqual(append(self.path, ls), 2)
        got = read(self.path)
        self.assertEqual([(l.card_id, l.outcome, l.tier_at_review, l.audit) for l in got],
                         [("framing-effect", "verified", "ai_confident", True),
                          ("salience-bias", "rejected", "needs_human", False)])
        self.assertEqual(got[1].note, "değil")

    def test_new_pattern_flag_is_carried(self):
        l = import_export(export(rev("ev1__framing-effect", "corrected", "n", new_pattern=True)), RESULTS, CARDS)[0]
        self.assertTrue(l.new_pattern)

    def test_structured_desk_review_is_carried_and_read_back(self):
        r = rev("ev1__framing-effect", "rejected", "", verdict="wrong", reason="wrong_concept", card="salience-bias",
                conditions=["met", "unmet"], ms=4200)
        append(self.path, import_export(export(r), RESULTS, CARDS))
        l = read(self.path)[0]
        self.assertEqual((l.verdict, l.reason, l.card_correct, l.conditions, l.seconds),
                         ("wrong", "wrong_concept", "salience-bias", ("met", "unmet"), 4.2))
        self.assertEqual(append(self.path, read(self.path)), 0)   # read-back labels are hashable and dedupe

    def test_desk_review_naming_an_unknown_concept_is_refused(self):
        r = rev("ev1__framing-effect", "rejected", verdict="wrong", reason="wrong_concept", card="no-such-card")
        with self.assertRaisesRegex(ValueError, "unknown correct concept"):
            import_export(export(r), RESULTS, CARDS)

    def test_old_label_lines_still_read(self):
        self.path.write_text(json.dumps({"event": "ev1", "card_id": "framing-effect", "pack_version": "p1", "text_sha256": "t",
                                         "outcome": "verified", "note": "", "tier_at_review": "", "audit": False,
                                         "new_pattern": False, "reviewed_at": ""}) + "\n")
        self.assertEqual(read(self.path)[0].reason, "")

    def test_narrative_reviews_are_skipped(self):
        ls = import_export(export(rev("narr__abc"), rev("ev1__framing-effect")), RESULTS, CARDS)
        self.assertEqual(len(ls), 1)

    def test_unknown_status_rejects_whole_file(self):
        with self.assertRaisesRegex(ValueError, "review 2"):
            import_export(export(rev("ev1__framing-effect"), rev("ev1__salience-bias", "maybe")), RESULTS, CARDS)

    def test_unknown_card_rejects_whole_file(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev1__no-such-card")), RESULTS, CARDS)

    def test_pair_not_in_results_rejects_whole_file(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev9__framing-effect")), RESULTS, CARDS)

    def test_bad_key_shape_rejects_whole_file(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev1-framing-effect")), RESULTS, CARDS)

    def test_duplicate_key_rejects_whole_file(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev1__framing-effect"), rev("ev1__framing-effect")), RESULTS, CARDS)

    def test_pack_mismatch_rejects_whole_file(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev1__framing-effect"), pack="p0"), RESULTS, CARDS)

    def test_review_made_on_other_text_is_rejected(self):
        with self.assertRaises(ValueError):
            import_export(export(rev("ev1__framing-effect", text="x" * 64)), RESULTS, CARDS)

    def test_append_is_idempotent(self):
        ls = import_export(export(rev("ev1__framing-effect")), RESULTS, CARDS)
        self.assertEqual((append(self.path, ls), append(self.path, ls)), (1, 0))
        self.assertEqual(len(read(self.path)), 1)

    def test_append_never_truncates(self):
        append(self.path, import_export(export(rev("ev1__framing-effect")), RESULTS, CARDS))
        append(self.path, import_export(export(rev("ev1__salience-bias", "rejected")), RESULTS, CARDS))
        self.assertEqual(len(read(self.path)), 2)

    def test_label_file_has_no_reviewer_identity(self):
        append(self.path, import_export(export(rev("ev1__framing-effect", user="aylin", email="a@b.c")), RESULTS, CARDS))
        self.assertNotRegex(self.path.read_text(encoding="utf-8"), r"aylin|a@b\.c|user|email")

    def test_read_missing_file_is_empty(self):
        self.assertEqual(read(self.path), [])


if __name__ == "__main__":
    unittest.main()
