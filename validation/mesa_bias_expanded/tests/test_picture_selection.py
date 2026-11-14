from copy import deepcopy

import pytest

from mechanisms import picture_selection


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for index, item in enumerate(contexts):
        context = deepcopy(item)
        context.update({
            "state": state,
            "peer_states": [],
            "round_index": index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = picture_selection.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def positive_context():
    return {
        "images": [
            {"id": "a-smile", "person_id": "p1", "expression": "smiling", "quality": 0.7},
            {"id": "z-angry", "person_id": "p1", "expression": "angry", "quality": 0.7},
        ],
        "editorial_frame": "angry",
    }


def test_positive_framing_selects_angry_alternative_with_numeric_oracle():
    baseline = picture_selection.evaluate(positive_context(), 0.0)
    framed = picture_selection.evaluate(positive_context(), 0.8)

    assert baseline["state"]["last_selected_id"] == "a-smile"
    # 0.7 + 0.8 * 0.5 = 1.1 beats the smiling image's 0.7 quality score.
    assert framed["state"]["last_selected_id"] == "z-angry"
    assert framed["metric"] == 1.0 > baseline["metric"] == 0.0
    assert framed["active"] is True


def test_boundary_without_same_person_contrast_matches_reference_at_point_8():
    context = positive_context()
    context["images"][1]["person_id"] = "p2"
    reference = picture_selection.evaluate(context, 0.0)
    boundary = picture_selection.evaluate(context, 0.8)

    assert boundary["metric"] == reference["metric"]
    assert boundary["state"]["last_selected_id"] == reference["state"]["last_selected_id"]
    assert boundary["active"] is False
    assert any("alternatives present: False" in line for line in boundary["trace"])


def test_zero_strength_is_quality_reference_and_state_is_completed():
    context = {
        "images": [
            {"id": "b", "person_id": "p", "expression": "angry", "quality": 0.4},
            {"id": "a", "person_id": "p", "expression": "smiling", "quality": 0.8},
        ],
        "editorial_frame": "angry",
        "state": {"steps": 2, "selected_ids": ["old"], "custom": "preserved"},
    }
    result = picture_selection.evaluate(context, 0.0)

    assert result["state"] == {
        "steps": 3,
        "selected_ids": ["old", "a"],
        "last_selected_id": "a",
        "custom": "preserved",
    }
    assert result["metric"] == 0.0
    assert result["active"] is False


def test_required_and_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        picture_selection.evaluate({"editorial_frame": "angry"}, 0.8)
    invalid = positive_context()
    invalid["images"][0]["quality"] = 1.01
    with pytest.raises(ValueError):
        picture_selection.evaluate(invalid, 0.8)
    invalid = positive_context()
    invalid["editorial_frame"] = "furious"
    with pytest.raises(ValueError):
        picture_selection.evaluate(invalid, 0.8)
    with pytest.raises(ValueError):
        picture_selection.evaluate(positive_context(), float("nan"))


def test_determinism_and_nested_input_nonmutation():
    context = positive_context()
    context["state"] = {"steps": 0, "selected_ids": [], "extra": {"items": [1, 2]}}
    before = deepcopy(context)
    first = picture_selection.evaluate(context, 0.8)
    second = picture_selection.evaluate(context, 0.8)

    assert context == before
    assert first == second
    first["state"]["extra"]["items"].append(3)
    assert context == before
    assert second["state"]["extra"]["items"] == [1, 2]


def test_chronological_calls_carry_complete_state_without_fictitious_step():
    outputs = run_sequence([positive_context(), positive_context()], 0.8)

    assert len(outputs) == 2
    assert outputs[-1]["state"]["steps"] == 2
    assert outputs[-1]["state"]["selected_ids"] == ["z-angry", "z-angry"]
    assert outputs[-1]["state"]["last_selected_id"] == "z-angry"
