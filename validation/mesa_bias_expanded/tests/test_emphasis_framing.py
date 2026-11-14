from copy import deepcopy

import pytest

from mechanisms import emphasis_framing


def case(focus="growth", growth=0.2, cost=0.8):
    return {
        "fact_id": "same_quarterly_fact",
        "dimensions": [
            {"id": "growth", "value": 12.0, "body_prominence": growth},
            {"id": "cost", "value": 4.0, "body_prominence": cost},
        ],
        "headline_focus": focus,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 2,
        "uniform": 0.5,
    }


def test_positive_discrepancy_increases_focus_attention_with_numeric_oracle():
    result = emphasis_framing.evaluate(case(), 0.8)
    # Reference focus share=.2, body/headline gap=.6, transfer=.8*.6=.48.
    assert result["metric"] == pytest.approx(0.68)
    assert result["state"]["last_attention_shares"] == pytest.approx(
        {"growth": 0.68, "cost": 0.32}
    )
    assert result["active"] is True
    assert any("transfer strength*gap" in line for line in result["trace"])


def test_boundary_when_headline_selects_already_dominant_body_dimension():
    context = case(focus="growth", growth=0.7, cost=0.3)
    baseline = emphasis_framing.evaluate(context, 0.0)
    boundary = emphasis_framing.evaluate(context, 0.8)
    assert boundary["metric"] == pytest.approx(baseline["metric"])
    assert boundary["metric"] == pytest.approx(0.7)
    assert boundary["active"] is False
    assert boundary["state"]["last_attention_shares"] == baseline["state"]["last_attention_shares"]


def test_strength_zero_is_exact_reference_normalized_body_prominence():
    context = case(growth=2.0, cost=8.0)
    result = emphasis_framing.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(0.2)
    assert result["state"]["last_attention_shares"] == pytest.approx(
        {"growth": 0.2, "cost": 0.8}
    )
    assert result["active"] is False
    assert result["state"]["exposure_count"] == 1


def test_invalid_strength_and_missing_or_impossible_evidence_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        emphasis_framing.evaluate(case(), float("nan"))
    with pytest.raises(ValueError, match="strength"):
        emphasis_framing.evaluate(case(), 1.01)
    incomplete = case()
    del incomplete["dimensions"][0]["body_prominence"]
    with pytest.raises(ValueError, match="body_prominence"):
        emphasis_framing.evaluate(incomplete, 0.8)
    impossible = case(growth=0.0, cost=0.0)
    with pytest.raises(ValueError, match="positive total"):
        emphasis_framing.evaluate(impossible, 0.8)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    context = case()
    context["state"] = {
        "exposure_count": 1,
        "cumulative_headline_attention": 0.4,
        "last_attention_shares": {"prior": 0.4, "other": 0.6},
    }
    before = deepcopy(context)
    first = emphasis_framing.evaluate(context, 0.8)
    second = emphasis_framing.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["exposure_count"] == 2
    assert first["state"]["cumulative_headline_attention"] == pytest.approx(1.08)
    assert first["state"] is not context["state"]


def test_full_strength_transfers_exact_gap_and_reversing_focus_reverses_effect():
    growth_headline = emphasis_framing.evaluate(case(), 1.0)
    cost_headline = emphasis_framing.evaluate(case(focus="cost"), 1.0)
    assert growth_headline["metric"] == pytest.approx(0.8)
    assert cost_headline["metric"] == pytest.approx(0.8)
    assert growth_headline["state"]["last_attention_shares"]["cost"] == pytest.approx(0.2)
    assert cost_headline["state"]["last_attention_shares"]["growth"] == pytest.approx(0.2)


def test_chronological_calls_carry_complete_state_without_extra_steps():
    initial = {}
    positive = case()
    positive["state"] = initial
    first = emphasis_framing.evaluate(positive, 0.8)
    boundary = case(focus="growth", growth=0.7, cost=0.3)
    boundary["state"] = first["state"]
    second = emphasis_framing.evaluate(boundary, 0.8)
    assert second["state"]["exposure_count"] == 2
    assert second["state"]["cumulative_headline_attention"] == pytest.approx(1.38)
    assert second["metric"] == pytest.approx(0.7)
