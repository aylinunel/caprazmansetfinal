"""Illustrative spin mechanism: convergent emphasis across authored media forms.

This is a hypothetical process model, not a detector, classifier, or empirical claim.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "spin",
    "name": "Spin",
    "kind": "media_practice",
    "description": (
        "Models how at least two distinct authored presentation forms that converge "
        "on the same directional evidence can jointly shift a story's weighted tone."
    ),
    "required_inputs": ["evidence", "presentation_forms"],
    "state_fields": ["step_count", "last_metric", "last_active", "last_framing_direction"],
    "metric_name": "presented_tone_index",
    "metric_units": "dimensionless evidence-direction index from -1 (negative) to +1 (positive)",
    "assumptions": [
        "Evidence direction and weight are explicit scenario inputs, not inferred from text.",
        "Distinct form kinds are independently authored choices; emphasis values are illustrative salience increments.",
        "Two or more forms agreeing on a directional evidence item are the necessary convergence condition.",
        "Strength scales added salience linearly and is an intervention setting, not prevalence or confidence.",
        "The reference rule is the evidence-weighted mean with no additional salience from presentation forms.",
    ],
    "limitations": [
        "This narrow model covers convergent salience only; it does not model all meanings of spin, intent, deception, or audience response.",
        "Evidence scores, weights, form choices, and coefficients are synthetic; no human validation or detection accuracy is claimed.",
        "Legitimate editorial emphasis and explanatory context can produce the same structured choices; emphasis is not classified as an error.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _validated_inputs(context: dict) -> tuple[list[dict], list[dict]]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "evidence" not in context:
        raise ValueError("missing required input: evidence")
    if "presentation_forms" not in context:
        raise ValueError("missing required input: presentation_forms")
    evidence = context["evidence"]
    forms = context["presentation_forms"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a non-empty list")
    if not isinstance(forms, list):
        raise ValueError("presentation_forms must be a list")

    seen_ids: set[str] = set()
    clean_evidence: list[dict] = []
    for i, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValueError(f"evidence[{i}] must be a dict")
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen_ids:
            raise ValueError(f"evidence[{i}].id must be a unique non-empty string")
        seen_ids.add(identifier)
        if "direction" not in item or "weight" not in item:
            raise ValueError(f"evidence[{i}] requires direction and weight")
        direction = _finite_number(item["direction"], f"evidence[{i}].direction")
        weight = _finite_number(item["weight"], f"evidence[{i}].weight")
        if not -1.0 <= direction <= 1.0:
            raise ValueError(f"evidence[{i}].direction must be in [-1, 1]")
        if weight <= 0.0:
            raise ValueError(f"evidence[{i}].weight must be greater than zero")
        clean_evidence.append({"id": identifier, "direction": direction, "weight": weight})

    kinds: set[str] = set()
    clean_forms: list[dict] = []
    for i, form in enumerate(forms):
        if not isinstance(form, dict):
            raise ValueError(f"presentation_forms[{i}] must be a dict")
        kind = form.get("kind")
        focus_id = form.get("focus_id")
        if not isinstance(kind, str) or not kind.strip() or kind in kinds:
            raise ValueError(f"presentation_forms[{i}].kind must be a unique non-empty string")
        if not isinstance(focus_id, str) or focus_id not in seen_ids:
            raise ValueError(f"presentation_forms[{i}].focus_id must reference supplied evidence")
        if "emphasis" not in form:
            raise ValueError(f"presentation_forms[{i}] requires emphasis")
        emphasis = _finite_number(form["emphasis"], f"presentation_forms[{i}].emphasis")
        if not 0.0 <= emphasis <= 1.0:
            raise ValueError(f"presentation_forms[{i}].emphasis must be in [0, 1]")
        kinds.add(kind)
        clean_forms.append({"kind": kind, "focus_id": focus_id, "emphasis": emphasis})
    return clean_evidence, clean_forms


def evaluate(context: dict, strength: float) -> dict:
    """Return the presented tone index and full next state without mutating inputs."""
    scale = _finite_number(strength, "strength")
    if not 0.0 <= scale <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    evidence, forms = _validated_inputs(context)

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    prior_count = prior_state.get("step_count", 0)
    if isinstance(prior_count, bool) or not isinstance(prior_count, int) or prior_count < 0:
        raise ValueError("state.step_count must be a non-negative integer")

    by_id = {item["id"]: item for item in evidence}
    votes = {-1: 0, 1: 0}
    for form in forms:
        sign = 1 if by_id[form["focus_id"]]["direction"] > 0 else -1 if by_id[form["focus_id"]]["direction"] < 0 else 0
        if sign:
            votes[sign] += 1
    framing_direction = None
    if votes[1] >= 2 and votes[1] > votes[-1]:
        framing_direction = 1
    elif votes[-1] >= 2 and votes[-1] > votes[1]:
        framing_direction = -1

    # Reference: weighted factual mean. Under convergence, each aligned form adds
    # strength * emphasis to its focused fact's salience multiplier.
    numerator_terms = []
    denominator_terms = []
    for item in evidence:
        aligned_emphasis = 0.0
        if framing_direction is not None and (item["direction"] > 0) == (framing_direction > 0) and item["direction"] != 0:
            aligned_emphasis = math.fsum(
                form["emphasis"] for form in forms
                if form["focus_id"] == item["id"]
                and (by_id[form["focus_id"]]["direction"] > 0) == (framing_direction > 0)
            )
        multiplier = 1.0 + scale * aligned_emphasis
        presented_weight = item["weight"] * multiplier
        numerator_terms.append(presented_weight * item["direction"])
        denominator_terms.append(presented_weight)

    metric = math.fsum(numerator_terms) / math.fsum(denominator_terms)
    reference_numerator = math.fsum(item["weight"] * item["direction"] for item in evidence)
    reference_denominator = math.fsum(item["weight"] for item in evidence)
    reference_metric = reference_numerator / reference_denominator
    active = not math.isclose(metric, reference_metric, rel_tol=0.0, abs_tol=1e-12)

    state = dict(prior_state)
    state.update({
        "step_count": prior_count + 1,
        "last_metric": metric,
        "last_active": active,
        "last_framing_direction": framing_direction,
    })
    trace = [
        f"Reference tone = sum(weight*direction)/sum(weight) = {reference_metric:.12g}.",
        f"Form-direction votes: positive={votes[1]}, negative={votes[-1]}; convergence requires at least two distinct kinds and a strict plurality.",
        f"Framing direction={framing_direction!r}; aligned fact weight is multiplied by 1 + strength*sum(emphasis) (strength={scale:g}).",
        f"Presented tone = sum(presented_weight*direction)/sum(presented_weight) = {metric:.12g}; active={active}.",
    ]
    return {"metric": metric, "active": active, "state": state, "trace": trace}


def scenarios() -> list[dict]:
    facts = [
        {"id": "service_gain", "direction": 0.8, "weight": 2.0},
        {"id": "service_gap", "direction": -0.6, "weight": 1.0},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "evidence": facts,
                "presentation_forms": [
                    {"kind": "headline", "focus_id": "service_gain", "emphasis": 1.0},
                    {"kind": "ordering", "focus_id": "service_gain", "emphasis": 0.5},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "evidence": facts,
                # Only one form: the required cross-form convergence is absent.
                "presentation_forms": [
                    {"kind": "headline", "focus_id": "service_gain", "emphasis": 1.0},
                ],
            }],
            "expectation": "equal",
        },
    ]
