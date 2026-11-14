from copy import deepcopy

import pytest

from mechanisms import word_choice


def _context(options=None, tone=1.0):
    if options is None:
        options = [
            {"term": "reported", "fact_id": "event", "factual_fit": 1.0, "connotation": 0.0},
            {"term": "hailed", "fact_id": "event", "factual_fit": 1.0, "connotation": 0.75},
            {"term": "noted", "fact_id": "event", "factual_fit": 1.0, "connotation": 0.2},
        ]
    return {
        "options": options,
        "reference_fact_id": "event",
        "presentation_tone": tone,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_tone_selects_connotative_word_with_numeric_oracle():
    context = _context()
    result = word_choice.evaluate(context, strength=0.8)
    baseline = word_choice.evaluate(context, strength=0.0)

    assert result["state"]["last_term"] == "hailed"
    assert result["metric"] == pytest.approx(0.75)  # tone 1 × connotation .75
    assert result["metric"] > baseline["metric"]
    assert result["active"] is True


def test_zero_strength_is_the_explicit_neutral_reference_rule():
    result = word_choice.evaluate(_context(), strength=0.0)

    assert result["state"]["last_term"] == "reported"
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_boundary_without_same_fact_word_alternative_matches_reference():
    boundary = _context(
        [
            {"term": "reported", "fact_id": "event", "factual_fit": 1.0, "connotation": 0.0},
            {"term": "celebrated", "fact_id": "mood", "factual_fit": 1.0, "connotation": 0.9},
        ]
    )
    at_zero = word_choice.evaluate(boundary, strength=0.0)
    at_intervention = word_choice.evaluate(boundary, strength=0.8)

    assert at_intervention["metric"] == at_zero["metric"]
    assert at_intervention["state"]["last_term"] == at_zero["state"]["last_term"]
    assert at_intervention["active"] is False


def test_missing_supporting_fact_is_rejected_not_scored_as_zero():
    context = _context()
    context["reference_fact_id"] = "unsupplied_fact"

    with pytest.raises(ValueError, match="no supplied option supports"):
        word_choice.evaluate(context, strength=0.8)


def test_invalid_strength_and_input_ranges_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        word_choice.evaluate(_context(), strength=1.1)

    bad = _context()
    bad["options"][1]["connotation"] = 1.01
    with pytest.raises(ValueError, match="connotation"):
        word_choice.evaluate(bad, strength=0.8)


def test_deterministic_repeat_and_nonmutating_nested_inputs_and_state():
    context = _context(tone=-1.0)
    context["state"] = {"decision_count": 2, "retained_note": {"source": "fixture"}}
    before = deepcopy(context)

    first = word_choice.evaluate(context, strength=0.8)
    second = word_choice.evaluate(context, strength=0.8)

    assert first == second
    assert context == before
    assert first["state"]["decision_count"] == 3
    assert first["state"]["retained_note"] == {"source": "fixture"}
    first["state"]["retained_note"]["source"] = "changed"
    assert context["state"]["retained_note"]["source"] == "fixture"


def test_scenario_contract_has_positive_and_boundary_with_effect_direction():
    scenarios = {item["name"]: item for item in word_choice.scenarios()}
    positive = scenarios["positive"]
    boundary = scenarios["boundary"]
    assert positive["expectation"] == "increase"
    assert boundary["expectation"] == "equal"
    positive_context = _context(positive["contexts"][0]["options"])
    positive_context["reference_fact_id"] = positive["contexts"][0]["reference_fact_id"]
    base = word_choice.evaluate(positive_context, 0.0)
    changed = word_choice.evaluate(positive_context, 0.8)
    assert changed["metric"] > base["metric"]
