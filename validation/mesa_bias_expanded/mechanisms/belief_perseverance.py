"""Illustrative evidence-ledger model for belief perseverance and backfire.

This is a synthetic process model, not an empirical estimate or detector.
"""
from __future__ import annotations

import math
from typing import Any

METADATA = {
    "id": "belief_perseverance",
    "name": "Belief Perseverance (with Backfire distinguished)",
    "kind": "cognitive_bias",
    "description": (
        "Tracks a claim probability from a prior and signed evidence. A correction "
        "can discredit a previously recorded item; the reference policy removes it, "
        "while the explicitly selected perseverance subtype retains some of its "
        "supporting log-odds contribution. The separately labeled backfire subtype "
        "uses an illustrative larger residual and is not implied by perseverance."
    ),
    "required_inputs": ["prior_probability", "event"],
    "state_fields": ["prior_probability", "evidence", "corrections", "belief_probability", "reference_probability"],
    "metric_name": "claim_belief_probability",
    "metric_units": "Probability on [0, 1], computed by a logistic transform of prior log-odds plus supplied evidence weights.",
    "assumptions": [
        "Evidence weight is an illustrative log-odds contribution, and direction is its sign.",
        "At a correction, the reference rule removes the cited evidence and does not infer additional evidence.",
        "Perseverance retains strength times the discredited positive weight; the distinct backfire subtype retains twice that amount.",
        "Strength is an illustrative intervention setting, not a prevalence or calibrated effect size.",
    ],
    "limitations": [
        "This stipulated ledger process is not empirically validated and makes no population-level claim.",
        "It does not model natural-language evidence, source credibility, motivations, or real-world belief measurement.",
        "The backfire coefficient is an explicit synthetic assumption; real corrections may reduce, preserve, or increase beliefs for many reasons.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_EPS = 1e-12
_MAX_WEIGHT = 20.0


def _finite_number(value: Any, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    number = float(value)
    if not math.isfinite(number) or number < low or number > high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return number


def _probability_to_logit(probability: float) -> float:
    # Avoid infinities at exact endpoints while preserving a finite observable.
    p = min(1.0 - _EPS, max(_EPS, probability))
    return math.log(p / (1.0 - p))


def _logistic(log_odds: float) -> float:
    # Stable logistic transform for the bounded evidence weights used here.
    if log_odds >= 0:
        z = math.exp(-log_odds)
        return 1.0 / (1.0 + z)
    z = math.exp(log_odds)
    return z / (1.0 + z)


def _copy_and_validate_state(state: Any, prior_probability: float) -> dict:
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    if not state:
        return {
            "prior_probability": prior_probability,
            "evidence": {},
            "corrections": {},
            "belief_probability": prior_probability,
            "reference_probability": prior_probability,
        }

    required = {"prior_probability", "evidence", "corrections"}
    if not required.issubset(state):
        raise ValueError("state must contain prior_probability, evidence, and corrections")
    stored_prior = _finite_number(state["prior_probability"], "state.prior_probability", 0.0, 1.0)
    if stored_prior != prior_probability:
        raise ValueError("prior_probability must remain constant throughout the sequence")
    evidence_in = state["evidence"]
    corrections_in = state["corrections"]
    if not isinstance(evidence_in, dict) or not isinstance(corrections_in, dict):
        raise ValueError("state evidence and corrections must be dictionaries")

    evidence: dict[str, dict] = {}
    for evidence_id, item in evidence_in.items():
        if not isinstance(evidence_id, str) or not evidence_id or not isinstance(item, dict):
            raise ValueError("state evidence entries must use nonempty string IDs and dictionaries")
        direction = item.get("direction")
        if isinstance(direction, bool) or not isinstance(direction, int) or direction not in (-1, 0, 1):
            raise ValueError("stored evidence direction must be -1, 0, or 1")
        weight = _finite_number(item.get("weight"), "state evidence weight", 0.0, _MAX_WEIGHT)
        discredited = item.get("discredited")
        if not isinstance(discredited, bool):
            raise ValueError("stored evidence discredited flag must be boolean")
        evidence[evidence_id] = {"direction": int(direction), "weight": weight, "discredited": discredited}

    corrections: dict[str, str] = {}
    for evidence_id, subtype in corrections_in.items():
        if evidence_id not in evidence or not evidence[evidence_id]["discredited"]:
            raise ValueError("stored correction must reference discredited evidence")
        if subtype not in ("perseverance", "backfire"):
            raise ValueError("stored correction subtype must be perseverance or backfire")
        corrections[evidence_id] = subtype

    return {
        "prior_probability": stored_prior,
        "evidence": evidence,
        "corrections": corrections,
        "belief_probability": _finite_number(state.get("belief_probability", prior_probability), "state.belief_probability", 0.0, 1.0),
        "reference_probability": _finite_number(state.get("reference_probability", prior_probability), "state.reference_probability", 0.0, 1.0),
    }


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological evidence or correction event without mutation."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    strength = _finite_number(strength, "strength", 0.0, 1.0)
    if "prior_probability" not in context:
        raise ValueError("missing required input: prior_probability")
    prior = _finite_number(context["prior_probability"], "prior_probability", 0.0, 1.0)
    if "event" not in context or not isinstance(context["event"], dict):
        raise ValueError("event must be a supplied evidence or correction dictionary")

    next_state = _copy_and_validate_state(context.get("state", {}), prior)
    # Rebuild containers so returned state never aliases context or prior state.
    evidence = {key: dict(value) for key, value in next_state["evidence"].items()}
    corrections = dict(next_state["corrections"])
    event = context["event"]
    event_type = event.get("type")
    event_active = False

    if event_type == "evidence":
        if set(event) != {"type", "id", "direction", "weight"}:
            raise ValueError("evidence event requires exactly type, id, direction, and weight")
        evidence_id = event["id"]
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError("evidence id must be a nonempty string")
        if evidence_id in evidence:
            raise ValueError("evidence IDs must be unique in a sequence")
        direction = event["direction"]
        if isinstance(direction, bool) or not isinstance(direction, int) or direction not in (-1, 0, 1):
            raise ValueError("evidence direction must be -1, 0, or 1")
        weight = _finite_number(event["weight"], "evidence weight", 0.0, _MAX_WEIGHT)
        evidence[evidence_id] = {"direction": int(direction), "weight": weight, "discredited": False}

    elif event_type == "correction":
        if set(event) != {"type", "target_id", "subtype"}:
            raise ValueError("correction event requires exactly type, target_id, and subtype")
        target_id = event["target_id"]
        subtype = event["subtype"]
        if not isinstance(target_id, str) or target_id not in evidence:
            raise ValueError("correction must cite previously supplied evidence")
        if evidence[target_id]["discredited"]:
            raise ValueError("evidence cannot be corrected more than once")
        if subtype not in ("perseverance", "backfire"):
            raise ValueError("subtype must be explicitly set to perseverance or backfire")
        evidence[target_id]["discredited"] = True
        corrections[target_id] = subtype
        # The necessary condition is a formerly supporting evidence item. Correcting
        # negative or neutral evidence does not instantiate belief perseverance.
        event_active = evidence[target_id]["direction"] == 1 and evidence[target_id]["weight"] > 0
    else:
        raise ValueError("event.type must be evidence or correction")

    prior_log_odds = _probability_to_logit(prior)
    reference_log_odds = prior_log_odds + sum(
        item["direction"] * item["weight"]
        for item in evidence.values()
        if not item["discredited"]
    )
    residual_log_odds = 0.0
    for evidence_id, subtype in corrections.items():
        item = evidence[evidence_id]
        if item["direction"] == 1:
            # Subtypes remain distinct: perseverance retains one unit of cited
            # support; the hypothesized backfire response retains two units.
            multiplier = 1.0 if subtype == "perseverance" else 2.0
            residual_log_odds += strength * multiplier * item["weight"]

    belief_log_odds = reference_log_odds + residual_log_odds
    reference_probability = _logistic(reference_log_odds)
    belief_probability = _logistic(belief_log_odds)
    active = bool(event_active and strength > 0 and residual_log_odds != 0)
    result_state = {
        "prior_probability": prior,
        "evidence": evidence,
        "corrections": corrections,
        "belief_probability": belief_probability,
        "reference_probability": reference_probability,
    }
    detail = (
        f"prior_log_odds={prior_log_odds:.12g}; reference_log_odds={reference_log_odds:.12g} "
        f"(prior plus signed weights of non-discredited evidence); residual_log_odds="
        f"{residual_log_odds:.12g} (strength={strength:g}; perseverance multiplier=1, "
        "explicit backfire multiplier=2, supporting evidence only); metric=logistic(reference + residual)."
    )
    return {
        "metric": belief_probability,
        "active": active,
        "state": result_state,
        "trace": [detail],
    }


def scenarios() -> list[dict]:
    prior = 0.4
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"prior_probability": prior, "event": {"type": "evidence", "id": "study-A", "direction": 1, "weight": 1.2}},
                {"prior_probability": prior, "event": {"type": "correction", "target_id": "study-A", "subtype": "perseverance"}},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"prior_probability": prior, "event": {"type": "evidence", "id": "study-B", "direction": -1, "weight": 0.8}},
                {"prior_probability": prior, "event": {"type": "correction", "target_id": "study-B", "subtype": "perseverance"}},
            ],
            "expectation": "equal",
        },
        {
            "name": "explicit_backfire_subtype",
            "initial_state": {},
            "contexts": [
                {"prior_probability": prior, "event": {"type": "evidence", "id": "study-C", "direction": 1, "weight": 1.2}},
                {"prior_probability": prior, "event": {"type": "correction", "target_id": "study-C", "subtype": "backfire"}},
            ],
            "expectation": "increase",
        },
    ]
