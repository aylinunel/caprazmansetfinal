from copy import deepcopy

import pytest

from mechanisms import disposition_effect


def pos(position_id, *, owned=True, cost=100.0, current=100.0, hold=90.0,
        sell=100.0, tax=0.0, hold_strategy=0.0, sell_strategy=0.0):
    return {
        "id": position_id,
        "owned": owned,
        "cost_basis": cost,
        "current_value": current,
        "expected_hold_value": hold,
        "sell_value": sell,
        "sell_tax": tax,
        "hold_strategy_adjustment": hold_strategy,
        "sell_strategy_adjustment": sell_strategy,
    }


def call(positions, strength, *, state=None):
    return disposition_effect.evaluate(
        {
            "positions": positions,
            "state": {} if state is None else state,
            "peer_states": [],
            "round_index": 0,
            "agent_index": 0,
            "uniform": 0.5,
        },
        strength,
    )


def test_positive_loss_retention_and_gain_sale_with_numeric_choice_oracle():
    positions = [
        # Reference sells at -5; loss pressure at .8 is +3.2, not quite enough? margin is set -3.
        pos("loser", cost=100, current=80, hold=77, sell=80),
        # Reference retains at +3; gain pressure at .8 is -3.84 and flips to sale.
        pos("winner", cost=100, current=120, hold=123, sell=120),
    ]
    reference = call(positions, 0.0)
    biased = call(positions, 0.8)
    assert [d["reference_action"] for d in biased["state"]["decision_history"][-1]] == ["sell", "retain"]
    assert [d["action"] for d in biased["state"]["decision_history"][-1]] == ["retain", "sell"]
    assert reference["metric"] == 0
    assert biased["metric"] == 2
    assert biased["active"] is True
    assert biased["state"]["decision_history"][-1][0]["status_pressure"] == pytest.approx(3.2)


def test_boundary_without_unrealized_status_matches_reference():
    positions = [
        pos("flat", cost=100, current=100, hold=92, sell=100, tax=3),
        pos("not_owned_loss", owned=False, cost=100, current=80, hold=75, sell=80),
    ]
    reference = call(positions, 0.0)
    boundary = call(positions, 0.8)
    assert boundary["metric"] == reference["metric"] == 0
    assert [d["action"] for d in boundary["state"]["decision_history"][-1]] == [
        d["action"] for d in reference["state"]["decision_history"][-1]
    ]
    assert boundary["active"] is False


def test_zero_strength_is_explicit_forward_value_reference_and_keeps_tax_strategy():
    positions = [
        # Net hold=108, net sale=95: retain despite the unrealized loss.
        pos("tax_strategy_hold", cost=100, current=80, hold=100, sell=100, tax=10,
            hold_strategy=8, sell_strategy=5),
        # Net hold=80, net sale=97: sell despite the unrealized gain.
        pos("strategy_sale", cost=100, current=120, hold=80, sell=100, tax=5,
            hold_strategy=0, sell_strategy=2),
    ]
    result = call(positions, 0.0)
    decisions = result["state"]["decision_history"][-1]
    assert [decision["action"] for decision in decisions] == ["retain", "sell"]
    assert result["metric"] == 0
    assert all(decision["reference_action"] == decision["action"] for decision in decisions)


def test_missing_required_position_evidence_is_rejected():
    incomplete = pos("missing_basis")
    del incomplete["cost_basis"]
    with pytest.raises(ValueError, match="cost_basis"):
        call([incomplete], 0.8)
    with pytest.raises(ValueError, match="non-empty list"):
        call([], 0.8)


@pytest.mark.parametrize("strength", [-0.01, 1.01, float("nan"), float("inf")])
def test_invalid_strength_is_rejected(strength):
    with pytest.raises(ValueError, match="strength"):
        call([pos("p")], strength)


def test_deterministic_nonmutating_and_history_is_carried():
    positions = [pos("loser", cost=100, current=80, hold=77, sell=80)]
    prior_state = {"decision_history": [[{"prior": "kept"}]], "other": {"nested": [1, 2]}}
    context = {
        "positions": positions,
        "state": prior_state,
        "peer_states": [],
        "round_index": 2,
        "agent_index": 4,
        "uniform": 0.5,
    }
    before = deepcopy(context)
    first = disposition_effect.evaluate(context, 0.8)
    second = disposition_effect.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first["state"]["decision_history"][0] == [{"prior": "kept"}]
    assert len(first["state"]["decision_history"]) == 2
    assert first["state"] is not prior_state
    assert first["trace"]


def test_required_scenarios_have_contract_names_and_expected_direction():
    by_name = {scenario["name"]: scenario for scenario in disposition_effect.scenarios()}
    assert set(by_name) >= {"positive", "boundary"}
    positive = by_name["positive"]["contexts"][0]["positions"]
    boundary = by_name["boundary"]["contexts"][0]["positions"]
    assert call(positive, 0.8)["metric"] > call(positive, 0.0)["metric"]
    assert call(boundary, 0.8)["metric"] == call(boundary, 0.0)["metric"]
