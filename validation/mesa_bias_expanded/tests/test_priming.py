from copy import deepcopy

import pytest

from mechanisms import priming


def _run(contexts, strength, initial=None):
    state = deepcopy(initial or {"activation": {}})
    results = []
    for index, task_inputs in enumerate(contexts):
        context = deepcopy(task_inputs)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = priming.evaluate(context, strength)
        results.append(result)
        state = deepcopy(result["state"])
    return results


def _scenario(name):
    return next(s for s in priming.scenarios() if s["name"] == name)


def test_numeric_choice_oracle_for_decay_and_activation_shift():
    positive = _scenario("positive")
    first, target = _run(positive["contexts"], 0.8)
    assert first["state"]["activation"] == {"nature": 1.0}
    assert target["state"]["activation"]["nature"] == pytest.approx(0.75)
    assert target["state"]["last_baseline_choice"] == "routine"
    assert target["state"]["last_choice"] == "nature"
    assert target["metric"] == 1.0
    assert target["active"] is True
    # nature's adjusted score is 0 + .8*.8*.75 = .48, exceeding .30.
    assert 0.8 * 0.8 * 0.75 > 0.30


def test_positive_scenario_has_expected_direction():
    positive = _scenario("positive")
    reference = _run(positive["contexts"], 0.0)[-1]["metric"]
    intervention = _run(positive["contexts"], 0.8)[-1]["metric"]
    assert intervention > reference


def test_boundary_removes_exposure_target_category_match():
    boundary = _scenario("boundary")
    assert boundary["contexts"][0]["exposures"][0]["category"] == "nature"
    assert all(o["category"] != "nature" for o in boundary["contexts"][-1]["options"])
    reference = _run(boundary["contexts"], 0.0)[-1]
    intervention = _run(boundary["contexts"], 0.8)[-1]
    assert intervention["metric"] == reference["metric"]
    assert intervention["state"]["last_choice"] == reference["state"]["last_choice"]
    assert intervention["active"] is False


def test_strength_zero_is_explicit_highest_baseline_score_reference():
    positive = _scenario("positive")
    target = _run(positive["contexts"], 0.0)[-1]
    assert target["state"]["last_choice"] == "routine"
    assert target["state"]["last_baseline_choice"] == "routine"
    assert target["metric"] == 0.0
    assert target["active"] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    with pytest.raises(ValueError, match="missing required task input options"):
        priming.evaluate({"exposures": []}, 0.8)
    base = {"exposures": [], "options": []}
    with pytest.raises(ValueError, match="explicit nonempty category"):
        priming.evaluate({**base, "exposures": [{"cue": "oak"}]}, 0.8)
    with pytest.raises(ValueError, match="finite number"):
        priming.evaluate({**base, "options": [{"id": "x", "category": "x", "score": float("nan")}]}, 0.8)
    with pytest.raises(ValueError, match="strength"):
        priming.evaluate(base, 1.1)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    positive = _scenario("positive")
    context = deepcopy(positive["contexts"][1])
    context.update({"state": {"activation": {"nature": 1.0}}, "peer_states": [{"activation": {}}],
                    "round_index": 1, "agent_index": 2, "uniform": 0.3})
    before = deepcopy(context)
    first = priming.evaluate(context, 0.8)
    second = priming.evaluate(context, 0.8)
    assert context == before
    assert first == second


def test_metadata_inputs_are_unconditional_top_level_scenario_keys():
    assert priming.METADATA["required_inputs"] == ["exposures", "options"]
    for scenario in priming.scenarios():
        assert all(set(priming.METADATA["required_inputs"]).issubset(context) for context in scenario["contexts"])
        assert not any({"state", "peer_states", "round_index", "agent_index", "uniform"}.intersection(context)
                       for context in scenario["contexts"])
