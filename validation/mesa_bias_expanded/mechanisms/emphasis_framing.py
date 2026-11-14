"""Illustrative attention-allocation process for emphasis framing.

This is a synthetic process model, not a detector or empirical claim.
"""
from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "emphasis_framing",
    "name": "Emphasis framing (Vurgu çerçevelemesi)",
    "kind": "media_practice",
    "description": (
        "When a headline foregrounds a dimension that is less prominent in the supplied "
        "body presentation of the same structured fact, shift a bounded share of modeled "
        "reader attention toward that dimension. Different emphasis alone is not an error."
    ),
    "required_inputs": ["fact_id", "dimensions", "headline_focus"],
    "state_fields": ["last_attention_shares", "exposure_count", "cumulative_headline_attention"],
    "metric_name": "headline_focus_attention_share",
    "metric_units": "fraction of modeled reader attention, from 0 to 1",
    "assumptions": [
        "Each supplied fact_id denotes one fact with at least two commensurable dimensions.",
        "body_prominence values are nonnegative authored-presentation weights; they are normalized to form the reference attention allocation.",
        "At nonzero strength, a headline/body prominence mismatch transfers strength times the prominence gap in attention mass from the other dimensions to the headline focus.",
        "Strength is an illustrative intervention setting, not an effect-size estimate or prevalence.",
    ],
    "limitations": [
        "The model assumes attention follows supplied prominence and does not model language, images, audience differences, comprehension, beliefs, or downstream decisions.",
        "A discrepancy can be benign, editorially appropriate, or useful; this model makes no claim about error, deception, or intent.",
        "Structured inputs and simulated attention are hypothetical and have not been empirically validated; this is not an NLP detector.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    if minimum is not None and number < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    return number


def _validate_context(context: dict) -> tuple[str, list[dict], str, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required input: {key}")
    fact_id = context["fact_id"]
    if not isinstance(fact_id, str) or not fact_id.strip():
        raise ValueError("fact_id must be a nonempty string identifying the same fact")
    dimensions = context["dimensions"]
    if not isinstance(dimensions, list) or len(dimensions) < 2:
        raise ValueError("dimensions must contain at least two structured fact dimensions")
    clean_dimensions = []
    seen = set()
    for index, item in enumerate(dimensions):
        if not isinstance(item, dict):
            raise ValueError(f"dimensions[{index}] must be a dict")
        dim_id = item.get("id")
        if not isinstance(dim_id, str) or not dim_id.strip() or dim_id in seen:
            raise ValueError("dimension ids must be nonempty and unique")
        seen.add(dim_id)
        if "value" not in item:
            raise ValueError(f"dimensions[{index}] is missing its supplied fact value")
        value = _finite_number(item["value"], f"dimensions[{index}].value")
        if "body_prominence" not in item:
            raise ValueError(f"dimensions[{index}] is missing body_prominence evidence")
        prominence = _finite_number(
            item["body_prominence"], f"dimensions[{index}].body_prominence", minimum=0.0
        )
        clean_dimensions.append({"id": dim_id, "value": value, "body_prominence": prominence})
    if not any(item["body_prominence"] > 0 for item in clean_dimensions):
        raise ValueError("body_prominence evidence must have a positive total")
    focus = context["headline_focus"]
    if not isinstance(focus, str) or focus not in seen:
        raise ValueError("headline_focus must identify one supplied fact dimension")
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    return fact_id, clean_dimensions, focus, state


def _prior_state(state: dict) -> tuple[int, float, dict]:
    count = state.get("exposure_count", 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.exposure_count must be a nonnegative integer")
    cumulative = _finite_number(
        state.get("cumulative_headline_attention", 0.0),
        "state.cumulative_headline_attention",
        minimum=0.0,
    )
    if cumulative > count + 1e-12:
        raise ValueError("state cumulative attention cannot exceed exposure_count")
    previous = state.get("last_attention_shares", {})
    if not isinstance(previous, dict):
        raise ValueError("state.last_attention_shares must be a dict")
    clean_previous = {}
    for key, value in previous.items():
        if not isinstance(key, str):
            raise ValueError("state attention dimension ids must be strings")
        clean_previous[key] = _finite_number(value, f"state.last_attention_shares[{key!r}]", minimum=0.0)
    if clean_previous and abs(sum(clean_previous.values()) - 1.0) > 1e-9:
        raise ValueError("state.last_attention_shares must sum to 1")
    return count, cumulative, clean_previous


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one presentation exposure without mutating inputs."""
    strength = _finite_number(strength, "strength", minimum=0.0)
    if strength > 1.0:
        raise ValueError("strength must be within [0, 1]")
    fact_id, dimensions, focus, incoming_state = _validate_context(context)
    count, cumulative, _previous = _prior_state(incoming_state)

    total = sum(item["body_prominence"] for item in dimensions)
    reference = {item["id"]: item["body_prominence"] / total for item in dimensions}
    focus_share = reference[focus]
    greatest_share = max(reference.values())
    # A necessary condition is a headline/body emphasis discrepancy: the headline
    # selects a dimension less prominent in the body than at least one alternative.
    gap = greatest_share - focus_share
    adjusted = dict(reference)
    if gap > 0.0 and strength > 0.0:
        transfer = strength * gap
        other_mass = 1.0 - focus_share
        if other_mass <= 0.0:  # defensive; impossible when gap is positive
            raise ValueError("inconsistent prominence evidence for headline focus")
        adjusted[focus] += transfer
        scale = (other_mass - transfer) / other_mass
        for dim_id in adjusted:
            if dim_id != focus:
                adjusted[dim_id] *= scale

    metric = adjusted[focus]
    active = any(abs(adjusted[key] - reference[key]) > 1e-15 for key in reference)
    next_state = {
        "last_attention_shares": dict(adjusted),
        "exposure_count": count + 1,
        "cumulative_headline_attention": cumulative + metric,
    }
    trace = [
        f"fact_id={fact_id!r}; normalized body_prominence gives reference attention={reference!r}.",
        f"headline_focus={focus!r}; prominence gap=max(reference)-focus_share={gap:.12g}; strength={strength:.12g}.",
        (
            "If gap>0, transfer strength*gap attention mass from non-focus dimensions "
            "proportionally to headline_focus; otherwise retain reference exactly. "
            f"Metric={metric:.12g}; active={active}."
        ),
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    positive = {
        "fact_id": "quarterly_outcome_A",
        "dimensions": [
            {"id": "revenue_growth", "value": 12.0, "body_prominence": 0.2},
            {"id": "operating_cost", "value": 4.0, "body_prominence": 0.8},
        ],
        "headline_focus": "revenue_growth",
    }
    boundary = {
        "fact_id": "quarterly_outcome_B",
        "dimensions": [
            {"id": "revenue_growth", "value": 12.0, "body_prominence": 0.7},
            {"id": "operating_cost", "value": 4.0, "body_prominence": 0.3},
        ],
        "headline_focus": "revenue_growth",
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
