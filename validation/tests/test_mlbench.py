import unittest

from validation.mlbench.data import Row
from validation.mlbench.evaluate import cross_validate, score_fixed
from validation.mlbench.models import Majority, TfidfLogReg


class MlbenchTest(unittest.TestCase):
    def test_groups_never_split_across_folds(self):
        rs = [Row(f"g{i // 3}", f"o{i}", f"metin {i}", "none" if i % 2 else "explicit", "Diğer") for i in range(30)]
        seen = []

        class Spy(Majority):
            def fit(self, texts, labels):
                seen.append(set(texts))
                super().fit(texts, labels)

        cross_validate(Spy, rs, "blame_level", folds=5)
        self.assertEqual(len(seen), 5)
        for train in seen:
            groups = {r.group for r in rs if r.text in train}
            self.assertFalse(any(r.group in groups and r.text not in train for r in rs))

    def test_single_class_training_fold_predicts_that_class(self):
        m = TfidfLogReg()
        m.fit(["a b", "c d"], ["none", "none"])
        self.assertEqual(m.predict(["e f"]), ["none"])

    def test_majority_baseline(self):
        rs = [Row("g1", "o", "x", "none", "Diğer")] * 3 + [Row("g2", "o", "y", "explicit", "Diğer")]
        self.assertEqual(score_fixed({("g1", "o"): "none", ("g2", "o"): "none"}, rs, "blame_level")["accuracy"], 0.75)


if __name__ == "__main__":
    unittest.main()
