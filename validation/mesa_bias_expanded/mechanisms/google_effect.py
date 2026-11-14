"""Illustrative memory-offloading process for the Google Effect concept.

This is a synthetic process model, not a detector or fitted psychological model.
"""

import math


_OFFLOAD_RATE = 0.60

METADATA = {
    "id": "google_effect",
    "name": "Google Effect",
    "kind": "learning_effect",
    "description": (
        "Expected future access to an external source attenuates memory-signal "
        "encoding during study; retrieval reports the resulting modeled recall."
    ),
    "required_inputs": ["action"],
    "conditional_inputs": {"study": ["items"], "retrieve": ["item_ids"]},
    "state_fields": ["memory_traces"],
    "metric_name": "modeled_recall_units",
    "metric_units": "sum of item-level recall probabilities on a retrieval step",
    "assumptions": [
        "A study event adds a baseline memory signal of 1/(1+difficulty).",
        "Expected external availability attenuates that signal by strength times 0.60.",
        "Recall probability for an item is 1-exp(-accumulated memory signal).",
        "Difficulty is a supplied task parameter, not an inferred learner trait.",
        "The strength parameter is an illustrative intervention setting, not an effect size.",
    ],
    "limitations": [
        "Synthetic, single-task process model; not empirically validated or calibrated.",
        "Does not model source quality, actual retrieval success, forgetting over time, or individual differences.",
        "Expected access must be explicitly supplied; it is not inferred from lookup behavior.",
        "Lower modeled recall is not by itself an error or harmful outcome; external lookup may be beneficial.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    if low is not None and number < low:
        raise ValueError(f"{label} must be >= {low}")
    if high is not None and number > high:
        raise ValueError(f"{label} must be <= {high}")
    return number


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    action = context.get("action")
    if action not in ("study", "retrieve"):
        raise ValueError("action must be 'study' or 'retrieve'")

    if action == "study":
        items = context.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("study requires a non-empty items list")
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("each study item must be a dict")
            item_id = item.get("item_id")
            if not isinstance(item_id, str) or not item_id.strip():
                raise ValueError("study item_id must be a non-empty string")
            if item_id in seen:
                raise ValueError("study item_ids must be unique within an event")
            seen.add(item_id)
            _finite_number(item.get("difficulty"), "difficulty", 0.0, 1.0)
            if type(item.get("expected_external_access")) is not bool:
                raise ValueError("expected_external_access must be bool")
            if type(item.get("external_lookup_used")) is not bool:
                raise ValueError("external_lookup_used must be bool")
    else:
        item_ids = context.get("item_ids")
        if not isinstance(item_ids, list) or not item_ids:
            raise ValueError("retrieve requires a non-empty item_ids list")
        if any(not isinstance(item_id, str) or not item_id.strip() for item_id in item_ids):
            raise ValueError("retrieval item_ids must be non-empty strings")
        if len(set(item_ids)) != len(item_ids):
            raise ValueError("retrieval item_ids must be unique")
    return action


def evaluate(context: dict, strength: float) -> dict:
    """Apply one study or retrieval event and return its metric and full next state."""
    strength = _finite_number(strength, "strength", 0.0, 1.0)
    action = _validate_context(context)

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    prior_traces = prior.get("memory_traces", {})
    if not isinstance(prior_traces, dict):
        raise ValueError("state.memory_traces must be a dict")
    traces = {}
    for item_id, signal in prior_traces.items():
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("state memory_traces keys must be non-empty strings")
        traces[item_id] = _finite_number(signal, f"memory trace for {item_id}", 0.0)

    metric = 0.0
    active = False
    trace = []
    if action == "study":
        for item in context["items"]:
            item_id = item["item_id"]
            difficulty = float(item["difficulty"])
            expected = item["expected_external_access"]
            lookup_used = item["external_lookup_used"]
            baseline_signal = 1.0 / (1.0 + difficulty)
            # Only an explicit expectation of later access changes encoding.
            # Lookup use alone is recorded as context, but is not sufficient.
            encoding_factor = 1.0 - strength * _OFFLOAD_RATE if expected else 1.0
            encoded_signal = baseline_signal * encoding_factor
            traces[item_id] = traces.get(item_id, 0.0) + encoded_signal
            changed = expected and strength > 0.0
            active = active or changed
            trace.append(
                f"study {item_id}: baseline=1/(1+{difficulty:g})={baseline_signal:.12g}; "
                f"expected_external_access={expected}; external_lookup_used={lookup_used}; "
                f"encoding_factor=1-{strength:g}*{_OFFLOAD_RATE:g}={encoding_factor:.12g}; "
                f"added_signal={encoded_signal:.12g}"
            )
    else:
        unknown = [item_id for item_id in context["item_ids"] if item_id not in traces]
        if unknown:
            raise ValueError(f"cannot retrieve items without study evidence: {unknown}")
        probabilities = []
        for item_id in context["item_ids"]:
            probability = 1.0 - math.exp(-traces[item_id])
            probabilities.append(probability)
            trace.append(
                f"retrieve {item_id}: signal={traces[item_id]:.12g}; "
                f"recall_probability=1-exp(-signal)={probability:.12g}"
            )
        metric = sum(probabilities)
        trace.append(f"metric=sum(recall probabilities)={metric:.12g}")

    if not math.isfinite(metric):
        raise ValueError("computed metric is not finite")
    return {
        "metric": metric,
        "active": bool(active),
        "state": {"memory_traces": traces},
        "trace": trace,
    }


def scenarios() -> list[dict]:
    """Return chronological, synthetic positive and necessary-condition boundary cases."""
    return [
        {
            "name": "positive",
            "initial_state": {"memory_traces": {}},
            "contexts": [
                {"action": "study", "items": [{"item_id": "river", "difficulty": 0.0,
                    "expected_external_access": True, "external_lookup_used": False}]},
                {"action": "retrieve", "item_ids": ["river"]},
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {"memory_traces": {}},
            "contexts": [
                {"action": "study", "items": [{"item_id": "river", "difficulty": 0.0,
                    "expected_external_access": False, "external_lookup_used": True}]},
                {"action": "retrieve", "item_ids": ["river"]},
            ],
            "expectation": "equal",
        },
    ]
