from copy import deepcopy

import pytest

from mechanisms import loaded_language


def _context(**overrides):
    values = {
        "event_valence": 0.2,
        "evaluation_present": True,
        "targets_event": True,
        "evaluation_valence": -0.8,
        "evaluation_intensity": 0.75,
    }
    values.update(overrides)
    return values


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, task_context in enumerate(contexts):
        full_context = deepcopy(task_context)
        full_context.update(
            {
                "state": state,
                "peer_states": [],
                "round_index": round_index,
                "agent_index": 0,
                "uniform": 0.5,
            }
        )
        result = loaded_language.evaluate(full_context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_linked_loaded_evaluation_shifts_appraisal_by_numeric_oracle():
    context = _context()
    reference = loaded_language.evaluate(context, 0.0)
    framed = loaded_language.evaluate(context, 0.8)

    # Weight=.8*.75=.6; appraisal=.4*.2 + .6*(-.8) = -.4.
    assert reference["metric"] == pytest.approx(0.2)
    assert framed["metric"] == pytest.approx(-0.4)
    assert framed["metric"] < reference["metric"]
    assert framed["active"] is True
    assert framed["state"]["last_loaded_shift"] == pytest.approx(-0.6)


def test_negative_event_reporting_without_evaluation_is_boundary_equivalent():
    boundary = _context(
        event_valence=-0.7,
        evaluation_present=False,
        targets_event=False,
        evaluation_valence=None,
        evaluation_intensity=None,
    )
    at_zero = loaded_language.evaluate(boundary, 0.0)
    at_strength = loaded_language.evaluate(boundary, 0.8)

    assert at_zero["metric"] == at_strength["metric"] == -0.7
    assert at_strength["active"] is False
    assert "no evaluation is present" in at_strength["trace"][1]


def test_zero_strength_is_the_explicit_factual_only_reference():
    context = _context(event_valence=-0.35, evaluation_valence=0.95)
    result = loaded_language.evaluate(context, 0.0)

    assert result["metric"] == -0.35
    assert result["state"]["last_loaded_shift"] == 0.0
    assert result["active"] is False


def test_unlinked_evaluative_wording_does_not_change_event_appraisal():
    context = _context(targets_event=False)
    result = loaded_language.evaluate(context, 0.8)

    assert result["metric"] == 0.2
    assert result["active"] is False
    assert "not linked" in result["trace"][1]


def test_missing_impossible_and_out_of_range_inputs_are_rejected():
    with pytest.raises(ValueError, match="missing required input"):
        loaded_language.evaluate({"event_valence": 0.0}, 0.5)
    with pytest.raises(ValueError, match="event_valence"):
        loaded_language.evaluate(_context(event_valence=1.1), 0.5)
    with pytest.raises(ValueError, match="evaluation_intensity"):
        loaded_language.evaluate(_context(evaluation_intensity=float("nan")), 0.5)
    with pytest.raises(ValueError, match="must be None"):
        loaded_language.evaluate(
            _context(evaluation_present=False, evaluation_valence=-0.2, evaluation_intensity=None), 0.5
        )
    with pytest.raises(ValueError, match="strength"):
        loaded_language.evaluate(_context(), 1.01)


def test_deterministic_and_nonmutating_with_nested_prior_state():
    context = _context()
    context["state"] = {
        "decision_count": 2,
        "appraisal_history": [0.1, -0.2],
        "last_appraisal": -0.2,
        "last_loaded_shift": 0.0,
        "unrelated_extension": {"kept": [1, 2]},
    }
    before = deepcopy(context)

    first = loaded_language.evaluate(context, 0.8)
    second = loaded_language.evaluate(context, 0.8)

    assert context == before
    assert first == second
    assert first["state"]["decision_count"] == 3
    assert first["state"]["appraisal_history"] == [0.1, -0.2, pytest.approx(-0.4)]
    assert first["state"]["unrelated_extension"] == {"kept": [1, 2]}
    first["state"]["unrelated_extension"]["kept"].append(3)
    assert context["state"]["unrelated_extension"] == {"kept": [1, 2]}


def test_scenario_catalog_contains_positive_effect_and_removed_condition_boundary():
    scenarios = {item["name"]: item for item in loaded_language.scenarios()}
    assert set(scenarios) >= {"positive", "boundary"}
    positive = _run(scenarios["positive"]["contexts"], 0.8)[-1]["metric"]
    positive_reference = _run(scenarios["positive"]["contexts"], 0.0)[-1]["metric"]
    boundary = _run(scenarios["boundary"]["contexts"], 0.8)[-1]["metric"]
    boundary_reference = _run(scenarios["boundary"]["contexts"], 0.0)[-1]["metric"]

    assert positive == pytest.approx(-0.4)
    assert positive < positive_reference
    assert boundary == boundary_reference == -0.7
