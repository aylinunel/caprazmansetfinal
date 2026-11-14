"""Illustrative process model for the illusion of transparency concept.

This is a hypothetical forecast model, not a detector or empirically fitted theory.
"""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any


METADATA = {
    "id": "illusion_of_transparency",
    "name": "Illusion of Transparency",
    "kind": "cognitive_bias",
    "description": (
        "Forecast audience recognition of an explicitly supplied private state. "
        "The illustrative mechanism projects some private intensity into the "
        "forecast when external cues are weak."
    ),
    "required_inputs": ["private_intensity", "cue_visibility", "audience_attention"],
    "state_fields": ["forecast_history", "last_forecast_probability", "step_count"],
    "metric_name": "forecast_audience_recognition_probability",
    "metric_units": "probability from 0 to 1 (unitless)",
    "assumptions": [
        "All three input values are explicit scenario facts normalized to [0, 1].",
        "Cue visibility times audience attention is the reference forecast.",
        "Strength linearly controls projection of private intensity into perceived visibility.",
        "The mechanism is a synthetic scenario assumption, not a measured human effect.",
    ],
    "limitations": [
        "Does not model real audiences, communication content, culture, or feedback.",
        "The numeric mapping and linear projection are illustrative, not empirically validated.",
        "It does not infer private states or classify text, images, or people.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(context: dict, name: str) -> float:
    if name not in context:
        raise ValueError(f"missing required input: {name}")
    value = context[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return the forecast and complete next state without mutating ``context``.

    Reference policy: forecast recognition from only externally supplied
    evidence, ``cue_visibility * audience_attention``. The mechanism adds a
    private-intensity projection, weighted by remaining cue opacity and
    audience attention: ``strength * private_intensity * attention *
    (1 - cue_visibility)``. Thus it cannot add a projection when private
    intensity is absent, audience attention is zero, or cues are fully visible.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    private_intensity = _unit_interval(context, "private_intensity")
    cue_visibility = _unit_interval(context, "cue_visibility")
    audience_attention = _unit_interval(context, "audience_attention")

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    prior = deepcopy(previous)
    history = prior.get("forecast_history", [])
    if not isinstance(history, list):
        raise ValueError("state.forecast_history must be a list")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(float(item))
        or not 0.0 <= float(item) <= 1.0
        for item in history
    ):
        raise ValueError("state.forecast_history must contain finite probabilities in [0, 1]")
    step_count = prior.get("step_count", len(history))
    if isinstance(step_count, bool) or not isinstance(step_count, int) or step_count < 0:
        raise ValueError("state.step_count must be a non-negative integer")
    if step_count != len(history):
        raise ValueError("state.step_count must match forecast_history length")

    reference = cue_visibility * audience_attention
    projection = strength * private_intensity * audience_attention * (1.0 - cue_visibility)
    forecast = reference + projection  # bounded by 1 for the validated inputs

    next_history = list(history)
    next_history.append(forecast)
    next_state = prior
    next_state["forecast_history"] = next_history
    next_state["last_forecast_probability"] = forecast
    next_state["step_count"] = step_count + 1
    return {
        "metric": float(forecast),
        "active": bool(projection > 0.0),
        "state": next_state,
        "trace": [
            f"reference=cue_visibility*audience_attention={reference:.6f}",
            "projection=strength*private_intensity*audience_attention*(1-cue_visibility)="
            f"{projection:.6f}",
            f"forecast=reference+projection={forecast:.6f}",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"private_intensity": 0.9, "cue_visibility": 0.2, "audience_attention": 0.8}
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                # No private feeling/intent to project: only the reference cue forecast remains.
                {"private_intensity": 0.0, "cue_visibility": 0.2, "audience_attention": 0.8}
            ],
            "expectation": "equal",
        },
    ]
