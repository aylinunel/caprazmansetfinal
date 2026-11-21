"""Offline checks for the 7.0 changes: field-independent behavioral gate and fail-closed replay.

    python -m unittest biasguard.test_news -v
"""
import json
import tempfile
import unittest
from pathlib import Path

from biasguard.engine import BiasGuard
from biasguard.news import FileReviewer, apply, merge_explain, validate_explain

TEXT = "[A · 09:00] Bakan: kriz yok — Açıklama tekrarlandı\n[B · 09:05] Krizi herkes görüyor, bakan inkâr etti"
CONTEXT = "Olay: Bakan açıklaması\nKurumlar: A, B"


def _card(policy):
    bg = BiasGuard()
    return next(c for c in bg.cards if c.get("review_policy") == policy)


def _review(card, role, kind, source="text"):
    quote = "Krizi herkes görüyor, bakan inkâr etti" if source == "text" else "Olay: Bakan açıklaması"
    return {"role": role, "assessments": [{
        "card_id": card["id"], "verdict": "supported",
        "evidence": [{"source": source, "quote": quote, "kind": kind}],
        "necessary_conditions": [{"condition_index": i, "status": "satisfied", "evidence_indices": [0]}
                                 for i in range(len(card["necessary_conditions"]))],
        "mechanism": "m", "alternative_explanation": "a", "missing_context": []}]}


class Reviewer:
    def __init__(self, card, kind):
        self.card, self.kind = card, kind

    def select(self, text, context, cards, n):
        return {"candidate_ids": [self.card["id"]], "selection_uncertainty": [], "selection_note": ""}

    def review(self, text, context, cards, role):
        assert [c["id"] for c in cards][0] == self.card["id"]
        out = _review(self.card, role, self.kind)
        # every selected card must be assessed; the rest are plain not_supported
        for c in cards[1:]:
            out["assessments"].append({"card_id": c["id"], "verdict": "not_supported", "evidence": [],
                                       "necessary_conditions": [], "mechanism": "", "alternative_explanation": "",
                                       "missing_context": []})
        return out


class GateTests(unittest.TestCase):
    def run_card(self, kind):
        card = _card("requires_behavioral_evidence")
        r = BiasGuard(reviewer=Reviewer(card, kind)).analyze(TEXT, CONTEXT, mode="ai", max_candidates=6)
        self.assertEqual(r["status"], "review_complete")
        return card, r

    def test_behavioral_quote_from_text_field_is_accepted(self):
        card, r = self.run_card("behavioral")
        self.assertIn(card["id"], [f["id"] for f in r["supported_findings"]])

    def test_statement_quote_still_cannot_publish_behavioral_card(self):
        card, r = self.run_card("statement")
        self.assertNotIn(card["id"], [f["id"] for f in r["supported_findings"]])
        self.assertIn(card["id"], [f["id"] for f in r["uncertain_findings"]])


class ReplayTests(unittest.TestCase):
    def test_missing_outputs_never_count_as_complete(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            items = [{"event": f"e{i}", "title": "t", "outlets": 2, "text": TEXT, "context": CONTEXT} for i in range(3)]
            (run / "inputs.jsonl").write_text("".join(json.dumps(x) + "\n" for x in items))
            (run / "selections").mkdir()
            (run / "selections" / "e0.json").write_text(json.dumps(
                {"candidate_ids": [], "selection_uncertainty": [], "selection_note": ""}))
            (run / "selections" / "e1.json").write_text("{not json")
            res = apply(run)
            st = {x["event"]: x["status"] for x in res["events"]}
            self.assertEqual(st, {"e0": "analysis_incomplete", "e1": "analysis_incomplete", "e2": "not_attempted"})
            self.assertEqual(res["summary"]["completed"], 0)

    def test_file_reviewer_raises_on_missing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Exception):
                FileReviewer(Path(d), "x").review("", "", [], "advocate")


GOOD = {"noticed": "A ve B aynı olayı farklı başlıkla verdi; B “Krizi herkes görüyor, bakan inkâr etti” dedi.",
        "why": "Başlık farkı tek başına niyet göstermez, okuyucuya bakan açıklamasının tamamı verilmemiş olabilir."}


class ExplainTests(unittest.TestCase):
    def test_validate_explain_accepts_good(self):
        self.assertEqual(validate_explain(GOOD, TEXT), [])

    def test_validate_explain_checks_means_when_present(self):
        self.assertEqual(validate_explain({**GOOD, "means": GOOD["why"]}, TEXT), [])
        self.assertTrue(validate_explain({**GOOD, "means": "kısa"}, TEXT))

    def test_validate_explain_rejects_status_words(self):
        for w in ("bağlam gerekli", "desteklendi", "uncertain"):
            bad = {**GOOD, "why": f"Bu durumda {w} çünkü başlıklar farklı ve okuyucu için eksik bilgi kalıyor."}
            self.assertTrue(validate_explain(bad, TEXT), w)

    def test_validate_explain_rejects_invented_quote(self):
        bad = {**GOOD, "noticed": "B başlığında “Bakan tamamen yalan söyledi ve istifa etti” yazıyor ve A bunu vermedi."}
        self.assertTrue(any("quote" in p for p in validate_explain(bad, TEXT)))

    def test_validate_explain_rejects_length_and_sentences(self):
        self.assertTrue(validate_explain({"noticed": "Kısa.", "why": GOOD["why"]}, TEXT))
        three = "Bir cümle burada yazıyor. İkinci cümle de burada yazıyor. Üçüncü cümle fazla olur burada."
        self.assertTrue(validate_explain({"noticed": three, "why": GOOD["why"]}, TEXT))

    def test_sentence_count_ignores_quotes_and_decimals(self):
        t = "[A · 09:00] Kanser tedavisi görüyordu! İş adamı Ahmet hayatını kaybetti\n[B · 09:01] 3.5 milyon lira"
        a = {"noticed": "A haberi “Kanser tedavisi görüyordu! İş adamı Ahmet hayatını kaybetti” diye verdi.", "why": GOOD["why"]}
        self.assertEqual(validate_explain(a, t), [])
        b = {"noticed": "B haberi 3.5 milyon lira diye verdi, A ise rakam vermedi ve başka bir çerçeve seçti.", "why": GOOD["why"]}
        self.assertEqual(validate_explain(b, t), [])

    def test_pack_carries_explain(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            (run / "explain").mkdir()
            (run / "explain" / "e0__c1.json").write_text(json.dumps(GOOD))
            (run / "explain" / "e0__c2.json").write_text(json.dumps({"noticed": "x", "why": "y"}))
            (run / "inputs.jsonl").write_text(json.dumps({"event": "e0", "text": TEXT, "context": CONTEXT}) + "\n")
            bg = {"events": [{"event": "e0", "supported": [{"id": "c1"}], "uncertain": [{"id": "c2"}]}]}
            merge_explain(bg, run)
            ev = bg["events"][0]
            self.assertEqual(ev["supported"][0]["explain"], GOOD)
            self.assertNotIn("explain", ev["uncertain"][0])


class TaskCatalogTests(unittest.TestCase):
    def _run(self, d):
        run = Path(d)
        (run / "inputs.jsonl").write_text(json.dumps(
            {"event": "e0", "title": "t", "outlets": 2, "text": TEXT, "context": CONTEXT}) + "\n")
        return run

    def _selected_run(self, d):
        # _run (inputs.jsonl with event e0) plus a selection, so the review stage has cards to send
        run = self._run(d)
        (run / "selections").mkdir()
        (run / "selections" / "e0.json").write_text(json.dumps(
            {"candidate_ids": ["framing-effect"], "selection_uncertainty": [], "selection_note": ""}))
        return run

    def test_review_tasks_carry_examples_from_other_events_only(self):
        from biasguard.news import write_tasks
        ex = {"framing-effect": [{"event": "e0", "text": "x", "present": "yes"},
                                 {"event": "e9", "text": "y", "present": "no"},
                                 {"event": "e8", "text": "z", "present": "yes"},
                                 {"event": "e7", "text": "w", "present": "no"}]}
        with tempfile.TemporaryDirectory() as d:
            run = self._selected_run(d)
            path = write_tasks(run, "review", 10, examples=ex)[0]
            task = json.loads(path.read_text())
            card = next(c for c in task["cards"] if c["id"] == "framing-effect")
        self.assertEqual([e["event"] for e in card["examples"]], ["e9", "e8"])  # never e0; at most 2
        self.assertIn("Örnekler başka olaylardan", task["system_prompt"])

    def test_no_examples_file_leaves_tasks_unchanged(self):
        from biasguard.news import write_tasks
        with tempfile.TemporaryDirectory() as d:
            task = json.loads(write_tasks(self._selected_run(d), "review", 10)[0].read_text())
        self.assertFalse(any("examples" in c for c in task["cards"]))
        self.assertNotIn("Örnekler başka olaylardan", task["system_prompt"])

    def test_small_catalogue_sends_every_card_like_the_engine(self):
        # the engine reviews every card of a catalogue at or under _DIRECT_REVIEW_LIMIT; the tasks must ask for all of them
        with tempfile.TemporaryDirectory() as d:
            from biasguard.engine import BiasGuard
            from biasguard.news import selected_cards
            run = self._run(d)
            small = BiasGuard(cards=BiasGuard().cards[:9])
            (run / "selections").mkdir()
            (run / "selections" / "e0.json").write_text(json.dumps(
                {"candidate_ids": [small.cards[0]["id"]], "selection_uncertainty": [], "selection_note": ""}))
            item = json.loads((run / "inputs.jsonl").read_text())
            self.assertEqual(selected_cards(small, run, item), [c["id"] for c in small.cards])

    def test_write_tasks_default_uses_the_stock_catalogue(self):
        with tempfile.TemporaryDirectory() as d:
            from biasguard.news import write_tasks
            task = json.loads(write_tasks(self._run(d), "select", 10)[0].read_text())
            self.assertEqual(len(task["cards"]), len(BiasGuard().cards))

    def test_review_tasks_are_one_file_per_role(self):
        with tempfile.TemporaryDirectory() as d:
            from biasguard.news import write_tasks
            run = self._run(d)
            sel = json.loads(write_tasks(run, "select", 10)[0].read_text())
            self.assertNotIn("enum", sel["output_schema"]["properties"]["candidate_ids"]["items"])
            ids = [c["id"] for c in sel["cards"][:2]]
            for e in sel["events"]:
                (run / "selections").mkdir(exist_ok=True)
                (run / "selections" / f"{e['event']}.json").write_text(json.dumps(
                    {"candidate_ids": ids, "selection_uncertainty": [], "selection_note": ""}))
            paths = write_tasks(run, "review", 10)
            self.assertEqual(sorted(p.parent.name for p in paths), ["advocate", "skeptic"])
            for p in paths:
                t = json.loads(p.read_text())
                self.assertEqual(t["role"], p.parent.name)
                self.assertEqual(t["schema_example"]["properties"]["role"]["const"], p.parent.name)
                self.assertNotIn("provenance", t["cards"][0])
                self.assertIn("necessary_conditions", t["cards"][0])

    def test_write_tasks_accepts_another_catalogue(self):
        with tempfile.TemporaryDirectory() as d:
            from biasguard.news import write_tasks
            small = BiasGuard(cards=BiasGuard().cards[:20])
            task = json.loads(write_tasks(self._run(d), "select", 10, bg=small)[0].read_text())
            self.assertEqual(len(task["cards"]), 20)


class RollbackTests(unittest.TestCase):
    def test_writing_results_keeps_the_previous_file(self):
        from biasguard.news import write_results
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "biasguard.json"
            write_results(out, {"v": 1})
            self.assertFalse((Path(d) / "biasguard.prev.json").exists())
            write_results(out, {"v": 2})
            self.assertEqual(json.loads(out.read_text()), {"v": 2})
            self.assertEqual(json.loads((Path(d) / "biasguard.prev.json").read_text()), {"v": 1})

    def test_rewriting_identical_results_does_not_replace_the_previous_file(self):
        from biasguard.news import write_results
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "biasguard.json"
            write_results(out, {"v": 1}); write_results(out, {"v": 2}); write_results(out, {"v": 2})
            self.assertEqual(json.loads((Path(d) / "biasguard.prev.json").read_text()), {"v": 1})


class MediaPassTests(unittest.TestCase):
    """The media-technique pass ("Medyanın oyunları") runs apart from the behavioural one."""

    def _run(self, d, card):
        run = Path(d)
        (run / "inputs.jsonl").write_text(json.dumps(
            {"event": "e0", "title": "t", "outlets": 2, "text": TEXT, "context": CONTEXT}) + "\n")
        for role in ("advocate", "skeptic"):
            (run / "reviews" / role).mkdir(parents=True)
            (run / "reviews" / role / "e0.json").write_text(json.dumps(_review(card, role, "behavioral")))
        return run

    def test_media_apply_uses_only_the_given_media_cards_and_tiers_findings(self):
        card = {**BiasGuard().cards[0], "id": "labeling", "name": "Labeling", "entry_type": "media_practice",
                "review_policy": "media_pattern_review"}
        with tempfile.TemporaryDirectory() as d:
            out = apply(self._run(d, card), catalog="media", cards=[card])
        f = out["events"][0]["supported"][0]
        self.assertEqual((f["id"], f["entry_type"], f["tier"]), ("labeling", "media_practice", "ai_confident"))
        self.assertEqual((out["catalog"], out["summary"]["catalog"]), ("media", 1))

    def test_cards_that_have_not_passed_the_lab_go_to_pending(self):
        card = {**BiasGuard().cards[0], "id": "labeling", "name": "Labeling", "entry_type": "media_practice",
                "review_policy": "media_pattern_review"}
        from unittest import mock
        with tempfile.TemporaryDirectory() as d:
            run = self._run(d, card)
            (run / "catalog.json").write_text(json.dumps([card]))   # the run was reviewed against "labeling"
            with mock.patch("biasguard.news.load_media_cards", return_value=[]):   # ...which has not passed the lab
                out = apply(run, catalog="media")
        self.assertEqual(out["events"][0]["supported"], [])
        self.assertEqual((out["summary"]["supported"], out["summary"]["cardIds"]), (0, []))
        self.assertEqual(out["pending"]["cards"], [{"id": "labeling", "name": "Labeling"}])
        self.assertEqual(out["pending"]["events"][0]["supported"][0]["id"], "labeling")

    def test_default_catalog_is_behavioural(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            (run / "inputs.jsonl").write_text("")
            out = apply(run)
        self.assertEqual((out["catalog"], out["summary"]["catalog"]), ("behavioural", 116))

    def test_empty_media_catalogue_refuses_to_apply(self):
        with tempfile.TemporaryDirectory() as d:
            run = Path(d)
            (run / "inputs.jsonl").write_text("")
            with self.assertRaisesRegex(ValueError, "media catalogue is empty"):
                apply(run, catalog="media", cards=[])


if __name__ == "__main__":
    unittest.main()
