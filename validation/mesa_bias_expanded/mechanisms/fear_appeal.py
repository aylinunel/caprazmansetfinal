"""Hypothetical structured process model for disproportionate fear-framed messages."""

from copy import deepcopy
import math


METADATA = {
    "id": "fear_appeal",
    "name": "Fear Appeal (Korkuya başvurma)",
    "kind": "media_practice",
    "description": (
        "Models excess reader precaution caused by explicit threat/disaster framing "
        "combined with a stated probability that exceeds the supplied evidence-supported probability."
    ),
    "required_inputs": [
        "threat_language",
        "threat_salience",
        "severity",
        "stated_probability",
        "evidence_supported_probability",
        "response_capacity",
    ],
    "state_fields": ["last_action_intensity", "cumulative_action_points", "steps"],
    "metric_name": "precaution_action_intensity",
    "metric_units": "illustrative normalized precaution points (0-2 per step; not an empirical scale)",
    "assumptions": [
        "All numeric fields are explicit synthetic inputs on [0,1], not text-derived estimates.",
        "The strength parameter scales the hypothetical response to unsupported probability inflation.",
        "Evidence-supported probability is the reference risk probability; severity and response capacity scale action.",
        "Threat salience scales the effect of the probability discrepancy and has no independent effect when probability is proportionate.",
    ],
    "limitations": [
        "This is a narrow illustrative media-practice model, not a validated account of fear, persuasion, or reader behavior.",
        "It requires structured probabilities and supplied threat annotations; it is not an NLP detector and does not assess whether evidence is actually adequate.",
        "Urgent threat communication can be proportionate or beneficial; this model marks no excess absent explicit framing and probability mismatch.",
        "The reference policy is a stipulated risk-calibrated precaution rule, not a claim of perfect rationality.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(context: dict, field: str) -> float:
    if field not in context:
        raise ValueError(f"missing required input: {field}")
    value = context[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one content exposure; caller owns both input and returned state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    if "threat_language" not in context or not isinstance(context["threat_language"], bool):
        raise ValueError("threat_language must be supplied as a bool")
    salience = _unit_interval(context, "threat_salience")
    severity = _unit_interval(context, "severity")
    stated_probability = _unit_interval(context, "stated_probability")
    evidence_probability = _unit_interval(context, "evidence_supported_probability")
    response_capacity = _unit_interval(context, "response_capacity")

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    prior_total = previous.get("cumulative_action_points", 0.0)
    prior_steps = previous.get("steps", 0)
    if (isinstance(prior_total, bool) or not isinstance(prior_total, (int, float))
            or not math.isfinite(float(prior_total)) or float(prior_total) < 0):
        raise ValueError("state.cumulative_action_points must be finite and nonnegative")
    if isinstance(prior_steps, bool) or not isinstance(prior_steps, int) or prior_steps < 0:
        raise ValueError("state.steps must be a nonnegative integer")

    # Reference: allocate precaution in proportion to evidence-supported expected harm.
    reference_action = severity * evidence_probability * response_capacity
    # The mechanism requires both explicit threat language and overstatement of probability.
    probability_gap = max(0.0, stated_probability - evidence_probability)
    active = context["threat_language"] and probability_gap > 0.0 and salience > 0.0 and strength > 0.0
    unsupported_urgency = (
        salience * probability_gap if context["threat_language"] else 0.0
    )
    metric = reference_action + strength * severity * response_capacity * unsupported_urgency

    next_state = deepcopy(previous)
    next_state.update({
        "last_action_intensity": metric,
        "cumulative_action_points": float(prior_total) + metric,
        "steps": prior_steps + 1,
    })
    return {
        "metric": float(metric),
        "active": bool(active),
        "state": next_state,
        "trace": [
            "Reference action = severity * evidence_supported_probability * response_capacity. "
            "With threat_language=true, unsupported_urgency = threat_salience * "
            "max(0, stated_probability - evidence_supported_probability); otherwise it is 0. "
            "Metric = reference action + strength * severity * response_capacity * "
            "unsupported_urgency. The metric is per-step normalized precaution points; "
            "state accumulates these points without mutating the input."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"last_action_intensity": 0.0, "cumulative_action_points": 0.0, "steps": 0},
            "contexts": [{
                "threat_language": True,
                "threat_salience": 0.8,
                "severity": 0.9,
                "stated_probability": 0.7,
                "evidence_supported_probability": 0.2,
                "response_capacity": 0.75,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"last_action_intensity": 0.0, "cumulative_action_points": 0.0, "steps": 0},
            "contexts": [{
                "threat_language": True,
                "threat_salience": 0.8,
                "severity": 0.9,
                "stated_probability": 0.2,
                "evidence_supported_probability": 0.2,
                "response_capacity": 0.75,
            }],
            "expectation": "equal",
        },
    ]
