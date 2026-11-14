from copy import deepcopy

import pytest

from mechanisms.consequence_framing import evaluate, scenarios


def _input(**overrides):
    value = {
        "event_label": "Council approves a transit plan",
        "event_salience": 0.40,
        "consequence_label": "Commute times are expected to fall",
        "consequence_salience": 0.70,
        "consequence_supported": True,
    }
    value.update(overrides)
    return value


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_scenario_increases_consequence_led_choice_at_point_eight():
    scenario = next(item for item in scenarios() if item["name"] == "positive")
    baseline = _run(scenario["contexts"], 0.0, scenario["initial_state"])[-1]
    modeled = _run(scenario["contexts"], 0.8, scenario["initial_state"])[-1]
    assert baseline["metric"] == 0.0
    assert modeled["metric"] == 1.0
    assert modeled["metric"] > baseline["metric"]
    assert modeled["active"] is True


def test_boundary_without_supported_effect_matches_strength_zero():
    scenario = next(item for item in scenarios() if item["name"] == "boundary")
    baseline = _run(scenario["contexts"], 0.0, scenario["initial_state"])[-1]
    modeled = _run(scenario["contexts"], 0.8, scenario["initial_state"])[-1]
    assert baseline["metric"] == modeled["metric"] == 0.0
    assert modeled["active"] is False
    assert modeled["state"]["last_focus"] == "event"


def test_zero_strength_is_explicit_event_led_reference_even_with_high_consequence():
    result = evaluate(
        _input(event_salience=0.05, consequence_salience=1.0), strength=0.0
    )
    assert result["metric"] == 0.0
    assert result["state"]["last_focus"] == "event"
    assert "weighted_consequence=strength*consequence_salience=0" in result["trace"][0]


def test_numeric_choice_oracle_uses_weighted_consequence_competition_and_strict_tie():
    # .8 × .7 = .56 > .4, so the consequence wins. At equality, event wins.
    consequence_wins = evaluate(_input(), strength=0.8)
    tied = evaluate(
        _input(event_salience=0.56, consequence_salience=0.70), strength=0.8
    )
    assert consequence_wins["metric"] == 1.0
    assert consequence_wins["state"]["consequence_led_count"] == 1
    assert tied["metric"] == 0.0
    assert tied["state"]["last_focus"] == "event"


def test_missing_or_invalid_evidence_is_rejected_not_scored_as_zero():
    missing = _input()
    del missing["consequence_supported"]
    with pytest.raises(ValueError, match="missing required"):
        evaluate(missing, 0.8)
    with pytest.raises(ValueError, match="explicit bool"):
        evaluate(_input(consequence_supported=None), 0.8)
    with pytest.raises(ValueError, match="finite number"):
        evaluate(_input(event_salience=float("nan")), 0.8)


def test_strength_validation_rejects_out_of_range_and_non_finite_values():
    for strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            evaluate(_input(), strength)


def test_deterministic_and_nonmutating_with_chronological_state_carry():
    context = _input(state={"steps": 2, "consequence_led_count": 1, "other": {"x": [3]}})
    original = deepcopy(context)
    first = evaluate(context, 0.8)
    second = evaluate(context, 0.8)
    assert first == second
    assert context == original
    assert first["state"]["steps"] == 3
    assert first["state"]["consequence_led_count"] == 2
    assert first["state"]["other"] == {"x": [3]}
