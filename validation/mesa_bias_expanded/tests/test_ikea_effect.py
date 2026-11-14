from copy import deepcopy

import pytest

from mechanisms import ikea_effect


BASE = {
    "objective_value": 40,
    "objective_customization_benefit": 5,
    "self_assembled": True,
    "assembly_effort_hours": 3,
    "owned": True,
}


def evaluate(context=None, strength=0.8):
    supplied = {} if context is None else deepcopy(context)
    supplied.setdefault("state", {})
    supplied.setdefault("peer_states", [])
    supplied.setdefault("round_index", 0)
    supplied.setdefault("agent_index", 0)
    supplied.setdefault("uniform", 0.5)
    return ikea_effect.evaluate(supplied, strength)


def test_positive_numeric_oracle_and_effect_direction():
    reference = evaluate(BASE, strength=0)
    result = evaluate(BASE, strength=0.8)
    # 40 objective + 5 explicit customization benefit + .8*2*3 effort premium.
    assert reference["metric"] == 45
    assert result["metric"] == 49.8
    assert result["metric"] > reference["metric"]
    assert result["active"] is True
    assert result["state"]["last_assembly_uplift"] == pytest.approx(4.8)
    assert "effort_hours=3" in result["trace"][0]


def test_boundary_ownership_without_personal_assembly_equals_reference():
    context = {**BASE, "self_assembled": False, "owned": True}
    result = evaluate(context, strength=0.8)
    reference = evaluate(context, strength=0)
    assert result["metric"] == reference["metric"] == 45
    assert result["active"] is False
    assert result["state"]["last_assembly_uplift"] == 0


def test_zero_strength_is_explicit_reference_policy():
    result = evaluate(BASE, strength=0)
    assert result["metric"] == 45
    assert result["active"] is False
    assert result["state"]["last_reference_value"] == 45


def test_objective_customization_benefit_counts_without_assembly():
    context = {
        **BASE,
        "self_assembled": False,
        "assembly_effort_hours": 0,
        "objective_customization_benefit": 7,
    }
    result = evaluate(context, strength=0.8)
    assert result["metric"] == 47
    assert result["active"] is False


def test_missing_or_impossible_required_evidence_is_rejected():
    missing = dict(BASE)
    del missing["owned"]
    with pytest.raises(ValueError, match="owned"):
        evaluate(missing)
    impossible = {**BASE, "assembly_effort_hours": 0}
    with pytest.raises(ValueError, match="positive assembly_effort_hours"):
        evaluate(impossible)
    malformed = {**BASE, "objective_value": float("nan")}
    with pytest.raises(ValueError, match="objective_value"):
        evaluate(malformed)


def test_strength_validation_rejects_out_of_range_and_nonfinite():
    with pytest.raises(ValueError):
        evaluate(BASE, strength=1.01)
    with pytest.raises(ValueError):
        evaluate(BASE, strength=float("inf"))


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        **BASE,
        "state": {"evaluation_count": 2, "custom": {"tags": ["kept"]}},
    }
    before = deepcopy(context)
    first = ikea_effect.evaluate(context, 0.8)
    second = ikea_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["evaluation_count"] == 3
    assert first["state"]["custom"] == {"tags": ["kept"]}
    first["state"]["custom"]["tags"].append("isolated")
    assert context["state"]["custom"]["tags"] == ["kept"]


def test_scenario_contract_names_and_expected_numeric_comparison():
    cases = {case["name"]: case for case in ikea_effect.scenarios()}
    assert {"positive", "boundary"}.issubset(cases)
    positive = cases["positive"]
    p = evaluate(positive["contexts"][0], 0.8)
    p0 = evaluate(positive["contexts"][0], 0)
    assert positive["expectation"] == "increase"
    assert p["metric"] > p0["metric"]
    boundary = cases["boundary"]
    b = evaluate(boundary["contexts"][0], 0.8)
    b0 = evaluate(boundary["contexts"][0], 0)
    assert boundary["expectation"] == "equal"
    assert b["metric"] == b0["metric"]
