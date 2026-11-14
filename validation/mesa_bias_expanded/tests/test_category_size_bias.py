from copy import deepcopy

import pytest

from mechanisms import category_size_bias


def _equal_chance_context():
    return {
        "outcomes": [
            {"id": "large-1", "category_id": "large", "individual_probability": 0.2},
            {"id": "large-2", "category_id": "large", "individual_probability": 0.2},
            {"id": "large-3", "category_id": "large", "individual_probability": 0.2},
            {"id": "small-1", "category_id": "small", "individual_probability": 0.2},
            {"id": "small-2", "category_id": "small", "individual_probability": 0.2},
        ],
        "focal_outcome_id": "large-1",
        "state": {"steps": 2, "memo": {"seen": ["prior"]}},
    }


def _unequal_chance_context():
    return {
        "outcomes": [
            {"id": "focal", "category_id": "pair", "individual_probability": 0.4},
            {"id": "member", "category_id": "pair", "individual_probability": 0.3},
            {"id": "other-a", "category_id": "singletons", "individual_probability": 0.2},
            {"id": "other-b", "category_id": "singletons", "individual_probability": 0.1},
        ],
        "focal_outcome_id": "focal",
    }


def test_equal_individuals_in_larger_category_shift_probability_with_numeric_oracle():
    context = _equal_chance_context()
    reference = category_size_bias.evaluate(context, 0.0)
    result = category_size_bias.evaluate(context, 0.8)
    # The focal category aggregates 3 equally likely 0.2 members: 0.6.
    # At strength .8 the reported individual chance interpolates: .2 + .8*(.6-.2)=.52.
    assert reference["metric"] == pytest.approx(0.2)
    assert result["state"]["last_category_probability"] == pytest.approx(0.6)
    assert result["metric"] == pytest.approx(0.52)
    assert result["metric"] > reference["metric"]
    assert result["active"] is True


def test_unequal_individual_chances_remove_necessary_condition_at_point_eight():
    context = _unequal_chance_context()
    reference = category_size_bias.evaluate(context, 0.0)
    result = category_size_bias.evaluate(context, 0.8)
    assert reference["metric"] == pytest.approx(0.4)
    assert result["metric"] == pytest.approx(reference["metric"])
    assert result["active"] is False
    assert result["state"]["last_category_probability"] == pytest.approx(0.7)


def test_zero_strength_reproduces_reference_individual_probability():
    result = category_size_bias.evaluate(_equal_chance_context(), 0.0)
    assert result["metric"] == pytest.approx(0.2)
    assert result["state"]["last_reference_probability"] == pytest.approx(0.2)
    assert result["active"] is False
    assert "Reference rule" in result["trace"][0]


def test_missing_or_impossible_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required inputs"):
        category_size_bias.evaluate({"focal_outcome_id": "x"}, 0.5)
    incomplete = _equal_chance_context()
    del incomplete["outcomes"][0]["individual_probability"]
    with pytest.raises(ValueError, match="missing individual_probability"):
        category_size_bias.evaluate(incomplete, 0.5)
    bad_sum = _equal_chance_context()
    bad_sum["outcomes"][0]["individual_probability"] = 0.1
    with pytest.raises(ValueError, match="sum to 1"):
        category_size_bias.evaluate(bad_sum, 0.5)
    with pytest.raises(ValueError, match="focal_outcome_id"):
        category_size_bias.evaluate({**_equal_chance_context(), "focal_outcome_id": "absent"}, 0.5)


def test_strength_and_input_ranges_are_validated():
    with pytest.raises(ValueError, match="strength"):
        category_size_bias.evaluate(_equal_chance_context(), 1.01)
    with pytest.raises(ValueError, match="strength"):
        category_size_bias.evaluate(_equal_chance_context(), float("nan"))
    bad = _equal_chance_context()
    bad["outcomes"][0]["individual_probability"] = -0.1
    with pytest.raises(ValueError, match="individual_probability"):
        category_size_bias.evaluate(bad, 0.5)


def test_deterministic_nonmutating_and_complete_next_state():
    context = _equal_chance_context()
    before = deepcopy(context)
    first = category_size_bias.evaluate(context, 0.8)
    second = category_size_bias.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["steps"] == 3
    assert first["state"]["memo"] == {"seen": ["prior"]}
    assert first["state"]["last_judged_probability"] == first["metric"]
    first["state"]["memo"]["seen"].append("changed")
    assert context["state"]["memo"]["seen"] == ["prior"]
    assert second["state"]["memo"]["seen"] == ["prior"]


def test_required_scenarios_encode_positive_and_boundary_expectations():
    cases = {scenario["name"]: scenario for scenario in category_size_bias.scenarios()}
    assert cases["positive"]["expectation"] == "increase"
    assert cases["boundary"]["expectation"] == "equal"
    positive = cases["positive"]["contexts"][0]
    boundary = cases["boundary"]["contexts"][0]
    assert category_size_bias.evaluate(positive, 0.8)["metric"] > category_size_bias.evaluate(positive, 0.0)["metric"]
    assert category_size_bias.evaluate(boundary, 0.8)["metric"] == pytest.approx(category_size_bias.evaluate(boundary, 0.0)["metric"])
