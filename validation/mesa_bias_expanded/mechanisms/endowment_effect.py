"""Illustrative ownership-referenced sale threshold, not a human-behavior detector.

The owner may set a reservation value above a market-adjusted pre-ownership
valuation when an explicit acquisition reference is higher. All coefficients
are synthetic assumptions; see specs/endowment_effect_implementation.md.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "endowment_effect",
    "name": "Endowment Effect",
    "kind": "cognitive_bias",
    "description": (
        "Models an owner's sale reservation price as a market-adjusted "
        "pre-ownership valuation plus a strength-scaled positive gap to an "
        "explicit acquisition reference value."
    ),
    "required_inputs": [
        "same_item",
        "is_owner",
        "pre_ownership_value",
        "pre_ownership_market_value",
        "current_market_value",
        "acquisition_reference_value",
        "sale_offer",
        "transaction_cost",
    ],
    "state_fields": [
        "last_reference_reservation_value",
        "last_ownership_premium",
        "last_reservation_value",
        "last_sale_accepted",
        "last_reference_sale_accepted",
    ],
    "metric_name": "sale_offer_accepted",
    "metric_units": "binary choice (1 = accept offer, 0 = retain item)",
    "assumptions": [
        "The scenario explicitly concerns the same item and supplies its pre-ownership valuation and market value.",
        "The strength-zero reference reservation value updates the pre-ownership valuation by observed market-value change and adds explicit sale transaction cost.",
        "For an owner only, the hypothetical ownership reference is acquisition_reference_value; the modeled premium is the positive gap between that reference and the market/cost-adjusted reference reservation value, scaled by strength.",
        "The agent accepts a sale offer when it is at least its reservation value; ties are accepted.",
        "Strength and acquisition reference are illustrative scenario settings, not calibrated effect sizes or estimates of real people.",
    ],
    "limitations": [
        "This narrow threshold rule operationalizes only an explicit ownership-related valuation gap; it is not a general theory, classifier, or diagnosis.",
        "A high acquisition reference can reflect legitimate preferences, quality information, or strategic pricing rather than an error; the output cannot distinguish these.",
        "Market change and transaction costs are modeled separately as ordinary reservation-value changes, but omitted factors could still explain observed valuation gaps.",
        "The model is hypothetical, synthetic-only, and has not been empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


def _nonnegative(value, field):
    value = _finite_number(value, field)
    if value < 0.0:
        raise ValueError(f"{field} must be nonnegative")
    return value


def _inputs(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    fields = METADATA["required_inputs"]
    for field in fields:
        if field not in context:
            raise ValueError(f"{field} is required")
    if context["same_item"] is not True:
        raise ValueError("same_item must be True; valuations must concern the identical item")
    if not isinstance(context["is_owner"], bool):
        raise ValueError("is_owner must be a boolean")
    values = {
        field: _nonnegative(context[field], field)
        for field in fields
        if field not in ("same_item", "is_owner")
    }
    return context["is_owner"], values


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate an explicit same-item sale offer under an ownership reference."""
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    is_owner, values = _inputs(context)
    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dictionary")

    market_change = values["current_market_value"] - values["pre_ownership_market_value"]
    reference_reservation = max(
        0.0,
        values["pre_ownership_value"] + market_change + values["transaction_cost"],
    )
    # Ownership operates only when this exact item is owned and the supplied
    # acquisition reference lies above the ordinary market/cost-adjusted value.
    ownership_gap = max(
        0.0, values["acquisition_reference_value"] - reference_reservation
    ) if is_owner else 0.0
    premium = strength * ownership_gap
    reservation = reference_reservation + premium
    reference_choice = int(values["sale_offer"] >= reference_reservation)
    choice = int(values["sale_offer"] >= reservation)
    metric = float(choice)
    if not math.isfinite(metric):
        raise ValueError("computed choice metric is not finite")

    next_state = deepcopy(previous)
    next_state.update({
        "last_reference_reservation_value": reference_reservation,
        "last_ownership_premium": premium,
        "last_reservation_value": reservation,
        "last_sale_accepted": choice,
        "last_reference_sale_accepted": reference_choice,
    })
    active = strength > 0.0 and choice != reference_choice
    trace = (
        f"Same item={context['same_item']}; owner={is_owner}; market change="
        f"{values['current_market_value']:.12g}-{values['pre_ownership_market_value']:.12g}="
        f"{market_change:.12g}; reference reservation=max(0, pre-ownership value + "
        f"market change + transaction cost)={reference_reservation:.12g}; ownership "
        f"gap=max(0, acquisition reference - reference reservation)={ownership_gap:.12g}; "
        f"premium={strength:.12g}*gap={premium:.12g}; reservation={reservation:.12g}; "
        f"offer={values['sale_offer']:.12g}; reference choice={reference_choice}, "
        f"current choice={choice}."
    )
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [trace],
    }


def scenarios() -> list[dict]:
    positive = {
        "same_item": True,
        "is_owner": True,
        "pre_ownership_value": 10.0,
        "pre_ownership_market_value": 10.0,
        "current_market_value": 10.0,
        "acquisition_reference_value": 16.0,
        "sale_offer": 13.0,
        "transaction_cost": 0.0,
    }
    boundary = {**positive, "is_owner": False}
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [positive],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
