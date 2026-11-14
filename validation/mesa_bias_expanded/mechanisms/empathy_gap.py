"""Illustrative state-projection mechanism for an explicit two-option forecast task.

This is a synthetic process model, not a classifier or empirical psychology model.
"""

from copy import deepcopy
import math
from numbers import Real


METADATA = {
    "id": "empathy_gap",
    "name": "Empathy Gap",
    "kind": "cognitive_bias",
    "description": (
        "A forecaster predicts a target's binary choice by blending the target's "
        "explicit state-conditioned utility difference with the forecaster's own "
        "state-conditioned utility difference, thereby projecting current-state "
        "preferences across a different-state boundary."
    ),
    "required_inputs": ["forecaster_state", "target_state", "utility_delta_by_state"],
    "state_fields": [
        "steps", "cumulative_error", "last_forecaster_state", "last_target_state",
        "last_forecast_choice", "last_reference_choice", "last_error",
    ],
    "metric_name": "binary_choice_forecast_error",
    "metric_units": "0 or 1 per decision (1 means forecast differs from target-state choice)",
    "assumptions": [
        "The supplied state labels and utility differences are explicit hypothetical task facts, not inferred internal states.",
        "Positive utility_delta_by_state values favor option A; zero or negative values favor option B.",
        "strength is an illustrative projection weight: the forecast blends the target-state utility difference with the forecaster-state difference.",
        "The target's choice follows the sign of its supplied state-conditioned utility difference.",
    ],
    "limitations": [
        "A binary, deterministic utility-difference task cannot represent nuanced interpersonal understanding or mixed motives.",
        "The utility values and projection weight are illustrative assumptions, not fitted or empirically validated parameters.",
        "The module evaluates structured evidence only; it does not detect emotions, infer states, or assess real people.",
        "Projection may be benign or useful in some contexts; this module scores forecast mismatch only and makes no moral judgment.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite real number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite real number")
    return value


def _choice(utility_delta):
    """Use the task's deterministic tie rule: a tie selects option B."""
    return "A" if utility_delta > 0 else "B"


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one forecast decision without mutating supplied context/state."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required evidence: {', '.join(missing)}")
    forecaster_state = context["forecaster_state"]
    target_state = context["target_state"]
    if not isinstance(forecaster_state, str) or not forecaster_state.strip():
        raise ValueError("forecaster_state must be a non-empty state label")
    if not isinstance(target_state, str) or not target_state.strip():
        raise ValueError("target_state must be a non-empty state label")
    utility_by_state = context["utility_delta_by_state"]
    if not isinstance(utility_by_state, dict):
        raise ValueError("utility_delta_by_state must map state labels to utility differences")
    if forecaster_state not in utility_by_state or target_state not in utility_by_state:
        raise ValueError("utility_delta_by_state must include both supplied states")
    own_delta = _finite_number(
        utility_by_state[forecaster_state], f"utility_delta_by_state[{forecaster_state!r}]"
    )
    target_delta = _finite_number(
        utility_by_state[target_state], f"utility_delta_by_state[{target_state!r}]"
    )

    # Strength zero is the explicit reference policy: forecast from the target's
    # supplied state-conditioned preference. Increasing strength projects more
    # of the forecaster's preference into that forecast.
    projected_delta = (1.0 - strength) * target_delta + strength * own_delta
    reference_choice = _choice(target_delta)
    forecast_choice = _choice(projected_delta)
    error = float(forecast_choice != reference_choice)

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict when supplied")
    next_state = deepcopy(prior)
    prior_steps = prior.get("steps", 0)
    if isinstance(prior_steps, bool) or not isinstance(prior_steps, int) or prior_steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    prior_error = _finite_number(prior.get("cumulative_error", 0.0), "state.cumulative_error")
    if prior_error < 0:
        raise ValueError("state.cumulative_error must be non-negative")
    next_state.update({
        "steps": prior_steps + 1,
        "cumulative_error": prior_error + error,
        "last_forecaster_state": forecaster_state,
        "last_target_state": target_state,
        "last_forecast_choice": forecast_choice,
        "last_reference_choice": reference_choice,
        "last_error": error,
    })
    active = forecast_choice != reference_choice
    trace = [
        f"Reference choice uses target state {target_state!r}: delta={target_delta:g}, choice={reference_choice} (delta > 0 selects A; tie selects B).",
        f"Projection equation: (1 - {strength:g})*target_delta + {strength:g}*forecaster_delta = {projected_delta:g}; forecaster state {forecaster_state!r} has delta={own_delta:g}, forecast={forecast_choice}.",
        f"Per-decision metric is binary choice mismatch={int(error)}; active={active} because the projected choice {'differs from' if active else 'matches'} the reference choice.",
    ]
    return {"metric": error, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "forecaster_state": "hungry",
                "target_state": "sated",
                "utility_delta_by_state": {"hungry": 2.0, "sated": -1.0},
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "forecaster_state": "calm",
                "target_state": "calm",
                "utility_delta_by_state": {"calm": 1.5},
            }],
            "expectation": "equal",
        },
    ]
