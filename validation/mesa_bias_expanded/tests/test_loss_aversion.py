from copy import deepcopy

import pytest

from mechanisms import loss_aversion as la


def context(options=None, reference_point=0, state=None):
    return {
        "reference_point": reference_point,
        "options": options if options is not None else [
            {"id": "gamble", "outcomes": [
                {"value": 10, "probability": 0.5},
                {"value": -8, "probability": 0.5},
            ]},
            {"id": "sure", "outcomes": [{"value": 0, "probability": 1.0}]},
        ],
        "state": {} if state is None else state,
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.25,
    }


def test_numeric_choice_oracle_and_loss_weighting():
    task = context()
    reference = la.evaluate(task, 0.0)
    intervention = la.evaluate(task, 0.8)

    # E[gamb] = 0.5*10 + 0.5*(-8) = 1. At s=.8, lambda=2.6,
    # its weighted score is 5 - 10.4 = -5.4, so the zero-payoff sure
    # option is selected. Reported metric remains actual expected payoff.
    assert reference["metric"] == pytest.approx(1.0)
    assert intervention["metric"] == pytest.approx(0.0)
    assert intervention["active"] is True
    assert "selected choice=sure" in " ".join(intervention["trace"])


def test_positive_scenario_changes_metric_downward_at_strength_point_eight():
    scenario = next(s for s in la.scenarios() if s["name"] == "positive")
    task = context(scenario["contexts"][0]["options"], scenario["contexts"][0]["reference_point"])
    assert la.evaluate(task, 0.8)["metric"] < la.evaluate(task, 0.0)["metric"]


def test_boundary_without_any_below_reference_outcome_matches_reference():
    scenario = next(s for s in la.scenarios() if s["name"] == "boundary")
    task = context(scenario["contexts"][0]["options"], scenario["contexts"][0]["reference_point"])
    baseline = la.evaluate(task, 0.0)
    result = la.evaluate(task, 0.8)

    assert all(o["value"] >= task["reference_point"]
               for option in task["options"] for o in option["outcomes"])
    assert result["metric"] == baseline["metric"]
    assert result["active"] is False


def test_zero_strength_is_expected_payoff_reference_policy():
    task = context(reference_point=2)
    task["options"] = [
        {"id": "a", "outcomes": [{"value": 6, "probability": 0.25}, {"value": 0, "probability": 0.75}]},
        {"id": "b", "outcomes": [{"value": 3, "probability": 1.0}]},
    ]
    # Relative expectations: A = .25*4 + .75*(-2) = -0.5; B = 1.
    assert la.evaluate(task, 0.0)["metric"] == pytest.approx(1.0)


@pytest.mark.parametrize("bad_task", [
    {"options": []},
    {"reference_point": 0},
    {"reference_point": float("nan"), "options": []},
])
def test_missing_or_invalid_required_task_input_is_rejected(bad_task):
    bad_task = {**bad_task, "state": {}}
    with pytest.raises(ValueError):
        la.evaluate(bad_task, 0.8)


def test_invalid_lottery_probabilities_are_rejected():
    task = context(options=[
        {"id": "bad", "outcomes": [{"value": 1, "probability": 0.4}]},
        {"id": "other", "outcomes": [{"value": 0, "probability": 1.0}]},
    ])
    with pytest.raises(ValueError, match="sum to 1"):
        la.evaluate(task, 0.8)


def test_deterministic_and_nonmutating_including_nested_state():
    task = context(state={"prior": {"chosen": "old"}, "count": 2})
    before = deepcopy(task)
    first = la.evaluate(task, 0.8)
    second = la.evaluate(task, 0.8)

    assert first == second
    assert task == before
    assert first["state"] == before["state"]
    assert first["state"] is not task["state"]
    first["state"]["prior"]["chosen"] = "changed"
    assert task["state"]["prior"]["chosen"] == "old"


def test_strength_outside_unit_interval_is_rejected():
    task = context()
    with pytest.raises(ValueError):
        la.evaluate(task, 1.01)
