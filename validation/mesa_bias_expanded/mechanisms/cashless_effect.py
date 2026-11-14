"""Illustrative cashless-versus-cash spending choice process model.

This is a synthetic task model, not a detector or validated psychology. See
specs/cashless_effect_implementation.md.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "cashless_effect",
    "name": "Cashless Effect",
    "kind": "cognitive_bias",
    "description": (
        "Models a purchase choice where a lower explicit payment-salience cost "
        "for cashless payment can increase willingness to buy relative to a "
        "physical-cash reference."
    ),
    "required_inputs": [
        "willingness_margin",
        "purchase_amount",
        "budget",
        "payment_mode",
        "cash_salience",
        "cashless_salience",
        "salience_sensitivity",
    ],
    "state_fields": [
        "last_willingness_margin",
        "last_reference_willingness_margin",
        "last_purchase_amount",
        "last_spend",
        "cumulative_spend",
    ],
    "metric_name": "spend_on_offered_purchase",
    "metric_units": "currency units committed to this offered purchase (0 or purchase_amount)",
    "assumptions": [
        "willingness_margin is an explicit, currency-equivalent surplus before payment-salience friction.",
        "Payment salience and salience_sensitivity are supplied hypothetical task inputs; strength linearly interpolates cashless salience toward physical-cash salience.",
        "The strength-zero reference always applies the physical-cash salience cost; an unaffordable purchase is declined.",
    ],
    "limitations": [
        "The linear salience-to-willingness equation is an illustrative assumption, not an estimated or empirically validated effect size.",
        "Inputs are explicit scenario facts; this module does not infer willingness, payment method, or salience from behavior or text.",
        "Real spending may depend on many omitted factors, and lower payment salience can be benign or offset by budgeting practices.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value, field, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{field} must be at most {maximum}")
    return value


def _inputs(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    fields = METADATA["required_inputs"]
    missing = [field for field in fields if field not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    willingness = _number(context["willingness_margin"], "willingness_margin")
    amount = _number(context["purchase_amount"], "purchase_amount", minimum=0.0)
    if amount <= 0.0:
        raise ValueError("purchase_amount must be greater than 0")
    budget = _number(context["budget"], "budget", minimum=0.0)
    cash_salience = _number(context["cash_salience"], "cash_salience", minimum=0.0, maximum=1.0)
    cashless_salience = _number(
        context["cashless_salience"], "cashless_salience", minimum=0.0, maximum=1.0
    )
    sensitivity = _number(context["salience_sensitivity"], "salience_sensitivity", minimum=0.0)
    mode = context["payment_mode"]
    if mode not in ("cashless", "physical_cash"):
        raise ValueError("payment_mode must be 'cashless' or 'physical_cash'")
    return willingness, amount, budget, mode, cash_salience, cashless_salience, sensitivity


def _strength(value):
    return _number(value, "strength", minimum=0.0, maximum=1.0)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one offered purchase and return spend plus updated task state."""
    strength = _strength(strength)
    (
        willingness,
        amount,
        budget,
        mode,
        cash_salience,
        cashless_salience,
        sensitivity,
    ) = _inputs(context)

    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    prior_total = _number(state.get("cumulative_spend", 0.0), "state.cumulative_spend", minimum=0.0)

    # The reference applies physical-cash salience in either payment mode.
    # The candidate can reduce that friction only for cashless payment and
    # only if the supplied cashless salience is strictly lower.
    gap = max(cash_salience - cashless_salience, 0.0)
    eligible = mode == "cashless" and gap > 0.0
    effective_salience = cash_salience - strength * gap if eligible else cash_salience
    reference_margin = willingness - sensitivity * amount * cash_salience
    adjusted_margin = willingness - sensitivity * amount * effective_salience
    reference_spend = amount if reference_margin >= 0.0 and amount <= budget else 0.0
    spend = amount if adjusted_margin >= 0.0 and amount <= budget else 0.0
    if not all(math.isfinite(v) for v in (reference_margin, adjusted_margin, spend, prior_total + spend)):
        raise ValueError("computed spending choice is not finite")

    next_state = deepcopy(state)
    next_state.update(
        {
            "last_willingness_margin": adjusted_margin,
            "last_reference_willingness_margin": reference_margin,
            "last_purchase_amount": amount,
            "last_spend": spend,
            "cumulative_spend": prior_total + spend,
        }
    )
    active = strength > 0.0 and adjusted_margin > reference_margin
    explanation = (
        f"reference_margin=willingness_margin-salience_sensitivity*purchase_amount*cash_salience="
        f"{reference_margin:.12g}; mode={mode}, eligible_cashless_gap={gap:.12g}, "
        f"effective_salience={effective_salience:.12g}, adjusted_margin="
        f"willingness_margin-salience_sensitivity*purchase_amount*effective_salience="
        f"{adjusted_margin:.12g}; budget={budget:.12g}, purchase_amount={amount:.12g}, "
        f"spend={spend:.12g} (reference spend={reference_spend:.12g})."
    )
    return {
        "metric": spend,
        "active": active,
        "state": next_state,
        "trace": [explanation],
    }


def scenarios() -> list[dict]:
    positive = {
        "willingness_margin": 3.0,
        "purchase_amount": 10.0,
        "budget": 20.0,
        "payment_mode": "cashless",
        "cash_salience": 0.8,
        "cashless_salience": 0.1,
        "salience_sensitivity": 0.5,
    }
    boundary = {
        "willingness_margin": 3.0,
        "purchase_amount": 10.0,
        "budget": 20.0,
        "payment_mode": "cashless",
        "cash_salience": 0.8,
        "cashless_salience": 0.8,
        "salience_sensitivity": 0.5,
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [positive],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
