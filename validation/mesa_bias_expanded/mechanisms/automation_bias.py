"""Illustrative, task-level automation-bias decision mechanism.

This is a synthetic decision process, not a detector or fitted psychological model.
"""
from __future__ import annotations

import math
from collections.abc import Mapping
from numbers import Real


# One half point is an explicit illustrative authority margin in task-score units.
# It represents how much modeled recommendation authority can sway a close choice.
_DEFERENCE_MARGIN = 0.5
_SCORE_MIN = 0.0
_SCORE_MAX = 100.0

METADATA = {
    "id": "automation_bias",
    "name": "Automation Bias",
    "kind": "cognitive_bias",
    "description": (
        "When an explicit independent check is available and contradicts an automated "
        "recommendation, recommendation authority adds a task-score bonus that can "
        "make the agent choose the inferior recommendation."
    ),
    "required_inputs": ["task_scores", "automation_recommendation", "verification_available"],
    "state_fields": ["decisions", "deference_overrides", "last_choice"],
    "metric_name": "selected_task_score",
    "metric_units": "synthetic task-score points on a 0-100 scale (higher is better)",
    "assumptions": [
        "task_scores are supplied synthetic outcome values; when verification_available is false they are evaluator-only and not used to choose",
        "the strength-scaled authority margin is 0.5 task-score points, an illustrative assumption rather than an empirical effect size",
        "strength is a generic intervention setting, not a probability or population prevalence",
        "ties are resolved by the option order in task_scores",
    ],
    "limitations": [
        "does not infer trust, intent, or bias from text or behavior",
        "models a single structured choice, not real-world human-computer interaction",
        "the verification flag and scores are stipulated scenario facts, not detected evidence",
        "not empirically validated; simulated outcomes cannot establish prevalence or causal effects",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Choose an option and report its supplied task score.

    Reference policy: use the highest task score when an independent verification
    check is available; otherwise use the automation recommendation. Under the
    necessary condition (available check plus recommendation contradicted by a
    strictly higher-scoring option), the mechanism adds
    ``strength * (best_score - recommendation_score + 0.5)`` to the
    recommendation's choice score. This can cause unjustified deference. The task
    metric remains the selected option's unadjusted score.
    """
    setting = _finite_number(strength, "strength")
    if not 0.0 <= setting <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    scores = context["task_scores"]
    if not isinstance(scores, Mapping) or len(scores) < 2:
        raise ValueError("task_scores must be a mapping with at least two options")
    checked_scores: dict[str, float] = {}
    for option, value in scores.items():
        if not isinstance(option, str) or not option:
            raise ValueError("task_scores option names must be non-empty strings")
        score = _finite_number(value, f"task_scores[{option!r}]")
        if not _SCORE_MIN <= score <= _SCORE_MAX:
            raise ValueError("task scores must be in [0, 100]")
        checked_scores[option] = score

    recommendation = context["automation_recommendation"]
    if not isinstance(recommendation, str) or recommendation not in checked_scores:
        raise ValueError("automation_recommendation must name an option in task_scores")
    verified = context["verification_available"]
    if type(verified) is not bool:
        raise ValueError("verification_available must be a bool")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    decisions = prior.get("decisions", 0)
    overrides = prior.get("deference_overrides", 0)
    if type(decisions) is not int or decisions < 0:
        raise ValueError("state.decisions must be a non-negative int")
    if type(overrides) is not int or overrides < 0 or overrides > decisions:
        raise ValueError("state.deference_overrides must be an int between 0 and decisions")
    last_choice = prior.get("last_choice")
    if last_choice is not None and (not isinstance(last_choice, str) or not last_choice):
        raise ValueError("state.last_choice must be None or a non-empty string")

    # This reference choice is intentional: without a usable check, the policy
    # defaults to the automated recommendation; with one, it selects the best score.
    if verified:
        baseline = max(checked_scores, key=checked_scores.get)
    else:
        baseline = recommendation

    chosen = baseline
    trace = [
        f"Reference policy selects {baseline!r} (verification_available={verified})."
    ]
    has_contradiction = verified and checked_scores[recommendation] < max(checked_scores.values())
    if has_contradiction and setting > 0:
        best_score = max(checked_scores.values())
        gap = best_score - checked_scores[recommendation]
        recommendation_choice_score = checked_scores[recommendation] + setting * (gap + _DEFERENCE_MARGIN)
        choice_scores = dict(checked_scores)
        choice_scores[recommendation] = recommendation_choice_score
        chosen = max(choice_scores, key=choice_scores.get)
        trace.append(
            "Independent check favors "
            f"{max(checked_scores, key=checked_scores.get)!r} ({best_score:g}); "
            f"recommendation {recommendation!r} scores {checked_scores[recommendation]:g}. "
            f"Authority-adjusted recommendation score = {checked_scores[recommendation]:g} "
            f"+ {setting:g} * ({gap:g} gap + {_DEFERENCE_MARGIN:g} margin) "
            f"= {recommendation_choice_score:g}; selected {chosen!r}."
        )
    elif has_contradiction:
        trace.append("Strength is zero: no authority bonus; reference choice is reproduced.")
    else:
        trace.append(
            "No necessary-condition contradiction: the recommendation is not inferior "
            "under an available check, or verification is unavailable; no bias adjustment."
        )

    active = chosen != baseline
    next_state = dict(prior)
    next_state.update(
        decisions=decisions + 1,
        deference_overrides=overrides + int(active),
        last_choice=chosen,
    )
    return {
        "metric": checked_scores[chosen],
        "active": active,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "task_scores": {"validated_option": 8.0, "automated_option": 7.5},
                    "automation_recommendation": "automated_option",
                    "verification_available": True,
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "task_scores": {"validated_option": 8.0, "automated_option": 7.5},
                    "automation_recommendation": "automated_option",
                    "verification_available": False,
                }
            ],
            "expectation": "equal",
        },
    ]
