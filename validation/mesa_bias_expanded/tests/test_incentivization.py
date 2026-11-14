from copy import deepcopy

import pytest

from mechanisms import incentivization


def task_context(**overrides):
    context = {
        "task_value": 2.0,
        "effort_cost": 5.0,
        "completion_reward": 3.5,
        "noncompletion_penalty": 0.5,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        context = deepcopy(item)
        context.update(
            {
                "state": state,
                "peer_states": [],
                "round_index": index,
                "agent_index": 0,
                "uniform": 0.5,
            }
        )
        result = incentivization.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_positive_reward_and_penalty_cross_intrinsic_completion_threshold():
    context = task_context()
    baseline = incentivization.evaluate(context, 0.0)
    incentivized = incentivization.evaluate(context, 0.8)

    # Intrinsic surplus is 2 - 5 = -3; incentive contribution is
    # .8 * (3.5 + .5) = 3.2, so effective surplus +.2 selects completion.
    assert baseline["metric"] == 0.0
    assert incentivized["state"]["last_effective_surplus"] == pytest.approx(0.2)
    assert incentivized["metric"] == 1.0
    assert incentivized["active"] is True


def test_boundary_without_any_consequence_contingency_matches_reference_at_point_8():
    context = task_context(completion_reward=0.0, noncompletion_penalty=0.0)
    reference = incentivization.evaluate(context, 0.0)
    boundary = incentivization.evaluate(context, 0.8)

    assert boundary["metric"] == reference["metric"] == 0.0
    assert boundary["state"]["last_completion"] == reference["state"]["last_completion"]
    assert boundary["active"] is False
    assert boundary["state"]["last_incentive_contribution"] == 0.0


def test_zero_strength_is_explicit_intrinsic_surplus_reference_and_completes_ties():
    context = task_context(
        task_value=4.0,
        effort_cost=4.0,
        completion_reward=0.0,
        noncompletion_penalty=0.0,
        state={"decision_count": 2, "custom": {"memo": ["kept"]}},
    )
    result = incentivization.evaluate(context, 0.0)

    assert result["metric"] == 1.0  # reference: task_value - effort_cost >= 0
    assert result["active"] is False
    assert result["state"]["decision_count"] == 3
    assert result["state"]["custom"] == {"memo": ["kept"]}
    assert result["state"]["last_intrinsic_surplus"] == 0.0


def test_missing_or_impossible_task_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        incentivization.evaluate({"task_value": 3.0}, 0.8)
    with pytest.raises(ValueError, match="nonnegative"):
        incentivization.evaluate(task_context(effort_cost=-1.0), 0.8)
    with pytest.raises(ValueError, match="finite"):
        incentivization.evaluate(task_context(completion_reward=float("inf")), 0.8)


def test_invalid_strength_and_wrong_field_types_are_rejected():
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        incentivization.evaluate(task_context(), 1.01)
    with pytest.raises(ValueError, match="finite number"):
        incentivization.evaluate(task_context(), float("nan"))
    with pytest.raises(ValueError, match="finite number"):
        incentivization.evaluate(task_context(task_value=True), 0.8)


def test_determinism_and_nested_input_nonmutation():
    context = task_context(state={"decision_count": 1, "extra": {"items": ["prior"]}})
    before = deepcopy(context)

    first = incentivization.evaluate(context, 0.8)
    second = incentivization.evaluate(context, 0.8)
    assert context == before
    assert first == second
    first["state"]["extra"]["items"].append("new")
    assert context == before
    assert second["state"]["extra"]["items"] == ["prior"]


def test_chronological_calls_carry_state_only_for_real_contexts():
    contexts = [
        {
            "task_value": 2.0,
            "effort_cost": 5.0,
            "completion_reward": 3.5,
            "noncompletion_penalty": 0.5,
        },
        {
            "task_value": 1.0,
            "effort_cost": 5.0,
            "completion_reward": 3.5,
            "noncompletion_penalty": 0.5,
        },
    ]
    outputs = run_sequence(contexts, 0.8)
    assert len(outputs) == 2
    assert outputs[0]["metric"] == 1.0
    assert outputs[1]["metric"] == 0.0  # second surplus is -4 + 3.2 = -0.8
    assert outputs[-1]["state"]["decision_count"] == 2
