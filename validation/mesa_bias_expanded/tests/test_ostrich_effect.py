from copy import deepcopy

import pytest

from mechanisms import ostrich_effect as plugin


def _context(info, state=None):
    return {
        "information": deepcopy(info),
        "state": deepcopy(state or {}),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.37,
    }


def _run(contexts, strength):
    state = {"information_value_accessed": 0.0, "reports_read": 0, "avoidance_choices": 0}
    result = None
    for index, task_input in enumerate(contexts):
        ctx = _context(task_input["information"], state)
        ctx["round_index"] = index
        result = plugin.evaluate(ctx, strength)
        state = result["state"]
    return result


def test_numeric_choice_oracle_and_trace_explain_concept_specific_threshold():
    ctx = _context({
        "decision_value": 3.0,
        "read_cost": 1.0,
        "threatening": True,
        "discomfort": 4.0,
        "practical_delay": False,
    })
    reference = plugin.evaluate(ctx, 0.0)
    intervention = plugin.evaluate(ctx, 0.8)
    assert reference["metric"] == 3.0  # 3 >= 1, so the reference reads.
    assert reference["state"]["reports_read"] == 1
    assert intervention["metric"] == 0.0  # 3 - (0.8*4) = -0.2 < 1, so it avoids.
    assert intervention["active"] is True
    assert intervention["state"]["avoidance_choices"] == 1
    assert any("0.8*4=3.2" in line for line in intervention["trace"])


def test_positive_scenario_reduces_cumulative_information_access():
    positive = next(s for s in plugin.scenarios() if s["name"] == "positive")
    reference = _run(positive["contexts"], 0.0)
    intervention = _run(positive["contexts"], 0.8)
    assert reference["metric"] == 7.5
    assert intervention["metric"] == 0.0
    assert intervention["metric"] < reference["metric"]
    assert intervention["state"]["avoidance_choices"] == 3


def test_boundary_nonthreatening_information_matches_reference_despite_discomfort():
    boundary = next(s for s in plugin.scenarios() if s["name"] == "boundary")
    reference = _run(boundary["contexts"], 0.0)
    intervention = _run(boundary["contexts"], 0.8)
    assert reference["metric"] == intervention["metric"] == 5.0
    assert intervention["state"]["reports_read"] == 2
    assert intervention["state"]["avoidance_choices"] == 0


def test_zero_strength_is_explicit_reference_policy_and_does_not_activate():
    info = {"decision_value": 1.0, "read_cost": 1.0, "threatening": True, "discomfort": 9.0, "practical_delay": False}
    result = plugin.evaluate(_context(info), 0.0)
    assert result["metric"] == 1.0  # threshold tie is read under the stated reference rule.
    assert result["active"] is False
    assert result["state"] == {"information_value_accessed": 1.0, "reports_read": 1, "avoidance_choices": 0}


def test_practical_delay_bypasses_avoidance_and_preserves_reference_choice():
    info = {"decision_value": 2.0, "read_cost": 1.0, "threatening": True, "discomfort": 4.0, "practical_delay": True}
    result = plugin.evaluate(_context(info), 0.8)
    assert result["metric"] == 2.0
    assert result["active"] is False
    assert result["state"]["avoidance_choices"] == 0


def test_missing_or_invalid_phase_specific_information_is_rejected():
    with pytest.raises(ValueError, match="missing required task input"):
        plugin.evaluate(_context_missing(), 0.8)
    with pytest.raises(ValueError, match="missing fields"):
        plugin.evaluate(_context({"decision_value": 2.0}), 0.8)
    bad = {"decision_value": -1, "read_cost": 0, "threatening": True, "discomfort": 1, "practical_delay": False}
    with pytest.raises(ValueError, match="finite nonnegative"):
        plugin.evaluate(_context(bad), 0.8)
    bad["decision_value"] = 2
    bad["threatening"] = 1
    with pytest.raises(ValueError, match="must be a boolean"):
        plugin.evaluate(_context(bad), 0.8)
    for strength in (-0.1, 1.1, float("nan")):
        with pytest.raises(ValueError, match="strength"):
            plugin.evaluate(_context({"decision_value": 1, "read_cost": 1, "threatening": False, "discomfort": 0, "practical_delay": False}), strength)


def _context_missing():
    return {"state": {}, "peer_states": [], "round_index": 0, "agent_index": 0, "uniform": 0.2}


def test_evaluation_is_deterministic_and_does_not_mutate_nested_input():
    context = _context({"decision_value": 2.0, "read_cost": 0.5, "threatening": True, "discomfort": 3.0, "practical_delay": False},
                       {"information_value_accessed": 1.25, "reports_read": 1, "avoidance_choices": 0})
    before = deepcopy(context)
    first = plugin.evaluate(context, 0.8)
    second = plugin.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["metric"] == 1.25  # 2 - 2.4 < .5, so no new information is accessed.
    assert first["state"] == {"information_value_accessed": 1.25, "reports_read": 1, "avoidance_choices": 1}
