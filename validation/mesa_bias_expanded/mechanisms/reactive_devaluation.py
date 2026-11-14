"""Illustrative source-attribution penalty in a proposal choice task.

This is a hypothetical process model, not a detector or a fitted account of
human judgment. See specs/reactive_devaluation_implementation.md.
"""
from __future__ import annotations

import math


_SOURCE_SENSITIVITY = 0.5  # illustrative coefficient; not an empirical estimate
_REQUIRED = ("proposal_utility", "status_quo_utility", "source_dislike", "credible_risk")

METADATA = {
    "id": "reactive_devaluation",
    "name": "Reactive devaluation",
    "kind": "cognitive_bias",
    "description": (
        "In a hypothetical proposal choice, subtracts an explicit source-dislike "
        "cue from proposal value, over and above substantive utility and credible risk."
    ),
    # Only keys required in every phase; values and ranges are checked in evaluate.
    "required_inputs": list(_REQUIRED),
    "state_fields": ["last_choice", "last_reference_choice", "last_adjusted_score", "last_active"],
    "metric_name": "proposal_acceptance",
    "metric_units": "binary choice per task step (1=accept proposal, 0=retain status quo)",
    "assumptions": [
        "Utilities, source dislike, and credible strategic risk are explicit hypothetical inputs normalized to [0,1].",
        "The strength-scaled source sensitivity is a user-set illustrative assumption, not a calibrated effect size.",
        "The strength-zero reference compares proposal utility minus credible risk with status-quo utility.",
        "A strict tie retains the status quo; the process is deterministic and uses no random draw.",
    ],
    "limitations": [
        "This narrow task omits bargaining, uncertainty, strategic interaction, and richer source histories.",
        "Source dislike is stipulated by the scenario, never inferred from text or identity; rejection can be justified by substantive risk.",
        "The toy equation does not establish prevalence, accuracy, diagnosis, or empirical validity.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(context: dict, key: str) -> float:
    if key not in context:
        raise ValueError(f"missing required task input {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Choose proposal vs status quo; do not mutate context or nested state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")

    proposal = _number(context, "proposal_utility")
    status_quo = _number(context, "status_quo_utility")
    dislike = _number(context, "source_dislike")
    risk = _number(context, "credible_risk")

    substantive_value = proposal - risk
    reference_choice = int(substantive_value > status_quo)
    source_penalty = strength * _SOURCE_SENSITIVITY * dislike
    adjusted_value = substantive_value - source_penalty
    choice = int(adjusted_value > status_quo)

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be an object")
    next_state = dict(prior)
    next_state.update({
        "last_choice": choice,
        "last_reference_choice": reference_choice,
        "last_adjusted_score": adjusted_value,
        "last_active": bool(choice != reference_choice),
    })
    active = bool(choice != reference_choice)
    return {
        "metric": float(choice),
        "active": active,
        "state": next_state,
        "trace": [
            "Reference: proposal_utility - credible_risk compared with status_quo_utility; strict ties retain status quo.",
            f"Applied source penalty = strength({strength:g}) * illustrative sensitivity({_SOURCE_SENSITIVITY:g}) * explicit source_dislike({dislike:g}); adjusted proposal value={adjusted_value:g}.",
            f"Choice: {'accept proposal' if choice else 'retain status quo'}; source process changed the reference choice={active}.",
        ],
    }


def scenarios() -> list[dict]:
    common = {
        "proposal_utility": 0.78,
        "status_quo_utility": 0.45,
        "source_dislike": 0.90,
        "credible_risk": 0.08,
    }
    boundary = dict(common, source_dislike=0.0)
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [common],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
