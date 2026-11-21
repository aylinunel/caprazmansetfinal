import json
import tempfile
import unittest
from argparse import Namespace
from unittest import mock
from datetime import date
from pathlib import Path

from biasguard.news import _load
from validation.answerkey.agreement import krippendorff_alpha, percent_agreement
from validation.answerkey.narrative_eval import compare
from validation.answerkey.behaviour_eval import as_card_stats, measure
from validation.answerkey.codebook import blame_level, frame_category, human_rows, load_codebook
from validation.answerkey.packets import behaviour_packet, read_export, repeat_packet, upsert
from validation.answerkey.record import Coding, agreement, append, from_core, gold

REPO = Path(__file__).resolve().parents[2]


class AlphaTest(unittest.TestCase):
    def test_textbook_example(self):  # Krippendorff (2011), "Computing Krippendorff's alpha", nominal: 0.743
        K = [[1, 1, None, 1], [2, 2, 3, 2], [3, 3, 3, 3], [3, 3, 3, 3], [2, 2, 2, 2], [1, 2, 3, 4], [4, 4, 4, 4],
             [1, 1, 2, 1], [2, 2, 2, 2], [None, 5, 5, 5], [None, None, 1, 1], [None, None, 3, None]]
        units = [[None if v is None else str(v) for v in u] for u in K]
        self.assertAlmostEqual(krippendorff_alpha(units), 0.743, places=3)

    def test_small_cases(self):
        self.assertAlmostEqual(krippendorff_alpha([["a", "a"], ["a", "a"], ["b", "b"], ["a", "b"]]), 0.5333, places=4)
        self.assertEqual(krippendorff_alpha([["a", "a"], ["b", "b"], ["c", "c"]]), 1.0)
        self.assertIsNone(krippendorff_alpha([["a", "a"], ["a", "a"]]))  # one value only: undefined
        self.assertAlmostEqual(
            krippendorff_alpha([["a", "a", None], ["a", "b", "b"], [None, "c", "c"], ["a", None, None]]), 0.625, places=4)

    def test_percent(self):
        self.assertEqual(percent_agreement([["a", "a"], ["a", "b"], ["c", None]]), 0.5)


class CodebookTest(unittest.TestCase):
    def test_blame_level(self):
        self.assertEqual(blame_level(""), "none")
        for raw in ("—", "Belirtilmiyor", "Belirsiz (ima)"):
            self.assertEqual(blame_level(raw), "none")
        self.assertEqual(blame_level("Yargı (ima)"), "implied")
        self.assertEqual(blame_level("Belediye yönetimi"), "explicit")

    def test_frame_category(self):
        cb = {"categories": ["Yargı ve soruşturma", "Diğer"], "frames": {"Adli süreç": "Yargı ve soruşturma"}}
        self.assertEqual(frame_category(" Adli süreç ", cb), "Yargı ve soruşturma")
        self.assertEqual(frame_category("Adli surec", cb), "Diğer")  # unmapped spelling -> Diğer, never a guess
        self.assertEqual(frame_category("", cb), "Diğer")

    def test_codebook_covers_every_human_frame(self):
        cb = load_codebook()
        core = _load(REPO / "public" / "data" / "core.bin")
        raw = {(r.get("frame") or "").strip() for r in human_rows(core)} - {""}
        self.assertEqual(sorted(raw - set(cb["frames"])), [])
        self.assertTrue(set(cb["frames"].values()) <= set(cb["categories"]))
        self.assertEqual(cb["categories"][-1], "Diğer")


class RecordTest(unittest.TestCase):
    def test_append_dedupes_and_refuses_a_changed_answer(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            a = Coding("e1__framing-effect", "A1", "present", "yes")
            self.assertEqual(append([a, a], p), 1)
            with self.assertRaisesRegex(ValueError, "e1__framing-effect"):
                append([Coding("e1__framing-effect", "A1", "present", "no")], p)
            with self.assertRaisesRegex(ValueError, "Ayşe"):
                append([Coding("e2__framing-effect", "Ayşe", "present", "no")], p)  # names never stored
            self.assertEqual(len(p.read_text(encoding="utf-8").splitlines()), 1)

    def test_append_checks_values_and_writes_nothing_on_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.jsonl"
            ok = Coding("i1", "A1", "present", "yes")
            for bad in (Coding("i2", "A1", "present", "maybe"), Coding("i2", "A1", "colour", "yes"),
                        Coding("i2", "A1", "frame_category", "not a category")):
                with self.assertRaises(ValueError):
                    append([ok, bad], p)
            self.assertFalse(p.exists())

    def test_conflicting_duplicate_slot_is_an_error(self):  # e.g. a file record colliding with a core A1 row
        a, b = Coding("k1__sabah", "A1", "present", "yes"), Coding("k1__sabah", "A1", "present", "no")
        with self.assertRaisesRegex(ValueError, "k1__sabah.*A1.*present"):
            agreement([a, b], "present")
        with self.assertRaises(ValueError):
            gold([a, b], "present")
        self.assertEqual(agreement([a, a], "present")["items_double"], 0)  # identical duplicate is fine

    def test_gold_and_disagreement(self):
        cs = [Coding("i1", "A1", "present", "yes"), Coding("i1", "A2", "present", "yes"),
              Coding("i2", "A1", "present", "yes"), Coding("i2", "A2", "present", "no"),
              Coding("i3", "A1", "present", "unsure")]
        self.assertEqual(gold(cs, "present"), ({"i1": "yes"}, ["i2"]))

    def test_usable_needs_thirty_items_coded_twice(self):
        cs = [Coding(f"i{n}", c, "present", "yes" if n % 2 else "no") for n in range(29) for c in ("A1", "A2")]
        self.assertFalse(agreement(cs, "present")["usable"])
        cs += [Coding("i29", c, "present", "yes") for c in ("A1", "A2")]
        self.assertTrue(agreement(cs, "present")["usable"])

    def test_two_passes_of_one_person_are_same_coder(self):
        cs = [Coding("i1", "A1", "present", "yes"), Coding("i1", "A2", "present", "yes")]
        self.assertEqual(agreement(cs, "present")["kind"], "same coder")
        self.assertEqual(agreement(cs + [Coding("i1", "B1", "present", "no")], "present")["kind"], "between coders")

    def test_core_rows_become_coder_a(self):
        core = {"N": {"k1": {"status": "headline_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": "Yargı (ima)"}]},
                      "k2": {"status": "agent_coded", "rows": [{"s": "sabah", "frame": "Adli süreç", "blame": ""}]}}}
        cb = {"categories": ["Yargı ve soruşturma", "Diğer"], "frames": {"Adli süreç": "Yargı ve soruşturma"}}
        self.assertEqual(sorted(from_core(core, cb)), [Coding("k1__sabah", "A1", "blame_level", "implied"),
                                                       Coding("k1__sabah", "A1", "frame_category", "Yargı ve soruşturma")])


RESULTS_FIXTURE = {"events": [{"event": "e1", "status": "review_complete", "selected": ["c1"], "supported": [],
                              "uncertain": [{"id": "c1"}]}]}
INPUTS_FIXTURE = {"e1": {"event": "e1", "title": "T", "text": "[a · 10:00] x"}}
CARDS_FIXTURE = [{"id": f"c{i}", "name": f"Card {i}", "definition": "d", "necessary_conditions": ["k"]} for i in range(1, 5)]
PACKETS_FIXTURE = {"packets": [{"id": "b-A1", "kind": "behaviour", "coder": "A1", "items": [{"item": "e1__c1"}]}]}


class PacketTest(unittest.TestCase):
    def test_behaviour_packet_is_balanced_and_carries_no_verdict(self):
        p, key = behaviour_packet(RESULTS_FIXTURE, INPUTS_FIXTURE, CARDS_FIXTURE, n_events=1, seed=1,
                                  pid="b-A1", coder="A1", today=date(2026, 11, 21))
        self.assertEqual(len(p["items"]), 3)  # 1 shown finding + max(1, 2) unselected cards
        self.assertEqual(set(p["items"][0]), {"item", "event", "card", "ad", "tanim", "kosullar"})
        self.assertNotIn("ai_shown", json.dumps(p))
        self.assertEqual(key["_unflagged"], {"e1": {"sampled": 2, "total": 3}})

    def test_repeat_packet_opens_after_the_gap(self):
        first = {"id": "b-A1", "kind": "behaviour", "coder": "A1", "events": {}, "items": [{"item": f"e1__c{i}"} for i in range(4)]}
        cs = [Coding("e1__c0", "A1", "present", "yes"), Coding("e1__c1", "A1", "present", "no"),
              Coding("e1__c2", "A1", "present", "unsure")]
        p = repeat_packet(first, cs, n_items=2, seed=1, pid="b-A2", coder="A2", today=date(2026, 11, 21))
        self.assertEqual(p["not_before"], "2026-12-05")
        self.assertEqual(sorted(i["item"] for i in p["items"]), ["e1__c0", "e1__c1"])
        with self.assertRaisesRegex(ValueError, "2"):
            repeat_packet(first, cs, n_items=3, seed=1, pid="b-A2", coder="A2", today=date(2026, 11, 21))

    def test_read_export_maps_answers_to_the_packet_slot(self):
        ex = {"reviews": [{"key": "blind__b-A1__e1__c1", "status": "coded", "answers": {"present": "yes"}},
                          {"key": "s1__framing-effect", "status": "verified"}]}
        self.assertEqual(read_export(ex, PACKETS_FIXTURE), [Coding("e1__c1", "A1", "present", "yes")])

    def test_read_export_refuses_an_item_no_packet_has(self):
        ex = {"reviews": [{"key": "blind__b-A1__e9__c1", "status": "coded", "answers": {"present": "yes"}}]}
        with self.assertRaisesRegex(ValueError, "blind__b-A1__e9__c1"):
            read_export(ex, PACKETS_FIXTURE)

    def test_upsert_refuses_changed_items(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "p.json"
            upsert({"id": "x", "items": [{"item": "a"}]}, ["Diğer"], path)
            upsert({"id": "x", "items": [{"item": "a"}]}, ["Diğer"], path)
            with self.assertRaisesRegex(ValueError, "x"):
                upsert({"id": "x", "items": [{"item": "b"}]}, ["Diğer"], path)

    def test_upsert_refuses_an_id_with_double_underscore(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, "a__b"):
                upsert({"id": "a__b", "items": []}, ["Diğer"], Path(d) / "p.json")


class CliTest(unittest.TestCase):
    def test_refused_rerun_leaves_the_key_file_unchanged(self):
        from biasguard.catalog import load_cards
        from validation.answerkey import __main__ as cli
        cid = load_cards()[0]["id"]
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            run = d / "run"
            run.mkdir()
            (run / "biasguard.json").write_text(json.dumps({"events": [
                {"event": "e1", "status": "review_complete", "selected": [cid], "supported": [], "uncertain": []}]}))
            (run / "inputs.jsonl").write_text(json.dumps({"event": "e1", "title": "T", "text": "x"}) + "\n")
            args = lambda seed: Namespace(repeat=None, kind="behaviour", run=run, events=1, items=None, coder="A1",
                                          id="b-A1", seed=seed, core=None)
            with mock.patch.object(cli, "KEYS", d / "keys"):
                cli.make_packet(args(1), d / "p.json")
                key = (d / "keys" / "b-A1.key.json").read_text(encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "b-A1"):
                    cli.make_packet(args(2), d / "p.json")
                self.assertEqual((d / "keys" / "b-A1.key.json").read_text(encoding="utf-8"), key)

    def test_agreement_command_writes_the_report(self):
        from validation.answerkey import __main__ as cli
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.md"
            with mock.patch.object(cli, "REPORT", out), mock.patch("builtins.print"):
                cli.main(["agreement", "--core", str(REPO / "public" / "data" / "core.bin")])
            self.assertIn("# Answer key: agreement", out.read_text(encoding="utf-8"))


class NarrativeEvalTest(unittest.TestCase):
    CODEBOOK = {"approved": False, "categories": ["Yargı ve soruşturma", "Diğer"],
                "frames": {"Adli süreç": "Yargı ve soruşturma"}}

    def test_compare_scores_matching_rows_only(self):
        core = {"N": {"k1": {"status": "headline_coded", "rows": [
            {"s": "sabah", "frame": "Adli süreç", "blame": "Yargı"}, {"s": "ntv", "frame": "Adli süreç", "blame": ""}]}}}
        agent = {"k1": {"rows": [{"s": "sabah", "frame": "Adli süreç", "blame": "Savcı"}, {"s": "ntv", "frame": "Spor", "blame": ""},
                                 {"s": "cnn", "frame": "x", "blame": ""}]}}
        r = compare(agent, core, self.CODEBOOK)
        self.assertEqual((r["blame_level"]["n"], r["blame_level"]["agreement"]), (2, 1.0))
        self.assertEqual(r["frame_category"]["agreement"], 0.5)
        self.assertEqual(r["unmapped_frames"], 1)

    def test_narrative_eval_command_writes_both_outputs(self):
        from validation.answerkey import __main__ as cli
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "coded").mkdir()
            core = _load(REPO / "public" / "data" / "core.bin")
            key = next(k for k, e in core["N"].items() if e.get("status") in ("hand_coded", "headline_coded"))
            rows = [{"s": r["s"], "frame": r["frame"], "blame": r["blame"]} for r in core["N"][key]["rows"]]
            (d / "coded" / f"{key}.json").write_text(json.dumps({"rows": rows}, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(cli, "NARRATIVE_QUALITY", d / "q.json"), mock.patch.object(cli, "NARRATIVE_REPORT", d / "r.md"), \
                    mock.patch("builtins.print"):
                cli.main(["narrative-eval", "--coded", str(d / "coded"), "--core", str(REPO / "public" / "data" / "core.bin")])
            q = json.loads((d / "q.json").read_text(encoding="utf-8"))
            self.assertEqual(q["events"], 1)
            self.assertEqual(q["blame_level"]["agreement"], 1.0)
            self.assertIn("measured", q)
            self.assertIn("# ", (d / "r.md").read_text(encoding="utf-8"))


class BehaviourEvalTest(unittest.TestCase):
    KEY = {"e1__c1": {"event": "e1", "card": "c1", "ai_shown": True},
           "e1__c2": {"event": "e1", "card": "c2", "ai_shown": True},
           "e1__c3": {"event": "e1", "card": "c3", "ai_shown": False},
           "_unflagged": {"e1": {"sampled": 1, "total": 4}}}

    def test_measure_estimates_misses_from_the_unflagged_sample(self):
        m = measure({"e1__c1": "yes", "e1__c2": "no", "e1__c3": "yes"}, self.KEY)
        self.assertEqual((m["overall"]["tp"], m["overall"]["fp"], m["overall"]["missed_est"]), (1, 1, 4.0))
        self.assertEqual(m["overall"]["precision"], 0.5)
        self.assertAlmostEqual(m["overall"]["recall_est"], 0.2)
        self.assertEqual(as_card_stats(m)["c1"]["kept"], 1)

    def test_measure_with_no_gold_is_none_not_a_crash(self):
        m = measure({}, self.KEY)
        self.assertIsNone(m["overall"]["precision"])
        self.assertIsNone(m["overall"]["precision_lower"])
        self.assertIsNone(m["overall"]["recall_est"])

    def test_command_writes_report_and_status(self):
        from validation.answerkey import __main__ as cli
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "k.json").write_text(json.dumps(self.KEY), encoding="utf-8")
            with mock.patch.object(cli, "BEHAVIOUR_REPORT", d / "r.md"), mock.patch.object(cli, "CARD_STATUS", d / "s.json"), \
                    mock.patch.object(cli, "gold", return_value=({"e1__c1": "yes", "e1__c2": "no"}, [])), mock.patch("builtins.print"):
                cli.main(["behaviour-eval", "--key", str(d / "k.json"), "--status"])
            self.assertIn("# ", (d / "r.md").read_text(encoding="utf-8"))
            s = json.loads((d / "s.json").read_text(encoding="utf-8"))
            self.assertEqual(s["measure"], "blind precision")
            self.assertEqual(s["cards"]["c1"]["status"], "unjudged")
