"""Illustrative adverse-forecast distortion under inadequately supported pessimism."""
from __future__ import annotations

import math


_ADVERSE_SUPPORT_THRESHOLD = 0.60
_EVIDENCE_LOG_ODDS_WEIGHT = 1.20
_PESSIMISM_LOG_ODDS_WEIGHT = 1.40
_EPSILON = 1e-12

METADATA = {
    "id": "pessimism_bias",
    "name": "Pessimism bias",
    "kind": "cognitive_bias",
    "description": (
        "Raises an adverse-outcome forecast by selectively discounting supplied "
        "favorable evidence, but only when adverse evidence is insufficiently corroborated."
    ),
    "required_inputs": ["base_adverse_rate", "favorable_evidence", "adverse_evidence"],
    "state_fields": ["last_adverse_probability", "last_reference_probability", "bias_log_odds"],
    "metric_name": "adverse_outcome_forecast",
    "metric_units": "probability from 0 to 1 for the supplied hypothetical task",
    "assumptions": [
        "The supplied base rate and evidence-support scores are hypothetical task facts, not inferred from text.",
        "Evidence shifts log odds symmetrically in the strength-zero reference; the illustrative bias adds an asymmetric favorable-evidence discount.",
        "Adverse support of 0.60 or more is treated as adequate corroboration; the coefficient is an uncalibrated modeling choice.",
        "Strength is an intervention setting in [0, 1], not prevalence, confidence, or a fitted psychological effect size.",
    ],
    "limitations": [
        "This toy process does not detect pessimism in people or estimate real-world outcome probabilities.",
        "Support scores compress evidence quality and quantity into supplied numbers and omit source dependence and calibration.",
        "A justified adverse forecast is protected only by the stipulated support threshold; actual adequacy is context-specific.",
        "No empirical validity, diagnostic, or population-level claim is made.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(context: dict, key: str) -> float:
    if key not in context:
        raise ValueError(f"missing required task input: {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    return value


def _logit(probability: float) -> float:
    bounded = min(1.0 - _EPSILON, max(_EPSILON, probability))
    return math.log(bounded / (1.0 - bounded))


def _logistic(value: float) -> float:
    # Stable for large finite log odds.
    if value >= 0.0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def evaluate(context: dict, strength: float) -> dict:
    """Return the hypothetical adverse forecast without mutating supplied inputs."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")

    base = _unit_interval(context, "base_adverse_rate")
    favorable = _unit_interval(context, "favorable_evidence")
    adverse = _unit_interval(context, "adverse_evidence")

    # Reference: supplied evidence moves prior log odds in opposite directions.
    reference_log_odds = (
        _logit(base) + _EVIDENCE_LOG_ODDS_WEIGHT * (adverse - favorable)
    )
    reference_probability = _logistic(reference_log_odds)

    # The bias requires both favorable evidence to discount and a lack of
    # adequate adverse corroboration. It cannot activate on a justified adverse case.
    if favorable > 0.0 and adverse < _ADVERSE_SUPPORT_THRESHOLD:
        unsupported_fraction = 1.0 - adverse / _ADVERSE_SUPPORT_THRESHOLD
        bias_log_odds = (
            strength * _PESSIMISM_LOG_ODDS_WEIGHT * favorable * unsupported_fraction
        )
    else:
        bias_log_odds = 0.0
    forecast = _logistic(reference_log_odds + bias_log_odds)

    return {
        "metric": forecast,
        "active": forecast != reference_probability,
        "state": {
            "last_adverse_probability": forecast,
            "last_reference_probability": reference_probability,
            "bias_log_odds": bias_log_odds,
        },
        "trace": [
            "Reference log odds = logit(base_adverse_rate) + 1.20*(adverse_evidence-favorable_evidence).",
            (
                "When favorable_evidence>0 and adverse_evidence<0.60, add "
                "strength*1.40*favorable_evidence*(1-adverse_evidence/0.60) "
                f"to adverse log odds; applied bias={bias_log_odds:.12g}."
            ),
            f"Adverse forecast={forecast:.12g}; strength-zero reference={reference_probability:.12g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "base_adverse_rate": 0.35,
                "favorable_evidence": 0.80,
                "adverse_evidence": 0.15,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "base_adverse_rate": 0.35,
                "favorable_evidence": 0.80,
                "adverse_evidence": 0.80,
            }],
            "expectation": "equal",
        },
    ]
