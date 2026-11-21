import tempfile
import unittest
from pathlib import Path

from biasguard.news import _load
from validation.answerkey.agreement import krippendorff_alpha, percent_agreement
from validation.answerkey.codebook import blame_level, frame_category, human_rows, load_codebook
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
