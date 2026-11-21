import unittest
from pathlib import Path

from biasguard.news import _load
from validation.answerkey.agreement import krippendorff_alpha, percent_agreement
from validation.answerkey.codebook import blame_level, frame_category, human_rows, load_codebook

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
