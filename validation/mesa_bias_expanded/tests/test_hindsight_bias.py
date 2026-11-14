import copy
import math

import pytest

from mechanisms import hindsight_bias


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    results = []
    for round_index, task_context in enumerate(contexts):
        context = copy.deepcopy(task_context)
        context.update(
            state=copy.deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = hindsight_bias.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_sequence_has_numeric_outcome_aligned_reconstruction_oracle():
    forecast, after_outcome = run_sequence(
        [
            {"stage": "forecast", "forecast_probability": 0.2},
            {"stage": "outcome", "outcome_known": True, "outcome": 1},
        ],
        0.8,
    )
    assert forecast["metric"] == 0.0
    assert after_outcome["state"]["original_probability"] == pytest.approx(0.2)
    assert after_outcome["state"]["recalled_probability"] == pytest.approx(0.84)
    assert after_outcome["metric"] == pytest.approx(0.64)
    assert after_outcome["active"] is True
    assert math.isfinite(after_outcome["metric"])


def test_boundary_without_known_outcome_matches_reference_primary_metric():
    contexts = [
        {"stage": "forecast", "forecast_probability": 0.2},
        {"stage": "outcome", "outcome_known": False},
    ]
    boundary = run_sequence(contexts, 0.8)[-1]
    reference = run_sequence(contexts, 0.0)[-1]
    assert boundary["metric"] == reference["metric"] == 0.0
    assert boundary["state"]["recalled_probability"] == pytest.approx(0.2)
    assert boundary["active"] is False


def test_zero_strength_is_verbatim_recorded_forecast_reference():
    result = run_sequence(
        [
            {"stage": "forecast", "forecast_probability": 0.35},
            {"stage": "outcome", "outcome_known": True, "outcome": 1},
        ],
        0.0,
    )[-1]
    assert result["state"]["recalled_probability"] == pytest.approx(0.35)
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_required_evidence_and_impossible_ranges_are_rejected():
    with pytest.raises(ValueError, match="forecast_probability"):
        hindsight_bias.evaluate({"stage": "forecast", "state": {}}, 0.5)
    with pytest.raises(ValueError, match="outcome stage requires a prior"):
        hindsight_bias.evaluate(
            {"stage": "outcome", "outcome_known": True, "outcome": 1, "state": {}}, 0.5
        )
    with pytest.raises(ValueError, match="explicit bool"):
        run_sequence(
            [
                {"stage": "forecast", "forecast_probability": 0.2},
                {"stage": "outcome", "outcome": 1},
            ],
            0.5,
        )
    with pytest.raises(ValueError, match="finite number"):
        hindsight_bias.evaluate(
            {"stage": "forecast", "forecast_probability": float("nan"), "state": {}}, 0.5
        )
    with pytest.raises(ValueError, match="integer 0 or 1"):
        run_sequence(
            [
                {"stage": "forecast", "forecast_probability": 0.2},
                {"stage": "outcome", "outcome_known": True, "outcome": 0.5},
            ],
            0.5,
        )


def test_strength_validation_rejects_nonfinite_and_out_of_range_values():
    valid = {"stage": "forecast", "forecast_probability": 0.2, "state": {}}
    for invalid in (float("nan"), float("inf"), -0.01, 1.01, True):
        with pytest.raises(ValueError, match="strength"):
            hindsight_bias.evaluate(valid, invalid)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        "stage": "outcome",
        "outcome_known": True,
        "outcome": 0,
        "state": {
            "has_forecast": True,
            "original_probability": 0.75,
            "recalled_probability": 0.75,
            "outcome_known": False,
            "outcome": None,
            "resolved": False,
            "extension": {"tag": ["leave", "alone"]},
        },
        "peer_states": [{"nested": [1, 2]}],
        "round_index": 1,
        "agent_index": 0,
        "uniform": 0.5,
    }
    original = copy.deepcopy(context)
    first = hindsight_bias.evaluate(context, 0.6)
    second = hindsight_bias.evaluate(context, 0.6)
    assert context == original
    assert first == second
    assert first["state"]["extension"] == {"tag": ["leave", "alone"]}
    assert first["metric"] == pytest.approx(0.45)
    assert first["state"]["recalled_probability"] == pytest.approx(0.3)
    assert isinstance(first["trace"], list) and first["trace"]


def test_scenarios_are_chronological_and_have_required_names():
    cases = {case["name"]: case for case in hindsight_bias.scenarios()}
    assert {"positive", "boundary"}.issubset(cases)
    assert all(len(case["contexts"]) >= 2 for case in cases.values())
    assert cases["positive"]["expectation"] == "increase"
    assert cases["boundary"]["expectation"] == "equal"
