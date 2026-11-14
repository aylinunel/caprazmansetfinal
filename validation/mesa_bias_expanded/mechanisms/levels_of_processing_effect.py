"""Illustrative, unvalidated levels-of-processing memory mechanism.

This is a transparent toy process model, not a psychological detector or fitted
account. See the implementation note for the task and assumptions.
"""
from __future__ import annotations

import math
from copy import deepcopy


_ENCODING_COEFFICIENT = 1.5
_RETRIEVAL_CRITERION = 1.5

METADATA = {
    "id": "levels_of_processing_effect",
    "name": "Levels of Processing",
    "kind": "learning_effect",
    "description": (
        "Meaning-oriented processing adds an explicit elaboration dose to an "
        "item's memory trace, with study exposure held constant."
    ),
    # Exposure and depth are study-only fields and are validated in evaluate().
    "required_inputs": ["action", "item_id"],
    "state_fields": ["items", "last_item_id", "last_action", "events"],
    "metric_name": "recall_probability",
    "metric_units": "deterministic model probability from 0 to 1; not an empirical estimate",
    "assumptions": [
        "Each study exposure adds one unit of reference trace per exposure_unit.",
        "Semantic processing depth is an explicit scenario input in [0, 1].",
        "At strength s, elaboration adds 1.5*s*depth times exposure_units to trace.",
        "Recall probability is the logistic transform of trace minus criterion 1.5.",
        "Repeated study events accumulate; exposure and probe conditions are otherwise controlled.",
    ],
    "limitations": [
        "Illustrative coefficients and logistic readout are user-set assumptions, not fitted effect sizes.",
        "The module does not infer processing depth, semantic meaning, or actual human recall.",
        "Attention, distinctiveness, prior knowledge, interference, and many other causes are omitted.",
        "A higher modeled recall probability is a memory-framework outcome, not irrationality or harm.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _empty_state() -> dict:
    return {"items": {}, "last_item_id": None, "last_action": None, "events": 0}


def _validated_state(raw: object) -> dict:
    if raw is None:
        return _empty_state()
    if not isinstance(raw, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(raw)
    items = state.get("items", {})
    if not isinstance(items, dict):
        raise ValueError("state.items must be a dict")
    validated_items = {}
    for item_id, record in items.items():
        if not isinstance(item_id, str) or not item_id or not isinstance(record, dict):
            raise ValueError("state.items must map nonempty item IDs to records")
        clean = {}
        for field in ("trace", "reference_trace", "exposure_units", "elaboration_dose"):
            if field not in record:
                raise ValueError(f"state item record missing {field}")
            clean[field] = _finite_number(record[field], f"state item {field}")
            if clean[field] < 0:
                raise ValueError(f"state item {field} cannot be negative")
        validated_items[item_id] = clean
    events = state.get("events", 0)
    if isinstance(events, bool) or not isinstance(events, int) or events < 0:
        raise ValueError("state.events must be a nonnegative integer")
    last_item_id = state.get("last_item_id")
    last_action = state.get("last_action")
    if last_item_id is not None and (not isinstance(last_item_id, str) or not last_item_id):
        raise ValueError("state.last_item_id must be a nonempty string or None")
    if last_action is not None and last_action not in ("study", "probe"):
        raise ValueError("state.last_action must be study, probe, or None")
    return {
        "items": validated_items,
        "last_item_id": last_item_id,
        "last_action": last_action,
        "events": events,
    }


def evaluate(context: dict, strength: float) -> dict:
    """Apply one study or probe event, returning metric, active flag, state, trace."""
    s = _finite_number(strength, "strength")
    if not 0.0 <= s <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    action = context.get("action")
    item_id = context.get("item_id")
    if action not in ("study", "probe"):
        raise ValueError("action must be 'study' or 'probe'")
    if not isinstance(item_id, str) or not item_id:
        raise ValueError("item_id must be a nonempty string")

    state = _validated_state(context.get("state"))
    record = state["items"].get(item_id)
    metric = 0.0
    active = False
    trace = []

    if action == "study":
        exposure = _finite_number(context.get("exposure_units"), "exposure_units")
        depth = _finite_number(context.get("processing_depth"), "processing_depth")
        if exposure <= 0:
            raise ValueError("exposure_units must be greater than zero")
        if not 0.0 <= depth <= 1.0:
            raise ValueError("processing_depth must be in [0, 1]")
        if record is None:
            record = {"trace": 0.0, "reference_trace": 0.0,
                      "exposure_units": 0.0, "elaboration_dose": 0.0}
        reference_increment = exposure
        elaboration_dose = exposure * depth
        trace_increment = reference_increment * (1.0 + _ENCODING_COEFFICIENT * s * depth)
        record["reference_trace"] += reference_increment
        record["trace"] += trace_increment
        record["exposure_units"] += exposure
        record["elaboration_dose"] += elaboration_dose
        state["items"][item_id] = record
        active = trace_increment > reference_increment
        trace.append(
            f"Study item {item_id!r}: exposure={exposure:g}, depth={depth:g}; "
            f"reference trace += {reference_increment:g}, modeled trace += "
            f"{trace_increment:g} = exposure*(1 + 1.5*strength*depth)."
        )
        trace.append("No retrieval was requested on this study event; metric is 0 until a probe.")
    else:
        if record is None or record["exposure_units"] <= 0:
            raise ValueError(f"cannot probe item {item_id!r} before a valid study event")
        metric = 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0,
                                                         record["trace"] - _RETRIEVAL_CRITERION))))
        reference_metric = 1.0 / (1.0 + math.exp(-max(-700.0, min(700.0,
                                                                  record["reference_trace"] - _RETRIEVAL_CRITERION))))
        active = not math.isclose(metric, reference_metric, rel_tol=0.0, abs_tol=1e-15)
        trace.append(
            f"Probe item {item_id!r}: recall_probability=sigmoid(trace-1.5)="
            f"{metric:.12g}; reference=sigmoid(reference_trace-1.5)="
            f"{reference_metric:.12g}."
        )

    state["last_item_id"] = item_id
    state["last_action"] = action
    state["events"] += 1
    return {"metric": float(metric), "active": bool(active), "state": state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"action": "study", "item_id": "word-A", "exposure_units": 1.0, "processing_depth": 1.0},
                {"action": "probe", "item_id": "word-A"},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"action": "study", "item_id": "word-A", "exposure_units": 1.0, "processing_depth": 0.0},
                {"action": "probe", "item_id": "word-A"},
            ],
            "expectation": "equal",
        },
    ]
