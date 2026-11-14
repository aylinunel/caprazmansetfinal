"""Illustrative structured model of perspective-skewed information selection.

This is a hypothetical media-presentation process, not a detector or empirical
model. It ranks supplied evidence for a fixed editorial package; it does not
invent or assess the truth of claims.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "commission_and_omission_of_information",
    "name": "Commission and omission of information",
    "kind": "media_practice",
    "description": (
        "Under a fixed publication capacity, rank supplied evidence by relevance "
        "and an explicit perspective-alignment preference; this can add items "
        "relative to a neutral package and leave other items out."
    ),
    "required_inputs": ["items", "capacity", "target_perspective", "bias_gain"],
    "state_fields": ["rounds", "cumulative_target_evidence", "last_presented_ids"],
    "metric_name": "target-oriented evidence in presented package",
    "metric_units": "signed evidence-weight units per round",
    "assumptions": [
        "Each supplied item is an already structured evidence unit with a unique id, a positive relevance/evidence weight, and stance +1 or -1 relative to a stated issue.",
        "An editor has a hard capacity and chooses items by the score documented below.",
        "The perspective preference and its bounded gain are hypothetical user-set parameters; strength is an intervention setting, not prevalence or calibrated confidence.",
        "The strength-zero comparator selects the most relevant items, with input order breaking ties.",
    ],
    "limitations": [
        "Models selection from supplied candidates only; it does not model fabricated content, truth, wording, audience inference, or exposure outside the package.",
        "The fixed-capacity score is a deliberately narrow illustrative operationalization, not a validated account of media practice or psychology.",
        "A selected-set difference is not by itself evidence of intent, harm, or bias in real-world reporting; relevance and space constraints may justify editorial choices.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        raise ValueError(f"{label} must be a finite number") from None
    if not math.isfinite(converted):
        raise ValueError(f"{label} must be a finite number")
    return converted


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    items = context["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")
    ids = set()
    normalized = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be a dict")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in ids:
            raise ValueError(f"items[{index}].id must be a unique non-empty string")
        ids.add(item_id)
        stance = item.get("stance")
        if isinstance(stance, bool) or not isinstance(stance, int) or stance not in (-1, 1):
            raise ValueError(f"items[{index}].stance must be -1 or +1")
        weight = _finite_number(item.get("evidence_weight"), f"items[{index}].evidence_weight")
        if weight <= 0:
            raise ValueError(f"items[{index}].evidence_weight must be positive")
        normalized.append({"id": item_id, "stance": int(stance), "evidence_weight": weight})

    capacity = context["capacity"]
    if isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= len(items):
        raise ValueError("capacity must be an integer from 1 through the number of items")
    target = context["target_perspective"]
    if isinstance(target, bool) or not isinstance(target, int) or target not in (-1, 1):
        raise ValueError("target_perspective must be -1 or +1")
    gain = _finite_number(context["bias_gain"], "bias_gain")
    if not 0 <= gain <= 1:
        raise ValueError("bias_gain must be in [0, 1]")

    return normalized, capacity, int(target), gain


def _validated_state(state):
    if not isinstance(state, dict):
        raise ValueError("context['state'] must be a dict")
    rounds = state.get("rounds", 0)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds must be a non-negative integer")
    cumulative = _finite_number(state.get("cumulative_target_evidence", 0.0), "state.cumulative_target_evidence")
    previous_ids = state.get("last_presented_ids", [])
    if not isinstance(previous_ids, list) or any(not isinstance(x, str) for x in previous_ids):
        raise ValueError("state.last_presented_ids must be a list of strings")
    return rounds, cumulative


def evaluate(context: dict, strength: float) -> dict:
    """Select a capacity-limited evidence package and return its signed metric."""
    strength_value = _finite_number(strength, "strength")
    if not 0 <= strength_value <= 1:
        raise ValueError("strength must be in [0, 1]")

    items, capacity, target, gain = _validate_context(context)
    if "state" not in context:
        raise ValueError("missing required reserved input: state")
    rounds, cumulative = _validated_state(context["state"])

    # The reference ranks on weight alone. The illustrative mechanism boosts
    # evidence aligned with the explicit target, while retaining a floor of zero
    # for every item's ranking multiplier because gain is bounded by one.
    reference = sorted(items, key=lambda item: -item["evidence_weight"])[:capacity]
    scored = sorted(
        items,
        key=lambda item: -item["evidence_weight"]
        * (1.0 + strength_value * gain * target * item["stance"]),
    )
    selected = scored[:capacity]
    selected_ids = [item["id"] for item in selected]
    reference_ids = [item["id"] for item in reference]
    selected_set, reference_set = set(selected_ids), set(reference_ids)
    commissioned = [item_id for item_id in selected_ids if item_id not in reference_set]
    omitted = [item_id for item_id in reference_ids if item_id not in selected_set]
    metric = sum(item["evidence_weight"] * target * item["stance"] for item in selected)
    if not math.isfinite(metric):
        raise ValueError("presented evidence produces a non-finite metric")
    cumulative_next = cumulative + metric
    if not math.isfinite(cumulative_next):
        raise ValueError("updated cumulative_target_evidence must remain finite")

    next_state = deepcopy(context["state"])
    next_state.update(
        {
            "rounds": rounds + 1,
            "cumulative_target_evidence": cumulative_next,
            "last_presented_ids": list(selected_ids),
        }
    )
    return {
        "metric": float(metric),
        "active": selected_ids != reference_ids,
        "state": next_state,
        "trace": [
            "Reference package: rank by evidence_weight descending; ties retain input order. "
            "Mechanism score: evidence_weight * (1 + strength * bias_gain * "
            "target_perspective * stance); rank descending, ties retain input order. "
            f"capacity={capacity}, target={target}, strength={strength_value}, gain={gain}.",
            f"reference_ids={reference_ids}; presented_ids={selected_ids}.",
            f"relative_commission_ids={commissioned}; relative_omission_ids={omitted}; "
            f"metric=sum(weight * target * stance for presented items)={metric}.",
        ],
    }


def scenarios() -> list[dict]:
    """Return a positive selective-package example and its boundary control."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "items": [
                        {"id": "support_high", "stance": 1, "evidence_weight": 1.0},
                        {"id": "support_low", "stance": 1, "evidence_weight": 0.9},
                        {"id": "counter_high", "stance": -1, "evidence_weight": 1.2},
                    ],
                    "capacity": 2,
                    "target_perspective": 1,
                    "bias_gain": 0.75,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "items": [
                        {"id": "support_high", "stance": 1, "evidence_weight": 1.0},
                        {"id": "support_mid", "stance": 1, "evidence_weight": 0.9},
                        {"id": "support_low", "stance": 1, "evidence_weight": 0.6},
                    ],
                    "capacity": 2,
                    "target_perspective": 1,
                    "bias_gain": 0.75,
                }
            ],
            "expectation": "equal",
        },
    ]
