"""Illustrative allocation process for the identifiable-victim effect.

This is a synthetic process model, not a detector or fitted psychological model.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any


# This coefficient is an explicit illustrative assumption, not an empirical estimate.
MAX_IDENTIFICATION_WEIGHT = 0.5
COMPARABILITY_REL_TOL = 1e-9
COMPARABILITY_ABS_TOL = 1e-12

METADATA = {
    "id": "identifiable_victim_effect",
    "name": "Identifiable Victim Effect",
    "kind": "cognitive_bias",
    "description": (
        "Allocates a fixed aid budget between two equally effective recipients; "
        "when one is individually identified, its allocation weight receives an "
        "illustrative salience multiplier."
    ),
    "required_inputs": [
        "identified",
        "identified_effectiveness",
        "anonymous_effectiveness",
        "budget",
    ],
    "state_fields": ["decisions", "total_identified_help", "total_anonymous_help"],
    "metric_name": "identified_recipient_help",
    "metric_units": "aid-budget units allocated to the identified-recipient option in this decision",
    "assumptions": [
        "The task allocates one finite budget between exactly two recipient options, one individual and one anonymous comparator.",
        "Effectiveness inputs are explicit positive expected-help-per-aid-unit values; they are not inferred from identity or text.",
        "The strength-zero reference allocates in proportion to supplied effectiveness.",
        "An identity salience multiplier of 1 + 0.5*strength applies only when the first recipient is identified and the two effectiveness values are comparable.",
        "The coefficient 0.5 is illustrative and user-settable, not a published effect size or calibrated confidence.",
    ],
    "limitations": [
        "This assumed two-option allocation process is not an empirical account of real charitable decisions, a population claim, or a detector.",
        "It operationalizes comparability as effectiveness values equal within a small numeric tolerance; it does not model need, urgency, recipient count, uncertainty, or constraints.",
        "An identified appeal can provide relevant information or improve effectiveness; unequal supplied effectiveness is therefore handled by the reference allocation without an identity bonus.",
        "The simple salience multiplier ignores deliberation, institutions, donation contexts, and individual differences; no effect size has been empirically validated here.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Allocate aid using an effectiveness reference plus a narrow identity bonus."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    identified = context["identified"]
    if not isinstance(identified, bool):
        raise ValueError("identified must be a bool stating whether the focal recipient is individually identified")
    effectiveness_identified = _finite_number(
        context["identified_effectiveness"], "identified_effectiveness"
    )
    effectiveness_anonymous = _finite_number(
        context["anonymous_effectiveness"], "anonymous_effectiveness"
    )
    if effectiveness_identified <= 0 or effectiveness_anonymous <= 0:
        raise ValueError("both effectiveness values must be positive")
    budget = _finite_number(context["budget"], "budget")
    if budget <= 0:
        raise ValueError("budget must be positive")

    comparable = math.isclose(
        effectiveness_identified,
        effectiveness_anonymous,
        rel_tol=COMPARABILITY_REL_TOL,
        abs_tol=COMPARABILITY_ABS_TOL,
    )
    active = identified and comparable and s > 0.0

    # Normalize before weighting to avoid overflow for very large but finite inputs.
    scale = max(effectiveness_identified, effectiveness_anonymous)
    identified_weight = effectiveness_identified / scale
    anonymous_weight = effectiveness_anonymous / scale
    reference_share = identified_weight / (identified_weight + anonymous_weight)
    if identified and comparable:
        adjusted_identified_weight = identified_weight * (1.0 + MAX_IDENTIFICATION_WEIGHT * s)
    else:
        # Identity alone is not enough: it must distinguish otherwise comparable outcomes.
        adjusted_identified_weight = identified_weight
    allocation_share = adjusted_identified_weight / (
        adjusted_identified_weight + anonymous_weight
    )
    identified_help = budget * allocation_share
    anonymous_help = budget - identified_help
    if not all(math.isfinite(value) for value in (identified_help, anonymous_help, reference_share)):
        raise ValueError("allocation produced a non-finite result")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    prior_decisions = prior.get("decisions", 0)
    if isinstance(prior_decisions, bool) or not isinstance(prior_decisions, int) or prior_decisions < 0:
        raise ValueError("state.decisions must be a nonnegative integer")
    total_identified = _finite_number(prior.get("total_identified_help", 0.0), "state.total_identified_help")
    total_anonymous = _finite_number(prior.get("total_anonymous_help", 0.0), "state.total_anonymous_help")
    if total_identified < 0 or total_anonymous < 0:
        raise ValueError("state aid totals must be nonnegative")
    next_identified_total = total_identified + identified_help
    next_anonymous_total = total_anonymous + anonymous_help
    if not math.isfinite(next_identified_total) or not math.isfinite(next_anonymous_total):
        raise ValueError("updated state totals must remain finite")
    next_state = {
        "decisions": prior_decisions + 1,
        "total_identified_help": next_identified_total,
        "total_anonymous_help": next_anonymous_total,
    }

    trace = [
        "Reference allocation uses effectiveness-proportional weights: "
        "identified_share = e_identified / (e_identified + e_anonymous).",
        (
            "Because the focal recipient is individually identified and effectiveness is comparable, "
            "the process uses e_identified*(1 + 0.5*strength) against e_anonymous; "
            "this coefficient is an illustrative salience assumption."
            if identified and comparable
            else "No identity bonus: the recipient is not identified or effectiveness is not comparable; "
            "allocation follows the effectiveness-proportional reference."
        ),
        f"Budget={budget:.12g}; identified allocation={identified_help:.12g}; "
        f"reference allocation={budget * reference_share:.12g}; active={active}.",
    ]
    return {
        "metric": identified_help,
        "active": active,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "identified": True,
                "identified_effectiveness": 1.0,
                "anonymous_effectiveness": 1.0,
                "budget": 12.0,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "identified": False,
                "identified_effectiveness": 1.0,
                "anonymous_effectiveness": 1.0,
                "budget": 12.0,
            }],
            "expectation": "equal",
        },
    ]
