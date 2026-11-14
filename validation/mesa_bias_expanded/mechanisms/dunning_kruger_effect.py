"""Illustrative evidence-gated review allocation for a structured task batch.

This is a hypothetical process model, not a detector, diagnosis, or population
claim. See specs/dunning_kruger_effect_implementation.md.
"""
from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "dunning_kruger_effect",
    "name": "Dunning–Kruger Effect",
    "kind": "cognitive_bias",
    "description": (
        "In a structured review task, repeated low accuracy paired with "
        "confidence above accuracy can suppress review priority for "
        "high-confidence items, leaving more incorrect answers unreviewed."
    ),
    "required_inputs": ["items", "review_budget"],
    "state_fields": [
        "attempted", "correct_count", "confidence_sum", "error_count",
        "reviewed_error_count", "unreviewed_error_count", "last_reviewed_ids",
    ],
    "metric_name": "unreviewed_errors",
    "metric_units": "count of incorrect answers left unreviewed in this batch",
    "assumptions": [
        "Each item supplies an ID, objectively scored correctness, confidence in [0, 1], and positive review_value (the task's value of checking it).",
        "The reference review queue ranks review_value multiplied by (1-confidence), prioritizing consequential uncertain answers.",
        "Accuracy below 0.5 is an illustrative marker for low demonstrated task competence, not a psychological threshold.",
        "A user-set coefficient of 6.0 scales confidence-based suppression only when cumulative low accuracy and overestimation co-occur.",
        "Strength scales this assumed process and is neither a prevalence estimate nor a calibrated effect size.",
    ],
    "limitations": [
        "This synthetic allocation model is not empirically validated and makes no diagnostic or population-level claim.",
        "At least four scored attempts and two observed errors are required; task difficulty and noisy scoring can mimic the pattern.",
        "It does not infer competence, confidence, motives, or error awareness from text, disagreement, or a single anecdote.",
        "It assumes comparable tasks, reliable answer keys and confidence reports, an externally meaningful review_value, and a particular review policy.",
        "It omits feedback, learning, incentives, contextual calibration, and alternative metacognitive processes.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_SUPPRESSION_COEFFICIENT = 6.0
_STATE_DEFAULTS = {
    "attempted": 0,
    "correct_count": 0,
    "confidence_sum": 0.0,
    "error_count": 0,
    "reviewed_error_count": 0,
    "unreviewed_error_count": 0,
    "last_reviewed_ids": [],
}


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def _read_state(raw_state: Any) -> dict[str, Any]:
    if raw_state is None:
        raw_state = {}
    if not isinstance(raw_state, dict):
        raise ValueError("state must be a dict")
    state = dict(_STATE_DEFAULTS)
    for key in _STATE_DEFAULTS:
        if key in raw_state:
            state[key] = raw_state[key]
    for key in (
        "attempted", "correct_count", "error_count",
        "reviewed_error_count", "unreviewed_error_count",
    ):
        value = state[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{key} must be a non-negative integer")
    if state["correct_count"] + state["error_count"] != state["attempted"]:
        raise ValueError("state counts must sum to attempted")
    state["confidence_sum"] = _finite_number(state["confidence_sum"], "state.confidence_sum")
    if state["confidence_sum"] < 0 or state["confidence_sum"] > state["attempted"]:
        raise ValueError("state.confidence_sum must be between 0 and attempted")
    if not isinstance(state["last_reviewed_ids"], list) or any(
        not isinstance(item_id, str) for item_id in state["last_reviewed_ids"]
    ):
        raise ValueError("state.last_reviewed_ids must be a list of strings")
    return state


def evaluate(context: dict, strength: float) -> dict:
    """Rank a bounded review queue and count incorrect items it leaves behind."""
    factor = _finite_number(strength, "strength")
    if not 0.0 <= factor <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    items = context["items"]
    budget = context["review_budget"]
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    if isinstance(budget, bool) or not isinstance(budget, int) or not 0 <= budget <= len(items):
        raise ValueError("review_budget must be an integer between zero and item count")

    batch_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be a dict")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"items[{index}].id must be a non-empty string")
        if item_id in batch_ids:
            raise ValueError("item ids must be unique within a batch")
        batch_ids.add(item_id)
        correct = item.get("correct")
        if not isinstance(correct, bool):
            raise ValueError(f"items[{index}].correct must be bool")
        confidence = _finite_number(item.get("confidence"), f"items[{index}].confidence")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"items[{index}].confidence must be in [0, 1]")
        review_value = _finite_number(item.get("review_value"), f"items[{index}].review_value")
        if review_value <= 0.0:
            raise ValueError(f"items[{index}].review_value must be positive")
        normalized.append({
            "id": item_id, "correct": correct,
            "confidence": confidence, "review_value": review_value,
        })

    previous = _read_state(context.get("state", {}))
    batch_correct = sum(item["correct"] for item in normalized)
    batch_errors = len(normalized) - batch_correct
    attempted = previous["attempted"] + len(normalized)
    correct_count = previous["correct_count"] + batch_correct
    error_count = previous["error_count"] + batch_errors
    if attempted < 4 or error_count < 2:
        raise ValueError("at least four scored attempts and two observed errors are required")

    confidence_sum = previous["confidence_sum"] + sum(item["confidence"] for item in normalized)
    accuracy = correct_count / attempted
    mean_confidence = confidence_sum / attempted
    low_competence = max(0.0, (0.5 - accuracy) / 0.5)
    overestimation = max(0.0, mean_confidence - accuracy)
    gate = low_competence * overestimation

    def priority(item: dict[str, Any], amount: float) -> float:
        # The base score values consequential uncertainty. Under the joint
        # evidence gate, confidence suppresses that item's review priority.
        return item["review_value"] * (
            (1.0 - item["confidence"])
            - _SUPPRESSION_COEFFICIENT * amount * gate * item["confidence"]
        )

    baseline_order = sorted(normalized, key=lambda item: (-priority(item, 0.0), item["id"]))
    selected = sorted(normalized, key=lambda item: (-priority(item, factor), item["id"]))[:budget]
    baseline_ids = {item["id"] for item in baseline_order[:budget]}
    selected_ids = {item["id"] for item in selected}
    reviewed_errors = sum(
        not item["correct"] for item in normalized if item["id"] in selected_ids
    )
    unreviewed_errors = batch_errors - reviewed_errors

    next_state = dict(previous)
    next_state.update({
        "attempted": attempted,
        "correct_count": correct_count,
        "confidence_sum": confidence_sum,
        "error_count": error_count,
        "reviewed_error_count": previous["reviewed_error_count"] + reviewed_errors,
        "unreviewed_error_count": previous["unreviewed_error_count"] + unreviewed_errors,
        "last_reviewed_ids": sorted(selected_ids),
    })
    return {
        "metric": float(unreviewed_errors),
        "active": bool(factor > 0.0 and gate > 0.0 and selected_ids != baseline_ids),
        "state": next_state,
        "trace": [
            (
                f"Cumulative accuracy={accuracy:.6f}, mean confidence={mean_confidence:.6f}; "
                f"low_competence=max(0,(0.5-accuracy)/0.5)={low_competence:.6f}, "
                f"overestimation=max(0,mean_confidence-accuracy)={overestimation:.6f}, "
                f"gate=product={gate:.6f}. Review priority=review_value*((1-confidence) "
                f"-{_SUPPRESSION_COEFFICIENT:g}*strength*gate*confidence); selected the "
                f"highest-priority items up to review_budget. Metric counts incorrect current-batch "
                f"items not selected; strength=0 ranks review_value*(1-confidence). "
                f"Selected IDs={sorted(selected_ids)}."
            )
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "items": [
                    {"id": "err-critical", "correct": False, "confidence": 0.90, "review_value": 10.0},
                    {"id": "correct-uncertain", "correct": True, "confidence": 0.20, "review_value": 1.0},
                    {"id": "err-other-a", "correct": False, "confidence": 0.95, "review_value": 1.0},
                    {"id": "err-other-b", "correct": False, "confidence": 0.95, "review_value": 1.0},
                ],
                "review_budget": 1,
            }, {
                "items": [
                    {"id": "err-critical-next", "correct": False, "confidence": 0.90, "review_value": 10.0},
                    {"id": "correct-uncertain-next", "correct": True, "confidence": 0.20, "review_value": 1.0},
                ],
                "review_budget": 1,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "items": [
                    {"id": "right-a", "correct": True, "confidence": 0.80, "review_value": 1.0},
                    {"id": "right-b", "correct": True, "confidence": 0.70, "review_value": 1.0},
                    {"id": "right-c", "correct": True, "confidence": 0.85, "review_value": 1.0},
                    {"id": "err-a", "correct": False, "confidence": 0.40, "review_value": 1.0},
                    {"id": "err-b", "correct": False, "confidence": 0.45, "review_value": 1.0},
                ],
                "review_budget": 2,
            }, {
                "items": [
                    {"id": "right-next", "correct": True, "confidence": 0.80, "review_value": 1.0},
                    {"id": "err-next", "correct": False, "confidence": 0.40, "review_value": 1.0},
                ],
                "review_budget": 1,
            }],
            "expectation": "equal",
        },
    ]
