"""Illustrative hindsight-bias reconstruction process for binary forecasts.

This is a synthetic process model, not a detector or empirically fitted model.
"""
from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "hindsight_bias",
    "name": "Hindsight Bias",
    "kind": "cognitive_bias",
    "description": (
        "After a binary outcome is known, reconstruct a remembered prior forecast "
        "by blending its recorded probability toward that outcome."
    ),
    "required_inputs": ["stage"],
    "conditional_inputs": {
        "forecast": ["forecast_probability"],
        "outcome": ["outcome_known"],
        "known_outcome": ["outcome"],
    },
    "state_fields": [
        "has_forecast",
        "original_probability",
        "recalled_probability",
        "outcome_known",
        "outcome",
        "resolved",
    ],
    "metric_name": "outcome-aligned retrospective forecast shift",
    "metric_units": "absolute probability-point change on a 0-1 scale",
    "assumptions": [
        "The recorded forecast is a trustworthy reference for what was stated before the outcome.",
        "Strength linearly controls illustrative reconstruction toward a known binary outcome.",
        "The effect is modeled only for a single binary event and an explicit forecast/outcome sequence.",
    ],
    "limitations": [
        "The linear blending rule is a task-specific illustrative assumption, not an estimated effect size.",
        "The process does not model memory noise, confidence reports, multiple outcomes, or decision quality.",
        "A numeric simulation is not an NLP detector and makes no population-level claim.",
        "Media practices and beneficial heuristics are outside this cognitive-bias mechanism.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _probability(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological forecast or outcome observation.

    Reference policy: retain the timestamped forecast verbatim. On the outcome
    stage, the modeled recollection is p + strength * (y - p), but only when
    outcome knowledge is explicitly available. The metric is the resulting
    shift toward y, in probability points; it is zero before/without outcome
    knowledge and at strength zero.
    """
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "stage" not in context:
        raise ValueError("missing required input: stage")
    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("state must be supplied as a dict")

    prior = context["state"]
    if "has_forecast" in prior and not isinstance(prior["has_forecast"], bool):
        raise ValueError("state.has_forecast must be bool")
    if "resolved" in prior and not isinstance(prior["resolved"], bool):
        raise ValueError("state.resolved must be bool")
    state = dict(prior)  # Preserve unrelated state fields; never mutate caller state.
    stage = context["stage"]
    metric = 0.0
    active = False

    if stage == "forecast":
        if prior.get("has_forecast", False):
            raise ValueError("a forecast is already stored; each event needs one forecast")
        if "forecast_probability" not in context:
            raise ValueError("missing required input: forecast_probability")
        p = _probability(context["forecast_probability"], "forecast_probability")
        state.update({
            "has_forecast": True,
            "original_probability": p,
            "recalled_probability": p,
            "outcome_known": False,
            "outcome": None,
            "resolved": False,
        })
        trace = (
            f"Forecast stage: recorded p={p:.6g}; baseline/reference and recalled probability "
            "remain p because no outcome has been revealed. Metric=0."
        )
    elif stage == "outcome":
        if not prior.get("has_forecast", False):
            raise ValueError("outcome stage requires a prior recorded forecast")
        if prior.get("resolved", False):
            raise ValueError("event has already been resolved")
        p = _probability(prior.get("original_probability"), "state.original_probability")
        if "outcome_known" not in context or not isinstance(context["outcome_known"], bool):
            raise ValueError("outcome stage requires explicit bool outcome_known")
        known = context["outcome_known"]
        if known:
            if "outcome" not in context:
                raise ValueError("known outcome requires outcome=0 or outcome=1")
            outcome = context["outcome"]
            if isinstance(outcome, bool) or not isinstance(outcome, int) or outcome not in (0, 1):
                raise ValueError("outcome must be integer 0 or 1")
            recalled = p + strength * (float(outcome) - p)
            metric = abs(recalled - p)
            active = metric > 0.0
            state.update({
                "recalled_probability": recalled,
                "outcome_known": True,
                "outcome": outcome,
                "resolved": True,
            })
            trace = (
                f"Known outcome stage: original p={p:.6g}, y={outcome}, strength={strength:.6g}; "
                f"recalled p = p + strength*(y-p) = {recalled:.6g}; "
                f"outcome-aligned shift=|recalled p-p|={metric:.6g}."
            )
        else:
            if "outcome" in context and context["outcome"] is not None:
                raise ValueError("outcome must be absent or None when outcome_known is false")
            recalled = p
            state.update({
                "recalled_probability": recalled,
                "outcome_known": False,
                "outcome": None,
                "resolved": True,
            })
            trace = (
                f"Outcome stage: outcome_known=False, so no outcome value is used; recorded and "
                f"recalled p both remain {p:.6g}. Metric=0 at strength={strength:.6g}."
            )
    else:
        raise ValueError("stage must be 'forecast' or 'outcome'")

    if not math.isfinite(metric):  # Defensive contract guarantee.
        raise ValueError("computed metric is not finite")
    return {"metric": metric, "active": active, "state": state, "trace": [trace]}


def scenarios() -> list[dict]:
    """Return chronological positive and necessary-condition boundary examples."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"stage": "forecast", "forecast_probability": 0.2},
                {"stage": "outcome", "outcome_known": True, "outcome": 1},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"stage": "forecast", "forecast_probability": 0.2},
                {"stage": "outcome", "outcome_known": False},
            ],
            "expectation": "equal",
        },
    ]
