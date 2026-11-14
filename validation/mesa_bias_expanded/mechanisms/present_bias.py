"""Illustrative present-bias choice process; not a detector or fitted model."""
from __future__ import annotations

import math


METADATA = {
    "id": "present_bias",
    "name": "Present Bias",
    "kind": "cognitive_bias",
    "description": (
        "In a stated two-option payoff task, a quasi-hyperbolic present weight "
        "discounts delayed rewards beyond the supplied exponential reference policy."
    ),
    # These keys must be supplied in every scenario phase; phase-specific timing
    # conditions are checked by evaluate rather than encoded as metadata prose.
    "required_inputs": ["options", "discount_rate", "present_weight"],
    "state_fields": ["choice_history"],
    "metric_name": "immediate_option_selected",
    "metric_units": "binary choice indicator (1 if a delay-0 option is selected, otherwise 0)",
    "assumptions": [
        "Exactly two explicitly specified options are compared by discounted payoff.",
        "The strength-scaled present weight is beta_s = 1 - strength*(1-beta); beta applies only to positive delays.",
        "The strength-zero reference sets beta_s to 1 while retaining the supplied exponential discount rate.",
        "Option order resolves exact utility ties; all coefficients are hypothetical user inputs.",
    ],
    "limitations": [
        "This stylized task does not represent liquidity constraints, uncertainty, changing circumstances, or full intertemporal preferences.",
        "The model overlaps with decreasing-impatience accounts and cannot identify a person's motive or diagnose bias.",
        "Strength is an uncalibrated intervention setting; no empirical validity or population claim is made.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label, *, minimum=None, maximum=None, exclusive_minimum=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if minimum is not None and (value <= minimum if exclusive_minimum else value < minimum):
        operator = ">" if exclusive_minimum else ">="
        raise ValueError(f"{label} must be {operator} {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return float(value)


def _options(raw):
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("options must be a list containing exactly two option objects")
    parsed = []
    ids = set()
    for option in raw:
        if not isinstance(option, dict) or not {"id", "payoff", "delay"}.issubset(option):
            raise ValueError("each option needs id, payoff, and delay")
        if not isinstance(option["id"], str) or not option["id"] or option["id"] in ids:
            raise ValueError("option ids must be distinct nonempty strings")
        ids.add(option["id"])
        parsed.append({
            "id": option["id"],
            "payoff": _finite_number(option["payoff"], "option payoff", minimum=0),
            "delay": _finite_number(option["delay"], "option delay", minimum=0),
        })
    return parsed


def _best(options, rate, beta):
    # One-step quasi-hyperbolic value: beta is omitted for a payoff available now.
    values = [o["payoff"] * math.exp(-rate * o["delay"]) * (1.0 if o["delay"] == 0 else beta)
              for o in options]
    index = max(range(len(options)), key=lambda i: values[i])
    return options[index], values[index], values


def evaluate(context: dict, strength: float) -> dict:
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError("missing required task input(s): " + ", ".join(missing))

    options = _options(context["options"])
    rate = _finite_number(context["discount_rate"], "discount_rate", minimum=0)
    beta = _finite_number(context["present_weight"], "present_weight", minimum=0,
                          maximum=1, exclusive_minimum=True)
    state_in = context.get("state", {})
    if not isinstance(state_in, dict):
        raise ValueError("state must be a dictionary")
    history = state_in.get("choice_history", [])
    if not isinstance(history, list):
        raise ValueError("state.choice_history must be a list")
    round_index = context.get("round_index", len(history))
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError("round_index must be a nonnegative integer")

    beta_s = 1.0 - float(strength) * (1.0 - beta)
    selected, selected_value, intervention_values = _best(options, rate, beta_s)
    reference, _, reference_values = _best(options, rate, 1.0)
    active = selected["id"] != reference["id"]
    entry = {
        "round": round_index,
        "choice": selected["id"],
        "delay": selected["delay"],
        "payoff": selected["payoff"],
    }
    next_state = dict(state_in)
    next_state["choice_history"] = list(history) + [entry]
    immediate = selected["delay"] == 0
    trace = (
        f"Compared the two supplied options using payoff*exp(-{rate:g}*delay)*beta_s for delayed rewards only; "
        f"beta_s={beta_s:.6g}. Selected {selected['id']} (value {selected_value:.6g}); "
        f"strength-zero reference selects {reference['id']}."
    )
    return {
        "metric": 1.0 if immediate else 0.0,
        "active": active,
        "state": next_state,
        "trace": [trace],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"choice_history": []},
            "contexts": [
                {"options": [{"id": "now", "payoff": 8, "delay": 0}, {"id": "later", "payoff": 10, "delay": 1}], "discount_rate": 0.05, "present_weight": 0.5},
                {"options": [{"id": "now", "payoff": 5, "delay": 0}, {"id": "later", "payoff": 7, "delay": 2}], "discount_rate": 0.05, "present_weight": 0.5},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"choice_history": []},
            # Both outcomes have the same positive delay: the immediate-vs-delayed
            # contrast necessary for this model is absent, though choice is not fixed.
            "contexts": [
                {"options": [{"id": "smaller", "payoff": 9, "delay": 1}, {"id": "larger", "payoff": 10, "delay": 1}], "discount_rate": 0.05, "present_weight": 0.5},
                {"options": [{"id": "smaller", "payoff": 6, "delay": 2}, {"id": "larger", "payoff": 8, "delay": 2}], "discount_rate": 0.05, "present_weight": 0.5},
            ],
            "expectation": "equal",
        },
    ]
