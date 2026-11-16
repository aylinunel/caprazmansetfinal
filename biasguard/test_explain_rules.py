import unittest
from pathlib import Path

from biasguard.catalog import load_cards
from biasguard.explain_rules import BR_ALIAS, compose
from biasguard.news import _load, validate_explain

TEXT = "[a · 09:00] Fon vurgunu soruşturması başladı — ayrıntı\n[b · 09:05] Fon soruşturması başladı"
NAMES = {"a": "Kurum A", "b": "Kurum B"}
F = {"id": "loaded-language", "missing": ["Soruşturmanın resmî adı kamuoyuna açıklanmadı."],
     "evidence": [{"q": "Fon vurgunu soruşturması başladı", "o": ["a"]}, {"q": "Fon soruşturması başladı", "o": ["b"]}],
     "mechanisms": [{"role": "advocate", "text": "Kurum A soruşturmayı kendi sesiyle 'vurgun' diye adlandırıyor; Kurum B nötr kalıyor. İkinci cümle."}],
     "alternatives": [{"role": "skeptic", "text": "Vurgun sözcüğü dava için yerleşmiş kısa ad olabilir ve değerlendirme taşımayabilir."}]}


class ComposeTest(unittest.TestCase):
    def test_fields_valid_and_from_reviewers(self):
        x = compose(F, TEXT, NAMES, "Okur olayı duygu yüklü bir sözcükle öğreniyor.")
        self.assertEqual(validate_explain(x, TEXT), [])
        self.assertTrue(x["noticed"].startswith("Kurum A soruşturmayı"))
        self.assertNotIn("İkinci cümle", x["noticed"])
        self.assertIn("Kurum A ve Kurum B", x["means"])
        self.assertTrue(x["why"].startswith("Vurgun sözcüğü"))

    def test_paraphrased_quote_falls_back_to_verbatim_quotes(self):
        f = {**F, "mechanisms": [{"role": "advocate", "text": "Kurum A “uydurma bir alıntı burada” diyor ve bu ton taşıyor."}]}
        x = compose(f, TEXT, NAMES, "Okur olayı duygu yüklü bir sözcükle öğreniyor.")
        self.assertIn("“Fon vurgunu soruşturması başladı”", x["noticed"])
        self.assertEqual(validate_explain(x, TEXT), [])

    def test_missing_alternatives_use_missing_context(self):
        x = compose({**F, "alternatives": []}, TEXT, NAMES, "Okur olayı duygu yüklü bir sözcükle öğreniyor.")
        self.assertTrue(x["why"].startswith("Eksik bilgi:"))


class SentenceTest(unittest.TestCase):
    def test_abbreviations_do_not_end_a_sentence(self):
        from biasguard.explain_rules import _first_sentence
        self.assertEqual(_first_sentence("Bakan Dr. Ahmet Yılmaz açıkladı. İkinci cümle."), "Bakan Dr. Ahmet Yılmaz açıkladı.")
        self.assertEqual(_first_sentence("USGS vb. Kurumlar ölçtü. Sonra."), "USGS vb. Kurumlar ölçtü.")
        self.assertEqual(_first_sentence("Tek cümle"), "Tek cümle")


class AliasTest(unittest.TestCase):
    def test_every_card_reaches_a_registry_entry(self):
        core = _load(Path(__file__).resolve().parents[1] / "public" / "data" / "core.bin")
        registry = {b["k"] for b in core["BR"]}
        missing = [c["id"] for c in load_cards() if BR_ALIAS.get(c["id"], c["id"]) not in registry]
        self.assertEqual(missing, [])
        self.assertEqual(core.get("BRA", BR_ALIAS), BR_ALIAS)  # the site reads the same map


if __name__ == "__main__":
    unittest.main()
