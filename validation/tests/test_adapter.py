import dataclasses
import unittest

from biasguard.catalog import load_cards
from biasguard.engine import BiasGuard
from validation.biaslab.adapter import normalize, verify_spans
from validation.biaslab.cases import DetectorInput
from validation.tests._stub import StubReviewer

TEXT = "[A · 09:00] Bakan: kriz yok — Açıklama tekrarlandı\n[B · 09:05] Krizi herkes görüyor, bakan inkâr etti"
CONTEXT = "Olay: Bakan açıklaması\nKurumlar: A, B"
QUOTE = "Krizi herkes görüyor, bakan inkâr etti"
CARDS = load_cards()
BIAS = next(c for c in CARDS if c.get("review_policy", "bias_error_review") == "bias_error_review")
EFFECT = next(c for c in CARDS if c.get("review_policy") == "effect_context_only")
OTHER = next(c for c in CARDS if c["id"] not in (BIAS["id"], EFFECT["id"]))


def run(card, text=TEXT, context=CONTEXT, quote=QUOTE, cards=None, mode="ai", **kw):
    reviewer = StubReviewer(card["id"], quote, **kw)
    return BiasGuard(cards=cards or [card, OTHER], reviewer=reviewer).analyze(text, context, mode=mode)


class AdapterTest(unittest.TestCase):
    def test_none_target_is_ineligible_without_reading_the_result(self):
        self.assertEqual(normalize({}, None).status, "ineligible")

    def test_offline_mode_is_unassessed_not_negative(self):
        self.assertEqual(normalize(run(BIAS, mode="offline"), BIAS["id"]).status, "unassessed")

    def test_both_supported_is_supported(self):
        a = normalize(run(BIAS), BIAS["id"])
        self.assertEqual((a.status, a.native_adjudication), ("supported", "pattern_supported"))

    def test_effect_context_only_card_is_contextual_effect(self):
        self.assertEqual(normalize(run(EFFECT), EFFECT["id"]).status, "contextual_effect")

    def test_disagreement_is_uncertain(self):
        self.assertEqual(normalize(run(BIAS, skeptic="not_supported"), BIAS["id"]).status, "uncertain")

    def test_both_uncertain_is_uncertain(self):
        self.assertEqual(normalize(run(BIAS, advocate="uncertain", skeptic="uncertain"), BIAS["id"]).status, "uncertain")

    def test_both_not_supported_is_not_supported(self):
        a = normalize(run(BIAS, advocate="not_supported", skeptic="not_supported"), BIAS["id"])
        self.assertEqual((a.status, a.native_adjudication), ("not_supported", "suppressed"))

    def test_reviewer_failure_is_error(self):
        a = normalize(run(BIAS, fail=True), BIAS["id"])
        self.assertEqual((a.status, a.native_status), ("error", "analysis_incomplete"))

    def test_rejected_input_is_error(self):
        result = BiasGuard(cards=[BIAS], reviewer=StubReviewer(BIAS["id"], QUOTE)).analyze("", "", mode="ai")
        self.assertEqual(normalize(result, BIAS["id"]).status, "error")

    def test_target_not_selected_is_unassessed(self):
        self.assertEqual(normalize(run(BIAS, cards=[BIAS, OTHER]), EFFECT["id"]).status, "unassessed")

    def test_repeated_quote_yields_one_span_per_occurrence(self):
        text = f"[A · 09:00] {QUOTE} — tekrar: {QUOTE}"
        a = normalize(run(BIAS, text=text), BIAS["id"])
        self.assertEqual(len(a.spans), 2)
        self.assertNotEqual(a.spans[0].start, a.spans[1].start)
        verify_spans(a, DetectorInput(text, CONTEXT))

    def test_turkish_and_emoji_offsets_round_trip(self):
        text = "🙂 İşçiler ığdır'da: Krizi herkes görüyor"
        a = normalize(run(BIAS, text=text, quote="Krizi herkes görüyor"), BIAS["id"])
        verify_spans(a, DetectorInput(text, CONTEXT))
        self.assertEqual(text[a.spans[0].start:a.spans[0].end], a.spans[0].quote)

    def test_context_evidence_keeps_its_source(self):
        a = normalize(run(EFFECT, quote="Olay: Bakan açıklaması", source="context"), EFFECT["id"])
        self.assertEqual({s.source for s in a.spans}, {"context"})

    def test_verify_spans_rejects_shifted_offsets(self):
        a = normalize(run(BIAS), BIAS["id"])
        shifted = dataclasses.replace(a, spans=(dataclasses.replace(a.spans[0], start=a.spans[0].start + 1,
                                                                    end=a.spans[0].end + 1),))
        with self.assertRaises(ValueError):
            verify_spans(shifted, DetectorInput(TEXT, CONTEXT))

    def test_other_supported_cards_are_listed_as_extra_not_errors(self):
        a = normalize(run(BIAS), OTHER["id"])
        self.assertEqual(a.status, "not_supported")
        self.assertEqual(a.extra_supported, (BIAS["id"],))


if __name__ == "__main__":
    unittest.main()
