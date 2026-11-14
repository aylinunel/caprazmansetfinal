"""Illustrative, task-specific IKEA-effect mechanism (not an empirical model)."""

from copy import deepcopy
import math
from numbers import Real


# Illustrative coefficient, not a measured effect size: valuation points/hour.
_UPLIFT_PER_ASSEMBLY_HOUR = 2.0

METADATA = {
    "id": "ikea_effect",
    "name": "IKEA Effect",
    "kind": "cognitive_bias",
    "description": (
        "A hypothetical reservation-value model in which personally assembling "
        "an object adds an effort-linked ownership premium beyond its objective value."
    ),
    "required_inputs": [
        "objective_value",
        "objective_customization_benefit",
        "self_assembled",
        "assembly_effort_hours",
        "owned",
    ],
    "state_fields": [
        "evaluation_count",
        "last_reference_value",
        "last_perceived_value",
        "last_assembly_uplift",
    ],
    "metric_name": "hypothetical_reservation_value",
    "metric_units": "valuation points (objective-value points plus effort-linked points)",
    "assumptions": [
        "The supplied objective value and objective customization benefit are known task facts.",
        "Self-assembly effort is measured in hours and is the only trigger for the modeled premium.",
        "The illustrative coefficient is 2 valuation points per assembly hour before strength scaling.",
        "Strength scales only the assembly premium; strength zero is the reference valuation policy.",
        "Ownership is supplied separately and has no direct effect in this mechanism.",
    ],
    "limitations": [
        "This is a synthetic, explicitly hypothetical process rule, not an empirically fitted effect size.",
        "It does not infer assembly, effort, ownership, or value from text or behavior.",
        "Effort may reflect learning, enjoyment, customization, or other benign value; this model cannot distinguish them.",
        "It represents one valuation task and does not claim a temporal or population-level effect.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_nonnegative(context: dict, key: str) -> float:
    if key not in context:
        raise ValueError(f"missing required input: {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{key} must be a finite nonnegative number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{key} must be a finite nonnegative number")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one hypothetical reservation-value decision without mutating inputs."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be a finite number in [0, 1]")

    objective_value = _finite_nonnegative(context, "objective_value")
    customization = _finite_nonnegative(context, "objective_customization_benefit")
    effort = _finite_nonnegative(context, "assembly_effort_hours")
    self_assembled = context.get("self_assembled")
    owned = context.get("owned")
    if not isinstance(self_assembled, bool):
        raise ValueError("self_assembled must be a bool")
    if not isinstance(owned, bool):
        raise ValueError("owned must be a bool")
    if self_assembled and effort <= 0:
        raise ValueError("self_assembled requires positive assembly_effort_hours")

    prior_state = context.get("state")
    if not isinstance(prior_state, dict):
        raise ValueError("context['state'] must be a dict")
    state = deepcopy(prior_state)
    count = state.get("evaluation_count", 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.evaluation_count must be a nonnegative integer")

    # Reference policy: count objective value and the explicit objective benefit
    # of customization; do not add value merely for ownership or assembly effort.
    reference_value = objective_value + customization
    uplift = (
        strength * _UPLIFT_PER_ASSEMBLY_HOUR * effort
        if self_assembled
        else 0.0
    )
    metric = reference_value + uplift
    if not all(math.isfinite(x) for x in (reference_value, uplift, metric)):
        raise ValueError("input magnitudes produce a non-finite valuation")

    state.update(
        {
            "evaluation_count": count + 1,
            "last_reference_value": reference_value,
            "last_perceived_value": metric,
            "last_assembly_uplift": uplift,
        }
    )
    trigger = self_assembled and effort > 0 and strength > 0
    trace = (
        f"reference={objective_value:g}+{customization:g}={reference_value:g}; "
        f"self_assembled={self_assembled}, owned={owned}, effort_hours={effort:g}; "
        f"uplift={strength:g}*{_UPLIFT_PER_ASSEMBLY_HOUR:g}*{effort:g} "
        f"when self_assembled, else 0 => {uplift:g}; metric={metric:g}."
    )
    return {
        "metric": metric,
        "active": bool(trigger),
        "state": state,
        "trace": [trace],
    }


def scenarios() -> list[dict]:
    """Return required positive and boundary cases for a direct task runner."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "objective_value": 40,
                    "objective_customization_benefit": 5,
                    "self_assembled": True,
                    "assembly_effort_hours": 3,
                    "owned": True,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "objective_value": 40,
                    "objective_customization_benefit": 5,
                    "self_assembled": False,
                    "assembly_effort_hours": 3,
                    "owned": True,
                }
            ],
            "expectation": "equal",
        },
    ]
