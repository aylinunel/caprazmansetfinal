"""Illustrative, hypothetical evidence-selection model for cherry-picking.

This is a structured-input process model, not a text detector or an empirical
model of a person's motives.
"""
from copy import deepcopy
import math


METADATA = {
    "id": "cherry_picking",
    "name": "Cherry Picking (Seçmeci kanıt kullanımı)",
    "kind": "media_practice",
    "description": (
        "Models a limited-slot authored evidence presentation that can rank "
        "claim-supporting records ahead of limiting records."
    ),
    "required_inputs": ["evidence", "publication_slots"],
    "state_fields": [
        "last_presented_ids",
        "last_presented_dates",
        "last_support_share",
        "last_omitted_limiting_ids",
    ],
    "metric_name": "presented_support_share",
    "metric_units": "fraction of selected evidence records marked as supporting the stated claim (0 to 1)",
    "assumptions": [
        "Evidence direction (supports/limits), date, and relative relevance are supplied structured facts, not inferred.",
        "The reference publisher selects the publication_slots records with highest supplied relevance, breaking ties by input order.",
        "The illustrative strength parameter multiplies the ranking relevance of supporting evidence by (1 + strength) only when both supporting and limiting records exist.",
        "A fixed slot limit represents a presentation constraint; it is not itself evidence of deceptive intent.",
    ],
    "limitations": [
        "Hypothetical and not empirically validated; coefficients are illustrative, not measured effect sizes.",
        "Does not assess evidence quality, representativeness, truth, editorial justification, audience effects, or intent.",
        "Does not detect cherry-picking in natural-language or real-world media; all classifications and relevance values are supplied by the scenario.",
        "A rise in presented support share is a selection outcome, not proof that the resulting claim is false or misleading.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    evidence = context["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a non-empty list of records")
    normalized = []
    seen_ids = set()
    for index, record in enumerate(evidence):
        if not isinstance(record, dict):
            raise ValueError(f"evidence[{index}] must be a dict")
        for key in ("id", "date", "direction", "relevance"):
            if key not in record:
                raise ValueError(f"evidence[{index}] is missing {key!r}")
        item_id, date, direction = record["id"], record["date"], record["direction"]
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"evidence[{index}].id must be a non-empty string")
        if item_id in seen_ids:
            raise ValueError("evidence record ids must be unique")
        seen_ids.add(item_id)
        if not isinstance(date, str) or not date.strip():
            raise ValueError(f"evidence[{index}].date must be a non-empty string")
        if direction not in ("supports", "limits"):
            raise ValueError(f"evidence[{index}].direction must be 'supports' or 'limits'")
        relevance = _finite_number(record["relevance"], f"evidence[{index}].relevance")
        if not 0.0 <= relevance <= 1.0:
            raise ValueError(f"evidence[{index}].relevance must be in [0, 1]")
        normalized.append({
            "id": item_id,
            "date": date,
            "direction": direction,
            "relevance": relevance,
        })

    slots = context["publication_slots"]
    if isinstance(slots, bool) or not isinstance(slots, int):
        raise ValueError("publication_slots must be an integer")
    if not 1 <= slots <= len(normalized):
        raise ValueError("publication_slots must be between 1 and the evidence count")
    return normalized, slots


def evaluate(context: dict, strength: float) -> dict:
    """Select evidence for one hypothetical publication step.

    At strength zero, select by relevance alone (input order breaks ties). When
    supporting and limiting evidence both exist, strength reweights supporting
    records' relevance for slot ranking; it does not modify the evidence facts.
    """
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    evidence, slots = _validate_context(context)

    old_state = context.get("state", {})
    if not isinstance(old_state, dict):
        raise ValueError("state must be a dict when supplied")
    next_state = deepcopy(old_state)

    has_both_directions = (
        any(item["direction"] == "supports" for item in evidence)
        and any(item["direction"] == "limits" for item in evidence)
    )
    ranked = []
    for index, item in enumerate(evidence):
        support_weight = 1.0 + strength if has_both_directions and item["direction"] == "supports" else 1.0
        rank_score = item["relevance"] * support_weight
        ranked.append((rank_score, item["relevance"], index, item))
    selected = [row[3] for row in sorted(ranked, key=lambda row: (-row[0], -row[1], row[2]))[:slots]]
    selected_ids = [item["id"] for item in selected]
    selected_dates = [item["date"] for item in selected]
    support_count = sum(item["direction"] == "supports" for item in selected)
    metric = support_count / slots
    omitted_limiting = [
        item["id"] for item in evidence
        if item["direction"] == "limits" and item["id"] not in selected_ids
    ]

    # Explicit strength-zero reference: rank by supplied relevance only.
    reference = sorted(evidence, key=lambda item: (-item["relevance"], evidence.index(item)))[:slots]
    reference_ids = [item["id"] for item in reference]
    active = strength > 0.0 and selected_ids != reference_ids

    next_state.update({
        "last_presented_ids": selected_ids,
        "last_presented_dates": selected_dates,
        "last_support_share": metric,
        "last_omitted_limiting_ids": omitted_limiting,
    })
    trace = [
        "Ranked each record by supplied relevance; strength reweighting applies only when both directions exist: supporting score = relevance * (1 + strength), limiting score = relevance. Ties use relevance then input order.",
        f"Selected {selected_ids} on dates {selected_dates} for {slots} slot(s); {support_count}/{slots} selected records support the claim (metric={metric:.6g}).",
        f"Omitted limiting evidence ids: {omitted_limiting}. Reference selection at strength zero: {reference_ids}; active={active}.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "evidence": [
                    {"id": "s-2024-01", "date": "2024-01", "direction": "supports", "relevance": 0.80},
                    {"id": "s-2024-02", "date": "2024-02", "direction": "supports", "relevance": 0.70},
                    {"id": "l-2024-03", "date": "2024-03", "direction": "limits", "relevance": 0.95},
                    {"id": "l-2024-04", "date": "2024-04", "direction": "limits", "relevance": 0.85},
                ],
                "publication_slots": 2,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "evidence": [
                    {"id": "s-2024-05", "date": "2024-05", "direction": "supports", "relevance": 0.60},
                    {"id": "s-2024-06", "date": "2024-06", "direction": "supports", "relevance": 0.95},
                    {"id": "s-2024-07", "date": "2024-07", "direction": "supports", "relevance": 0.75},
                ],
                "publication_slots": 2,
            }],
            "expectation": "equal",
        },
    ]
