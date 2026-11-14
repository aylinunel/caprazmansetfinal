"""Illustrative impact-bias process; structured inputs, not a detector or diagnosis."""
from __future__ import annotations

import math
from copy import deepcopy
from numbers import Real


METADATA = {
    "id": "impact_bias",
    "name": "Impact Bias",
    "kind": "cognitive_bias",
    "description": (
        "For each explicitly matched forecast and observed emotional course, "
        "amplifies only forecast peak intensity and duration that exceed the "
        "corresponding observed dimensions, then tracks burden error by event."
    ),
    "required_inputs": ["event_id", "forecast_peak", "forecast_duration", "observed_trajectory"],
    "state_fields": ["event_ids", "event_count", "cumulative_forecast_error"],
    "metric_name": "mean_predicted_emotional_burden_error",
    "metric_units": "intensity-steps per matched event (modeled peak × duration minus observed trajectory area)",
    "assumptions": [
        "Emotion intensity is on an illustrative 0–10 scale, and each trajectory entry is one time step.",
        "The supplied, complete trajectory is a comparable observation for this explicitly matched event.",
        "Forecast duration and count of positive observed steps use the same discrete time unit.",
        "Strength linearly controls illustrative amplification of positive peak and duration discrepancies; it is not calibrated confidence.",
    ],
    "limitations": [
        "This is a synthetic process assumption, not an empirically fitted or validated psychological law.",
        "An observed past trajectory may not predict a different event or person; context and emotion type are not modeled.",
        "The module requires structured matched data and does not detect forecasts, emotions, or diagnoses from text.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value: object, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    result = float(value)
    if not math.isfinite(result) or result < low or result > high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return result


def _validated_state(context: dict) -> dict:
    raw = context.get("state", {})
    if not isinstance(raw, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(raw)
    ids = state.get("event_ids", [])
    count = state.get("event_count", 0)
    error_sum = state.get("cumulative_forecast_error", 0.0)
    if not isinstance(ids, list) or any(not isinstance(item, str) for item in ids):
        raise ValueError("state.event_ids must be a list of strings")
    if len(set(ids)) != len(ids):
        raise ValueError("state.event_ids must be unique")
    if isinstance(count, bool) or not isinstance(count, int) or count != len(ids):
        raise ValueError("state.event_count must equal the number of stored event_ids")
    if isinstance(error_sum, bool) or not isinstance(error_sum, Real) or not math.isfinite(float(error_sum)):
        raise ValueError("state.cumulative_forecast_error must be finite")
    return {**state, "event_ids": ids, "event_count": count,
            "cumulative_forecast_error": float(error_sum)}


def evaluate(context: dict, strength: float) -> dict:
    """Score one explicitly matched forecast/outcome and retain chronological history."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required evidence: {', '.join(missing)}")
    event_id = context["event_id"]
    if not isinstance(event_id, str) or not event_id.strip():
        raise ValueError("event_id must be a non-empty string")
    forecast_peak = _number(context["forecast_peak"], "forecast_peak", 0.0, 10.0)
    forecast_duration = context["forecast_duration"]
    if isinstance(forecast_duration, bool) or not isinstance(forecast_duration, int) or forecast_duration <= 0:
        raise ValueError("forecast_duration must be a positive integer")
    trajectory = context["observed_trajectory"]
    if not isinstance(trajectory, (list, tuple)) or not trajectory:
        raise ValueError("observed_trajectory must be a non-empty sequence of intensities")
    observed = [_number(value, f"observed_trajectory[{i}]", 0.0, 10.0)
                for i, value in enumerate(trajectory)]
    # A complete discrete course uses trailing zeros after emotional intensity ends.
    first_zero = next((i for i, value in enumerate(observed) if value == 0.0), len(observed))
    if any(value != 0.0 for value in observed[first_zero:]):
        raise ValueError("observed_trajectory must have only trailing zeros after intensity ends")
    observed_peak = max(observed)
    observed_duration = first_zero
    observed_area = sum(observed)

    state = _validated_state(context)
    if event_id in state["event_ids"]:
        raise ValueError("event_id must be new; each matched event is scored once")

    # Strength-zero reference: retain the explicit supplied peak × duration forecast.
    # The illustrative impact-bias process exaggerates only dimensions where the
    # matched forecast exceeds the observed course; no excess means no intervention.
    peak_excess = max(0.0, forecast_peak - observed_peak)
    duration_excess = max(0, forecast_duration - observed_duration)
    modeled_peak = forecast_peak + strength * peak_excess
    modeled_duration = forecast_duration + strength * duration_excess
    raw_burden = forecast_peak * forecast_duration
    modeled_burden = modeled_peak * modeled_duration
    event_error = modeled_burden - observed_area

    state["event_ids"].append(event_id)
    state["event_count"] += 1
    state["cumulative_forecast_error"] += event_error
    metric = state["cumulative_forecast_error"] / state["event_count"]
    active = modeled_peak != forecast_peak or modeled_duration != forecast_duration
    return {
        "metric": float(metric),
        "active": bool(active),
        "state": state,
        "trace": [
            f"Matched event {event_id}: observed peak={observed_peak:g}, positive duration={observed_duration}, trajectory area={observed_area:g}.",
            f"Reference burden={raw_burden:g}; positive peak excess={peak_excess:g}, duration excess={duration_excess}; strength={strength:g} models peak={modeled_peak:g}, duration={modeled_duration:g}.",
            f"State records {state['event_count']} unique chronological event(s); mean modeled burden error={metric:g} intensity-steps/event.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"event_id": "loss-a", "forecast_peak": 8.0, "forecast_duration": 6,
                 "observed_trajectory": [6.0, 4.0, 2.0, 0.0]},
                {"event_id": "loss-b", "forecast_peak": 7.0, "forecast_duration": 5,
                 "observed_trajectory": [5.0, 3.0, 1.0, 0.0]},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"event_id": "matched-a", "forecast_peak": 6.0, "forecast_duration": 2,
                 "observed_trajectory": [6.0, 4.0, 0.0]},
                {"event_id": "matched-b", "forecast_peak": 4.0, "forecast_duration": 1,
                 "observed_trajectory": [4.0, 0.0]},
            ],
            "expectation": "equal",
        },
    ]
