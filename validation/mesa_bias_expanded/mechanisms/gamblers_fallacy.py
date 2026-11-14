"""Illustrative, synthetic gamblers' fallacy forecast process; not a detector."""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "gamblers_fallacy",
    "name": "Gambler's Fallacy",
    "kind": "cognitive_bias",
    "description": (
        "In a binary forecast task, a run of identical outcomes shifts the agent's "
        "subjective next-outcome probability toward reversal despite explicitly "
        "independent draws with stable base odds."
    ),
    "required_inputs": ["outcome", "base_probability_one", "independent"],
    "state_fields": ["observed_outcomes", "base_probability_one", "last_forecast"],
    "metric_name": "forecast_next_outcome_one",
    "metric_units": "Binary forecast (1 predicts outcome 1; 0 predicts outcome 0).",
    "assumptions": [
        "Each context supplies the realized binary outcome for this round and the stable probability that the next outcome is 1.",
        "At strength zero, the reference predicts 1 when base_probability_one >= 0.5 and otherwise predicts 0; ties predict 1.",
        "The illustrative reversal shift is 0.12 times the prior run length, capped at four, times strength; this coefficient is not an estimated effect size.",
        "A supplied independent=True is an explicit task fact. Stable base odds are checked across the carried sequence.",
        "Forecasting occurs before the current round's outcome is appended to history."
    ],
    "limitations": [
        "This is an explicit hypothetical process model, not empirically validated psychology, a classifier, or a population estimate.",
        "The run-length coefficient, cap, binary-choice threshold, and reference policy are illustrative assumptions, not calibrated measurements.",
        "The module does not infer independence or probability stability; non-independent processes suppress the reversal shift, and changing base odds are rejected.",
        "It does not model confidence, payoff-sensitive decisions, richer outcome spaces, or the beneficial use of streaks when odds genuinely change."
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _strength_value(strength: float) -> float:
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    value = float(strength)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    return value


def _probability(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return result


def _valid_history(value: object) -> list[int]:
    if not isinstance(value, list):
        raise ValueError("state.observed_outcomes must be a list of binary outcomes")
    if any(type(outcome) is not int or outcome not in (0, 1) for outcome in value):
        raise ValueError("state.observed_outcomes must contain only integer 0/1 outcomes")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Forecast once from prior history, then append this round's observation."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    strength = _strength_value(strength)
    for key in ("outcome", "base_probability_one", "independent"):
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    outcome = context["outcome"]
    if type(outcome) is not int or outcome not in (0, 1):
        raise ValueError("outcome must be integer 0 or 1")
    base_p = _probability(context["base_probability_one"], "base_probability_one")
    independent = context["independent"]
    if not isinstance(independent, bool):
        raise ValueError("independent must be supplied as a bool")

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    history = _valid_history(previous.get("observed_outcomes", []))
    prior_p = previous.get("base_probability_one")
    if history:
        prior_p = _probability(prior_p, "state.base_probability_one")
        if prior_p != base_p:
            raise ValueError("base_probability_one must remain stable across the sequence")
    elif prior_p is not None:
        raise ValueError("state.base_probability_one must be None when history is empty")

    last_forecast = previous.get("last_forecast")
    if last_forecast is not None and (type(last_forecast) is not int or last_forecast not in (0, 1)):
        raise ValueError("state.last_forecast must be None or integer 0/1")
    if not history and last_forecast is not None:
        raise ValueError("state.last_forecast must be None when history is empty")

    reference_forecast = int(base_p >= 0.5)
    run_length = 0
    if history:
        last_outcome = history[-1]
        for observed in reversed(history):
            if observed != last_outcome:
                break
            run_length += 1
    else:
        last_outcome = None

    eligible = independent and run_length > 0
    adjusted_p = base_p
    if eligible:
        reversal_shift = strength * 0.12 * min(run_length, 4)
        direction = 1.0 if last_outcome == 1 else -1.0
        adjusted_p = min(1.0, max(0.0, base_p - direction * reversal_shift))
    forecast = int(adjusted_p >= 0.5)

    next_history = history + [outcome]
    next_state = {
        "observed_outcomes": next_history,
        "base_probability_one": base_p,
        "last_forecast": forecast,
    }
    metric = float(forecast)
    if not math.isfinite(metric):
        raise ArithmeticError("metric is not finite")
    active = bool(forecast != reference_forecast)
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            f"Prior observed sequence={history}; prior same-outcome run length={run_length}.",
            f"Reference uses p1={base_p:g} and predicts {reference_forecast} (ties predict 1).",
            f"independent={independent}, eligible={eligible}; adjusted p1={adjusted_p:g} after "
            f"strength-scaled reversal shift, forecast={forecast}, active={active}.",
            f"Current outcome {outcome} appended only after forecasting; next history={next_history}.",
        ],
    }


def scenarios() -> list[dict]:
    streak = [
        {"outcome": 1, "base_probability_one": 0.5, "independent": True}
        for _ in range(5)
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": streak,
            "expectation": "difference",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [dict(item, independent=False) for item in streak],
            "expectation": "equal",
        },
    ]
