"""Illustrative reader-appraisal process for explicitly supplied loaded wording.

This is a structured hypothetical model, not an NLP detector or an empirical claim.
"""

from copy import deepcopy
import math

METADATA = {
    "id": "loaded_language",
    "name": "Loaded language (Duygu yüklü dil)",
    "kind": "media_practice",
    "description": (
        "Models how explicitly supplied evaluative wording linked to an event can"
        " shift a reader's appraisal away from the reported factual appraisal."
    ),
    "required_inputs": [
        "event_valence",
        "evaluation_present",
        "targets_event",
        "evaluation_valence",
        "evaluation_intensity",
    ],
    "state_fields": [
        "decision_count",
        "appraisal_history",
        "last_appraisal",
        "last_loaded_shift",
    ],
    "metric_name": "reader appraisal",
    "metric_units": "normalized appraisal points on [-1, 1]; negative to positive evaluation",
    "assumptions": [
        "The event's reported factual appraisal, presence/linkage of evaluative wording, evaluation valence, and intensity are explicit hypothetical inputs.",
        "The strength setting scales a deterministic blend between factual appraisal and the supplied evaluation; it is not a probability or calibrated effect size.",
        "The strength-zero reference policy appraises the event using its reported factual appraisal alone.",
    ],
    "limitations": [
        "No words are inspected: this module neither detects loaded language nor judges whether supplied wording is warranted, accurate, or harmful.",
        "The blend equation is an illustrative assumption, not a fitted or empirically validated audience-response model.",
        "Negative factual reporting without linked evaluative wording leaves appraisal unchanged; evaluative language can also be ordinary, justified, or benign rhetoric.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    event_valence = _finite_number(context["event_valence"], "event_valence")
    if not -1.0 <= event_valence <= 1.0:
        raise ValueError("event_valence must be in [-1, 1]")

    evaluation_present = context["evaluation_present"]
    targets_event = context["targets_event"]
    if not isinstance(evaluation_present, bool):
        raise ValueError("evaluation_present must be a bool")
    if not isinstance(targets_event, bool):
        raise ValueError("targets_event must be a bool")

    evaluation_valence = context["evaluation_valence"]
    evaluation_intensity = context["evaluation_intensity"]
    if not evaluation_present:
        if evaluation_valence is not None or evaluation_intensity is not None:
            raise ValueError(
                "evaluation_valence and evaluation_intensity must be None when evaluation_present is false"
            )
        return event_valence, False, targets_event, None, None

    evaluation_valence = _finite_number(evaluation_valence, "evaluation_valence")
    evaluation_intensity = _finite_number(evaluation_intensity, "evaluation_intensity")
    if not -1.0 <= evaluation_valence <= 1.0:
        raise ValueError("evaluation_valence must be in [-1, 1]")
    if not 0.0 <= evaluation_intensity <= 1.0:
        raise ValueError("evaluation_intensity must be in [0, 1]")
    return event_valence, True, targets_event, evaluation_valence, evaluation_intensity


def _validate_state(state):
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    count = state.get("decision_count", 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.decision_count must be a non-negative integer")
    history = state.get("appraisal_history", [])
    if not isinstance(history, list):
        raise ValueError("state.appraisal_history must be a list")
    for index, value in enumerate(history):
        value = _finite_number(value, f"state.appraisal_history[{index}]")
        if not -1.0 <= value <= 1.0:
            raise ValueError(f"state.appraisal_history[{index}] must be in [-1, 1]")
    for key in ("last_appraisal", "last_loaded_shift"):
        if key in state and state[key] is not None:
            _finite_number(state[key], f"state.{key}")
    return count, list(history)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one supplied presentation without changing input or nested state."""
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    event_valence, evaluation_present, targets_event, evaluation_valence, intensity = (
        _validate_context(context)
    )
    state_in = context.get("state", {})
    prior_count, history = _validate_state(state_in)

    linked_evaluation = evaluation_present and targets_event
    weight = strength * intensity if linked_evaluation else 0.0
    # Reference = event facts alone. A linked evaluation blends its appraisal into
    # that factual reference in proportion to the supplied intensity and strength.
    appraisal = (1.0 - weight) * event_valence + (
        weight * evaluation_valence if linked_evaluation else 0.0
    )
    shift = appraisal - event_valence
    active = linked_evaluation and shift != 0.0

    next_state = deepcopy(state_in)
    history.append(float(appraisal))
    next_state.update(
        {
            "decision_count": prior_count + 1,
            "appraisal_history": history,
            "last_appraisal": float(appraisal),
            "last_loaded_shift": float(shift),
        }
    )
    if not math.isfinite(appraisal):  # Defensive guard; validated bounded inputs imply this cannot occur.
        raise ValueError("computed appraisal must be finite")

    if linked_evaluation:
        condition = (
            f"linked evaluation present (valence={evaluation_valence:g}, intensity={intensity:g})"
        )
    elif evaluation_present:
        condition = "evaluation is not linked to this event; factual-only reference applies"
    else:
        condition = "no evaluation is present; factual-only reference applies"
    intensity_text = f"{intensity:g}" if intensity is not None else "not applicable"
    return {
        "metric": float(appraisal),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"Reference appraisal = event_valence ({event_valence:g}).",
            f"{condition}; blend weight = strength ({strength:g}) × intensity ({intensity_text}) when linked, otherwise 0 ({weight:g}).",
            f"Appraisal = (1 − weight) × event_valence + weight × evaluation_valence when linked; result = {appraisal:g} (shift {shift:g}); active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "event_valence": 0.2,
                    "evaluation_present": True,
                    "targets_event": True,
                    "evaluation_valence": -0.8,
                    "evaluation_intensity": 0.75,
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "event_valence": -0.7,
                    "evaluation_present": False,
                    "targets_event": False,
                    "evaluation_valence": None,
                    "evaluation_intensity": None,
                }
            ],
            "expectation": "equal",
        },
    ]
