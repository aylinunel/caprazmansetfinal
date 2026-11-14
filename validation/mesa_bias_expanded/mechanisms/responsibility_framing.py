"""Illustrative structured process model for premature responsibility framing.

This is a synthetic editorial-choice mechanism, not a headline detector or an
empirical claim about journalists or readers.
"""
from copy import deepcopy
import math


METADATA = {
    "id": "responsibility_framing",
    "name": "Attribution of Responsibility Framing",
    "kind": "media_practice",
    "description": (
        "Selects between a responsibility-attribution lead and a process-status "
        "lead; before the process is complete, strength adds pressure to use an "
        "available attribution frame beyond the explicit evidential support."
    ),
    "required_inputs": [
        "process_complete",
        "responsibility_claim_available",
        "evidence_support",
        "attribution_salience",
        "process_salience",
    ],
    "state_fields": ["frame_history", "last_frame"],
    "metric_name": "headline_attribution_choice",
    "metric_units": "binary choice encoded as 1.0 (attribution lead) or 0.0 (process lead)",
    "assumptions": [
        "The two supplied salience values represent task-specific editorial value on a 0-1 scale.",
        "Evidence support is an explicit input, not inferred from wording or hidden intent.",
        "An incomplete process and an available responsibility proposition are necessary for the framing pressure.",
        "Strength is an illustrative intervention setting, not a prevalence or effect-size estimate.",
    ],
    "limitations": [
        "This binary choice model omits headline language, audience interpretation, legal context, and alternative frame options.",
        "The support-weighted utility and pressure equation are stipulated for illustration and are not empirically validated.",
        "An attribution lead can be justified or beneficial when sufficiently supported; this model does not label attribution itself as an error.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Choose a headline frame from explicit task facts and prior state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")

    missing = [field for field in METADATA["required_inputs"] if field not in context]
    if missing:
        raise ValueError(f"missing required evidence/input(s): {', '.join(missing)}")

    process_complete = context["process_complete"]
    claim_available = context["responsibility_claim_available"]
    if type(process_complete) is not bool:
        raise ValueError("process_complete must be a bool")
    if type(claim_available) is not bool:
        raise ValueError("responsibility_claim_available must be a bool")
    evidence = _unit_interval(context["evidence_support"], "evidence_support")
    attribution_salience = _unit_interval(context["attribution_salience"], "attribution_salience")
    process_salience = _unit_interval(context["process_salience"], "process_salience")

    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("state must be a dictionary supplied by the runner")
    prior_state = context["state"]
    history = prior_state.get("frame_history", [])
    if not isinstance(history, list) or any(item not in ("attribution", "process") for item in history):
        raise ValueError("state.frame_history must be a list of prior frame choices")
    previous = prior_state.get("last_frame")
    if previous is not None and previous not in ("attribution", "process"):
        raise ValueError("state.last_frame must be 'attribution', 'process', or None")

    # Reference policy: choose the attribution lead only when its explicit,
    # support-weighted salience exceeds the process-status lead. A tie favors
    # process status. This is a stipulated editorial reference rule, not a claim
    # of perfect or universally appropriate practice.
    reference_score = attribution_salience * evidence
    reference_frame = (
        "attribution"
        if claim_available and reference_score > process_salience
        else "process"
    )

    # The additional utility is specific to settling responsibility early:
    # editorial salience × unsupported share × incomplete-process indicator ×
    # availability of the responsibility claim × intervention strength.
    # Thus a finalized process, no available claim, or fully supported claim
    # removes the mechanism's increment.
    premature_pressure = (
        strength
        * (0.0 if process_complete else 1.0)
        * (1.0 if claim_available else 0.0)
        * attribution_salience
        * (1.0 - evidence)
    )
    attribution_score = reference_score + premature_pressure
    selected_frame = (
        "attribution"
        if claim_available and attribution_score > process_salience
        else "process"
    )
    active = selected_frame != reference_frame

    next_state = deepcopy(prior_state)
    next_history = list(history)
    next_history.append(selected_frame)
    next_state["frame_history"] = next_history
    next_state["last_frame"] = selected_frame

    return {
        "metric": 1.0 if selected_frame == "attribution" else 0.0,
        "active": active,
        "state": next_state,
        "trace": [
            "Reference attribution score = attribution_salience × evidence_support; "
            "the reference selects attribution only when that score strictly exceeds process_salience and a claim is available.",
            "Premature pressure = strength × (process incomplete) × (claim available) × "
            "attribution_salience × (1 − evidence_support); selected frame is attribution only when reference score + pressure strictly exceeds process_salience.",
            f"Inputs: process_complete={process_complete}, claim_available={claim_available}, "
            f"evidence_support={evidence:.6g}, attribution_salience={attribution_salience:.6g}, "
            f"process_salience={process_salience:.6g}, strength={strength:.6g}; "
            f"scores reference={reference_score:.6g}, pressure={premature_pressure:.6g}, "
            f"combined={attribution_score:.6g}; selected={selected_frame}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "process_complete": False,
                    "responsibility_claim_available": True,
                    "evidence_support": 0.20,
                    "attribution_salience": 0.90,
                    "process_salience": 0.40,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "process_complete": True,
                    "responsibility_claim_available": True,
                    "evidence_support": 0.20,
                    "attribution_salience": 0.90,
                    "process_salience": 0.40,
                }
            ],
            "expectation": "equal",
        },
    ]
