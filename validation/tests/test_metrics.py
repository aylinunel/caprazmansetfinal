import unittest

from validation.biaslab.cases import expected
from validation.biaslab.metrics import Row, paired_bootstrap, ratio, summarize


def row(kind="positive", status="supported", family="f1", span_ok=True, resolvable=True, base_status=None, case="c"):
    e = expected(kind, resolvable)
    return Row(case, family, kind, status, e.acceptable, e.forbidden, span_ok, base_status)


class MetricsTest(unittest.TestCase):
    def test_zero_denominator_is_none(self):
        self.assertIsNone(ratio(0, 0))
        self.assertEqual(ratio(0, 4), 0.0)

    def test_precision_with_no_positives_predicted_is_none_not_one(self):
        s = summarize([row(kind="boundary_control", status="not_supported")])
        self.assertIsNone(s["strict_precision"]["value"])

    def test_errors_count_against_end_to_end_recall_but_not_conditional(self):
        s = summarize([row("positive", "supported"), row("positive", "error")])
        self.assertEqual((s["end_to_end_recall"]["value"], s["conditional_recall"]["value"]), (0.5, 1.0))

    def test_uncertain_counts_as_end_to_end_miss(self):
        s = summarize([row("positive", "supported"), row("positive", "uncertain")])
        self.assertEqual(s["end_to_end_recall"]["value"], 0.5)

    def test_supported_with_bad_span_is_not_a_strict_true_positive(self):
        s = summarize([row("positive", "supported", span_ok=False), row("positive", "supported")])
        self.assertEqual(s["strict_precision"]["value"], 0.5)

    def test_supported_control_lowers_precision_and_raises_forbidden_rate(self):
        s = summarize([row("positive", "supported"), row("quoted_control", "supported"),
                       row("quoted_control", "not_supported")])
        self.assertEqual(s["strict_precision"]["value"], 0.5)
        self.assertEqual(s["forbidden_rate"]["value"], 0.5)

    def test_ineligible_rows_leave_semantic_denominators(self):
        s = summarize([row("positive", "ineligible", resolvable=False), row("positive", "supported")])
        self.assertEqual(s["end_to_end_recall"]["d"], 1)
        self.assertEqual(s["eligible"]["value"], 0.5)

    def test_all_error_run_has_no_estimable_semantic_metric(self):
        s = summarize([row("positive", "error")] * 3)
        self.assertEqual(s["completion"]["value"], 0.0)
        self.assertIsNone(s["conditional_recall"]["value"])
        self.assertIsNone(s["strict_precision"]["value"])

    def test_missing_context_supported_is_an_unsupported_assertion(self):
        s = summarize([row("missing_context", "supported"), row("missing_context", "uncertain")])
        self.assertEqual(s["unsupported_assertion_rate"]["value"], 0.5)

    def test_perturbation_consistency_ignores_pairs_where_either_side_errored(self):
        s = summarize([row(status="supported", base_status="supported"), row(status="uncertain", base_status="supported"),
                       row(status="error", base_status="supported"), row(status="supported", base_status="error")])
        self.assertEqual((s["perturbation_consistency"]["n"], s["perturbation_consistency"]["d"]), (1, 2))

    def test_counts_and_families_are_reported(self):
        s = summarize([row(family="a"), row(family="b", status="error")])
        self.assertEqual(s["families"], 2)
        self.assertEqual(s["counts_by_status"], {"supported": 1, "error": 1})

    def test_bootstrap_resamples_families_not_rows(self):
        base = [row(status="uncertain", family=f, case=f"{f}{i}") for f in ("a", "b") for i in range(50)]
        cand = [row(status="supported", family=f, case=f"{f}{i}") for f in ("a", "b") for i in range(50)]
        out = paired_bootstrap(base, cand, "end_to_end_recall")
        self.assertEqual(out["families"], 2)
        self.assertEqual(out["point"], 1.0)
        self.assertIsNone(out["lo"])
        self.assertIsNone(out["hi"])

    def test_bootstrap_gives_an_interval_with_enough_families(self):
        base = [row(status="uncertain", family=f"f{i}", case=f"c{i}") for i in range(20)]
        cand = [row(status="supported" if i % 2 else "uncertain", family=f"f{i}", case=f"c{i}") for i in range(20)]
        out = paired_bootstrap(base, cand, "end_to_end_recall", n_boot=300)
        self.assertEqual(out["point"], 0.5)
        self.assertLess(out["lo"], 0.5)
        self.assertGreater(out["hi"], 0.5)

    def test_bootstrap_is_deterministic_for_a_seed(self):
        base = [row(status="uncertain", family=f"f{i}", case=f"c{i}") for i in range(12)]
        cand = [row(status="supported" if i % 3 else "uncertain", family=f"f{i}", case=f"c{i}") for i in range(12)]
        self.assertEqual(paired_bootstrap(base, cand, "end_to_end_recall", n_boot=200, seed=3),
                         paired_bootstrap(base, cand, "end_to_end_recall", n_boot=200, seed=3))

    def test_bootstrap_requires_matching_case_sets(self):
        with self.assertRaises(ValueError):
            paired_bootstrap([row(case="a")], [row(case="b")], "end_to_end_recall")


if __name__ == "__main__":
    unittest.main()
