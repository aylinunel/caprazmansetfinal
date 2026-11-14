"""Illustrative process model for the illusion of validity.

This is a hypothetical, task-specific mechanism, not a psychological classifier.
"""

from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "illusion_of_validity",
    "name": "Illusion of Validity",
    "kind": "cognitive_bias",
    "description": (
        "In a binary prediction task, a unanimous set of cues can create an "
        "overconfident report when the cues' validated accuracy is below the "
        "accuracy used to interpret them."
    ),
    "required_inputs": [
        "cue_signs",
        "claimed_accuracy",
        "validated_accuracy",
        "base_rate",
    ],
    "state_fields": ["predicted_label", "confidence", "cue_count", "coherence"],
    "metric_name": "reported_prediction_confidence",
    "metric_units": "probability from 0 to 1 that the selected binary label is correct",
    "assumptions": [
        "Each cue is treated as conditionally independent by the reference rule.",
        "claimed_accuracy is the accuracy used to interpret each cue; validated_accuracy is an externally supplied task-level estimate.",
        "The illustrative confidence increase is proportional to cue unanimity, the claimed-versus-validated accuracy gap, and remaining headroom to certainty.",
        "Strength is a user-settable mechanism intensity, not a measured psychological effect size.",
    ],
    "limitations": [
        "This does not estimate real-world accuracy or detect the concept from text or behavior.",
        "Conditional independence and the confidence-inflation equation are stipulated for a synthetic demonstration, not empirically fitted.",
        "A coherent signal can be justified when its supplied validation supports its claimed accuracy; such cases receive no inflation.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value: Any, name: str, low: float, high: float, *, high_open: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or value < low or (value >= high if high_open else value > high):
        bracket = f"[{low}, {high})" if high_open else f"[{low}, {high}]"
        raise ValueError(f"{name} must be in {bracket}")
    return value


def _sigmoid(x: float) -> float:
    # Stable logistic transform, including very strong but finite evidence.
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one prediction step without mutating context or its state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    strength = _number(strength, "strength", 0.0, 1.0)
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required evidence: {', '.join(missing)}")

    cues = context["cue_signs"]
    if not isinstance(cues, (list, tuple)) or not cues:
        raise ValueError("cue_signs must be a non-empty list or tuple of -1/+1 values")
    if any(isinstance(cue, bool) or cue not in (-1, 1) for cue in cues):
        raise ValueError("each cue_sign must be exactly -1 or +1")
    cues = tuple(int(cue) for cue in cues)
    claimed = _number(context["claimed_accuracy"], "claimed_accuracy", 0.5, 1.0, high_open=True)
    validated = _number(context["validated_accuracy"], "validated_accuracy", 0.0, 1.0)
    base_rate = _number(context["base_rate"], "base_rate", 0.0, 1.0, high_open=True)
    if base_rate == 1.0:
        raise ValueError("base_rate must be strictly below 1")

    prior_log_odds = math.log(base_rate / (1.0 - base_rate))
    cue_log_likelihood_ratio = math.log(claimed / (1.0 - claimed))
    log_odds = prior_log_odds + sum(cues) * cue_log_likelihood_ratio
    predicted_label = 1 if log_odds >= 0.0 else -1
    reference_confidence = _sigmoid(abs(log_odds))

    positive_share = sum(1 for cue in cues if cue == 1) / len(cues)
    coherence = max(positive_share, 1.0 - positive_share)
    unanimous = coherence == 1.0
    overclaimed = validated < claimed
    necessary_condition = unanimous and overclaimed

    # The modeled illusion uses remaining confidence headroom: coherent
    # evidence and a larger reliability gap produce more unwarranted confidence.
    gap = max(0.0, claimed - validated) if necessary_condition else 0.0
    confidence_inflation = strength * coherence * gap * (1.0 - reference_confidence)
    metric = reference_confidence + confidence_inflation
    active = confidence_inflation > 0.0

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dictionary")
    next_state = dict(prior_state)
    next_state.update(
        {
            "predicted_label": predicted_label,
            "confidence": metric,
            "cue_count": len(cues),
            "coherence": coherence,
        }
    )
    trace = [
        "Reference: log_odds = log(base_rate/(1-base_rate)) + sum(cue_signs)*log(claimed_accuracy/(1-claimed_accuracy)); confidence = sigmoid(abs(log_odds)).",
        f"Cues={cues}; claimed_accuracy={claimed:.6g}; validated_accuracy={validated:.6g}; unanimous={unanimous}; overclaimed={overclaimed}; coherence={coherence:.6g}.",
        f"Concept process: inflation = strength*coherence*max(0, claimed_accuracy-validated_accuracy)*(1-reference_confidence) when unanimous and overclaimed, otherwise 0; metric={metric:.12g}.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "cue_signs": [1, 1, 1],
                    "claimed_accuracy": 0.8,
                    "validated_accuracy": 0.55,
                    "base_rate": 0.5,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "cue_signs": [1, 1, -1],
                    "claimed_accuracy": 0.8,
                    "validated_accuracy": 0.55,
                    "base_rate": 0.5,
                }
            ],
            "expectation": "equal",
        },
    ]
