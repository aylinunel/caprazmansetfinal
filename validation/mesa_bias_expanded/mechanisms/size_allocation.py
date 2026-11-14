"""Illustrative, non-empirically-validated editorial size allocation policy."""
from __future__ import annotations

import math
from numbers import Real
from typing import Any


METADATA = {
    "id": "size_allocation",
    "name": "Size allocation",
    "kind": "media_practice",
    "description": (
        "Distributes a finite presentation budget by interpolating between equal "
        "shares and shares proportional to explicit editorial-priority scores."
    ),
    "required_inputs": ["stories", "focal_story_id", "total_units"],
    "state_fields": ["allocation_history", "last_allocations", "last_focal_story_id"],
    "metric_name": "focal_story_size",
    "metric_units": "presentation units (for example, words, seconds, or layout units)",
    "assumptions": [
        "Each story has a supplied, finite, nonnegative editorial_priority score; scores are relative within the current package.",
        "The total presentation budget is positive and is divided completely among the listed stories.",
        "Strength interpolates from an equal-share reference policy (0) to score-proportional allocation (1); it is not a calibrated effect size.",
        "Priority scores are authored inputs, not inferred from story text or validated judgments of public value.",
    ],
    "limitations": [
        "This is an illustrative allocation rule, not an empirical model of newsroom behavior or a detector of unfairness/bias.",
        "The spec supplies no annotation boundary; this implementation narrowly demonstrates size allocation conditional on explicit priority scores.",
        "The model omits format-specific constraints, editorial deliberation, audience effects, and potentially benign explanations for unequal size.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Allocate this round's finite size budget; no input or prior state is mutated."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    stories = context["stories"]
    if not isinstance(stories, list) or len(stories) < 2:
        raise ValueError("stories must be a list containing at least two stories")
    story_ids: list[str] = []
    scores: list[float] = []
    for index, story in enumerate(stories):
        if not isinstance(story, dict):
            raise ValueError(f"stories[{index}] must be a dict")
        if not isinstance(story.get("id"), str) or not story["id"].strip():
            raise ValueError(f"stories[{index}].id must be a non-empty string")
        if "editorial_priority" not in story:
            raise ValueError(f"stories[{index}] is missing editorial_priority evidence")
        score = _finite_number(story["editorial_priority"], f"stories[{index}].editorial_priority")
        if score < 0:
            raise ValueError("editorial_priority scores must be nonnegative")
        story_ids.append(story["id"])
        scores.append(score)
    if len(set(story_ids)) != len(story_ids):
        raise ValueError("story ids must be unique")
    score_sum = math.fsum(scores)
    if score_sum <= 0:
        raise ValueError("at least one editorial_priority score must be positive")

    focal_id = context["focal_story_id"]
    if not isinstance(focal_id, str) or focal_id not in story_ids:
        raise ValueError("focal_story_id must identify one of the supplied stories")
    budget = _finite_number(context["total_units"], "total_units")
    if budget <= 0:
        raise ValueError("total_units must be positive")

    n = len(stories)
    equal_share = budget / n
    allocations = {
        story_id: (1.0 - s) * equal_share + s * budget * score / score_sum
        for story_id, score in zip(story_ids, scores)
    }
    # Keep the returned package total exactly equal to budget up to floating point,
    # by assigning any rounding residue to the last listed story.
    allocations[story_ids[-1]] += budget - math.fsum(allocations.values())
    metric = allocations[focal_id]
    baseline = equal_share
    active = any(
        not math.isclose(allocation, baseline, rel_tol=1e-12, abs_tol=1e-12)
        for allocation in allocations.values()
    )

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    history = prior.get("allocation_history", [])
    if not isinstance(history, list):
        raise ValueError("state.allocation_history must be a list")
    # Copy the prior history and each record to avoid aliasing caller-owned state.
    copied_history = [dict(item) if isinstance(item, dict) else item for item in history]
    copied_history.append({"focal_story_id": focal_id, "focal_story_size": metric, "strength": s})
    next_state = {
        **prior,
        "allocation_history": copied_history,
        "last_allocations": dict(allocations),
        "last_focal_story_id": focal_id,
    }
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            "For each story i, allocation_i = (1-strength)*(total_units/n) "
            "+ strength*total_units*editorial_priority_i/sum(editorial_priority).",
            f"Used {n} stories, budget={budget:g} units, focal={focal_id!r}, "
            f"focal score={scores[story_ids.index(focal_id)]:g}, score sum={score_sum:g}; "
            f"focal allocation={metric:.12g} units versus equal-share reference={baseline:.12g} units.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "stories": [
                    {"id": "focal", "editorial_priority": 8},
                    {"id": "other_a", "editorial_priority": 2},
                    {"id": "other_b", "editorial_priority": 2},
                ],
                "focal_story_id": "focal",
                "total_units": 120,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "stories": [
                    {"id": "focal", "editorial_priority": 4},
                    {"id": "other_a", "editorial_priority": 4},
                    {"id": "other_b", "editorial_priority": 4},
                ],
                "focal_story_id": "focal",
                "total_units": 120,
            }],
            "expectation": "equal",
        },
    ]
