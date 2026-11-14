"""Illustrative process model for underuse of a component in a priced bundle."""

from copy import deepcopy
from math import isfinite

METADATA = {
    "id": "bundling_bias",
    "name": "Bundling Bias",
    "kind": "cognitive_bias",
    "description": (
        "For an eligible purchased bundle, package-total price salience shifts "
        "the decision hurdle for a component above its marginal price, which "
        "can suppress use when component value lies between those prices."
    ),
    "required_inputs": [
        "bundle_purchased",
        "component_in_bundle",
        "bundle_component_count",
        "bundle_price",
        "component_marginal_price",
        "component_use_value",
    ],
    "state_fields": ["last_reference_use", "last_use", "last_perceived_cost"],
    "metric_name": "component_use_decision",
    "metric_units": "binary decision (1 = use this component, 0 = do not use)",
    "assumptions": [
        "The reference decision uses component value >= its marginal component price.",
        "When an eligible bundle's total price is salient, perceived component cost is a linear blend of marginal price and total bundle price; strength sets the blend weight.",
        "The modeled decision is a hypothetical, single-step component-use choice after purchase; prices and use value are comparable monetary units.",
        "All coefficients are illustrative assumptions, not measured effect sizes.",
    ],
    "limitations": [
        "This is a transparent toy choice rule, not an empirically validated account of bundling or a detector of real decisions.",
        "It assumes bundle price overshadows rather than lowers perceived component cost; actual bundles, sunk-cost responses, and use opportunities may behave differently.",
        "The binary metric omits intensity, component complementarity, budget constraints, and beneficial purchase/use heuristics.",
        "Bundle purchase alone does not activate the mechanism; required component, multiplicity, and price conditions must also hold.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(context, key):
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite nonnegative number")
    value = float(value)
    if not isfinite(value) or value < 0:
        raise ValueError(f"{key} must be a finite nonnegative number")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one component-use decision without mutating supplied data."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")

    required = METADATA["required_inputs"]
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")
    for key in ("bundle_purchased", "component_in_bundle"):
        if not isinstance(context[key], bool):
            raise ValueError(f"{key} must be a bool")
    count = context["bundle_component_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("bundle_component_count must be an integer >= 1")

    bundle_price = _number(context, "bundle_price")
    marginal_price = _number(context, "component_marginal_price")
    use_value = _number(context, "component_use_value")
    if bundle_price < marginal_price:
        raise ValueError("bundle_price cannot be below component_marginal_price")

    eligible = (
        context["bundle_purchased"]
        and context["component_in_bundle"]
        and count >= 2
        and bundle_price > marginal_price
    )
    reference_use = int(use_value >= marginal_price)
    perceived_cost = (
        marginal_price + strength * (bundle_price - marginal_price)
        if eligible
        else marginal_price
    )
    use = int(use_value >= perceived_cost)
    state_in = context.get("state", {})
    if not isinstance(state_in, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(state_in)
    state.update({
        "last_reference_use": reference_use,
        "last_use": use,
        "last_perceived_cost": perceived_cost,
    })

    if eligible:
        condition = (
            "purchased bundle includes component, has at least two components, "
            "and bundle_price > component_marginal_price"
        )
        formula = (
            "perceived_cost = marginal_price + strength * "
            "(bundle_price - marginal_price)"
        )
    else:
        condition = "eligibility condition false; use reference marginal-price hurdle"
        formula = "perceived_cost = marginal_price"
    return {
        "metric": float(use),
        "active": bool(use != reference_use),
        "state": state,
        "trace": [
            f"{condition}; {formula}.",
            f"use_value={use_value:g}, marginal_price={marginal_price:g}, "
            f"bundle_price={bundle_price:g}, strength={strength:g}, "
            f"perceived_cost={perceived_cost:g}; reference_use={reference_use}, use={use}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "bundle_purchased": True,
                    "component_in_bundle": True,
                    "bundle_component_count": 3,
                    "bundle_price": 8.0,
                    "component_marginal_price": 2.0,
                    "component_use_value": 4.0,
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "bundle_purchased": True,
                    "component_in_bundle": False,
                    "bundle_component_count": 3,
                    "bundle_price": 8.0,
                    "component_marginal_price": 2.0,
                    "component_use_value": 4.0,
                }
            ],
            "expectation": "equal",
        },
    ]
