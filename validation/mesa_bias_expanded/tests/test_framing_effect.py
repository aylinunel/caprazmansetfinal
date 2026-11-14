from copy import deepcopy

import pytest

from mechanisms import framing_effect


def paired_context(frame="gain"):
    distributions = [
        {"id": "certain", "outcomes": [{"probability": 1.0, "value": 90.0}]},
        {
            "id": "lottery",
            "outcomes": [
                {"probability": 0.5, "value": 0.0},
                {"probability": 0.5, "value": 200.0},
            ],
        },
    ]
    return {
        "frame": frame,
        "presentations": [
            {"frame": "gain", "options": deepcopy(distributions)},
            {"frame": "loss", "options": deepcopy(distributions)},
        ],
        "state": {"prior_note": "preserve"},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 3,
        "uniform": 0.5,
    }


def non_equivalent_context():
    context = paired_context()
    context["presentations"][1]["options"][1]["outcomes"][1]["value"] = 180.0
    return context


def test_positive_gain_frame_changes_choice_by_the_variance_equation():
    context = paired_context("gain")
    reference = framing_effect.evaluate(context, 0.0)
    framed = framing_effect.evaluate(context, 0.8)
    # EV(lottery)=100; gain score=100 - .8*.002*10000 = 84;
    # certain score=90, so reference lottery index 1 becomes certain index 0.
    assert reference["metric"] == 1.0
    assert framed["metric"] == 0.0
    assert framed["active"] is True
    assert framed["state"]["last_choice"] == "certain"


def test_loss_frame_applies_the_opposite_risk_premium():
    result = framing_effect.evaluate(paired_context("loss"), 0.8)
    # Loss score for lottery is 100 + 16, so it remains the expected-value winner.
    assert result["metric"] == 1.0
    assert result["active"] is False


def test_boundary_non_equivalent_distributions_match_reference_at_strength_point_eight():
    context = non_equivalent_context()
    reference = framing_effect.evaluate(context, 0.0)
    boundary = framing_effect.evaluate(context, 0.8)
    assert boundary["metric"] == reference["metric"] == 1.0
    assert boundary["active"] is False
    assert boundary["state"]["eligible"] is False
    assert any("condition is absent" in line for line in boundary["trace"])


def test_zero_strength_is_explicit_expected_value_reference_rule():
    result = framing_effect.evaluate(paired_context(), 0.0)
    assert result["metric"] == 1.0  # 100 expected points beats 90; first-listed tie rule is unused.
    assert result["active"] is False
    assert "highest expected outcome" in result["trace"][2]


def test_missing_required_paired_evidence_raises_instead_of_returning_zero():
    with pytest.raises(ValueError, match="presentations"):
        framing_effect.evaluate({"frame": "gain"}, 0.8)


def test_invalid_probability_mass_and_strength_are_rejected():
    context = paired_context()
    context["presentations"][0]["options"][0]["outcomes"][0]["probability"] = 0.7
    with pytest.raises(ValueError, match="sum to 1"):
        framing_effect.evaluate(context, 0.5)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        framing_effect.evaluate(paired_context(), 1.01)


def test_evaluation_is_deterministic_nonmutating_and_preserves_state():
    context = paired_context()
    original = deepcopy(context)
    first = framing_effect.evaluate(context, 0.8)
    second = framing_effect.evaluate(context, 0.8)
    assert context == original
    assert first == second
    assert first["state"]["prior_note"] == "preserve"
    assert first["state"] is not context["state"]


def test_scenario_contract_has_positive_and_boundary_inputs():
    scenarios = framing_effect.scenarios()
    assert {scenario["name"] for scenario in scenarios} == {"positive", "boundary"}
    assert all(scenario["contexts"] for scenario in scenarios)
    assert scenarios[0]["expectation"] == "decrease"
    assert scenarios[1]["expectation"] == "equal"
