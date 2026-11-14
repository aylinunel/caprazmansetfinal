from copy import deepcopy

import pytest

from mechanisms import bye_now_effect as mechanism


WAIT = {"id": "wait", "utility": 0.0, "price": 0.0, "purchase": False, "sound_association": 0.0}
BUY = {"id": "buy_item", "utility": -0.2, "price": 20.0, "purchase": True, "sound_association": 1.0}


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for round_index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(state=deepcopy(state), peer_states=[], round_index=round_index, agent_index=0, uniform=0.5)
        result = mechanism.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_temporal_effect_has_exact_spending_oracle():
    contexts = [
        {"bye_exposure": True, "options": [WAIT]},
        {"bye_exposure": False, "options": [WAIT, BUY]},
    ]
    baseline = run_sequence(contexts, 0.0)
    primed = run_sequence(contexts, 0.8)

    # At step 2: activation=.5, so target utility -0.2 + .8*.75*.5 = 0.1 > wait's 0.
    assert baseline[-1]["state"]["last_choice"] == "wait"
    assert primed[-1]["state"]["last_choice"] == "buy_item"
    assert baseline[-1]["metric"] == 0.0
    assert primed[-1]["metric"] == 20.0
    assert primed[-1]["active"] is True
    assert primed[-1]["state"]["activation"] == pytest.approx(0.5)


def test_boundary_without_exposure_matches_reference_metric():
    contexts = [
        {"bye_exposure": False, "options": [WAIT, BUY]},
        {"bye_exposure": False, "options": [WAIT, BUY]},
    ]
    reference = run_sequence(contexts, 0.0)
    boundary = run_sequence(contexts, 0.8)
    assert boundary[-1]["metric"] == reference[-1]["metric"] == 0.0
    assert boundary[-1]["state"]["last_choice"] == "wait"
    assert boundary[-1]["active"] is False


def test_zero_strength_is_explicit_highest_base_utility_reference():
    result = mechanism.evaluate(
        {"bye_exposure": True, "options": [WAIT, BUY], "state": {}, "peer_states": [],
         "round_index": 0, "agent_index": 0, "uniform": 0.5},
        0.0,
    )
    assert result["state"]["last_choice"] == "wait"
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert "Reference choice maximizes supplied utility" in " ".join(result["trace"])


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="bye_exposure"):
        mechanism.evaluate({"options": [WAIT]}, 0.5)
    with pytest.raises(ValueError, match="sound_association"):
        mechanism.evaluate(
            {"bye_exposure": True, "options": [{"id": "x", "utility": 0, "price": 1, "purchase": True}]},
            0.5,
        )
    with pytest.raises(ValueError, match="must be a purchase"):
        mechanism.evaluate(
            {"bye_exposure": True, "options": [{"id": "x", "utility": 0, "price": 0, "purchase": False, "sound_association": 0.2}]},
            0.5,
        )


def test_strength_validation_rejects_out_of_range_and_nonfinite_values():
    context = {"bye_exposure": False, "options": [WAIT]}
    for strength in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            mechanism.evaluate(context, strength)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_inputs():
    context = {
        "bye_exposure": True,
        "options": [dict(WAIT), dict(BUY)],
        "state": {"activation": 0.25, "cumulative_spend": 2.0, "last_choice": "old", "exposure_count": 2,
                  "annotation": {"tags": ["kept"]}},
        "peer_states": [{"unrelated": [1, 2]}],
        "round_index": 3,
        "agent_index": 4,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["activation"] == pytest.approx(1.0)
    assert first["state"]["cumulative_spend"] == 22.0
    assert first["state"]["annotation"] == {"tags": ["kept"]}


def test_scenario_catalog_has_multistep_positive_and_boundary_cases():
    positive, boundary = mechanism.scenarios()
    assert positive["name"] == "positive" and positive["expectation"] == "increase"
    assert boundary["name"] == "boundary" and boundary["expectation"] == "equal"
    for case in (positive, boundary):
        assert len(case["contexts"]) >= 2
        assert run_sequence(case["contexts"], 0.8)[-1]["metric"] == pytest.approx(
            run_sequence(case["contexts"], 0.0)[-1]["metric"]
            + (20.0 if case["name"] == "positive" else 0.0)
        )
