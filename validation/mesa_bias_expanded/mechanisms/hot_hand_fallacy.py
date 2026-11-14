"""Illustrative process model for unsupported hot-hand forecasts.

This is a synthetic mechanism, not a classifier or empirically fitted model.
"""

import math
from numbers import Real


METADATA = {
    "id": "hot_hand_fallacy",
    "name": "Hot Hand Fallacy",
    "kind": "cognitive_bias",
    "description": (
        "After consecutive successes, an agent overpredicts next-trial success "
        "when no task-specific persistence evidence supports the increase."
    ),
    "required_inputs": ["outcome", "base_rate", "supported_persistence_delta"],
    "state_fields": ["success_streak", "last_outcome", "last_forecast"],
    "metric_name": "next_trial_success_forecast",
    "metric_units": "probability, from 0 to 1",
    "assumptions": [
        "The supplied base_rate is the task's reference forecast absent streak evidence.",
        "supported_persistence_delta is an explicit, task-grounded forecast increment; zero means no such support was supplied.",
        "A streak of at least two consecutive successes can trigger an illustrative unsupported uplift.",
        "The illustrative uplift coefficient is 0.12 and is not an empirical effect size.",
        "strength in [0,1] scales only the unsupported uplift; strength zero uses the reference policy.",
    ],
    "limitations": [
        "This is a compact hypothetical process model, not an NLP detector or a claim about real people.",
        "Persistence evidence and base rates must be supplied by the caller and are not inferred or validated.",
        "The streak threshold and uplift curve are illustrative, not empirically validated or calibrated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_UPLIFT_COEFFICIENT = 0.12


def _probability(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Forecast next-trial success and return a fresh, complete task state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    for field in ("outcome", "base_rate", "supported_persistence_delta"):
        if field not in context:
            raise ValueError(f"missing required input: {field}")
    outcome = context["outcome"]
    if not isinstance(outcome, bool):
        raise ValueError("outcome must be a bool")
    base_rate = _probability(context["base_rate"], "base_rate")
    persistence_delta = _probability(
        context["supported_persistence_delta"], "supported_persistence_delta"
    )
    if base_rate + persistence_delta > 1.0:
        raise ValueError("base_rate plus supported_persistence_delta cannot exceed 1")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    prior_streak = prior.get("success_streak", 0)
    if isinstance(prior_streak, bool) or not isinstance(prior_streak, int) or prior_streak < 0:
        raise ValueError("state.success_streak must be a nonnegative integer")
    last_outcome = prior.get("last_outcome")
    if last_outcome is not None and not isinstance(last_outcome, bool):
        raise ValueError("state.last_outcome must be bool or None")
    prior_forecast = prior.get("last_forecast")
    if prior_forecast is not None:
        _probability(prior_forecast, "state.last_forecast")

    streak = prior_streak + 1 if outcome else 0
    # Reference policy accepts only the supplied base rate and explicit
    # persistence increment. Unsupported streak uplift is a saturating curve.
    reference_forecast = base_rate + persistence_delta
    unsupported_streak = streak >= 2 and persistence_delta == 0.0
    raw_uplift = (
        _UPLIFT_COEFFICIENT * (streak - 1) / (streak + 1)
        if unsupported_streak
        else 0.0
    )
    uplift = min(1.0 - reference_forecast, strength * raw_uplift)
    forecast = reference_forecast + uplift

    next_state = {
        "success_streak": streak,
        "last_outcome": outcome,
        "last_forecast": forecast,
    }
    active = uplift > 0.0
    trace = [
        f"Updated consecutive-success streak to {streak} from outcome={outcome}.",
        f"Reference forecast = base_rate ({base_rate:.6g}) + supported persistence delta ({persistence_delta:.6g}) = {reference_forecast:.6g}.",
        (
            f"Unsupported streak={unsupported_streak}; raw uplift = 0.12*(streak-1)/(streak+1) = {raw_uplift:.6g}; "
            f"scaled/capped uplift = {uplift:.6g} at strength={strength:.6g}."
        ),
        f"Next-trial success forecast={forecast:.6g}; active={active}.",
    ]
    return {"metric": forecast, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"success_streak": 0, "last_outcome": None, "last_forecast": None},
            "contexts": [
                {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.0},
                {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.0},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"success_streak": 0, "last_outcome": None, "last_forecast": None},
            "contexts": [
                {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.1},
                {"outcome": True, "base_rate": 0.5, "supported_persistence_delta": 0.1},
            ],
            "expectation": "equal",
        },
    ]
