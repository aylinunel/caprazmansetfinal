"""Illustrative source-selection process: allocate a limited source budget by view."""
from __future__ import annotations

import copy
import math
from typing import Any


METADATA = {
    "id": "source_selection",
    "name": "Source selection",
    "kind": "media_practice",
    "description": (
        "A structured editorial source-allocation process increasingly favors sources "
        "whose stated view supports a designated target view, when eligible alternatives exist."
    ),
    "required_inputs": ["sources", "target_view", "selection_budget"],
    "state_fields": ["rounds", "selected_source_ids_by_round", "last_metric"],
    "metric_name": "target_view_share",
    "metric_units": "Fraction of selected eligible sources whose view equals target_view (0 to 1).",
    "assumptions": [
        "Each source has a supplied view label and eligibility flag; the model does not infer either from text.",
        "The strength parameter multiplies the allocation weight for target-view sources by (1 + 4*strength).",
        "The strength-zero reference allocates source slots in proportion to the number of eligible sources in target and alternative groups.",
        "When rounded weighted quotas exceed group capacity, unfilled slots go to remaining alternative capacity, then target capacity.",
        "Source order breaks ties within each group; the process is a hypothetical editorial selection rule, not an estimate of human behavior.",
    ],
    "limitations": [
        "Structured view labels and eligibility are assumed rather than detected or validated.",
        "The binary target-versus-alternative grouping collapses all non-target views together and does not model source quality, independence, or relevance.",
        "Coefficients and quota rounding are illustrative choices, not empirically fitted effects.",
        "This module does not distinguish deliberate one-sided sourcing from benign task constraints unless those constraints are represented in eligibility and the supplied roster.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _validate(context: dict[str, Any], strength: float) -> tuple[list[dict[str, Any]], str, int]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    if strength < 0 or strength > 1:
        raise ValueError("strength must be a finite number in [0, 1]")
    try:
        finite_strength = math.isfinite(float(strength))
    except (OverflowError, TypeError, ValueError):
        finite_strength = False
    if not finite_strength:
        raise ValueError("strength must be a finite number in [0, 1]")
    for key in ("sources", "target_view", "selection_budget"):
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    sources = context["sources"]
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources must be a non-empty list of source records")
    seen: set[str] = set()
    clean_sources: list[dict[str, Any]] = []
    for i, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{i}] must be a dict")
        source_id, view, eligible = source.get("source_id"), source.get("view"), source.get("eligible")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"sources[{i}].source_id must be a non-empty string")
        if source_id in seen:
            raise ValueError("source_id values must be unique")
        seen.add(source_id)
        if not isinstance(view, str) or not view.strip():
            raise ValueError(f"sources[{i}].view must be a non-empty string")
        if not isinstance(eligible, bool):
            raise ValueError(f"sources[{i}].eligible must be bool")
        clean_sources.append({"source_id": source_id, "view": view, "eligible": eligible})

    target = context["target_view"]
    if not isinstance(target, str) or not target.strip():
        raise ValueError("target_view must be a non-empty string")
    budget = context["selection_budget"]
    if isinstance(budget, bool) or not isinstance(budget, int) or budget <= 0:
        raise ValueError("selection_budget must be a positive integer")
    eligible_sources = [source for source in clean_sources if source["eligible"]]
    if not eligible_sources:
        raise ValueError("at least one eligible source is required; missing evidence is not a zero metric")
    return eligible_sources, target, budget


def _quota(target_count: int, alternative_count: int, slots: int, strength: float) -> int:
    """Return rounded target-group allocation under weighted proportional quotas."""
    if alternative_count == 0:
        return slots
    if target_count == 0:
        return 0
    target_weight = target_count * (1.0 + 4.0 * strength)
    alternative_weight = float(alternative_count)
    raw = slots * target_weight / (target_weight + alternative_weight)
    return min(target_count, max(0, math.floor(raw + 0.5)))


def _select(eligible_sources: list[dict[str, Any]], target: str, budget: int, strength: float) -> list[str]:
    targets = [s["source_id"] for s in eligible_sources if s["view"] == target]
    alternatives = [s["source_id"] for s in eligible_sources if s["view"] != target]
    slots = min(budget, len(eligible_sources))
    target_slots = _quota(len(targets), len(alternatives), slots, strength)
    alternative_slots = slots - target_slots

    # With rounding plus capacity limits, fill any residual slots deterministically.
    alternative_slots = min(alternative_slots, len(alternatives))
    target_slots = min(slots - alternative_slots, len(targets))
    residual = slots - target_slots - alternative_slots
    add_alternative = min(residual, len(alternatives) - alternative_slots)
    alternative_slots += add_alternative
    residual -= add_alternative
    target_slots += min(residual, len(targets) - target_slots)
    return targets[:target_slots] + alternatives[:alternative_slots]


def _state_from_context(context: dict[str, Any]) -> dict[str, Any]:
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    result = copy.deepcopy(state)
    rounds = result.get("rounds", 0)
    history = result.get("selected_source_ids_by_round", [])
    last_metric = result.get("last_metric", None)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds must be a non-negative integer")
    if not isinstance(history, list) or any(not isinstance(row, list) for row in history):
        raise ValueError("state.selected_source_ids_by_round must be a list of lists")
    if last_metric is not None and (
        isinstance(last_metric, bool) or not isinstance(last_metric, (int, float)) or not math.isfinite(last_metric)
    ):
        raise ValueError("state.last_metric must be finite numeric or None")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Select a finite source set under a weighted view-allocation rule."""
    eligible, target, budget = _validate(context, strength)
    state = _state_from_context(context)
    selected = _select(eligible, target, budget, float(strength))
    reference = _select(eligible, target, budget, 0.0)
    support_count = sum(1 for s in eligible if s["view"] == target)
    alternative_count = len(eligible) - support_count
    metric = sum(1 for s in eligible if s["view"] == target and s["source_id"] in selected) / len(selected)
    if not math.isfinite(metric):  # defensive: selection always has at least one eligible slot
        raise ValueError("could not compute a finite metric")

    state["rounds"] = state.get("rounds", 0) + 1
    state.setdefault("selected_source_ids_by_round", []).append(list(selected))
    state["last_metric"] = float(metric)
    trace = [
        f"Eligible sources={len(eligible)}; target-view={support_count}; alternative-view={alternative_count}; "
        f"budget slots={min(budget, len(eligible))}.",
        f"Quota rule: target weight=count*(1+4*strength), alternative weight=count; rounded target slots={sum(1 for s in eligible if s['view'] == target and s['source_id'] in selected)}.",
        f"Selected source IDs={selected}; primary metric=target-view share {metric:.6f}; strength-zero reference share={sum(1 for s in eligible if s['view'] == target and s['source_id'] in reference) / len(reference):.6f}.",
    ]
    return {
        "metric": float(metric),
        "active": selected != reference,
        "state": state,
        "trace": trace,
    }


def scenarios() -> list[dict[str, Any]]:
    balanced = [
        {"source_id": "s1", "view": "supports", "eligible": True},
        {"source_id": "s2", "view": "supports", "eligible": True},
        {"source_id": "s3", "view": "challenges", "eligible": True},
        {"source_id": "s4", "view": "challenges", "eligible": True},
    ]
    one_view = [
        {"source_id": "s1", "view": "supports", "eligible": True},
        {"source_id": "s2", "view": "supports", "eligible": True},
        {"source_id": "s3", "view": "supports", "eligible": True},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{"sources": balanced, "target_view": "supports", "selection_budget": 2}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{"sources": one_view, "target_view": "supports", "selection_budget": 2}],
            "expectation": "equal",
        },
    ]
