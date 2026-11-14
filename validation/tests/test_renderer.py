import dataclasses
import re
import unittest

from validation.biaslab.cases import DetectorInput
from validation.biaslab.renderer import Leak, assert_no_leak, kinds, render, variants
from validation.biaslab.sim import realize, scenario

SS = "selective_statistics"
IT = "illusory_truth_effect"
_pos = realize(SS, scenario(SS, "positive"))
ACTIVE = next(r for r in _pos if r.active)
INACTIVE = next(r for r in _pos if not r.active)
BOUNDARY = realize(SS, scenario(SS, "boundary"))[0]
IT_POS = realize(IT, scenario(IT, "positive"))[0]
IT_BND = realize(IT, scenario(IT, "boundary"))[0]


class RendererTest(unittest.TestCase):
    def test_output_is_only_text_and_context(self):
        self.assertEqual(set(dataclasses.asdict(render(ACTIVE, "positive", 0))), {"text", "context"})

    def test_active_positive_states_the_narrow_rate_and_supplies_the_wide_cohort(self):
        d = render(ACTIVE, "positive", 0)
        self.assertIn("yüzde 50", d.text)
        self.assertIn("20 dosyanın 10", d.text)
        self.assertIn("100 dosyanın 10", d.context)

    def test_inactive_agent_renders_the_reference_rate(self):
        self.assertIn("yüzde 10", render(INACTIVE, "inactive_control", 0).text)

    def test_missing_context_removes_the_comparison(self):
        d = render(ACTIVE, "missing_context", 0)
        self.assertNotIn("Karşılaştırma", d.context)
        self.assertEqual(d.text, render(ACTIVE, "positive", 0).text)

    def test_boundary_pair_renders_identically(self):
        ref = realize(SS, scenario(SS, "boundary"), strength=0.0)[0]
        self.assertEqual(render(ref, "boundary_control", 0), render(BOUNDARY, "boundary_control", 0))

    def test_private_state_changes_do_not_change_rendering(self):
        changed = dataclasses.replace(ACTIVE, trace=("x",), seed=7, strength=0.3, agent=99)
        self.assertEqual(render(ACTIVE, "positive", 0), render(changed, "positive", 0))

    def test_quoted_control_attributes_and_corrects_the_figure(self):
        d = render(ACTIVE, "quoted_control", 0)
        self.assertIn('"', d.text)
        self.assertIn("yüzde 10", d.text)

    def test_every_variant_of_every_kind_passes_the_leak_check(self):
        for concept, sample in ((SS, ACTIVE), (IT, IT_POS)):
            for v in range(variants(concept)):
                for kind in kinds(concept):
                    assert_no_leak(render(sample, kind, v), concept, concept.replace("_", "-"), "ab12cd34ef567890")

    def test_each_concept_has_at_least_two_variants(self):
        self.assertGreaterEqual(variants(SS), 3)
        self.assertGreaterEqual(variants(IT), 2)

    def test_leak_check_catches_label_in_text(self):
        with self.assertRaises(Leak):
            assert_no_leak(DetectorInput("bu bir positive örnek"), SS, None, "ab12")

    def test_leak_check_catches_concept_id_in_a_key_or_filename(self):
        with self.assertRaises(Leak):
            assert_no_leak({"file": "selective-statistics-01.json"}, SS, None, "ab12")

    def test_leak_check_catches_family_id(self):
        with self.assertRaises(Leak):
            assert_no_leak({"event": "c-ab12cd34ef567890"}, SS, None, "ab12cd34ef567890")

    def test_leak_check_does_not_fire_inside_ordinary_words(self):
        assert_no_leak(DetectorInput("interactive seedling splitter"), SS, None, "ab12")

    def test_charged_wording_is_not_confined_to_positives(self):
        self.assertTrue(any("Skandal" in render(INACTIVE, "inactive_control", v).text for v in range(variants(SS))))
        self.assertTrue(any("Skandal" not in render(ACTIVE, "positive", v).text for v in range(variants(SS))))

    def test_unsupported_concept_raises_keyerror(self):
        with self.assertRaises(KeyError):
            render(dataclasses.replace(ACTIVE, concept="halo_effect"), "positive", 0)

    def test_unsupported_kind_for_concept_raises_keyerror(self):
        with self.assertRaises(KeyError):
            render(IT_POS, "missing_context", 0)

    def test_relabel_changes_only_outlet_names(self):
        a, b = render(ACTIVE, "positive", 0), render(ACTIVE, "positive", 0, "relabel_outlets")
        self.assertEqual(a.text.replace("Kurum A", "Kurum X"), b.text)
        self.assertEqual(a.context, b.context)

    def test_irrelevant_detail_keeps_every_number(self):
        a, b = render(ACTIVE, "positive", 0), render(ACTIVE, "positive", 0, "irrelevant_detail")
        self.assertNotEqual(a.text, b.text)
        self.assertEqual(re.findall(r"\d+", a.text), re.findall(r"\d+", b.text))

    def test_reverse_outlets_reverses_line_order_for_multi_line_input(self):
        a, b = render(IT_POS, "positive", 0), render(IT_POS, "positive", 0, "reverse_outlets")
        self.assertEqual(a.text.splitlines()[::-1], b.text.splitlines())

    def test_reverse_outlets_leaves_single_line_input_unchanged(self):
        self.assertEqual(render(ACTIVE, "positive", 0), render(ACTIVE, "positive", 0, "reverse_outlets"))

    def test_illusory_truth_positive_repeats_without_new_source(self):
        d = render(IT_POS, "positive", 0)
        self.assertEqual(len(d.text.splitlines()), 3)
        self.assertNotIn("rapor", d.text)

    def test_illusory_truth_boundary_adds_a_new_report_each_time(self):
        d = render(IT_BND, "boundary_control", 0)
        self.assertEqual(len(re.findall(r"bağımsız \S+ raporu", d.text)), 3)

    def test_unknown_perturbation_raises(self):
        with self.assertRaises(ValueError):
            render(ACTIVE, "positive", 0, "shuffle")


if __name__ == "__main__":
    unittest.main()
