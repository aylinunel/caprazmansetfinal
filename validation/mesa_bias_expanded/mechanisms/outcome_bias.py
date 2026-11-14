"""Illustrative outcome-bias process for retrospective decision appraisal.

This is a hypothetical process model, not a detector or fitted psychological law.
"""
from __future__ import annotations

import math
from copy import deepcopy


METADATA = {
    "id": "outcome_bias",
    "name": "Outcome bias",
    "kind": "cognitive_bias",
    "description": (
        "Retrospective decision-quality appraisal is pulled from the quality of "
        "the realized result toward that result, despite a recorded ex-ante "
        "evidence-based quality score."
    ),
    "required_inputs": [
        "case_id",
        "evidence_quality",
        "outcome_observed",
        "outcome_quality",
    ],
    "state_fields": ["evaluations"],
    "metric_name": "retrospective_decision_quality_appraisal",
    "metric_units": "normalized appraisal points on a 0-to-1 scale",
    "assumptions": [
        "evidence_quality is a supplied, fixed appraisal of decision quality using information available when the decision was made.",
        "outcome_quality is a supplied score for the realized result, not a measure of what was predictable beforehand.",
        "strength is an uncalibrated interpolation weight between the evidence-based reference and the result-based appraisal.",
    ],
    "limitations": [
        "The interpolation is a compact hypothetical illustration, not an empirically estimated effect or a model of all outcome judgments.",
        "The structured scores and observation flag are explicit task inputs; this module does not infer them from text or diagnose people.",
        "A poor result can arise despite sound reasoning, and a good result can arise despite weak reasoning; the example does not establish actual decision quality.",
        "The model isolates outcome-based appraisal drift and does not model hindsight judgments about prior predictability.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _score(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Appraise a recorded decision; outcome can influence rating only if observed."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")

    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required task input {key}")
    case_id = context["case_id"]
    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError("case_id must be a nonempty string")
    evidence = _score(context["evidence_quality"], "evidence_quality")
    observed = context["outcome_observed"]
    if not isinstance(observed, bool):
        raise ValueError("outcome_observed must be a boolean")
    if observed:
        outcome = _score(context["outcome_quality"], "outcome_quality")
        # The actual concept-specific operation: ex-post quality is interpolated
        # toward the realized result only when that result is part of the record.
        appraisal = evidence + strength * (outcome - evidence)
    else:
        if context["outcome_quality"] is not None:
            raise ValueError("unobserved outcomes must have outcome_quality=None")
        outcome = None
        appraisal = evidence

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be an object")
    evaluations = prior.get("evaluations", [])
    if not isinstance(evaluations, list):
        raise ValueError("state.evaluations must be a list")
    # Build fresh containers so neither caller-owned state nor nested history is mutated.
    next_evaluations = deepcopy(evaluations)
    next_evaluations.append({
        "case_id": case_id,
        "evidence_quality": evidence,
        "outcome_observed": observed,
        "outcome_quality": outcome,
        "appraisal": appraisal,
    })
    active = observed and strength > 0.0 and outcome != evidence
    return {
        "metric": appraisal,
        "active": active,
        "state": {"evaluations": next_evaluations},
        "trace": [
            "Retrospective appraisal = evidence_quality + strength * "
            "(outcome_quality - evidence_quality) when the outcome is observed; "
            "otherwise appraisal = evidence_quality. This is appraisal of decision "
            "quality, not a judgment that the outcome was predictable."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"evaluations": []},
            "contexts": [
                {
                    "case_id": "sound-process-unlucky-1",
                    "evidence_quality": 0.80,
                    "outcome_observed": True,
                    "outcome_quality": 0.20,
                },
                {
                    "case_id": "sound-process-unlucky-2",
                    "evidence_quality": 0.70,
                    "outcome_observed": True,
                    "outcome_quality": 0.30,
                },
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {"evaluations": []},
            "contexts": [
                {
                    "case_id": "result-not-yet-known",
                    "evidence_quality": 0.80,
                    "outcome_observed": False,
                    "outcome_quality": None,
                }
            ],
            "expectation": "equal",
        },
    ]
