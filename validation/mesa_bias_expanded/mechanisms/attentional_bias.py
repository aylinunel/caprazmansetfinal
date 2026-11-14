"""Illustrative attention-allocation model for the attentional_bias concept.

This is a hypothetical process model, not a detector or empirically fitted account.
"""

from __future__ import annotations

import math
from numbers import Real
from typing import Any


METADATA = {
    "id": "attentional_bias",
    "name": "Attentional Bias",
    "kind": "cognitive_bias",
    "description": (
        "Selects one item from a supplied display by blending task relevance with "
        "its explicit attentional-capture value; this models selection, not later judgment."
    ),
    "required_inputs": ["stimuli"],
    "state_fields": ["last_attended_id", "attention_history"],
    "metric_name": "attended_task_relevance",
    "metric_units": "unitless relevance of the selected item, on the supplied 0–1 scale",
    "assumptions": [
        "Each display offers one attention slot and the supplied relevance and capture values are meaningful on a common 0–1 scale.",
        "Strength linearly interpolates between a relevance-only reference policy and capture-weighted selection; it is not a calibrated psychological quantity.",
        "Ties are resolved by input order, which is an explicit deterministic convention.",
    ],
    "limitations": [
        "The supplied structured values are hypothetical inputs; this does not infer attention from text, images, or people.",
        "One-item selection omits divided attention, changing salience, task goals, memory, and individual differences.",
        "Attending to a high-capture item can be useful when that item is relevant; the mechanism is not inherently harmful.",
        "No empirical validation or detection accuracy is claimed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def _validate_stimuli(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError("stimuli must be a list containing at least two items")

    checked: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, stimulus in enumerate(value):
        if not isinstance(stimulus, dict):
            raise ValueError(f"stimuli[{index}] must be an object")
        missing = {"id", "relevance", "capture"} - stimulus.keys()
        if missing:
            raise ValueError(f"stimuli[{index}] missing required fields: {sorted(missing)}")
        item_id = stimulus["id"]
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"stimuli[{index}].id must be a non-empty string")
        if item_id in seen_ids:
            raise ValueError("stimulus ids must be unique")
        seen_ids.add(item_id)
        checked.append({
            "id": item_id,
            "relevance": _unit_interval(stimulus["relevance"], f"stimuli[{index}].relevance"),
            "capture": _unit_interval(stimulus["capture"], f"stimuli[{index}].capture"),
        })

    if not any(item["relevance"] > 0.0 for item in checked):
        raise ValueError("stimuli must contain some task-relevant information")
    return checked


def evaluate(context: dict, strength: float) -> dict:
    """Allocate one attention slot; caller-owned context/state is never mutated."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if "stimuli" not in context:
        raise ValueError("missing required input: stimuli")
    stimuli = _validate_stimuli(context["stimuli"])

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dictionary")
    old_history = prior.get("attention_history", [])
    if not isinstance(old_history, list):
        raise ValueError("state.attention_history must be a list")

    # The explicit strength-zero reference attends to the item with greatest
    # task relevance (first item wins ties), not a claim of globally optimality.
    reference = max(stimuli, key=lambda item: item["relevance"])
    # Capture competes with relevance: s=0 gives relevance-only selection;
    # at s>0 the item score is (1-s)*relevance + s*capture.
    scored = [
        ((1.0 - strength) * item["relevance"] + strength * item["capture"], index, item)
        for index, item in enumerate(stimuli)
    ]
    _, _, attended = max(scored, key=lambda entry: (entry[0], -entry[1]))
    active = attended["id"] != reference["id"]

    # Copy the list and records so even nested caller state stays untouched.
    history = [dict(record) if isinstance(record, dict) else record for record in old_history]
    round_index = context.get("round_index", len(history))
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError("round_index must be a non-negative integer")
    history.append({
        "round_index": round_index,
        "attended_id": attended["id"],
        "reference_id": reference["id"],
        "attended_relevance": attended["relevance"],
    })
    next_state = dict(prior)
    next_state.update({"last_attended_id": attended["id"], "attention_history": history})

    return {
        "metric": attended["relevance"],
        "active": active,
        "state": next_state,
        "trace": [
            "For each supplied item, score=(1-strength)*relevance + strength*capture; "
            "select the greatest score (input order breaks ties). The strength-zero "
            f"reference selects maximum relevance ({reference['id']}); selected "
            f"{attended['id']} with relevance {attended['relevance']:.6g}. "
            f"Attention selection differs from reference: {str(active).lower()}."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "stimuli": [
                    {"id": "relevant_detail", "relevance": 1.0, "capture": 0.0},
                    {"id": "salient_distractor", "relevance": 0.4, "capture": 1.0},
                ]
            }],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "stimuli": [
                    {"id": "relevant_detail", "relevance": 1.0, "capture": 0.5},
                    {"id": "less_relevant_detail", "relevance": 0.4, "capture": 0.5},
                ]
            }],
            "expectation": "equal",
        },
    ]
