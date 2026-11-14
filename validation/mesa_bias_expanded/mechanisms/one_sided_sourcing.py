"""Illustrative source-slot allocation model for one-sided sourcing.

This is a hypothetical editorial process model, not a text detector or empirical
model. Inputs must describe a reviewed full-story source inventory.
"""

from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "one_sided_sourcing",
    "name": "One-sided sourcing (Tek taraflı kaynak seçimi)",
    "kind": "media_practice",
    "description": (
        "Models a two-slot story editor reallocating a relevant counter-view slot "
        "to a second focus-side source when its quality advantage overcomes a "
        "strength-scaled viewpoint-diversity safeguard."
    ),
    "required_inputs": ["full_story_reviewed", "focus_side", "claims"],
    "state_fields": ["selected_source_ids", "represented_sides", "source_slots_filled", "one_sided_sourcing"],
    "metric_name": "one_sided_sourcing_indicator",
    "metric_units": "Per-story binary indicator: 1 if relevant counter-view evidence exists but no such side is selected; otherwise 0.",
    "assumptions": [
        "The caller supplies a complete, explicit source/claim inventory from the full story, not a short RSS excerpt.",
        "Each claim's relevance and evidence quality are supplied facts for this hypothetical task; neither is inferred from text.",
        "The story has two evidence slots and one declared editorial focus side.",
        "The diversity safeguard has illustrative utility weight 2.0 on a 0-to-1 quality scale; it is not a fitted effect size.",
        "Strength scales the safeguard and is an intervention setting, not prevalence or calibrated confidence.",
    ],
    "limitations": [
        "This compact process model cannot establish whether real journalism is one-sided, fair, or misleading.",
        "Source quality, claim relevance, story completeness, and editorial focus require explicit external annotation.",
        "No empirical validation or detection-accuracy measurement is claimed.",
        "A quality-based source-slot choice can have benign explanations, including space limits, verification differences, or story scope.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_SLOT_BUDGET = 2
_DIVERSITY_WEIGHT = 2.0


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _validate(context: dict, strength: float) -> tuple[list[dict], str, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    strength_value = _finite_number(strength, "strength")
    if not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    if context.get("full_story_reviewed") is not True:
        raise ValueError("full_story_reviewed must be True; excerpts cannot establish absent sourcing")
    focus_side = context.get("focus_side")
    if not isinstance(focus_side, str) or not focus_side.strip():
        raise ValueError("focus_side must be a non-empty string")
    raw_claims = context.get("claims")
    if not isinstance(raw_claims, list) or not raw_claims:
        raise ValueError("claims must be a non-empty full-story evidence inventory")

    claims: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_claims):
        if not isinstance(raw, dict):
            raise ValueError(f"claims[{index}] must be a dict")
        source_id = raw.get("source_id")
        side = raw.get("side")
        relevant = raw.get("relevant")
        quality = _finite_number(raw.get("quality"), f"claims[{index}].quality")
        if not isinstance(source_id, str) or not source_id.strip() or source_id in seen_ids:
            raise ValueError(f"claims[{index}].source_id must be a unique non-empty string")
        if not isinstance(side, str) or not side.strip():
            raise ValueError(f"claims[{index}].side must be a non-empty string")
        if type(relevant) is not bool:
            raise ValueError(f"claims[{index}].relevant must be bool")
        if not 0.0 <= quality <= 1.0:
            raise ValueError(f"claims[{index}].quality must be within [0, 1]")
        seen_ids.add(source_id)
        claims.append({"source_id": source_id, "side": side, "relevant": relevant, "quality": quality})

    eligible = [claim for claim in claims if claim["relevant"]]
    if not eligible:
        raise ValueError("at least one relevant claim is required to define a story evidence task")
    if not any(claim["side"] == focus_side for claim in eligible):
        raise ValueError("the reviewed inventory must contain relevant evidence for focus_side")
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    return eligible, focus_side, state


def _rank(claims: list[dict]) -> list[dict]:
    return sorted(claims, key=lambda claim: (-claim["quality"], claim["source_id"]))


def _select(eligible: list[dict], focus_side: str, strength: float) -> list[dict]:
    focus = _rank([claim for claim in eligible if claim["side"] == focus_side])
    counter = _rank([claim for claim in eligible if claim["side"] != focus_side])

    # Explicit strength-zero reference policy: when both viewpoints are present,
    # spend one slot on the strongest relevant claim from each; otherwise take
    # the two highest-quality relevant claims available.
    if not counter:
        return _rank(eligible)[:_SLOT_BUDGET]
    if len(focus) < 2:
        return [focus[0], counter[0]]

    # The competing two-slot allocations share the best focus-side source. The
    # second focus-side source displaces the best counter-view only when its
    # evidence-quality gain exceeds the remaining viewpoint-diversity utility.
    # On the bounded [0,1] quality scale, weight 2.0 guarantees the reference
    # allocation at strength zero; at higher strength the safeguard relaxes.
    gain = focus[1]["quality"] - counter[0]["quality"]
    remaining_diversity_utility = _DIVERSITY_WEIGHT * (1.0 - strength)
    if gain > remaining_diversity_utility:
        return focus[:_SLOT_BUDGET]
    return [focus[0], counter[0]]


def evaluate(context: dict, strength: float) -> dict:
    """Select two evidence sources and measure omission of a supplied counter-view."""
    eligible, focus_side, prior_state = _validate(context, strength)
    strength_value = float(strength)
    reference_selection = _select(eligible, focus_side, 0.0)
    selected = _select(eligible, focus_side, strength_value)
    counter_exists = any(claim["side"] != focus_side for claim in eligible)
    counter_selected = any(claim["side"] != focus_side for claim in selected)
    metric = float(counter_exists and not counter_selected)
    active = [claim["source_id"] for claim in selected] != [
        claim["source_id"] for claim in reference_selection
    ]

    # Copy, do not mutate the caller's state. The fields below describe the
    # current story's completed two-slot editorial choice.
    next_state = dict(prior_state)
    next_state.update(
        {
            "selected_source_ids": [claim["source_id"] for claim in selected],
            "represented_sides": sorted({claim["side"] for claim in selected}),
            "source_slots_filled": len(selected),
            "one_sided_sourcing": metric,
        }
    )
    if counter_exists:
        focus = _rank([claim for claim in eligible if claim["side"] == focus_side])
        counter = _rank([claim for claim in eligible if claim["side"] != focus_side])
        gain = focus[1]["quality"] - counter[0]["quality"] if len(focus) > 1 else None
        comparison = (
            f"second-focus quality gain {gain:.6g} versus remaining diversity utility "
            f"{_DIVERSITY_WEIGHT * (1.0 - strength_value):.6g}"
            if gain is not None
            else "fewer than two relevant focus-side claims; retain one counter-view slot"
        )
    else:
        comparison = "no relevant counter-view exists in the reviewed inventory"
    trace = [
        "Used only relevant claims from a caller-declared full-story inventory; no text or excerpt was classified.",
        f"Selected sources {next_state['selected_source_ids']} in a {_SLOT_BUDGET}-slot story; {comparison}.",
        f"Metric is 1 only when a relevant non-focus side exists and none is selected; active={active} means selected slots differ from the strength-zero coverage-first reference.",
    ]
    return {"metric": metric, "active": bool(active), "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "full_story_reviewed": True,
                    "focus_side": "policy_support",
                    "claims": [
                        {"source_id": "support_primary", "side": "policy_support", "relevant": True, "quality": 0.99},
                        {"source_id": "support_secondary", "side": "policy_support", "relevant": True, "quality": 0.95},
                        {"source_id": "opposition_primary", "side": "policy_opposition", "relevant": True, "quality": 0.30},
                    ],
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "full_story_reviewed": True,
                    "focus_side": "policy_support",
                    "claims": [
                        {"source_id": "support_primary", "side": "policy_support", "relevant": True, "quality": 0.9},
                        {"source_id": "support_secondary", "side": "policy_support", "relevant": True, "quality": 0.6},
                        {"source_id": "off_scope_opposition", "side": "policy_opposition", "relevant": False, "quality": 0.8},
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
