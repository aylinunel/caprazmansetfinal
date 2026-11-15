import json
import re
import unittest

from biasguard.catalog import validate_cards
from validation.biaslab import crosswalk
from validation.biaslab.cases import DetectorInput
from validation.biaslab.configs import PROPOSED_DIR, target
from validation.biaslab.renderer import assert_no_leak, kinds, render, variants
from validation.biaslab.run import lab_concepts
from validation.biaslab.sim import realize, scenario

IDS = ("ad_hominem causal_overclaim cherry_picking consequence_framing emphasis_framing episodic_framing "
       "false_dilemma fear_appeal labeling loaded_language metaphorical_framing responsibility_framing "
       "selective_statistics spin strawman thematic_framing word_choice").split()
CARDS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in PROPOSED_DIR.glob("*.json")}


class MediaCardsTest(unittest.TestCase):
    def test_all_seventeen_cards_exist_and_validate(self):
        self.assertEqual(set(CARDS), {i.replace("_", "-") for i in IDS})
        validate_cards(list(CARDS.values()))
        self.assertTrue(all(c["id"] == stem and c["entry_type"] == "media_practice" for stem, c in CARDS.items()))

    def test_every_card_has_two_to_four_conditions(self):
        self.assertTrue(all(2 <= len(c["necessary_conditions"]) <= 4 for c in CARDS.values()))

    def test_every_card_has_quoted_speech_and_opinion_non_examples(self):
        for cid, c in CARDS.items():
            text = " ".join(c["non_examples"]).lower()
            self.assertGreaterEqual(len(c["non_examples"]), 3, cid)
            self.assertRegex(text, r"quotes or attributes", cid)
            self.assertRegex(text, r"opinion column", cid)

    def test_no_card_claims_intent(self):
        # The only mention of purpose allowed is the limitation that disclaims it.
        for cid, c in CARDS.items():
            body = json.dumps({k: v for k, v in c.items() if k != "limitations"}, ensure_ascii=False).casefold()
            self.assertNotRegex(body, r"kasıt|kasten|niyet|\bintent|deliberate|on purpose|manipül|manipulat|deceiv|deceptive", cid)
            self.assertIn("niyet hakkında bir şey söylemez", c["limitations"], cid)

    def test_every_card_is_marked_as_a_lab_only_proposal(self):
        self.assertTrue(all(c["provenance"].startswith("LAB-ONLY PROPOSAL, not reviewed, not in production")
                            for c in CARDS.values()))

    def test_context_effect_cards_have_context_only_policy(self):
        self.assertEqual({cid for cid, c in CARDS.items() if c["review_policy"] == "effect_context_only"},
                         {"thematic-framing", "spin"})

    def test_crosswalk_resolves_the_seventeen_plus_illusory_truth_on_candidate(self):
        resolvable = {s for s in crosswalk.load() if target(s, "candidate")}
        self.assertEqual(resolvable, set(IDS) | {"illusory_truth_effect"})
        self.assertEqual({s for s in crosswalk.load() if target(s, "baseline")}, {"illusory_truth_effect"})
        self.assertEqual(set(lab_concepts()), resolvable)


class MediaRendererTest(unittest.TestCase):
    def test_every_concept_renders_three_kinds_and_passes_leak_check(self):
        for concept in IDS:
            if concept == "selective_statistics":
                continue
            r = realize(concept, scenario(concept, "positive"))[0]
            self.assertGreaterEqual(variants(concept), 2, concept)
            self.assertEqual(set(kinds(concept)), {"positive", "boundary_control", "quoted_control"}, concept)
            for v in range(variants(concept)):
                seen = set()
                for kind in kinds(concept):
                    d = render(r, kind, v)
                    assert_no_leak(d, concept, concept.replace("_", "-"), "ffffffffffffffff")
                    self.assertTrue(d.context.startswith("Olay: "), concept)
                    seen.add(d.text)
                self.assertEqual(len(seen), 3, f"{concept} v{v}: kinds must render differently")

    def test_quoted_control_attributes_the_phrase_to_a_named_speaker(self):
        for concept in ("labeling", "fear_appeal", "strawman"):
            r = realize(concept, scenario(concept, "positive"))[0]
            first = render(r, "quoted_control", 0).text.splitlines()[0]
            self.assertRegex(first, r'^\[Kurum A · \d\d:\d\d\] [^"]+: "[^"]+" — Kurum bu sözleri aktardı\.', concept)

    def test_positive_and_control_share_event_and_context(self):
        r = realize("cherry_picking", scenario("cherry_picking", "positive"))[0]
        self.assertEqual(render(r, "positive", 0).context, render(r, "boundary_control", 0).context)

    def test_comparative_concepts_render_two_outlets(self):
        for concept in ("labeling", "word_choice", "emphasis_framing", "spin"):
            r = realize(concept, scenario(concept, "positive"))[0]
            self.assertEqual(len(render(r, "positive", 0).text.splitlines()), 2, concept)

    def test_plain_control_of_a_comparative_concept_has_identical_outlet_wording(self):
        r = realize("word_choice", scenario("word_choice", "positive"))[0]
        a, b = (line.split("] ", 1)[1] for line in render(r, "boundary_control", 0).text.splitlines())
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
