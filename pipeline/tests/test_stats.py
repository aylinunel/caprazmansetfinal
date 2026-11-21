import unittest

from capraz_pipeline.stats import bh_q, cmh_p, mh_rr

S = [(8, 10, 10, 40), (6, 10, 5, 40)]


class StatsTest(unittest.TestCase):
    def test_mh_rr_and_interval(self):
        rr, lo, hi = mh_rr(S)
        self.assertAlmostEqual(rr, 3.7333, places=4)
        self.assertAlmostEqual(lo, 2.2015, places=4)
        self.assertAlmostEqual(hi, 6.3311, places=4)

    def test_cmh_p(self):
        self.assertAlmostEqual(cmh_p(S), 2.1324e-05, delta=1e-8)

    def test_strata_without_others_are_dropped(self):
        self.assertEqual(mh_rr(S + [(1, 1, 0, 0)]), mh_rr(S))

    def test_zero_and_infinite_ratios_stay_json_safe(self):
        rr, lo, hi = mh_rr([(0, 10, 5, 40), (0, 10, 4, 40)])
        self.assertEqual((rr, lo, hi), (0.0, None, None))
        rr, lo, hi = mh_rr([(5, 10, 0, 40)])
        self.assertEqual((rr, lo, hi), (None, None, None))

    def test_bh(self):
        self.assertEqual([round(q, 4) for q in bh_q([0.01, 0.04, 0.03, 0.005])], [0.02, 0.04, 0.04, 0.02])


if __name__ == "__main__":
    unittest.main()
