import unittest

from validation.biaslab.cases import DetectorInput, case_id, expected, family_id, split_of


class CasesTest(unittest.TestCase):
    def test_same_facts_share_family_and_split(self):
        a = family_id("selective_statistics", {"event_count": 10, "relevant_denominator": 100, "selected_denominator": 20})
        b = family_id("selective_statistics", {"selected_denominator": 20, "relevant_denominator": 100, "event_count": 10})
        self.assertEqual(a, b)
        self.assertEqual(split_of(a), split_of(b))

    def test_different_facts_get_different_families(self):
        self.assertNotEqual(family_id("c", {"x": 1}), family_id("c", {"x": 2}))

    def test_split_is_dev_or_test(self):
        self.assertEqual({split_of(family_id("c", {"x": i})) for i in range(200)}, {"dev", "test"})

    def test_case_id_is_opaque(self):
        self.assertRegex(case_id(DetectorInput("metin", "bağlam"), salt="s"), r"^c-[0-9a-f]{12}$")

    def test_case_id_changes_with_salt(self):
        d = DetectorInput("metin", "bağlam")
        self.assertNotEqual(case_id(d, "a"), case_id(d, "b"))

    def test_case_id_separates_text_from_context(self):
        self.assertNotEqual(case_id(DetectorInput("ab", "c"), "s"), case_id(DetectorInput("a", "bc"), "s"))

    def test_unresolvable_target_expects_ineligible(self):
        self.assertEqual(expected("positive", False).acceptable, frozenset({"ineligible"}))

    def test_positive_accepts_supported_or_contextual_effect(self):
        self.assertEqual(expected("positive", True).acceptable, frozenset({"supported", "contextual_effect"}))

    def test_missing_context_forbids_supported(self):
        self.assertIn("supported", expected("missing_context", True).forbidden)

    def test_controls_forbid_supported(self):
        for kind in ("inactive_control", "boundary_control", "quoted_control"):
            self.assertEqual(expected(kind, True).forbidden, frozenset({"supported", "contextual_effect"}), kind)

    def test_unknown_kind_raises(self):
        with self.assertRaises(ValueError):
            expected("nonsense", True)


if __name__ == "__main__":
    unittest.main()
