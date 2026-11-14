import copy
import math

import pytest

from mechanisms import belief_perseverance as bp


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        context = copy.deepcopy(item)
        context.update({"state": state, "peer_states": [], "round_index": index, "agent_index": 0, "uniform": 0.5})
        result = bp.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def logistic(x):
    return 1 / (1 + math.exp(-x))


def logit(p):
    return math.log(p / (1 - p))


def test_perseverance_positive_direction_and_numeric_oracle():
    scenario = next(s for s in bp.scenarios() if s["name"] == "positive")
    biased = run_sequence(scenario["contexts"], 0.8)[-1]
    reference = run_sequence(scenario["contexts"], 0.0)[-1]
    expected = logistic(logit(0.4) + 0.8 * 1.2)
    assert biased["metric"] == pytest.approx(expected, abs=1e-12)
    assert biased["metric"] > reference["metric"]
    assert biased["active"] is True
    assert "residual_log_odds=0.96" in biased["trace"][0]


def test_boundary_without_supporting_evidence_matches_reference():
    scenario = next(s for s in bp.scenarios() if s["name"] == "boundary")
    at_strength = run_sequence(scenario["contexts"], 0.8)[-1]
    at_zero = run_sequence(scenario["contexts"], 0.0)[-1]
    assert at_strength["metric"] == pytest.approx(at_zero["metric"], abs=1e-12)
    assert at_strength["active"] is False


def test_zero_strength_is_explicit_reference_policy_even_before_correction():
    context = {"prior_probability": 0.3, "event": {"type": "evidence", "id": "e1", "direction": 1, "weight": 0.7}}
    result = bp.evaluate({**context, "state": {}}, 0.0)
    expected = logistic(logit(0.3) + 0.7)
    assert result["metric"] == pytest.approx(expected, abs=1e-12)
    assert result["metric"] == result["state"]["reference_probability"]
    assert result["active"] is False


def test_backfire_is_explicitly_distinct_from_perseverance():
    contexts = [
        {"prior_probability": 0.4, "event": {"type": "evidence", "id": "e1", "direction": 1, "weight": 1.0}},
        {"prior_probability": 0.4, "event": {"type": "correction", "target_id": "e1", "subtype": "perseverance"}},
    ]
    backfire_contexts = copy.deepcopy(contexts)
    backfire_contexts[-1]["event"]["subtype"] = "backfire"
    persistence_metric = run_sequence(contexts, 0.8)[-1]["metric"]
    backfire_metric = run_sequence(backfire_contexts, 0.8)[-1]["metric"]
    assert persistence_metric == pytest.approx(logistic(logit(0.4) + 0.8), abs=1e-12)
    assert backfire_metric == pytest.approx(logistic(logit(0.4) + 1.6), abs=1e-12)
    assert backfire_metric > persistence_metric


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="prior_probability"):
        bp.evaluate({"event": {"type": "evidence", "id": "e", "direction": 1, "weight": 1}}, 0.5)
    with pytest.raises(ValueError, match="previously supplied evidence"):
        bp.evaluate({"prior_probability": 0.5, "state": {}, "event": {"type": "correction", "target_id": "unknown", "subtype": "perseverance"}}, 0.5)
    with pytest.raises(ValueError, match="finite number"):
        bp.evaluate({"prior_probability": 0.5, "event": {"type": "evidence", "id": "e", "direction": 1, "weight": float("nan")}}, 0.5)
    with pytest.raises(ValueError, match="direction"):
        bp.evaluate({"prior_probability": 0.5, "event": {"type": "evidence", "id": "e", "direction": 1.0, "weight": 1}}, 0.5)


def test_determinism_and_nonmutation_of_nested_context_state():
    contexts = next(s for s in bp.scenarios() if s["name"] == "positive")["contexts"]
    first = {**copy.deepcopy(contexts[0]), "state": {}}
    first_before = copy.deepcopy(first)
    out1 = bp.evaluate(first, 0.8)
    out2 = bp.evaluate(first, 0.8)
    assert first == first_before
    assert out1 == out2
    second = {**copy.deepcopy(contexts[1]), "state": out1["state"]}
    second_before = copy.deepcopy(second)
    result = bp.evaluate(second, 0.8)
    assert second == second_before
    assert result["state"] is not second["state"]
    assert math.isfinite(result["metric"])
    assert result["state"]["evidence"]["study-A"]["discredited"] is True
    assert result["state"]["belief_probability"] == result["metric"]


def test_strength_and_prior_ranges_are_validated():
    valid = {"prior_probability": 0.5, "event": {"type": "evidence", "id": "e", "direction": 0, "weight": 0}}
    for strength in (-0.01, 1.01, float("inf")):
        with pytest.raises(ValueError):
            bp.evaluate(valid, strength)
    invalid_prior = {**valid, "prior_probability": -0.1}
    with pytest.raises(ValueError):
        bp.evaluate(invalid_prior, 0.5)
