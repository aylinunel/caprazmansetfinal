"""Illustrative authored-denominator selection process for selective statistics.

This is a synthetic media-practice model, not a detector or empirical claim.
"""
from __future__ import annotations

import math
from typing import Any

METADATA = {
    "id": "selective_statistics",
    "name": "Selective statistics (Seçici istatistik)",
    "kind": "media_practice",
    "description": (
        "An authored presentation may use a supplied alternative denominator "
        "instead of a documented, relevant comparison denominator."
    ),
    "required_inputs": [
        "event_count",
        "relevant_denominator",
        "selected_denominator",
        "denominator_evidence",
    ],
    "state_fields": [
        "steps_evaluated",
        "last_denominator_used",
        "last_rate_per_100",
    ],
    "metric_name": "presented event rate",
    "metric_units": "events per 100 members of the denominator used",
    "assumptions": [
        "The supplied evidence object attests that the comparison denominator exists and is relevant.",
        "The supplied alternative denominator represents an authored presentation choice.",
        "Strength is the probability of choosing that alternative, implemented with the supplied uniform draw.",
        "The counted events are members of both supplied denominator populations.",
    ],
    "limitations": [
        "Synthetic process model; not empirically validated and not an NLP detector.",
        "A changed denominator or rate alone does not establish deception, error, or intent.",
        "The model cannot verify the truth or quality of supplied denominator evidence.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _positive_integer(context: dict, key: str, *, allow_zero: bool = False) -> int:
    value = context.get(key)
    lower_ok = value >= 0 if type(value) is int and allow_zero else value > 0 if type(value) is int else False
    if not lower_ok:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{key} must be a {qualifier} integer")
    return value


def _valid_uniform(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("uniform must be a finite number in [0, 1)")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value < 1.0:
        raise ValueError("uniform must be a finite number in [0, 1)")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Compute a rate under explicit alternative-denominator selection.

    At strength zero, the reference rule reports events per 100 using the
    documented relevant denominator. At positive strength, the authored
    alternative is selected exactly when the supplied uniform draw is below
    strength. Missing comparative evidence is rejected, never scored as zero.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    count = _positive_integer(context, "event_count", allow_zero=True)
    relevant = _positive_integer(context, "relevant_denominator")
    selected = _positive_integer(context, "selected_denominator")
    if count > relevant or count > selected:
        raise ValueError("event_count cannot exceed either denominator")

    evidence = context.get("denominator_evidence")
    if not isinstance(evidence, dict):
        raise ValueError("denominator_evidence must attest existence and relevance")
    if evidence.get("exists") is not True or evidence.get("relevant") is not True:
        raise ValueError("comparative denominator must be evidenced as existing and relevant")
    basis = evidence.get("basis")
    if not isinstance(basis, str) or not basis.strip():
        raise ValueError("denominator_evidence.basis must describe the comparative evidence")

    uniform = _valid_uniform(context.get("uniform"))
    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    steps = previous.get("steps_evaluated", 0)
    if type(steps) is not int or steps < 0:
        raise ValueError("state.steps_evaluated must be a non-negative integer")

    # The comparator is an explicit reference policy, not a claim of perfect
    # rationality: use the supported denominator unless the alternative is
    # actually selected by the authored-choice process.
    use_alternative = uniform < strength
    denominator_used = selected if use_alternative else relevant
    metric = (count / denominator_used) * 100.0
    active = use_alternative and selected != relevant
    if not math.isfinite(metric):  # defensive guard for the numeric interface
        raise ValueError("computed rate must be finite")

    next_state = dict(previous)
    next_state.update(
        {
            "steps_evaluated": steps + 1,
            "last_denominator_used": denominator_used,
            "last_rate_per_100": metric,
        }
    )
    trace = [
        f"Evidence attests a relevant denominator exists ({basis.strip()!r}); "
        f"event_count={count}, relevant_denominator={relevant}, "
        f"selected_denominator={selected}.",
        f"Selection rule: use selected_denominator iff uniform {uniform:g} < "
        f"strength {strength:g}; denominator_used={denominator_used}.",
        f"Metric = event_count / denominator_used * 100 = {metric:.12g} events per 100.",
        f"Active={active}; alternative selection changes the denominator only when it differs from the relevant reference.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    evidence = {
        "exists": True,
        "relevant": True,
        "basis": "provided cohort table identifies the comparison population",
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "event_count": 10,
                    "relevant_denominator": 100,
                    "selected_denominator": 20,
                    "denominator_evidence": dict(evidence),
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "event_count": 10,
                    "relevant_denominator": 100,
                    "selected_denominator": 100,
                    "denominator_evidence": dict(evidence),
                }
            ],
            "expectation": "equal",
        },
    ]
