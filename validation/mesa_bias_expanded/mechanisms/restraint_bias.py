"""Illustrative choice model for overestimating resistance to temptation."""
import math


METADATA = {
    "id": "restraint_bias",
    "name": "Restraint Bias",
    "kind": "cognitive_bias",
    "description": (
        "Overstated self-assessed resistance lowers predicted lapse risk and can "
        "make a tempting option appear preferable to a safe alternative."
    ),
    "required_inputs": [
        "temptation_reward", "safe_reward", "temptation_load",
        "actual_resistance", "self_assessed_resistance", "lapse_cost",
    ],
    "state_fields": [
        "estimated_resistance", "predicted_lapse_probability", "chosen_option",
    ],
    "metric_name": "temptation_option_selected",
    "metric_units": "binary choice indicator (1=temptation, 0=safe alternative)",
    "assumptions": [
        "Task capacities and temptation load are supplied hypothetical values on [0,1].",
        "Lapse probability is max(0, temptation_load - estimated_resistance).",
        "Expected payoff of temptation is success_probability*temptation_reward minus lapse_probability*lapse_cost.",
        "The strength setting blends accurate task resistance toward the self-assessed value only when that value is overconfident.",
    ],
    "limitations": [
        "This deterministic, one-choice toy model is not a detector, diagnosis, or population claim.",
        "Task values and the linear lapse-risk relation are illustrative assumptions, not calibrated effect sizes.",
        "Real self-control, opportunity, habits, support, fatigue, and strategic precommitment are not modeled.",
        "Choosing temptation is not inherently harmful; the task only encodes a supplied lapse cost.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(context, key, low=None, high=None, *, positive=False):
    if key not in context:
        raise ValueError(f"missing required task input {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key} must be a finite number")
    value = float(value)
    if positive and value <= 0:
        raise ValueError(f"{key} must be positive")
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f"{key} must be in [{low}, {high}]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Choose the higher-valued option using biased or accurate resistance."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")

    temptation_reward = _number(context, "temptation_reward", positive=True)
    safe_reward = _number(context, "safe_reward", low=0)
    load = _number(context, "temptation_load", low=0, high=1)
    actual = _number(context, "actual_resistance", low=0, high=1)
    assessed = _number(context, "self_assessed_resistance", low=0, high=1)
    lapse_cost = _number(context, "lapse_cost", positive=True)

    # Only overconfidence (assessed > actual) is eligible for the bias. At
    # strength zero, the reference uses the supplied task-specific capacity.
    overconfidence = max(0.0, assessed - actual)
    estimated = actual + float(strength) * overconfidence
    actual_lapse = max(0.0, min(1.0, load - actual))
    predicted_lapse = max(0.0, min(1.0, load - estimated))
    temptation_value = (1.0 - predicted_lapse) * temptation_reward - predicted_lapse * lapse_cost
    chosen = "temptation" if temptation_value > safe_reward else "safe"
    changed_risk = predicted_lapse != actual_lapse

    return {
        "metric": 1.0 if chosen == "temptation" else 0.0,
        "active": bool(changed_risk),
        "state": {
            "estimated_resistance": estimated,
            "predicted_lapse_probability": predicted_lapse,
            "chosen_option": chosen,
        },
        "trace": [
            "estimated_resistance = actual_resistance + strength * max(0, self_assessed_resistance - actual_resistance); "
            "predicted_lapse_probability = clamp(temptation_load - estimated_resistance, 0, 1); "
            "temptation expected payoff = (1 - predicted_lapse_probability) * temptation_reward "
            "- predicted_lapse_probability * lapse_cost; choose temptation only if it exceeds safe_reward."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "temptation_reward": 8.0,
                "safe_reward": 1.0,
                "temptation_load": 0.75,
                "actual_resistance": 0.25,
                "self_assessed_resistance": 0.85,
                "lapse_cost": 12.0,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "temptation_reward": 8.0,
                "safe_reward": 1.0,
                "temptation_load": 0.75,
                "actual_resistance": 0.25,
                "self_assessed_resistance": 0.25,
                "lapse_cost": 12.0,
            }],
            "expectation": "equal",
        },
    ]
