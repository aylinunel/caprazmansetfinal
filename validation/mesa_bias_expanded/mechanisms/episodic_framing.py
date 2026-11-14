"""Illustrative structured model of episodic framing in authored coverage.

This is a synthetic process model, not a detector or empirical effect estimate.
"""
from __future__ import annotations

import math
from typing import Any

METADATA = {
    "id": "episodic_framing",
    "name": "Episodic Framing (Olay odaklı çerçeveleme)",
    "kind": "media_practice",
    "description": (
        "Allocates a finite authored context budget between a salient single-event "
        "account and supplied structural context; episodic framing increases the "
        "event's allocation weight only when causal structural evidence is present."
    ),
    "required_inputs": [
        "context_budget",
        "event_relevance",
        "structural_relevance",
        "single_event_focus",
        "structural_cause_evidence",
    ],
    "state_fields": [
        "steps",
        "cumulative_structural_units",
        "last_structural_units",
        "last_reference_units",
    ],
    "metric_name": "structural_context_units",
    "metric_units": "illustrative units of authored context budget allocated to structural causes",
    "assumptions": [
        "The supplied relevance weights and causal-evidence flag are explicit scenario facts, not inferred from prose.",
        "The reference policy allocates a fixed budget in proportion to event and structural relevance.",
        "Strength is an illustrative intervention setting that multiplicatively increases event weight by up to 100%; it is not a prevalence or calibrated effect size.",
    ],
    "limitations": [
        "No empirical validation, population claim, or natural-language detection is provided.",
        "The model reduces editorial framing to one event-versus-structure budget choice and cannot establish whether coverage is misleading or whether other story elements supply context.",
        "Legitimate event-centered reporting and beneficial narrative choices are not classified as errors by this simulation.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_REQUIRED = tuple(METADATA["required_inputs"])
_STATE_DEFAULTS = {
    "steps": 0,
    "cumulative_structural_units": 0.0,
    "last_structural_units": 0.0,
    "last_reference_units": 0.0,
}


def _finite_number(value: Any, name: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or (minimum is not None and number < minimum):
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one authored-coverage choice without mutating the supplied context."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    s = _finite_number(strength, "strength", minimum=0.0)
    if s > 1.0:
        raise ValueError("strength must be in [0, 1]")
    missing = [key for key in _REQUIRED if key not in context]
    if missing:
        raise ValueError(f"missing required evidence: {', '.join(missing)}")

    budget = _finite_number(context["context_budget"], "context_budget", minimum=0.0)
    if budget <= 0.0:
        raise ValueError("context_budget must be > 0")
    event = _finite_number(context["event_relevance"], "event_relevance", minimum=0.0)
    structure = _finite_number(context["structural_relevance"], "structural_relevance", minimum=0.0)
    if event <= 0.0 or structure <= 0.0:
        raise ValueError("event_relevance and structural_relevance must both be > 0")
    single_event = context["single_event_focus"]
    cause_evidence = context["structural_cause_evidence"]
    if type(single_event) is not bool or type(cause_evidence) is not bool:
        raise ValueError("single_event_focus and structural_cause_evidence must be bools")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    steps = prior.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a nonnegative integer")
    cumulative = _finite_number(prior.get("cumulative_structural_units", 0.0), "state.cumulative_structural_units", minimum=0.0)
    _finite_number(prior.get("last_structural_units", 0.0), "state.last_structural_units", minimum=0.0)
    _finite_number(prior.get("last_reference_units", 0.0), "state.last_reference_units", minimum=0.0)

    # Explicit reference policy: the finite context budget is shared in proportion
    # to supplied event and structural relevance, with no episodic adjustment.
    reference = budget * structure / (structure + event)
    # Necessary condition from the definition: an authored single-event focus AND
    # supplied evidence that structural causes produce the issue. The mechanism
    # increases event weight rather than subtracting an arbitrary fixed penalty.
    eligible = single_event and cause_evidence
    event_weight = event * (1.0 + s) if eligible else event
    metric = budget * structure / (structure + event_weight)
    if not math.isfinite(metric):
        raise ValueError("computed metric is not finite")

    # Preserve other prior state fields, and update the complete mechanism state.
    next_state = dict(prior)
    next_state.update({
        "steps": steps + 1,
        "cumulative_structural_units": cumulative + metric,
        "last_structural_units": metric,
        "last_reference_units": reference,
    })
    return {
        "metric": metric,
        "active": bool(eligible and s > 0.0 and metric != reference),
        "state": next_state,
        "trace": [
            f"Reference structural allocation = budget*structure/(structure+event) = {reference:.6g} units.",
            f"single_event_focus={single_event}; structural_cause_evidence={cause_evidence}; eligible={eligible}.",
            f"event_weight = event*(1+strength) when eligible, otherwise event; event_weight={event_weight:.6g}.",
            f"Reported structural_context_units = budget*structure/(structure+event_weight) = {metric:.6g} units; prior state was not mutated.",
        ],
    }


def scenarios() -> list[dict]:
    common = {
        "context_budget": 100.0,
        "event_relevance": 3.0,
        "structural_relevance": 2.0,
        "single_event_focus": True,
        "structural_cause_evidence": True,
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [dict(common)],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{**common, "structural_cause_evidence": False}],
            "expectation": "equal",
        },
    ]
