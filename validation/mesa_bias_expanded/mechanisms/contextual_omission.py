"""Illustrative reader-side model of comparison shifts from omitted context.

This is a structured-facts process model, not a text detector or empirical claim.
"""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any


METADATA = {
    "id": "contextual_omission",
    "name": "Contextual omission (Bağlam eksiltme)",
    "kind": "media_practice",
    "description": (
        "Models how a reader's comparison contrast shifts toward the presented contrast "
        "when accessible, relevant counter-evidence is absent from a presentation."
    ),
    "required_inputs": ["base_comparison", "full_text_available", "evidence"],
    "state_fields": [
        "comparison_history",
        "last_comparison",
        "cumulative_omitted_adjustment",
    ],
    "metric_name": "reader_comparison_contrast",
    "metric_units": "synthetic percentage-point contrast between the compared groups",
    "assumptions": [
        "base_comparison is the contrast calculated from the presented headline-level facts before contextual adjustments.",
        "Each evidence adjustment is a supplied, signed change to that contrast; only evidence explicitly marked accessible, relevant, and counter-evidence qualifies.",
        "Strength is the fraction of the full-text versus presented contrast gap that the modeled reader fails to recover; it is an illustrative setting, not a calibrated effect size.",
        "A complete, available full text and at least one accessible relevant context fact are required for this modeled comparison.",
        "The model does not infer author intent, factual truth, relevance, or counter-evidence from words. Those are explicit scenario inputs.",
    ],
    "limitations": [
        "This is a synthetic reader-side arithmetic model, not an NLP omission detector, psychological theory, or empirical estimate.",
        "It covers only signed contextual adjustments represented as structured facts and does not model ambiguity, competing interpretations, or context interactions.",
        "Omitting a fact can be benign compression or an editorial practice; the modeled contrast shift alone does not establish error, intent, or harm.",
        "A candidate without accessible full text and relevant counter-evidence cannot be evaluated by this mechanism.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one presented comparison without mutating inputs.

    Contrast equation:
      full = base + sum(qualifying context adjustments)
      presented = base + sum(adjustments for qualifying facts shown)
      reader = full - strength * (full - presented)

    Thus strength=0 is the explicit full-text reference policy. At strength=1,
    the reader reports the presented contrast. Only accessible, relevant facts
    explicitly identified as counter-evidence enter the contextual sum.
    """
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")

    required = ("base_comparison", "full_text_available", "evidence")
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    if context["full_text_available"] is not True:
        raise ValueError("full_text_available must be True; missing full text is not a zero metric")
    base = _finite_number(context["base_comparison"], "base_comparison")
    evidence = context["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a non-empty list of supplied full-text facts")

    seen_ids: set[str] = set()
    has_accessible_relevant_context = False
    full_adjustment = 0.0
    presented_adjustment = 0.0
    qualifying_ids: list[str] = []
    omitted_ids: list[str] = []
    for index, fact in enumerate(evidence):
        if not isinstance(fact, dict):
            raise ValueError(f"evidence[{index}] must be a dictionary")
        fact_required = ("id", "adjustment", "accessible", "relevant", "counter_evidence", "included")
        absent = [key for key in fact_required if key not in fact]
        if absent:
            raise ValueError(f"evidence[{index}] missing required field(s): {', '.join(absent)}")
        fact_id = fact["id"]
        if not isinstance(fact_id, str) or not fact_id.strip() or fact_id in seen_ids:
            raise ValueError(f"evidence[{index}].id must be a unique non-empty string")
        seen_ids.add(fact_id)
        adjustment = _finite_number(fact["adjustment"], f"evidence[{index}].adjustment")
        for flag in ("accessible", "relevant", "counter_evidence", "included"):
            if type(fact[flag]) is not bool:
                raise ValueError(f"evidence[{index}].{flag} must be a boolean")
        if fact["accessible"] and fact["relevant"]:
            has_accessible_relevant_context = True
        qualifies = fact["accessible"] and fact["relevant"] and fact["counter_evidence"]
        if qualifies:
            qualifying_ids.append(fact_id)
            full_adjustment += adjustment
            if fact["included"]:
                presented_adjustment += adjustment
            else:
                omitted_ids.append(fact_id)

    if not has_accessible_relevant_context:
        raise ValueError("no accessible relevant context fact was supplied; evidence is insufficient")

    full_contrast = base + full_adjustment
    presented_contrast = base + presented_adjustment
    omitted_adjustment = full_contrast - presented_contrast
    metric = full_contrast - s * omitted_adjustment
    if not all(math.isfinite(x) for x in (full_contrast, presented_contrast, omitted_adjustment, metric)):
        raise ValueError("computed contrast is not finite")

    old_state = context.get("state", {})
    if not isinstance(old_state, dict):
        raise ValueError("state must be a dictionary")
    old_history = old_state.get("comparison_history", [])
    if not isinstance(old_history, list) or any(not isinstance(item, dict) for item in old_history):
        raise ValueError("state.comparison_history must be a list of dictionaries")
    previous_cumulative = _finite_number(
        old_state.get("cumulative_omitted_adjustment", 0.0),
        "state.cumulative_omitted_adjustment",
    )
    round_index = context.get("round_index", len(old_history))
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError("round_index must be a non-negative integer")

    observation = {
        "round_index": round_index,
        "base_comparison": base,
        "full_text_comparison": full_contrast,
        "presented_comparison": presented_contrast,
        "reported_comparison": metric,
        "omitted_counter_evidence_ids": list(omitted_ids),
    }
    next_state = deepcopy(old_state)
    next_state["comparison_history"] = deepcopy(old_history) + [observation]
    next_state["last_comparison"] = metric
    next_state["cumulative_omitted_adjustment"] = previous_cumulative + omitted_adjustment
    if not math.isfinite(next_state["cumulative_omitted_adjustment"]):
        raise ValueError("cumulative omitted adjustment is not finite")

    active = bool(s > 0.0 and omitted_adjustment != 0.0)
    trace = [
        "Qualifying context facts: accessible=True, relevant=True, counter_evidence=True; "
        f"ids={qualifying_ids}; omitted ids={omitted_ids}.",
        f"Full-text contrast = base {base:g} + contextual adjustments {full_adjustment:g} = {full_contrast:g}.",
        f"Presented contrast = base {base:g} + included qualifying adjustments {presented_adjustment:g} = {presented_contrast:g}.",
        f"Reported contrast = full-text contrast - strength {s:g} * omitted adjustment {omitted_adjustment:g} = {metric:g}; strength zero is the full-text reference.",
        "A shift is a modeled presentation/reader effect only; it does not infer intent or establish that omission is harmful.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"comparison_history": [], "cumulative_omitted_adjustment": 0.0},
            "contexts": [
                {
                    "base_comparison": 12.0,
                    "full_text_available": True,
                    "evidence": [
                        {
                            "id": "denominator_context",
                            "adjustment": -8.0,
                            "accessible": True,
                            "relevant": True,
                            "counter_evidence": True,
                            "included": False,
                        }
                    ],
                }
            ],
            "expectation": "difference",
        },
        {
            "name": "boundary",
            "initial_state": {"comparison_history": [], "cumulative_omitted_adjustment": 0.0},
            "contexts": [
                {
                    "base_comparison": 12.0,
                    "full_text_available": True,
                    "evidence": [
                        {
                            "id": "supporting_context_only",
                            "adjustment": 0.0,
                            "accessible": True,
                            "relevant": True,
                            "counter_evidence": False,
                            "included": False,
                        }
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
