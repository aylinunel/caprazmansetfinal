"""Illustrative, non-empirical model of the disposition effect in portfolio choices."""

from __future__ import annotations

import copy
import math
from typing import Any


# This coefficient is an explicit illustrative assumption, not an estimated effect.
_STATUS_SENSITIVITY = 0.25

METADATA = {
    "id": "disposition_effect",
    "name": "Disposition Effect",
    "kind": "cognitive_bias",
    "description": (
        "For an owned position, unrealized loss status adds pressure to retain and "
        "unrealized gain status adds pressure to sell, potentially overriding a "
        "forward-value comparison."
    ),
    "required_inputs": ["positions"],
    "state_fields": ["decision_history"],
    "metric_name": "status_driven_choice_changes",
    "metric_units": "count of owned positions whose action differs from the forward-value reference",
    "assumptions": [
        "Expected hold value and sell value are comparable values on the same horizon and scale.",
        "Tax and strategy adjustments are explicit scenario inputs; they are not inferred from purchase price.",
        "At a tie, the reference and simulated policies retain the position.",
        "The status sensitivity coefficient 0.25 is illustrative and not empirically calibrated.",
    ],
    "limitations": [
        "This deterministic toy choice rule is not a psychological classifier or population model.",
        "It does not estimate a person's motives; status pressure is imposed explicitly by the model.",
        "Real tax, liquidity, risk, portfolio interactions, and investment horizons are simplified to supplied values.",
        "No empirical validation or detection-accuracy measurement has been performed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_POSITION_FIELDS = (
    "id",
    "owned",
    "cost_basis",
    "current_value",
    "expected_hold_value",
    "sell_value",
    "sell_tax",
    "hold_strategy_adjustment",
    "sell_strategy_adjustment",
)


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _finite_derived(value: float, label: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"derived {label} is not finite")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one portfolio snapshot without modifying the supplied context."""
    strength_value = _finite_number(strength, "strength")
    if not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "positions" not in context:
        raise ValueError("missing required input: positions")
    positions = context["positions"]
    if not isinstance(positions, list) or not positions:
        raise ValueError("positions must be a non-empty list")

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    prior_history = prior_state.get("decision_history", [])
    if not isinstance(prior_history, list):
        raise ValueError("state.decision_history must be a list")

    seen_ids: set[str] = set()
    decisions: list[dict[str, Any]] = []
    trace = [
        "Reference: retain iff expected_hold_value + hold_strategy_adjustment "
        ">= sell_value - sell_tax + sell_strategy_adjustment. For owned positions "
        "with nonzero unrealized return r=(current_value-cost_basis)/cost_basis, "
        "the modeled retention margin shifts by -sign(r) * strength * 0.25 * "
        "abs(r) * current_value; purchase price affects status only, not the reference.",
    ]
    changed_count = 0

    for index, position in enumerate(positions):
        if not isinstance(position, dict):
            raise ValueError(f"positions[{index}] must be a dict")
        missing = [field for field in _POSITION_FIELDS if field not in position]
        if missing:
            raise ValueError(f"positions[{index}] missing required fields: {', '.join(missing)}")

        position_id = position["id"]
        if not isinstance(position_id, str) or not position_id.strip():
            raise ValueError(f"positions[{index}].id must be a non-empty string")
        if position_id in seen_ids:
            raise ValueError(f"duplicate position id: {position_id}")
        seen_ids.add(position_id)
        owned = position["owned"]
        if not isinstance(owned, bool):
            raise ValueError(f"positions[{index}].owned must be a bool")

        cost_basis = _finite_number(position["cost_basis"], f"{position_id}.cost_basis")
        current_value = _finite_number(position["current_value"], f"{position_id}.current_value")
        hold_value = _finite_number(position["expected_hold_value"], f"{position_id}.expected_hold_value")
        sell_value = _finite_number(position["sell_value"], f"{position_id}.sell_value")
        sell_tax = _finite_number(position["sell_tax"], f"{position_id}.sell_tax")
        hold_strategy = _finite_number(position["hold_strategy_adjustment"], f"{position_id}.hold_strategy_adjustment")
        sell_strategy = _finite_number(position["sell_strategy_adjustment"], f"{position_id}.sell_strategy_adjustment")

        if cost_basis <= 0.0:
            raise ValueError(f"{position_id}.cost_basis must be > 0")
        if current_value <= 0.0:
            raise ValueError(f"{position_id}.current_value must be > 0")
        if hold_value < 0.0 or sell_value < 0.0:
            raise ValueError(f"{position_id} expected_hold_value and sell_value must be >= 0")
        if sell_tax < 0.0 or sell_tax > sell_value:
            raise ValueError(f"{position_id}.sell_tax must be between 0 and sell_value")

        net_hold = _finite_derived(hold_value + hold_strategy, f"{position_id} net hold value")
        net_sell = _finite_derived(sell_value - sell_tax + sell_strategy, f"{position_id} net sell value")
        reference_margin = _finite_derived(net_hold - net_sell, f"{position_id} reference margin")
        reference_action = "retain" if reference_margin >= 0.0 else "sell"

        unrealized_return = _finite_derived((current_value - cost_basis) / cost_basis, f"{position_id} unrealized return")
        pressure = 0.0
        adjusted_margin = reference_margin
        if owned and unrealized_return != 0.0:
            pressure = _finite_derived(
                strength_value * _STATUS_SENSITIVITY * abs(unrealized_return) * current_value,
                f"{position_id} status pressure",
            )
            direction = -1.0 if unrealized_return > 0.0 else 1.0
            adjusted_margin = _finite_derived(
                reference_margin + direction * pressure,
                f"{position_id} adjusted retention margin",
            )
        action = "retain" if adjusted_margin >= 0.0 else "sell"
        changed = bool(owned and action != reference_action)
        changed_count += int(changed)

        decision = {
            "id": position_id,
            "owned": owned,
            "unrealized_return": unrealized_return,
            "reference_margin": reference_margin,
            "status_pressure": pressure,
            "adjusted_margin": adjusted_margin,
            "reference_action": reference_action,
            "action": action if owned else "not_owned",
            "status_driven_change": changed,
        }
        decisions.append(decision)
        trace.append(
            f"{position_id}: owned={owned}, r={unrealized_return:.6g}, "
            f"reference_margin={reference_margin:.6g}, pressure={pressure:.6g}, "
            f"adjusted_margin={adjusted_margin:.6g}, reference={reference_action}, "
            f"action={decision['action']}, status_driven_change={changed}."
        )

    next_state = copy.deepcopy(prior_state)
    next_state["decision_history"] = copy.deepcopy(prior_history) + [copy.deepcopy(decisions)]
    return {
        "metric": changed_count,
        "active": changed_count > 0,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "positions": [
                        {
                            "id": "losing_position",
                            "owned": True,
                            "cost_basis": 100.0,
                            "current_value": 80.0,
                            "expected_hold_value": 75.0,
                            "sell_value": 80.0,
                            "sell_tax": 0.0,
                            "hold_strategy_adjustment": 0.0,
                            "sell_strategy_adjustment": 0.0,
                        },
                        {
                            "id": "winning_position",
                            "owned": True,
                            "cost_basis": 100.0,
                            "current_value": 120.0,
                            "expected_hold_value": 123.0,
                            "sell_value": 120.0,
                            "sell_tax": 0.0,
                            "hold_strategy_adjustment": 0.0,
                            "sell_strategy_adjustment": 0.0,
                        },
                    ]
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "positions": [
                        {
                            "id": "break_even_owned",
                            "owned": True,
                            "cost_basis": 100.0,
                            "current_value": 100.0,
                            "expected_hold_value": 90.0,
                            "sell_value": 100.0,
                            "sell_tax": 5.0,
                            "hold_strategy_adjustment": 0.0,
                            "sell_strategy_adjustment": 0.0,
                        },
                        {
                            "id": "not_owned",
                            "owned": False,
                            "cost_basis": 100.0,
                            "current_value": 80.0,
                            "expected_hold_value": 75.0,
                            "sell_value": 80.0,
                            "sell_tax": 0.0,
                            "hold_strategy_adjustment": 0.0,
                            "sell_strategy_adjustment": 0.0,
                        },
                    ]
                }
            ],
            "expectation": "equal",
        },
    ]
