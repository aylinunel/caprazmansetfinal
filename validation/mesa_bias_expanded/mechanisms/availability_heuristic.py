"""Illustrative recall-accessibility substitution model.

This is a task-specific process model, not a classifier or validated account of
human judgment. See specs/availability_heuristic_implementation.md.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "availability_heuristic",
    "name": "Availability Heuristic",
    "kind": "cognitive_bias",
    "description": (
        "Blends the observed event frequency with an accessibility-weighted "
        "frequency estimate, modeling recall ease substituting for evidence."
    ),
    "required_inputs": ["cases"],
    "state_fields": ["last_judgment", "last_evidence_rate", "last_availability_rate"],
    "metric_name": "subjective_event_probability",
    "metric_units": "probability judgment on a 0–1 scale",
    "assumptions": [
        "Each case is one equally weighted observed event or non-event.",
        "recall_ease is an explicit, hypothetical nonnegative accessibility weight.",
        "strength linearly controls substitution of accessibility-weighted frequency for observed frequency.",
    ],
    "limitations": [
        "The accessibility proxy and linear blend are illustrative, not fitted or empirically validated.",
        "The model does not infer recall ease from language, recency, vividness, or other hidden facts.",
        "Accessibility can be informative in some real settings; this model represents a possible distortion only when weighted and observed frequencies differ.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def _rates(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    cases = context.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a non-empty list of observed evidence")

    event_count = 0
    accessible_events = 0.0
    total_accessibility = 0.0
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"cases[{index}] must be a dictionary")
        outcome = case.get("event")
        if type(outcome) is not bool:
            raise ValueError(f"cases[{index}].event must be a boolean")
        if "recall_ease" not in case:
            raise ValueError(f"cases[{index}].recall_ease is required")
        ease = case["recall_ease"]
        if isinstance(ease, bool) or not isinstance(ease, (int, float)):
            raise ValueError(f"cases[{index}].recall_ease must be a finite number in [0, 1]")
        ease = float(ease)
        if not math.isfinite(ease) or not 0.0 <= ease <= 1.0:
            raise ValueError(f"cases[{index}].recall_ease must be a finite number in [0, 1]")
        event_count += int(outcome)
        total_accessibility += ease
        if outcome:
            accessible_events += ease

    if total_accessibility <= 0.0:
        raise ValueError("evidence must include at least one recall-accessible case")
    evidence_rate = event_count / len(cases)
    availability_rate = accessible_events / total_accessibility
    return evidence_rate, availability_rate


def evaluate(context: dict, strength: float) -> dict:
    """Return a recall-weighted probability judgment for one evidence task."""
    strength = _unit_interval(strength, "strength")
    evidence_rate, availability_rate = _rates(context)
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")

    # Reference policy is the ordinary observed frequency; the availability
    # process substitutes its weighted frequency in proportion to strength.
    metric = (1.0 - strength) * evidence_rate + strength * availability_rate
    if not math.isfinite(metric):
        raise ValueError("computed judgment is not finite")

    next_state = deepcopy(state)
    next_state.update(
        {
            "last_judgment": metric,
            "last_evidence_rate": evidence_rate,
            "last_availability_rate": availability_rate,
        }
    )
    active = strength > 0.0 and not math.isclose(
        availability_rate, evidence_rate, rel_tol=0.0, abs_tol=1e-12
    )
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            (
                f"Observed frequency={evidence_rate:.12g} ({sum(case['event'] for case in context['cases'])}/"
                f"{len(context['cases'])}); accessibility-weighted frequency="
                f"{availability_rate:.12g} (sum(event recall_ease)/sum(all recall_ease)); "
                f"judgment=(1-{strength:.12g})*observed_frequency+"
                f"{strength:.12g}*accessibility_weighted_frequency={metric:.12g}."
            )
        ],
    }


def scenarios() -> list[dict]:
    positive = {
        "cases": [
            {"event": True, "recall_ease": 1.0},
            {"event": False, "recall_ease": 0.1},
            {"event": False, "recall_ease": 0.1},
            {"event": False, "recall_ease": 0.1},
        ]
    }
    boundary = {
        "cases": [
            {"event": True, "recall_ease": 0.7},
            {"event": False, "recall_ease": 0.7},
            {"event": False, "recall_ease": 0.7},
            {"event": False, "recall_ease": 0.7},
        ]
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
