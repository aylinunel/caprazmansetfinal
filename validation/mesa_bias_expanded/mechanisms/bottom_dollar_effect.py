"""Illustrative process model for the bottom-dollar effect (not a detector)."""

from copy import deepcopy
import math


METADATA = {
    "id": "bottom_dollar_effect",
    "name": "Bottom-Dollar Effect",
    "kind": "cognitive_bias",
    "description": (
        "Hypothetically lowers a purchase's satisfaction rating when the purchase "
        "uses the buyer's last available funds despite essential obligations being covered."
    ),
    "required_inputs": [
        "item_satisfaction",
        "funds_before",
        "purchase_cost",
        "budget_secure_after",
    ],
    "state_fields": ["last_item_satisfaction", "last_funds_after", "last_effect_applied"],
    "metric_name": "purchase_satisfaction",
    "metric_units": "normalized satisfaction points on a 0–1 scale",
    "assumptions": [
        "Input satisfaction is the reference rating absent this mechanism.",
        "A depleted but explicitly secure budget isolates reduced item satisfaction from rational budget concern.",
        "Strength linearly scales the hypothesized proportional satisfaction reduction; it is not calibrated.",
    ],
    "limitations": [
        "This is a synthetic illustrative process, not an empirical effect estimate or classifier.",
        "Budget security is supplied explicitly; the model does not infer obligations or hidden states.",
        "The model represents a single purchase step and does not model later adaptation or memory.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(context, key, *, minimum=None, maximum=None, strictly_positive=False):
    if key not in context:
        raise ValueError(f"missing required input: {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    value = float(value)
    if strictly_positive and value <= 0:
        raise ValueError(f"{key} must be greater than zero")
    if minimum is not None and value < minimum:
        raise ValueError(f"{key} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{key} must be at most {maximum}")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one purchase without mutating context or its state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be a finite number in [0, 1]")

    satisfaction = _number(context, "item_satisfaction", minimum=0.0, maximum=1.0)
    funds = _number(context, "funds_before", strictly_positive=True)
    cost = _number(context, "purchase_cost", strictly_positive=True)
    if cost > funds:
        raise ValueError("purchase_cost cannot exceed funds_before")
    if "budget_secure_after" not in context or not isinstance(context["budget_secure_after"], bool):
        raise ValueError("budget_secure_after must be an explicit bool")

    after = funds - cost
    # Exact depletion is the necessary 'last available funds' condition.
    depleted = after == 0.0
    secure = context["budget_secure_after"]
    effect_condition = depleted and secure

    # Explicit strength-zero reference: retain the supplied item rating.
    # Under the hypothesized effect, satisfaction is scaled by (1 - strength)
    # only for a secure-budget purchase that consumes all available funds.
    metric = satisfaction * (1.0 - float(strength)) if effect_condition else satisfaction
    metric = float(metric)
    active = effect_condition and metric != satisfaction

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    next_state = deepcopy(prior_state)
    next_state.update({
        "last_item_satisfaction": metric,
        "last_funds_after": after,
        "last_effect_applied": active,
    })
    trace = [
        f"Reference satisfaction={satisfaction:.6g}; funds_after={funds:.6g}-{cost:.6g}={after:.6g}.",
        f"Necessary conditions: funds_after == 0 ({depleted}) and budget_secure_after ({secure}); effect_condition={effect_condition}.",
        f"Metric=satisfaction*(1-strength) if condition else satisfaction = {metric:.6g}; active={active}.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "item_satisfaction": 0.8,
                "funds_before": 100.0,
                "purchase_cost": 100.0,
                "budget_secure_after": True,
            }],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "item_satisfaction": 0.8,
                "funds_before": 100.0,
                "purchase_cost": 99.0,
                "budget_secure_after": True,
            }],
            "expectation": "equal",
        },
    ]
