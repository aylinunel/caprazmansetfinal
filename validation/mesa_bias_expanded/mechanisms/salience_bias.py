"""Illustrative structured attention-allocation model for salience bias."""
from __future__ import annotations

from copy import deepcopy
import math
from numbers import Real
from typing import Any


METADATA = {
    "id": "salience_bias",
    "name": "Salience Bias",
    "kind": "cognitive_bias",
    "description": (
        "Allocates a finite attention budget using supplied diagnostic relevance, "
        "with relative excess prominence adding attraction to conspicuous evidence."
    ),
    "required_inputs": ["attention_items", "attention_budget"],
    "state_fields": ["attention_history", "last_attention_shares", "last_metric"],
    "metric_name": "relevance_weighted_attention_quality",
    "metric_units": "mean supplied relevance units (0-1) per attention unit",
    "assumptions": [
        "Each task supplies at least two evidence items with explicit relevance and prominence in [0, 1].",
        "The strength-scaled prominence attraction is proportional to the item's positive prominence excess over the package mean, multiplied by the highest supplied relevance.",
        "At strength zero, the reference allocates attention in proportion to supplied relevance; this is a task reference, not a claim of perfect rationality.",
        "Attention is divisible and the supplied budget is fully allocated; relevance and prominence are authored task facts, not inferred from text.",
        "Strength and the attraction equation are illustrative settings, not calibrated effect sizes or prevalence estimates.",
    ],
    "limitations": [
        "Synthetic process illustration only; no empirical validation, human validation, or detection accuracy is claimed.",
        "This models prominence-driven allocation only, not broader attentional bias arising from internal concerns.",
        "It does not infer visual prominence, diagnostic relevance, reader attention, or judgment from natural-language or image content.",
        "Continuous divisible attention and linear attraction omit task context, learning, cognitive limits, and benign reasons to inspect conspicuous evidence.",
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
    """Allocate this round's attention budget without mutating caller-owned data."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    items = context["attention_items"]
    if not isinstance(items, list) or len(items) < 2:
        raise ValueError("attention_items must be a list containing at least two evidence items")
    ids: list[str] = []
    relevances: list[float] = []
    prominences: list[float] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"attention_items[{index}] must be a dict")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"attention_items[{index}].id must be a non-empty string")
        for field in ("relevance", "prominence"):
            if field not in item:
                raise ValueError(f"attention_items[{index}] is missing {field} evidence")
        relevance = _finite_number(item["relevance"], f"attention_items[{index}].relevance")
        prominence = _finite_number(item["prominence"], f"attention_items[{index}].prominence")
        if not 0.0 <= relevance <= 1.0:
            raise ValueError("relevance scores must be in [0, 1]")
        if not 0.0 <= prominence <= 1.0:
            raise ValueError("prominence scores must be in [0, 1]")
        ids.append(item_id)
        relevances.append(relevance)
        prominences.append(prominence)
    if len(set(ids)) != len(ids):
        raise ValueError("evidence item ids must be unique")
    max_relevance = max(relevances)
    if max_relevance <= 0:
        raise ValueError("at least one evidence item must have positive relevance")

    budget = _finite_number(context["attention_budget"], "attention_budget")
    if budget <= 0:
        raise ValueError("attention_budget must be positive")

    mean_prominence = math.fsum(prominences) / len(prominences)
    # Positive relative prominence, rather than raw prominence, is the necessary
    # salience condition. Equal-prominence packages therefore exactly recover the
    # relevance-only reference, regardless of their common prominence level.
    weights = [
        relevance + s * max_relevance * max(0.0, prominence - mean_prominence)
        for relevance, prominence in zip(relevances, prominences)
    ]
    weight_sum = math.fsum(weights)
    if weight_sum <= 0 or not math.isfinite(weight_sum):
        raise ValueError("evidence produces no finite positive attention weights")
    shares = {item_id: weight / weight_sum for item_id, weight in zip(ids, weights)}
    allocations = {item_id: budget * share for item_id, share in shares.items()}
    # Compensate for floating point residue so the returned allocations sum to budget.
    allocations[ids[-1]] += budget - math.fsum(allocations.values())
    shares[ids[-1]] = allocations[ids[-1]] / budget
    metric = math.fsum(
        relevance * allocations[item_id] for item_id, relevance in zip(ids, relevances)
    ) / budget
    baseline_shares = {item_id: relevance / math.fsum(relevances) for item_id, relevance in zip(ids, relevances)}
    active = any(
        not math.isclose(shares[item_id], baseline_shares[item_id], rel_tol=1e-12, abs_tol=1e-12)
        for item_id in ids
    )

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    history = prior.get("attention_history", [])
    if not isinstance(history, list):
        raise ValueError("state.attention_history must be a list")
    next_state = deepcopy(prior)
    next_history = deepcopy(history)
    next_history.append({
        "shares": dict(shares),
        "metric": metric,
        "strength": s,
        "round_index": context.get("round_index", 0),
    })
    next_state.update({
        "attention_history": next_history,
        "last_attention_shares": dict(shares),
        "last_metric": metric,
    })
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            "For item i, attention_weight_i = relevance_i + strength * max(relevance) "
            "* max(0, prominence_i - mean(prominence)); attention shares normalize these weights.",
            f"Allocated {budget:g} attention units across {len(items)} items; relevance-weighted "
            f"quality={metric:.12g} versus relevance-only reference="
            f"{math.fsum(r * r for r in relevances) / math.fsum(relevances):.12g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "attention_items": [
                    {"id": "quiet_diagnostic", "relevance": 0.9, "prominence": 0.0},
                    {"id": "conspicuous_weak", "relevance": 0.1, "prominence": 1.0},
                ],
                "attention_budget": 10.0,
            }],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "attention_items": [
                    {"id": "item_a", "relevance": 0.9, "prominence": 0.7},
                    {"id": "item_b", "relevance": 0.1, "prominence": 0.7},
                ],
                "attention_budget": 10.0,
            }],
            "expectation": "equal",
        },
    ]
