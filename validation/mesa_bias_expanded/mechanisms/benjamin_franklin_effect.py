"""Illustrative, explicitly hypothetical Benjamin Franklin effect process model."""

from copy import deepcopy
import math


METADATA = {
    "id": "benjamin_franklin_effect",
    "name": "Benjamin Franklin effect",
    "kind": "learning_effect",
    "description": (
        "An assumed helper-side liking adjustment after the helper gives a favor: "
        "effort-weighted self-justification closes a fraction of the remaining "
        "distance to the top of an explicit liking scale. Receiving a favor does not qualify."
    ),
    "required_inputs": [
        "direction",
        "target_id",
        "favor_effort",
        "liking_before",
        "favor_event_id",
    ],
    "state_fields": ["liking_by_person", "processed_favor_event_ids"],
    "metric_name": "helper_liking_rating",
    "metric_units": "hypothetical rating points on a 0-100 scale",
    "assumptions": [
        "A helper's liking can be represented by an explicit 0-100 rating.",
        "Only an act classified as the helper giving a favor can trigger the process.",
        "Favor effort is supplied on a 0-1 scale and scales the adjustment linearly.",
        "The illustrative coefficient 0.25 is an uncalibrated assumption, not an effect size.",
        "For each qualifying favor, the adjustment is 0.25 * strength * effort * (100 - current liking).",
    ],
    "limitations": [
        "This is a synthetic process illustration, not an empirical estimate, classifier, or claim about population behavior.",
        "The model takes favor direction, effort, and baseline liking as explicit facts; it cannot infer them from text or hidden motives.",
        "It omits relationship history, favor costs, cultural context, individual differences, and alternative explanations.",
        "The linear effort rule and 0.25 ceiling-gap coefficient are user-unvalidated assumptions.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_SCALE_MAX = 100.0
_ADJUSTMENT_FRACTION = 0.25
_DIRECTIONS = {"given", "received", "none"}


def _finite_number(value, label, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    number = float(value)
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological event without mutating context or its state."""
    intervention = _finite_number(strength, "strength", 0.0, 1.0)
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    required = METADATA["required_inputs"]
    missing = [field for field in required if field not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")

    direction = context["direction"]
    if not isinstance(direction, str) or direction not in _DIRECTIONS:
        raise ValueError("direction must be one of: given, received, none")
    target_id = context["target_id"]
    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("target_id must be a non-empty string")
    event_id = context["favor_event_id"]
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("favor_event_id must be a non-empty string")
    effort = _finite_number(context["favor_effort"], "favor_effort", 0.0, 1.0)
    initial_liking = _finite_number(context["liking_before"], "liking_before", 0.0, _SCALE_MAX)

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(prior_state)
    liking_by_person = state.get("liking_by_person", {})
    processed_ids = state.get("processed_favor_event_ids", [])
    if not isinstance(liking_by_person, dict):
        raise ValueError("state.liking_by_person must be a dict")
    if not isinstance(processed_ids, list) or any(not isinstance(item, str) for item in processed_ids):
        raise ValueError("state.processed_favor_event_ids must be a list of strings")

    # Validate all existing scores before preserving them in the returned state.
    normalized_likes = {}
    for person, score in liking_by_person.items():
        if not isinstance(person, str) or not person.strip():
            raise ValueError("state.liking_by_person keys must be non-empty strings")
        normalized_likes[person] = _finite_number(score, f"state liking for {person}", 0.0, _SCALE_MAX)

    current = normalized_likes.get(target_id, initial_liking)
    eligible = direction == "given" and effort > 0.0 and event_id not in processed_ids
    delta = 0.0
    if eligible:
        # A task-specific helper-rating process: a given favor closes an assumed
        # effort- and strength-weighted fraction of the remaining liking-scale gap.
        delta = _ADJUSTMENT_FRACTION * intervention * effort * (_SCALE_MAX - current)
    updated = min(_SCALE_MAX, current + delta)
    normalized_likes[target_id] = updated

    if direction == "given" and effort > 0.0 and event_id not in processed_ids:
        processed_ids = list(processed_ids)
        processed_ids.append(event_id)
    state["liking_by_person"] = normalized_likes
    state["processed_favor_event_ids"] = processed_ids

    trace = [
        f"target={target_id!r}; direction={direction!r}; effort={effort:.6g}; "
        f"strength={intervention:.6g}; prior_liking={current:.6g}.",
        "Reference rule: retain current helper liking; qualifying own-given favor rule: "
        "delta=0.25*strength*favor_effort*(100-current_liking).",
        f"eligible={eligible}; applied_delta={updated - current:.6g}; next_liking={updated:.6g}.",
    ]
    return {
        "metric": updated,
        "active": bool(updated != current),
        "state": state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    """Return paired chronological examples for the qualifying event and boundary."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "direction": "none",
                    "target_id": "colleague_A",
                    "favor_effort": 0.0,
                    "liking_before": 50.0,
                    "favor_event_id": "baseline-observation",
                },
                {
                    "direction": "given",
                    "target_id": "colleague_A",
                    "favor_effort": 0.5,
                    "liking_before": 50.0,
                    "favor_event_id": "favor-001",
                },
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "direction": "none",
                    "target_id": "colleague_A",
                    "favor_effort": 0.0,
                    "liking_before": 50.0,
                    "favor_event_id": "baseline-observation",
                },
                {
                    "direction": "received",
                    "target_id": "colleague_A",
                    "favor_effort": 0.5,
                    "liking_before": 50.0,
                    "favor_event_id": "received-favor-001",
                },
            ],
            "expectation": "equal",
        },
    ]
