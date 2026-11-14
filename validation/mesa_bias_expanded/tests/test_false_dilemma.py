import copy

import pytest

from mechanisms import false_dilemma


def _context(raw, state=None):
    result = copy.deepcopy(raw)
    result.update(
        {
            "state": {} if state is None else copy.deepcopy(state),
            "peer_states": [],
            "round_index": 0,
            "agent_index": 0,
            "uniform": 0.5,
        }
    )
    return result


def _scenario(name):
    return next(item for item in false_dilemma.scenarios() if item["name"] == name)


def test_positive_scenario_increases_regret_with_numeric_and_choice_oracle():
    raw = _scenario("positive")["contexts"][0]
    result = false_dilemma.evaluate(_context(raw), 0.8)
    # The best full-menu utility is .90; best framed utility is .60.
    assert result["metric"] == pytest.approx(0.8 * (0.90 - 0.60))
    assert result["state"]["last_choice_probabilities"] == pytest.approx(
        {"accept": 0.0, "reject": 0.8, "revise": 0.2}
    )
    assert result["active"] is True


def test_positive_direction_compared_with_zero_strength():
    raw = _scenario("positive")["contexts"][0]
    zero = false_dilemma.evaluate(_context(raw), 0.0)
    positive = false_dilemma.evaluate(_context(raw), 0.8)
    assert positive["metric"] > zero["metric"]
    assert zero["metric"] == 0.0


def test_boundary_without_third_feasible_option_matches_reference():
    raw = _scenario("boundary")["contexts"][0]
    boundary = false_dilemma.evaluate(_context(raw), 0.8)
    reference = false_dilemma.evaluate(_context(raw), 0.0)
    assert boundary["metric"] == reference["metric"] == 0.0
    assert boundary["state"]["last_choice_probabilities"] == reference["state"]["last_choice_probabilities"]
    assert boundary["active"] is False


def test_zero_strength_reproduces_full_menu_reference_choice():
    raw = _scenario("positive")["contexts"][0]
    result = false_dilemma.evaluate(_context(raw), 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["last_choice_probabilities"] == {
        "accept": 0.0,
        "reject": 0.0,
        "revise": 1.0,
    }
    assert result["state"]["last_expected_utility"] == pytest.approx(0.90)


def test_missing_option_utility_evidence_is_rejected_not_zeroed():
    raw = _scenario("positive")["contexts"][0]
    del raw["options"][2]["utility"]
    with pytest.raises(ValueError, match="missing utility evidence"):
        false_dilemma.evaluate(_context(raw), 0.8)


def test_invalid_strength_and_utility_ranges_are_rejected():
    raw = _scenario("positive")["contexts"][0]
    with pytest.raises(ValueError, match=r"strength must be in \[0, 1\]"):
        false_dilemma.evaluate(_context(raw), 1.01)
    invalid = copy.deepcopy(raw)
    invalid["options"][0]["utility"] = 1.5
    with pytest.raises(ValueError, match=r"utility must be in \[0, 1\]"):
        false_dilemma.evaluate(_context(invalid), 0.8)


def test_non_exhaustive_binary_presentation_is_a_boundary():
    raw = copy.deepcopy(_scenario("positive")["contexts"][0])
    raw["frame_claims_exhaustive"] = False
    result = false_dilemma.evaluate(_context(raw), 0.8)
    assert result["metric"] == 0.0
    assert result["state"]["last_choice_probabilities"]["revise"] == 1.0


def test_deterministic_and_does_not_mutate_input_or_nested_state():
    raw = _scenario("positive")["contexts"][0]
    context = _context(raw, {"steps": 3, "cumulative_expected_regret": 0.1, "extra": {"tags": ["keep"]}})
    before = copy.deepcopy(context)
    first = false_dilemma.evaluate(context, 0.8)
    second = false_dilemma.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["steps"] == 4
    assert first["state"]["cumulative_expected_regret"] == pytest.approx(0.34)
    first["state"]["extra"]["tags"].append("edited")
    assert context["state"]["extra"]["tags"] == ["keep"]


def test_required_top_level_inputs_are_validated():
    raw = _scenario("positive")["contexts"][0]
    del raw["framed_pair"]
    with pytest.raises(ValueError, match="missing required input: framed_pair"):
        false_dilemma.evaluate(_context(raw), 0.8)
