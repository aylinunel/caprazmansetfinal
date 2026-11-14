from copy import deepcopy

import pytest

from mechanisms import noble_edge_effect as mechanism


def context_for(name="ethical", csr_score=0.9, evidence=True):
    return {
        "focal_option": name,
        "products": [
            {"id": "ethical", "quality_score": 70, "price_index": 20,
             "perceived_csr_score": csr_score, "csr_evidence": evidence},
            {"id": "alternative", "quality_score": 72, "price_index": 20,
             "perceived_csr_score": 0.0, "csr_evidence": False},
        ],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.25,
    }


def test_numeric_oracle_and_strength_changes_selection():
    context = context_for()
    treated = mechanism.evaluate(context, 0.8)
    reference = mechanism.evaluate(context, 0.0)
    # Focal baseline = 70 - .35*20 = 63; CSR premium = 20*.8*.9 = 14.4.
    assert treated["metric"] == pytest.approx(77.4)
    assert treated["state"]["csr_premium"] == pytest.approx(14.4)
    assert treated["state"]["selected_option"] == "ethical"
    assert reference["metric"] == pytest.approx(63.0)
    assert reference["state"]["selected_option"] == "alternative"
    assert treated["active"] is True


def test_positive_scenario_has_greater_focal_appeal_than_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    context = {**scenario["contexts"][0], "state": {}, "peer_states": [],
               "round_index": 0, "agent_index": 0, "uniform": 0.5}
    assert mechanism.evaluate(context, 0.8)["metric"] > mechanism.evaluate(context, 0.0)["metric"]


def test_boundary_removes_csr_evidence_and_matches_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "boundary")
    context = {**scenario["contexts"][0], "state": {}, "peer_states": [],
               "round_index": 0, "agent_index": 0, "uniform": 0.5}
    assert context["products"][0]["csr_evidence"] is False
    assert context["products"][0]["perceived_csr_score"] == 0
    result = mechanism.evaluate(context, 0.8)
    reference = mechanism.evaluate(context, 0.0)
    assert result["metric"] == reference["metric"]
    assert result["state"]["selected_option"] == reference["state"]["selected_option"]
    assert result["active"] is False


def test_zero_strength_is_explicit_quality_price_reference():
    result = mechanism.evaluate(context_for(), 0)
    assert result["metric"] == pytest.approx(63.0)
    assert result["state"]["csr_premium"] == 0
    assert result["state"]["selected_option"] == "alternative"
    assert result["active"] is False


def test_missing_required_top_level_input_is_rejected():
    context = context_for()
    del context["products"]
    with pytest.raises(ValueError, match="products"):
        mechanism.evaluate(context, 0.8)


def test_invalid_phase_specific_csr_fields_are_rejected():
    context = context_for()
    context["products"][0]["perceived_csr_score"] = 1.2
    with pytest.raises(ValueError, match="perceived_csr_score"):
        mechanism.evaluate(context, 0.8)
    context = context_for()
    context["products"][0]["csr_evidence"] = "yes"
    with pytest.raises(ValueError, match="csr_evidence"):
        mechanism.evaluate(context, 0.8)


def test_invalid_strength_is_rejected():
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(context_for(), float("nan"))
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(context_for(), 1.01)


def test_deterministic_and_nonmutating_with_nested_state():
    context = context_for()
    context["state"] = {"selected_option": "prior", "custom": {"seen": [1, 2]}}
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert first == second
    assert context == before
