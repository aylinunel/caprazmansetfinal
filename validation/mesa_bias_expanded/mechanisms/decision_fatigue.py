"""Illustrative sequential decision-fatigue process model; not a detector."""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "decision_fatigue",
    "name": "Decision Fatigue",
    "kind": "psychological_state",
    "description": (
        "A hypothetical accumulated decision-load state can trigger an effort-avoidant "
        "choice shortcut on a later decision."
    ),
    "required_inputs": ["options", "decision_load"],
    "state_fields": ["accumulated_load", "decisions_seen", "last_choice"],
    "metric_name": "utility_regret",
    "metric_units": "utility units lost versus selecting the highest-utility option on this task",
    "assumptions": [
        "Each decision_load is an explicit, normalized [0,1] task-load observation, not a time-of-day proxy.",
        "Load carries forward with illustrative retention 0.75 per decision.",
        "At strength × carried load >= 0.60, a hypothetical exhausted chooser selects the least-effort option.",
        "The strength parameter is an illustrative sensitivity setting, not a fitted effect size.",
    ],
    "limitations": [
        "This is an assumed process model, not a diagnosis, classifier, or empirically validated psychology model.",
        "Utility and effort are supplied by the scenario; real fatigue can have many causes and outcomes.",
        "A shortcut may be benign or even utility-improving; only utility loss is counted as regret.",
        "The model does not infer fatigue from time, wording, or unobserved internal states.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_DECAY = 0.75
_THRESHOLD = 0.60


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological choice without mutating supplied context/state."""
    strength_value = _finite_number(strength, "strength")
    if not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be within [0,1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in ("options", "decision_load", "state") if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    load = _finite_number(context["decision_load"], "decision_load")
    if not 0.0 <= load <= 1.0:
        raise ValueError("decision_load must be within [0,1]")

    raw_options = context["options"]
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError("options must be a list containing at least two options")
    options = []
    seen_ids = set()
    for index, raw in enumerate(raw_options):
        if not isinstance(raw, dict):
            raise ValueError(f"options[{index}] must be a dict")
        option_id = raw.get("id")
        if not isinstance(option_id, str) or not option_id.strip() or option_id in seen_ids:
            raise ValueError("each option must have a unique non-empty string id")
        seen_ids.add(option_id)
        utility = _finite_number(raw.get("utility"), f"options[{index}].utility")
        effort = _finite_number(raw.get("effort"), f"options[{index}].effort")
        if not 0.0 <= effort <= 1.0:
            raise ValueError(f"options[{index}].effort must be within [0,1]")
        options.append({"id": option_id, "utility": utility, "effort": effort})

    prior = context["state"]
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    burden = _finite_number(prior.get("accumulated_load", 0.0), "state.accumulated_load")
    count_value = prior.get("decisions_seen", 0)
    if isinstance(count_value, bool) or not isinstance(count_value, int) or count_value < 0:
        raise ValueError("state.decisions_seen must be a non-negative integer")
    last_choice = prior.get("last_choice")
    if last_choice is not None and not isinstance(last_choice, str):
        raise ValueError("state.last_choice must be a string or None")
    if burden < 0.0:
        raise ValueError("state.accumulated_load must be non-negative")

    # Reference policy: choose maximum supplied utility; input order breaks ties.
    reference = max(options, key=lambda option: option["utility"])
    # Fatigue acts only on a later choice, using load accumulated by earlier decisions.
    pressure = strength_value * burden
    fatigued = count_value > 0 and pressure >= _THRESHOLD
    chosen = min(options, key=lambda option: option["effort"]) if fatigued else reference
    # If effort ties, min() consistently keeps the first input option.
    regret = reference["utility"] - chosen["utility"]
    next_state = {
        "accumulated_load": _DECAY * burden + load,
        "decisions_seen": count_value + 1,
        "last_choice": chosen["id"],
    }
    return {
        "metric": float(regret),
        "active": bool(fatigued and chosen["id"] != reference["id"]),
        "state": next_state,
        "trace": [
            f"Carried load={burden:.6g}; current decision_load={load:.6g}; "
            f"fatigue pressure=strength({strength_value:.6g}) × carried load={pressure:.6g} "
            f"(threshold {_THRESHOLD}, prior decisions={count_value}).",
            f"Reference chooses max utility ({reference['id']}={reference['utility']:.6g}); "
            f"fatigue shortcut={'least effort' if fatigued else 'not triggered'} chooses {chosen['id']}.",
            f"Metric is max utility minus chosen utility = {regret:.6g}; next load="
            f"{_DECAY} × {burden:.6g} + {load:.6g}.",
        ],
    }


def scenarios() -> list[dict]:
    tradeoff = [
        {"id": "thorough", "utility": 10.0, "effort": 0.9},
        {"id": "defer", "utility": 6.0, "effort": 0.1},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"options": tradeoff, "decision_load": 0.8},
                {"options": tradeoff, "decision_load": 0.8},
                {"options": tradeoff, "decision_load": 0.8},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"options": tradeoff, "decision_load": 0.0},
                {"options": tradeoff, "decision_load": 0.0},
                {"options": tradeoff, "decision_load": 0.0},
            ],
            "expectation": "equal",
        },
    ]
