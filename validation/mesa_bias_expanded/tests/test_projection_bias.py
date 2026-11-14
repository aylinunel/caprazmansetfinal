from copy import deepcopy

import pytest

from mechanisms import projection_bias as plugin


POSITIVE = {
    "current_utilities": {"present_favorite": 1.0, "future_favorite": 0.0},
    "future_utilities": {"present_favorite": 0.0, "future_favorite": 1.0},
}


def context_for(task, state=None):
    context = deepcopy(task)
    context.update({
        "state": {} if state is None else deepcopy(state),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    })
    return context


def test_numeric_choice_oracle_uses_current_future_utility_blend():
    result = plugin.evaluate(context_for(POSITIVE), 0.8)
    assert result["state"]["last_projected_utilities"] == {
        "present_favorite": pytest.approx(0.8),
        "future_favorite": pytest.approx(0.2),
    }
    assert result["state"]["last_choice"] == "present_favorite"
    assert result["state"]["last_reference_choice"] == "future_favorite"
    assert result["metric"] == 0.0
    assert result["active"] is True
    assert result["trace"] and "projected_i" in result["trace"][0]


def test_positive_strength_reduces_future_satisfaction():
    reference = plugin.evaluate(context_for(POSITIVE), 0.0)
    projected = plugin.evaluate(context_for(POSITIVE), 0.8)
    assert reference["metric"] == 1.0
    assert projected["metric"] < reference["metric"]


def test_boundary_removes_current_future_divergence():
    boundary = {
        "current_utilities": {"tea": 1.0, "coffee": 0.2},
        "future_utilities": {"tea": 1.0, "coffee": 0.2},
    }
    no_projection = plugin.evaluate(context_for(boundary), 0.0)
    with_projection = plugin.evaluate(context_for(boundary), 0.8)
    assert with_projection["metric"] == no_projection["metric"] == 1.0
    assert with_projection["state"]["last_choice"] == no_projection["state"]["last_choice"]
    assert with_projection["active"] is False


def test_zero_strength_is_explicit_future_only_reference():
    result = plugin.evaluate(context_for(POSITIVE), 0.0)
    assert result["state"]["last_projected_utilities"] == POSITIVE["future_utilities"]
    assert result["state"]["last_choice"] == "future_favorite"
    assert result["state"]["last_choice"] == result["state"]["last_reference_choice"]
    assert result["active"] is False


def test_rejects_missing_and_invalid_phase_inputs():
    with pytest.raises(ValueError, match="current_utilities is required"):
        plugin.evaluate(context_for({"future_utilities": POSITIVE["future_utilities"]}), 0.5)
    with pytest.raises(ValueError, match="identical options"):
        plugin.evaluate(context_for({
            "current_utilities": {"a": 0.5, "b": 0.4},
            "future_utilities": {"a": 0.5, "c": 0.4},
        }), 0.5)
    with pytest.raises(ValueError, match="finite utility"):
        plugin.evaluate(context_for({
            "current_utilities": {"a": float("nan"), "b": 0.4},
            "future_utilities": {"a": 0.5, "b": 0.4},
        }), 0.5)


def test_strength_validation_and_deterministic_nonmutation():
    original = context_for(POSITIVE, {"choice_count": 3, "nested": {"keep": [1, 2]}})
    before = deepcopy(original)
    first = plugin.evaluate(original, 0.8)
    second = plugin.evaluate(original, 0.8)
    assert original == before
    assert first == second
    assert first["state"]["choice_count"] == 4
    assert first["state"]["nested"] == {"keep": [1, 2]}
    for strength in (-0.01, 1.01, float("nan"), True):
        with pytest.raises(ValueError):
            plugin.evaluate(context_for(POSITIVE), strength)


def test_metadata_required_inputs_are_common_task_keys_only():
    assert plugin.METADATA["required_inputs"] == ["current_utilities", "future_utilities"]
    for scenario in plugin.scenarios():
        for task_context in scenario["contexts"]:
            assert set(plugin.METADATA["required_inputs"]).issubset(task_context)
            assert not ({"state", "peer_states", "uniform", "round_index", "agent_index"} & task_context.keys())
