"""Illustrative attention-allocation model for ad hominem arguments.

This is a synthetic process model, not a detector or empirical psychology claim.
"""
from __future__ import annotations

import math
from copy import deepcopy
from numbers import Real
from typing import Any


METADATA = {
    "id": "ad_hominem",
    "name": "Ad Hominem (Kişiye saldırı)",
    "kind": "cognitive_bias",
    "description": (
        "Models a reviewer diverting a bounded share of attention from supplied "
        "claim evidence to a personal attack explicitly rated as irrelevant."
    ),
    "required_inputs": [
        "claim_evidence_units",
        "personal_attack_present",
        "attack_intensity",
        "attack_claim_relevance",
    ],
    "state_fields": [
        "claim_evidence_units_reviewed_total",
        "diverted_attention_total",
        "turns_processed",
    ],
    "metric_name": "claim_evidence_units_reviewed",
    "metric_units": "units of supplied claim evidence reviewed this turn",
    "assumptions": [
        "Each turn has one normalized attention budget, and supplied claim evidence is reviewable within it.",
        "Attack intensity and relevance are explicit scenario facts on [0, 1], not inferred from wording.",
        "At strength s, irrelevant personal-attack salience diverts s * intensity * (1 - relevance) of the budget.",
        "A relevant critique, such as task-relevant expertise evidence, is not an ad hominem diversion in this model.",
        "Strength is an illustrative intervention setting, not a prevalence or calibrated effect size.",
    ],
    "limitations": [
        "The supplied concept spec leaves the annotation boundary blank; this module makes the explicit operational boundary that the attack is person-directed and irrelevant to the claim.",
        "It assumes a normalized bounded attention budget and does not model actual human attention, belief, emotion, or persuasion.",
        "Inputs must be manually supplied structured facts; this is not a natural-language detector and makes no inference about speaker intent.",
        "The coefficient and linear allocation rule are hypothetical and not empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_STATE_DEFAULTS = {
    "claim_evidence_units_reviewed_total": 0.0,
    "diverted_attention_total": 0.0,
    "turns_processed": 0,
}


def _unit_interval(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def _positive_units(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number greater than zero")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be a finite number greater than zero")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Return this turn's claim-evidence attention share and accumulated state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    required = METADATA["required_inputs"]
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required evidence/input: {', '.join(missing)}")

    # A positive, explicit amount prevents an absent-evidence case from being
    # silently represented as a zero-valued metric. It is retained in the trace.
    evidence_units = _positive_units(context["claim_evidence_units"], "claim_evidence_units")
    personal = context["personal_attack_present"]
    if not isinstance(personal, bool):
        raise ValueError("personal_attack_present must be bool")
    intensity = _unit_interval(context["attack_intensity"], "attack_intensity")
    relevance = _unit_interval(context["attack_claim_relevance"], "attack_claim_relevance")

    previous = context.get("state")
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    next_state = deepcopy(_STATE_DEFAULTS)
    for key, default in _STATE_DEFAULTS.items():
        if key in previous:
            value = previous[key]
            if key == "turns_processed":
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ValueError("state.turns_processed must be a nonnegative integer")
                next_state[key] = value
            else:
                if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)) or value < 0:
                    raise ValueError(f"state.{key} must be a finite nonnegative number")
                next_state[key] = float(value)
        else:
            next_state[key] = default
    # Preserve unrelated caller state without mutating its original object.
    for key, value in previous.items():
        if key not in next_state:
            next_state[key] = deepcopy(value)

    # The task-specific process is allocation of a unit reviewer budget:
    # only explicit person-directed attacks with nonzero intensity can compete
    # with claim review, and relevance discounts that competing demand.
    attack_demand = intensity * (1.0 - relevance) if personal else 0.0
    diverted = strength * attack_demand
    claim_attention = 1.0 - diverted
    if not math.isfinite(claim_attention):  # defensive invariant
        raise ValueError("computed attention metric is not finite")

    reviewed_evidence = evidence_units * claim_attention
    next_state["claim_evidence_units_reviewed_total"] += reviewed_evidence
    next_state["diverted_attention_total"] += diverted
    next_state["turns_processed"] += 1
    active = diverted > 0.0
    trace = [
        f"Evidence availability={evidence_units:g} unit(s); normalized attention budget=1.",
        f"Attack demand=intensity({intensity:g}) * (1-relevance({relevance:g})) = {attack_demand:g} when personal_attack_present={personal}; otherwise 0.",
        f"Diverted attention=strength({strength:g}) * attack demand({attack_demand:g}) = {diverted:g}; evidence reviewed={evidence_units:g} * (1-{diverted:g}) = {reviewed_evidence:g} unit(s).",
        f"Accumulated state now records {next_state['turns_processed']} turn(s).",
    ]
    return {
        "metric": evidence_units * claim_attention,
        "active": active,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "claim_evidence_units": 3,
                    "personal_attack_present": True,
                    "attack_intensity": 0.6,
                    "attack_claim_relevance": 0.0,
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "claim_evidence_units": 3,
                    "personal_attack_present": True,
                    "attack_intensity": 0.6,
                    "attack_claim_relevance": 1.0,
                }
            ],
            "expectation": "equal",
        },
    ]
