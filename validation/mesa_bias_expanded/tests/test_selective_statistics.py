from copy import deepcopy

import pytest

from mechanisms import selective_statistics as mechanism


def make_context(**overrides):
    context = {
        "event_count": 10,
        "relevant_denominator": 100,
        "selected_denominator": 20,
        "denominator_evidence": {
            "exists": True,
            "relevant": True,
            "basis": "provided cohort table establishes a relevant comparison group",
        },
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.1,
    }
    context.update(overrides)
    return context


def test_positive_choice_increases_rate_with_numeric_oracle():
    context = make_context()
    reference = mechanism.evaluate(context, 0.0)
    selected = mechanism.evaluate(context, 0.8)

    assert reference["metric"] == pytest.approx(10.0)  # 10 / 100 * 100
    assert selected["metric"] == pytest.approx(50.0)  # 10 / 20 * 100
    assert selected["metric"] > reference["metric"]
    assert selected["active"] is True


def test_boundary_equal_denominators_match_reference_at_strength_point_8():
    context = make_context(selected_denominator=100, uniform=0.1)
    reference = mechanism.evaluate(context, 0.0)
    boundary = mechanism.evaluate(context, 0.8)

    assert boundary["metric"] == reference["metric"] == pytest.approx(10.0)
    assert boundary["active"] is False


def test_zero_strength_uses_relevant_denominator_even_when_draw_would_select():
    context = make_context(uniform=0.0)
    result = mechanism.evaluate(context, 0.0)

    assert result["state"]["last_denominator_used"] == 100
    assert result["metric"] == pytest.approx(10.0)
    assert result["active"] is False


def test_missing_or_irrelevant_comparative_evidence_is_rejected():
    with pytest.raises(ValueError, match="denominator_evidence"):
        mechanism.evaluate(make_context(denominator_evidence=None), 0.8)
    with pytest.raises(ValueError, match="existing and relevant"):
        mechanism.evaluate(
            make_context(
                denominator_evidence={
                    "exists": True,
                    "relevant": False,
                    "basis": "not a relevant comparator",
                }
            ),
            0.8,
        )


def test_input_and_strength_ranges_are_validated():
    with pytest.raises(ValueError, match="event_count"):
        mechanism.evaluate(make_context(event_count=-1), 0.8)
    with pytest.raises(ValueError, match="either denominator"):
        mechanism.evaluate(make_context(event_count=21), 0.8)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(make_context(), float("nan"))
    with pytest.raises(ValueError, match="uniform"):
        mechanism.evaluate(make_context(uniform=1.0), 0.8)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_context():
    context = make_context()
    context["state"] = {"steps_evaluated": 3, "extension": {"keep": [1, 2]}}
    before = deepcopy(context)

    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)

    assert first == second
    assert context == before
    assert first["state"]["steps_evaluated"] == 4
    assert first["state"]["extension"] == {"keep": [1, 2]}


def test_chronological_calls_carry_complete_state():
    first_context = make_context()
    first = mechanism.evaluate(first_context, 0.8)
    second_context = make_context(state=first["state"], round_index=1, uniform=0.9)
    second = mechanism.evaluate(second_context, 0.8)

    assert first["state"]["steps_evaluated"] == 1
    assert second["state"]["steps_evaluated"] == 2
    assert second["state"]["last_denominator_used"] == 100
    assert second["metric"] == pytest.approx(10.0)


def test_scenarios_expose_required_positive_and_boundary_cases():
    scenarios = {scenario["name"]: scenario for scenario in mechanism.scenarios()}
    assert set(scenarios) >= {"positive", "boundary"}
    for scenario in scenarios.values():
        assert scenario["contexts"]
        assert scenario["expectation"] in {"increase", "decrease", "difference", "equal"}
