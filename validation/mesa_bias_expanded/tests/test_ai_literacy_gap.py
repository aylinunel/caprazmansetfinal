from copy import deepcopy

import pytest

from mechanisms import ai_literacy_gap as mechanism


def direct(context, strength, state=None, round_index=0):
    """Call the plugin with the runner's reserved inputs and an isolated state copy."""
    supplied = deepcopy(context)
    supplied.setdefault("state", deepcopy(state or {}))
    supplied.setdefault("peer_states", [])
    supplied.setdefault("round_index", round_index)
    supplied.setdefault("agent_index", 0)
    supplied.setdefault("uniform", 0.5)
    return mechanism.evaluate(supplied, strength)


def test_positive_gap_crosses_validation_gate_and_matches_choice_oracle():
    context = mechanism.scenarios()[0]["contexts"][0]
    baseline = direct(context, 0.0)
    modeled = direct(context, 0.8)

    # 0.4 + 0.8 * (0.9 - 0.4) = 0.8 >= 0.7; baseline 0.4 < 0.7.
    assert baseline["metric"] == 0
    assert baseline["state"]["last_choice"] == "non_ai"
    assert modeled["metric"] == 1
    assert modeled["state"]["last_choice"] == "ai"
    assert modeled["state"]["unverified_reliance"] == 1
    assert modeled["active"] is True


def test_boundary_without_comfort_competence_gap_matches_reference():
    context = mechanism.scenarios()[1]["contexts"][0]
    assert context["use_frequency"] == 1.0  # frequent use alone is not the trigger
    baseline = direct(context, 0.0)
    modeled = direct(context, 0.8)
    assert baseline["metric"] == modeled["metric"] == 0
    assert baseline["state"]["last_choice"] == modeled["state"]["last_choice"] == "non_ai"
    assert modeled["active"] is False


def test_zero_strength_is_explicit_reference_policy():
    context = {
        "ai_comfort": 1.0,
        "ai_competence": 0.7,
        "task_ai_advantage": 0.2,
        "validation_demand": 0.7,
    }
    result = direct(context, 0.0)
    assert result["state"]["last_choice"] == "ai"
    assert result["metric"] == 0  # selected, but actual competence meets demand
    assert result["active"] is False


def test_no_ai_advantage_blocks_selection_despite_large_gap():
    context = {
        "ai_comfort": 1.0,
        "ai_competence": 0.1,
        "task_ai_advantage": 0.0,
        "validation_demand": 0.8,
    }
    result = direct(context, 1.0)
    assert result["metric"] == 0
    assert result["state"]["last_choice"] == "non_ai"


@pytest.mark.parametrize(
    "context,strength",
    [
        ({"ai_comfort": 0.9, "ai_competence": 0.4, "task_ai_advantage": 0.5}, 0.8),
        ({"ai_comfort": 1.1, "ai_competence": 0.4, "task_ai_advantage": 0.5, "validation_demand": 0.7}, 0.8),
        ({"ai_comfort": 0.9, "ai_competence": 0.4, "task_ai_advantage": 0.5, "validation_demand": 0.7}, float("nan")),
        ({"ai_comfort": 0.9, "ai_competence": 0.4, "task_ai_advantage": 0.5, "validation_demand": 0.7}, 1.01),
    ],
)
def test_missing_or_impossible_evidence_and_invalid_strength_raise(context, strength):
    with pytest.raises(ValueError):
        direct(context, strength)


def test_deterministic_and_nonmutating_with_prior_state():
    context = {
        "ai_comfort": 0.9,
        "ai_competence": 0.4,
        "task_ai_advantage": 0.5,
        "validation_demand": 0.7,
        "use_frequency": 0.95,
        "state": {
            "rounds": 2,
            "ai_selected": 1,
            "unverified_reliance": 1,
            "last_choice": "ai",
            "caller_note": "preserved",
        },
    }
    untouched = deepcopy(context)
    first = direct(context, 0.8, round_index=2)
    second = direct(context, 0.8, round_index=2)
    assert context == untouched
    assert first == second
    assert first["state"]["rounds"] == 3
    assert first["state"]["unverified_reliance"] == 2
    assert first["state"]["caller_note"] == "preserved"
    assert isinstance(first["metric"], (int, float))


def test_scenario_contract_names_and_direction():
    positive, boundary = mechanism.scenarios()
    assert positive["name"] == "positive" and positive["expectation"] == "increase"
    assert boundary["name"] == "boundary" and boundary["expectation"] == "equal"
    assert positive["contexts"] and boundary["contexts"]
