"""Illustrative structured process model for leveling and sharpening in retelling."""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "leveling_and_sharpening",
    "name": "Leveling and Sharpening",
    "kind": "cognitive_bias",
    "description": (
        "Across supplied retellings, details with below-average salience lose "
        "more remembered intensity toward neutral, while above-average-salience "
        "details retain and accentuate more intensity."
    ),
    "required_inputs": ["details", "retention"],
    "state_fields": ["source_details", "memory", "retell_count", "history"],
    "metric_name": "mean_absolute_detail_distortion",
    "metric_units": "mean absolute intensity difference from source, on a 0-1 scale",
    "assumptions": [
        "Each detail has a supplied normalized intensity and salience in [0,1].",
        "Intensity 0.5 is a neutral point toward which leveling acts.",
        "The supplied retention is a baseline per-retelling retention applied equally by the reference policy.",
        "The differential salience coefficient 0.5 is an illustrative modeling choice, not an estimated effect size.",
    ],
    "limitations": [
        "This is a hypothetical structured process model, not an empirical finding, diagnosis, or detector.",
        "Salience and detail intensities are explicit inputs; the module does not infer them from text or hidden mental states.",
        "Ordinary summarization and intentional editing are not identified as memory distortion by this model.",
        "The one-dimensional intensity representation omits semantic content, retrieval cues, social goals, and individual differences.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_NEUTRAL = 0.5
_DIFFERENTIAL_COEFFICIENT = 0.5
_TOL = 1e-12


def _unit_interval(value, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    return number


def _validate_details(details) -> list[dict]:
    if not isinstance(details, list) or not details:
        raise ValueError("details must be a non-empty list of {id, intensity, salience}")
    result = []
    seen = set()
    for index, item in enumerate(details):
        if not isinstance(item, dict) or not {"id", "intensity", "salience"}.issubset(item):
            raise ValueError(f"details[{index}] must contain id, intensity, and salience")
        identifier = item["id"]
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("detail ids must be unique, non-empty strings")
        seen.add(identifier)
        result.append({
            "id": identifier,
            "intensity": _unit_interval(item["intensity"], f"details[{index}].intensity"),
            "salience": _unit_interval(item["salience"], f"details[{index}].salience"),
        })
    return result


def _validate_prior_state(state, details) -> tuple[list[float], int, list]:
    ids = [detail["id"] for detail in details]
    if state == {}:
        return [detail["intensity"] for detail in details], 0, []
    if not isinstance(state, dict) or not {"source_details", "memory", "retell_count", "history"}.issubset(state):
        raise ValueError("state must be empty initially or contain the complete mechanism state")
    if state["source_details"] != details:
        raise ValueError("source details and saliences must remain unchanged across retellings")
    memory = state["memory"]
    if not isinstance(memory, list) or len(memory) != len(ids):
        raise ValueError("state.memory must contain one intensity for every source detail")
    values = [_unit_interval(value, "state.memory intensity") for value in memory]
    count = state["retell_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise ValueError("state.retell_count must be a positive integer")
    history = state["history"]
    if not isinstance(history, list) or len(history) != count:
        raise ValueError("state.history must contain one snapshot per prior retelling")
    for snapshot in history:
        if not isinstance(snapshot, list) or len(snapshot) != len(ids):
            raise ValueError("each history snapshot must align with source details")
        for value in snapshot:
            _unit_interval(value, "state.history intensity")
    return values, count, [list(snapshot) for snapshot in history]


def evaluate(context: dict, strength: float) -> dict:
    """Advance one chronological retelling and report distortion from source."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "details" not in context or "retention" not in context:
        raise ValueError("required evidence missing: details and retention are required")
    details = _validate_details(context["details"])
    retention = _unit_interval(context["retention"], "retention")
    state = context.get("state", {})
    previous, prior_count, history = _validate_prior_state(state, details)

    mean_salience = sum(item["salience"] for item in details) / len(details)
    updated = []
    reference = []
    for item, remembered in zip(details, previous):
        # Reference is uniform retention. The mechanism changes the retention
        # multiplier according to signed salience distance from the item mean.
        ref_value = _NEUTRAL + (remembered - _NEUTRAL) * retention
        multiplier = 1.0 + _DIFFERENTIAL_COEFFICIENT * strength * (item["salience"] - mean_salience)
        raw_value = _NEUTRAL + (remembered - _NEUTRAL) * retention * multiplier
        # Intensities are bounded quantities, so sharpening saturates at the
        # scale endpoint rather than creating an impossible remembered value.
        value = min(1.0, max(0.0, raw_value))
        reference.append(ref_value)
        updated.append(value)

    distortion = sum(abs(value - item["intensity"]) for value, item in zip(updated, details)) / len(details)
    active = any(abs(value - ref) > _TOL for value, ref in zip(updated, reference))
    history.append(list(updated))
    next_state = {
        "source_details": [dict(item) for item in details],
        "memory": list(updated),
        "retell_count": prior_count + 1,
        "history": history,
    }
    trace = [
        "Per detail: m_next = 0.5 + (m_prev - 0.5) * retention * "
        "[1 + 0.5 * strength * (salience - mean_salience)].",
        f"Inputs: strength={strength:g}, retention={retention:g}, mean_salience={mean_salience:g}, "
        f"retell={prior_count + 1}; detail intensities={updated}.",
        "Primary metric is the unweighted mean absolute difference between current remembered "
        "intensities and supplied source intensities; equal-salience details make the "
        "differential multiplier exactly 1.",
    ]
    return {"metric": float(distortion), "active": bool(active), "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    positive_details = [
        {"id": "minor", "intensity": 0.8, "salience": 0.2},
        {"id": "central", "intensity": 0.7, "salience": 0.8},
    ]
    equal_salience_details = [
        {"id": "detail_a", "intensity": 0.8, "salience": 0.5},
        {"id": "detail_b", "intensity": 0.9, "salience": 0.5},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"details": positive_details, "retention": 1.0},
                {"details": positive_details, "retention": 1.0},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"details": equal_salience_details, "retention": 1.0},
                {"details": equal_salience_details, "retention": 1.0},
            ],
            "expectation": "equal",
        },
    ]
