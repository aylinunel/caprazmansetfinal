from copy import deepcopy

import pytest

from mechanisms import outcome_bias


def context(**overrides):
    data = {
        "case_id": "case-1",
        "evidence_quality": 0.8,
        "outcome_observed": True,
        "outcome_quality": 0.2,
        "state": {"evaluations": []},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.25,
    }
    data.update(overrides)
    return data


def run_contexts(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {"evaluations": []})
    outputs = []
    for round_index, task in enumerate(contexts):
        current = deepcopy(task)
        current.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.25,
        })
        output = outcome_bias.evaluate(current, strength)
        outputs.append(output)
        state = output["state"]
    return outputs


def test_numeric_oracle_is_interpolation_toward_realized_result():
    result = outcome_bias.evaluate(context(), 0.75)
    assert result["metric"] == pytest.approx(0.35)
    assert result["state"]["evaluations"][-1]["appraisal"] == pytest.approx(0.35)
    assert result["active"] is True
    assert "predictable" in result["trace"][0]


def test_positive_scenario_reduces_appraisal_vs_evidence_reference():
    scenario = outcome_bias.scenarios()[0]
    intervention = run_contexts(scenario["contexts"], 0.8, scenario["initial_state"])
    reference = run_contexts(scenario["contexts"], 0.0, scenario["initial_state"])
    assert intervention[-1]["metric"] < reference[-1]["metric"]
    assert intervention[-1]["metric"] == pytest.approx(0.38)
    assert len(intervention[-1]["state"]["evaluations"]) == 2


def test_boundary_withholds_the_necessary_observed_outcome():
    scenario = outcome_bias.scenarios()[1]
    intervention = run_contexts(scenario["contexts"], 0.8, scenario["initial_state"])[-1]
    reference = run_contexts(scenario["contexts"], 0.0, scenario["initial_state"])[-1]
    assert scenario["contexts"][0]["outcome_observed"] is False
    assert scenario["contexts"][0]["outcome_quality"] is None
    assert intervention["metric"] == reference["metric"] == pytest.approx(0.8)
    assert intervention["active"] is False


def test_zero_strength_is_explicit_evidence_based_reference():
    result = outcome_bias.evaluate(context(), 0.0)
    assert result["metric"] == pytest.approx(0.8)
    assert result["state"]["evaluations"][-1]["appraisal"] == pytest.approx(0.8)
    assert result["active"] is False


def test_missing_and_invalid_phase_inputs_are_rejected():
    missing = context()
    del missing["outcome_observed"]
    with pytest.raises(ValueError, match="outcome_observed"):
        outcome_bias.evaluate(missing, 0.8)
    with pytest.raises(ValueError, match="outcome_quality"):
        outcome_bias.evaluate(context(outcome_quality=1.5), 0.8)
    with pytest.raises(ValueError, match="outcome_quality=None"):
        outcome_bias.evaluate(context(outcome_observed=False, outcome_quality=0.2), 0.8)
    with pytest.raises(ValueError, match="strength"):
        outcome_bias.evaluate(context(), float("nan"))


def test_deterministic_and_nonmutating_for_context_and_nested_history():
    original = context(state={"evaluations": [{"case_id": "earlier", "meta": {"x": 1}}]})
    before = deepcopy(original)
    first = outcome_bias.evaluate(original, 0.6)
    second = outcome_bias.evaluate(original, 0.6)
    assert original == before
    assert first == second
    first["state"]["evaluations"][0]["meta"]["x"] = 99
    assert original["state"]["evaluations"][0]["meta"]["x"] == 1


def test_outcome_bias_is_not_a_hindsight_predictability_update():
    # No predictability input exists: holding process evidence fixed, only the
    # observed realized result can shift this decision-quality appraisal.
    good_result = outcome_bias.evaluate(context(outcome_quality=0.9), 0.5)
    bad_result = outcome_bias.evaluate(context(outcome_quality=0.1), 0.5)
    assert good_result["metric"] == pytest.approx(0.85)
    assert bad_result["metric"] == pytest.approx(0.45)
    assert good_result["state"]["evaluations"][-1]["evidence_quality"] == bad_result["state"]["evaluations"][-1]["evidence_quality"]
