import copy
import math

import pytest

from mechanisms import decoy_effect


def run_context(context, strength, state=None):
    """Call the module with runner-like reserved defaults and carry its state."""
    task_context = copy.deepcopy(context)
    task_context.update({
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    })
    return decoy_effect.evaluate(task_context, strength)


def _option_map(context):
    return {option["id"]: option for option in context["options"]}


def _baseline(context):
    options = _option_map(context)
    target = context["target_id"]
    maximum = max(option["utility"] for option in options.values())
    weights = {key: math.exp(option["utility"] - maximum) for key, option in options.items()}
    return weights[target] / sum(weights.values())


def test_positive_asymmetric_decoy_increases_target_probability():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    reference = run_context(positive, 0.0)
    affected = run_context(positive, 0.8)
    assert affected["metric"] > reference["metric"]
    assert affected["active"] is True
    assert affected["state"]["last_asymmetric_dominance"] is True


def test_boundary_when_competitor_also_dominates_matches_reference():
    boundary = decoy_effect.scenarios()[1]["contexts"][0]
    reference = run_context(boundary, 0.0)
    at_strength = run_context(boundary, 0.8)
    assert at_strength["state"]["last_asymmetric_dominance"] is False
    assert at_strength["active"] is False
    assert at_strength["metric"] == reference["metric"]


def test_zero_strength_is_exact_stated_softmax_reference():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    result = run_context(positive, 0.0)
    assert result["metric"] == _baseline(positive)
    assert result["active"] is False


def test_numeric_choice_oracle_matches_target_logit_bonus():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    options = _option_map(positive)
    similarity = 1.0 - sum(
        abs(a - b) for a, b in zip(options["target"]["attributes"], options["decoy"]["attributes"])
    ) / 2.0
    strength = 0.8
    target_logit = options["target"]["utility"] + strength * 1.2 * similarity
    logits = [target_logit, options["competitor"]["utility"], options["decoy"]["utility"]]
    expected = math.exp(target_logit - max(logits)) / sum(math.exp(value - max(logits)) for value in logits)
    actual = run_context(positive, strength)["metric"]
    assert actual == pytest.approx(expected, abs=1e-15)


def test_missing_or_impossible_required_evidence_is_rejected():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    missing = copy.deepcopy(positive)
    del missing["decoy_id"]
    with pytest.raises(ValueError, match="decoy_id"):
        run_context(missing, 0.5)
    impossible = copy.deepcopy(positive)
    impossible["options"][0]["attributes"] = [0.5, 0.4]
    with pytest.raises(ValueError, match="strictly dominate"):
        run_context(impossible, 0.5)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    context = copy.deepcopy(positive)
    context["state"] = {"history": {"tag": ["kept"]}}
    before = copy.deepcopy(context)
    first = decoy_effect.evaluate(context, 0.8)
    second = decoy_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    first["state"]["history"]["tag"].append("independent")
    assert context["state"]["history"]["tag"] == ["kept"]


def test_strength_and_attribute_ranges_are_validated():
    positive = decoy_effect.scenarios()[0]["contexts"][0]
    with pytest.raises(ValueError, match="strength"):
        run_context(positive, float("nan"))
    malformed = copy.deepcopy(positive)
    malformed["options"][0]["utility"] = 1.1
    with pytest.raises(ValueError, match="utility"):
        run_context(malformed, 0.5)
