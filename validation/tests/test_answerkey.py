import unittest

from validation.answerkey.agreement import krippendorff_alpha, percent_agreement


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
