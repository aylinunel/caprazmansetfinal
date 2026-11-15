import json
import tempfile
import unittest
from pathlib import Path

from biasguard import news
from biasguard.catalog import load_cards
from biasguard.engine import BiasGuard
from validation.feedback.labels import Label
from validation.learning.replay import ReplayCase, build, read, score, write, write_inputs
from validation.tests._stub import assessment

TEXT = "[A · 09:00] Bakan: kriz yok — Açıklama tekrarlandı\n[B · 09:05] Krizi herkes görüyor, bakan inkâr etti"
CONTEXT = "Olay: Bakan açıklaması\nKurumlar: A, B"
QUOTE = "Krizi herkes görüyor, bakan inkâr etti"
CARD = "framing-effect"
INPUTS = [{"event": "e1", "title": "t", "outlets": 2, "text": TEXT, "context": CONTEXT},
          {"event": "e2", "title": "t", "outlets": 2, "text": TEXT + " ek", "context": CONTEXT}]


def label(event, outcome, at="2026-11-14T00:00:00Z", text=None, card=CARD):
    import hashlib
    item = next(i for i in INPUTS if i["event"] == event)
    h = text or hashlib.sha256(item["text"].encode()).hexdigest()
    return Label(event, card, "p1", h, outcome, "not", "ai_confident", False, False, at)


class ReplayTest(unittest.TestCase):
    def test_every_review_becomes_exactly_one_case(self):
        cases = build([label("e1", "verified"), label("e2", "rejected")], INPUTS, [])
        self.assertEqual([(c.event, c.expect) for c in cases], [("e1", "present"), ("e2", "absent")])
        self.assertTrue(all(c.text and c.retired is None for c in cases))

    def test_corrected_expects_present(self):
        self.assertEqual(build([label("e1", "corrected")], INPUTS, [])[0].expect, "present")

    def test_rebuild_adds_nothing_when_no_new_labels(self):
        first = build([label("e1", "verified")], INPUTS, [])
        self.assertEqual(build([label("e1", "verified")], INPUTS, first), first)

    def test_case_keeps_its_original_text_when_the_pack_changes(self):
        first = build([label("e1", "verified")], INPUTS, [])
        changed = [{**INPUTS[0], "text": "bambaşka"}, INPUTS[1]]
        again = build([label("e1", "verified")], changed, first)
        self.assertEqual(again[0].text, TEXT)

    def test_label_for_text_no_longer_available_is_skipped(self):
        self.assertEqual(build([label("e1", "verified", text="f" * 64)], INPUTS, []), [])

    def test_superseded_label_retires_the_old_case(self):
        first = build([label("e1", "verified", at="2026-11-14T00:00:00Z")], INPUTS, [])
        again = build([label("e1", "verified", at="2026-11-14T00:00:00Z"),
                       label("e1", "rejected", at="2026-11-15T00:00:00Z")], INPUTS, first)
        self.assertEqual([(c.expect, c.retired) for c in again], [("present", "superseded"), ("absent", None)])

    def test_file_round_trip_is_append_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "replay.jsonl"
            first = build([label("e1", "verified")], INPUTS, [])
            write(path, first)
            write(path, build([label("e1", "verified"), label("e2", "rejected")], INPUTS, read(path)))
            self.assertEqual([c.event for c in read(path)], ["e1", "e2"])

    def _reviewed_run(self, d, cases, verdicts):
        run = Path(d)
        write_inputs(cases, run)
        cards = load_cards()
        by_id = {c["id"]: c for c in cards}
        bg = BiasGuard(cards=cards)
        for item in news._inputs(run):
            verdict = verdicts.get(item["event"])
            if verdict is None:
                continue   # no reviewer output: a failed review
            (run / "selections").mkdir(exist_ok=True)
            (run / "selections" / f"{item['event']}.json").write_text(json.dumps(
                {"candidate_ids": [CARD], "selection_uncertainty": [], "selection_note": ""}))
            ids = news.selected_cards(bg, run, item)
            for role in ("advocate", "skeptic"):
                (run / "reviews" / role).mkdir(parents=True, exist_ok=True)
                out = [assessment(by_id[i], verdict if i == CARD else "not_supported", QUOTE if i == CARD else "")
                       for i in ids]
                (run / "reviews" / role / f"{item['event']}.json").write_text(
                    json.dumps({"role": role, "assessments": out}, ensure_ascii=False))
        return run, cards

    def test_rejected_finding_reappearing_is_counted_as_reintroduced(self):
        cases = build([label("e1", "verified"), label("e2", "rejected")], INPUTS, [])
        ids = {c.event: c.case_id for c in cases}
        with tempfile.TemporaryDirectory() as d:
            run, cards = self._reviewed_run(d, cases, {ids["e1"]: "supported", ids["e2"]: "supported"})
            s = score(cases, run, cards)
        self.assertEqual((s["kept_present"], s["reintroduced_absent"], s["lost_present"], s["errors"]), (1, 1, 0, 0))
        self.assertEqual(s["by_card"][CARD]["reintroduced_absent"], 1)

    def test_rejected_finding_still_raised_as_uncertain_is_counted_separately(self):
        cases = build([label("e2", "rejected")], INPUTS, [])
        with tempfile.TemporaryDirectory() as d:
            run, cards = self._reviewed_run(d, cases, {cases[0].case_id: "uncertain"})
            s = score(cases, run, cards)
        self.assertEqual((s["still_shown_absent"], s["reintroduced_absent"], s["kept_absent"]), (1, 0, 0))

    def test_present_case_that_is_now_suppressed_is_lost(self):
        cases = build([label("e1", "verified")], INPUTS, [])
        with tempfile.TemporaryDirectory() as d:
            run, cards = self._reviewed_run(d, cases, {cases[0].case_id: "not_supported"})
            self.assertEqual(score(cases, run, cards)["lost_present"], 1)

    def test_reviewer_failure_counts_as_error_not_as_kept(self):
        cases = build([label("e1", "verified")], INPUTS, [])
        with tempfile.TemporaryDirectory() as d:
            run, cards = self._reviewed_run(d, cases, {})
            s = score(cases, run, cards)
        self.assertEqual((s["errors"], s["kept_present"]), (1, 0))

    def test_retired_cases_are_not_scored(self):
        case = build([label("e1", "verified")], INPUTS, [])[0]
        retired = ReplayCase(**{**case.__dict__, "retired": "superseded"})
        with tempfile.TemporaryDirectory() as d:
            run, cards = self._reviewed_run(d, [retired], {})
            self.assertEqual(score([retired], run, cards)["scored"], 0)


if __name__ == "__main__":
    unittest.main()
