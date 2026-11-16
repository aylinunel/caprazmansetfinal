import unittest

from capraz_pipeline.aix import auc, compute, kappa, spearman, wilson


def core_fixture():
    S = [{"s": "a", "lean": 20}, {"s": "b", "lean": 80}, {"s": "c", "lean": 50}]
    E, arts, bgm = [], {}, []
    for k in range(25):
        ev = f"e{k}"
        ids = [f"{ev}-{s['s']}" for s in S]
        E.append({"i": ev, "a": ids, "s": [s["s"] for s in S], "tp": ["siyaset"], "f": "2026-11-0%dT10:00" % (1 + k % 9), "bs": None})
        for i, s in zip(ids, S):
            arts[i] = {"s": s["s"], "d": "2026-11-01T10:00", "v": 30 if s["s"] == "a" else 5}
        cited = ["a"] if k % 2 else ["b"]
        bgm.append({"event": ev, "status": "review_complete", "outlets": 3,
                    "supported": [{"id": "word-choice", "name": "Word choice", "evidence": [{"q": "x", "o": cited}]}],
                    "uncertain": [{"id": "responsibility-framing", "name": "Resp", "evidence": [{"q": "y", "o": ["a"]}]}]})
    N = {"n1": {"ev": "e1", "rows": [{"s": "a", "blame": "Hükümet"}, {"s": "b", "blame": "belirtilmiyor"}, {"s": "c", "blame": ""}]}}
    return {"S": S, "E": E, "BGM": {"events": bgm}, "BG": {"events": []}, "N": N}, arts


class StatsTest(unittest.TestCase):
    def test_wilson_bounds(self):
        lo, hi = wilson(5, 10)
        self.assertTrue(0 < lo < .5 < hi < 1)
        self.assertEqual(wilson(0, 0), (0.0, 0.0))

    def test_auc_extremes(self):
        self.assertEqual(auc([3, 4], [1, 2]), 1.0)
        self.assertEqual(auc([1], [1]), 0.5)

    def test_spearman_and_kappa(self):
        self.assertAlmostEqual(spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(kappa(10, 0, 0, 10), 1.0)
        self.assertAlmostEqual(kappa(5, 5, 5, 5), 0.0)


class HelperTest(unittest.TestCase):
    def test_bloc_uses_the_configured_thresholds(self):
        from capraz_pipeline import aix
        from capraz_pipeline.config import PARAMS
        self.assertEqual(aix._bloc(PARAMS.bloc_left_below - 1), "left")
        self.assertEqual(aix._bloc(PARAMS.bloc_left_below), "mid")
        self.assertEqual(aix._bloc(PARAMS.bloc_right_above + 1), "right")
        self.assertIsNone(aix._bloc(None))

    def test_quote_without_outlets_falls_back_to_headlines(self):
        from capraz_pipeline.aix import _cited, _fold
        heads = [("a", _fold("İSTANBUL'da Fon VURGUNU soruşturması")), ("b", _fold("Fon soruşturması sürüyor"))]
        f = {"evidence": [{"q": "fon vurgunu", "o": []}, {"q": "x", "o": ["c"]}]}
        self.assertEqual(_cited(f, heads), {"a", "c"})
        self.assertEqual(_cited(f), {"c"})                       # no headlines given: only explicit outlets
        self.assertEqual(_fold("İĞÜŞÖÇI"), "igusoci")             # same folding as trFold in logic.js


class ComputeTest(unittest.TestCase):
    def test_compute_shapes_and_rates(self):
        core, arts = core_fixture()
        r = compute(core, arts)
        by = {o["s"]: o for o in r["wording"]["outlets"]}
        self.assertEqual(by["a"]["k"], 12)          # cited in odd events
        self.assertEqual(by["a"]["n"], 25)
        self.assertGreater(r["wording"]["headlines"]["auc"], .5)  # 'a' has the higher rule score
        heat = {h["id"]: h for h in r["heat"]}
        self.assertEqual(heat["word-choice"]["left"]["n"], 25)    # per outlet-event, not per event
        self.assertEqual(r["blame"]["events"], 1)
        self.assertEqual(r["blame"]["both"], 1)    # 'a': blame set and AI cited for responsibility
        self.assertEqual(r["blame"]["neither"], 2)


if __name__ == "__main__":
    unittest.main()
