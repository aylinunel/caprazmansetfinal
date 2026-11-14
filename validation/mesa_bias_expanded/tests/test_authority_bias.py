from copy import deepcopy

import pytest

from mechanisms import authority_bias


def _context(**overrides):
    context = {
        "claim_id": "claim-1",
        "direct_evidence": 0.25,
        "expertise_relevance": False,
        "expert_testimony": 0.95,
        "authority_status": 0.95,
        "acceptance_threshold": 0.70,
        "authority_sufficiency_threshold": 0.65,
        "state": {"steps": 2, "reviewed_claim_ids": ["older"], "accepted_claim_ids": []},
    }
    context.update(overrides)
    return context


def test_positive_authority_cue_changes_choice_with_numeric_oracle():
    context = _context()
    reference = authority_bias.evaluate(context, 0.0)
    result = authority_bias.evaluate(context, 0.8)
    # Explicit task oracle: evidence .25 < .70; status route .8*.95=.76 >= .65.
    assert reference["metric"] == 0.0
    assert result["metric"] == 1.0
    assert result["active"] is True
    assert result["state"]["accepted_claim_ids"] == ["claim-1"]


def test_relevant_expertise_boundary_equals_reference_at_strength_point_eight():
    context = _context(expertise_relevance=True, expert_testimony=0.80)
    reference = authority_bias.evaluate(context, 0.0)
    result = authority_bias.evaluate(context, 0.8)
    assert reference["metric"] == result["metric"] == 1.0
    assert result["active"] is False
    assert "route=False" in result["trace"][1]


def test_zero_strength_reproduces_documented_evidence_reference_rule():
    context = _context(direct_evidence=0.72, expert_testimony=0.99)
    result = authority_bias.evaluate(context, 0.0)
    assert result["metric"] == 1.0  # direct evidence alone reaches .70
    assert result["active"] is False
    weak = authority_bias.evaluate(_context(expert_testimony=0.99), 0.0)
    assert weak["metric"] == 0.0  # irrelevant testimony cannot satisfy reference


def test_missing_and_impossible_evidence_are_rejected():
    with pytest.raises(ValueError, match="missing required inputs"):
        authority_bias.evaluate({"claim_id": "x"}, 0.5)
    with pytest.raises(ValueError, match="direct_evidence"):
        authority_bias.evaluate(_context(direct_evidence=float("nan")), 0.5)
    with pytest.raises(ValueError, match="expertise_relevance"):
        authority_bias.evaluate(_context(expertise_relevance=1), 0.5)


def test_invalid_strength_and_sufficiency_cutoff_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        authority_bias.evaluate(_context(), 1.01)
    with pytest.raises(ValueError, match="authority_sufficiency_threshold"):
        authority_bias.evaluate(_context(authority_sufficiency_threshold=0.0), 0.5)


def test_determinism_and_input_state_nonmutation():
    context = _context(metadata={"nested": [1, 2]})
    before = deepcopy(context)
    first = authority_bias.evaluate(context, 0.8)
    second = authority_bias.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["steps"] == 3
    assert first["state"]["reviewed_claim_ids"] == ["older", "claim-1"]
    # Returned state is independent of both context and later result mutation.
    first["state"]["reviewed_claim_ids"].append("mutated")
    assert context["state"]["reviewed_claim_ids"] == ["older"]
    assert second["state"]["reviewed_claim_ids"] == ["older", "claim-1"]


def test_scenarios_encode_required_positive_and_boundary_outcomes():
    scenarios = {item["name"]: item for item in authority_bias.scenarios()}
    assert set(("positive", "boundary")).issubset(scenarios)
    positive = scenarios["positive"]["contexts"][0]
    boundary = scenarios["boundary"]["contexts"][0]
    assert authority_bias.evaluate(positive, 0.8)["metric"] > authority_bias.evaluate(positive, 0.0)["metric"]
    assert authority_bias.evaluate(boundary, 0.8)["metric"] == authority_bias.evaluate(boundary, 0.0)["metric"]
