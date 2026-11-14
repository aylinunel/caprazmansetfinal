"""Illustrative model of authored story prominence and reader attention allocation.

This is a synthetic process model, not an empirical estimate or detector.
"""

from __future__ import annotations

import math
from typing import Any


_CONTENT_SENSITIVITY = 4.0
_PLACEMENT_SENSITIVITY = 4.0

METADATA = {
    "id": "story_placement",
    "name": "Story placement",
    "kind": "media_practice",
    "description": (
        "Models how supplied authored prominence ratings combine with content-based "
        "utility to allocate simulated reader attention across stories."
    ),
    "required_inputs": ["stories", "focal_story_id"],
    "state_fields": ["steps", "cumulative_focal_attention", "last_attention_shares"],
    "metric_name": "focal_story_attention_share",
    "metric_units": "fraction of one round's simulated reader attention (0 to 1)",
    "assumptions": [
        "Each story has an explicit content_importance and authored placement_prominence in [0, 1].",
        "Attention share follows a softmax allocation over content utility plus a placement cue.",
        "Illustrative sensitivities are fixed model choices, not fitted effect sizes.",
        "Strength controls the placement-cue contribution; strength zero is content-only.",
    ],
    "limitations": [
        "Synthetic structured-input model only; it does not inspect or classify real media.",
        "Does not model readership heterogeneity, editorial intent, exposure duration, or causal effects.",
        "Prominent placement can be justified or beneficial; a modeled attention shift is not inherently an error.",
        "No empirical validation or detection-accuracy measurement is claimed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    return result


def _validate_context(context: dict) -> tuple[list[dict], str]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    stories = context.get("stories")
    if not isinstance(stories, list) or len(stories) < 2:
        raise ValueError("stories must contain at least two structured stories")
    cleaned = []
    seen = set()
    for index, story in enumerate(stories):
        if not isinstance(story, dict):
            raise ValueError(f"stories[{index}] must be a dict")
        story_id = story.get("id")
        if not isinstance(story_id, str) or not story_id.strip() or story_id in seen:
            raise ValueError("each story must have a unique non-empty string id")
        seen.add(story_id)
        cleaned.append({
            "id": story_id,
            "content_importance": _unit_interval(
                story.get("content_importance"), f"stories[{index}].content_importance"
            ),
            "placement_prominence": _unit_interval(
                story.get("placement_prominence"), f"stories[{index}].placement_prominence"
            ),
        })
    focal = context.get("focal_story_id")
    if not isinstance(focal, str) or focal not in seen:
        raise ValueError("focal_story_id must identify one of the supplied stories")
    return cleaned, focal


def _attention_shares(stories: list[dict], strength: float) -> dict[str, float]:
    """Normalize exp(4*content + 4*strength*prominence) using stable softmax."""
    logits = [
        _CONTENT_SENSITIVITY * story["content_importance"]
        + _PLACEMENT_SENSITIVITY * strength * story["placement_prominence"]
        for story in stories
    ]
    peak = max(logits)
    weights = [math.exp(value - peak) for value in logits]
    total = sum(weights)
    return {story["id"]: weight / total for story, weight in zip(stories, weights)}


def _prior_state(context: dict) -> tuple[int, float]:
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    steps = state.get("steps", 0)
    cumulative = state.get("cumulative_focal_attention", 0.0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    if isinstance(cumulative, bool) or not isinstance(cumulative, (int, float)):
        raise ValueError("state.cumulative_focal_attention must be finite and non-negative")
    cumulative = float(cumulative)
    if not math.isfinite(cumulative) or cumulative < 0.0:
        raise ValueError("state.cumulative_focal_attention must be finite and non-negative")
    return steps, cumulative


def evaluate(context: dict, strength: float) -> dict:
    """Return the focal story's simulated attention share for one round."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    stories, focal = _validate_context(context)
    previous_steps, previous_total = _prior_state(context)
    shares = _attention_shares(stories, strength)
    metric = shares[focal]
    # A common prominence offset cancels from softmax. Only relative placement
    # prominence can change the content-only allocation in this round.
    placement_varies = len({story["placement_prominence"] for story in stories}) > 1
    active = bool(strength > 0.0 and placement_varies)
    return {
        "metric": metric,
        "active": active,
        "state": {
            "steps": previous_steps + 1,
            "cumulative_focal_attention": previous_total + metric,
            "last_attention_shares": dict(shares),
        },
        "trace": [
            "For each supplied story, logit = 4*content_importance + "
            f"4*{strength:g}*placement_prominence; stable softmax gives attention shares.",
            f"Focal story {focal!r} receives share {metric:.12g}; strength-zero reference "
            "uses the same softmax with placement contribution zero.",
            "The placement cue changes the allocation only when supplied prominence "
            "ratings differ; this media practice is not classified as inherently harmful.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "stories": [
                    {"id": "content_lead", "content_importance": 0.9, "placement_prominence": 0.0},
                    {"id": "promoted", "content_importance": 0.2, "placement_prominence": 1.0},
                ],
                "focal_story_id": "promoted",
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "stories": [
                    {"id": "a", "content_importance": 0.8, "placement_prominence": 0.5},
                    {"id": "b", "content_importance": 0.3, "placement_prominence": 0.5},
                ],
                "focal_story_id": "b",
            }],
            "expectation": "equal",
        },
    ]
