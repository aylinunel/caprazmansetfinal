"""Illustrative sequential model of the hard-easy confidence calibration pattern."""

from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "hard_easy_effect",
    "name": "Hard-easy effect",
    "kind": "cognitive_bias",
    "description": (
        "After both task-difficulty levels are represented, confidence is nudged "
        "toward 1 on hard tasks and toward 0 on easy tasks; the observable is "
        "the difference in mean signed calibration residuals across the levels."
    ),
    "required_inputs": ["difficulty", "reference_confidence", "outcome"],
    "state_fields": ["observations", "last_confidence"],
    "metric_name": "hard_minus_easy_mean_calibration_residual",
    "metric_units": "probability points (confidence minus binary outcome; unit interval scale)",
    "assumptions": [
        "Difficulty is supplied explicitly as 'hard' or 'easy'; it is not inferred.",
        "reference_confidence is the explicit confidence from a fixed reference policy.",
        "outcome is a known binary task result, used to calculate signed calibration residuals.",
        "The illustrative maximum adjustment coefficient is 0.25; strength scales it linearly.",
        "The cross-difficulty pattern is eligible only after at least one task of each level has occurred.",
    ],
    "limitations": [
        "This is a stipulated toy process, not an empirically fitted or validated psychological model.",
        "The model assumes exogenous difficulty labels, reference confidences, and outcomes.",
        "A short or unbalanced sequence gives a noisy descriptive contrast, not a population estimate.",
        "No natural-language task classifier, individual diagnosis, or causal inference is provided.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_ADJUSTMENT_COEFFICIENT = 0.25
_VALID_DIFFICULTIES = {"hard", "easy"}


def _probability(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return result


def _validate_observation(item: object, index: int) -> dict:
    if not isinstance(item, dict):
        raise ValueError(f"state.observations[{index}] must be a mapping")
    difficulty = item.get("difficulty")
    if not isinstance(difficulty, str) or difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"state.observations[{index}].difficulty must be 'hard' or 'easy'")
    reference = _probability(item.get("reference_confidence"), f"state.observations[{index}].reference_confidence")
    outcome = item.get("outcome")
    if isinstance(outcome, bool) or not isinstance(outcome, Real) or outcome not in (0, 1):
        raise ValueError(f"state.observations[{index}].outcome must be numeric 0 or 1")
    confidence = _probability(item.get("confidence"), f"state.observations[{index}].confidence")
    return {
        "difficulty": difficulty,
        "reference_confidence": reference,
        "outcome": int(outcome),
        "confidence": confidence,
    }


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one task and return its confidence, calibration contrast, and next state."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a mapping")

    missing = [field for field in METADATA["required_inputs"] if field not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    difficulty = context["difficulty"]
    if not isinstance(difficulty, str) or difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be exactly 'hard' or 'easy'")
    reference = _probability(context["reference_confidence"], "reference_confidence")
    outcome = context["outcome"]
    if isinstance(outcome, bool) or not isinstance(outcome, Real) or outcome not in (0, 1):
        raise ValueError("outcome must be numeric 0 or 1")
    outcome = int(outcome)

    raw_state = context.get("state", {})
    if not isinstance(raw_state, dict):
        raise ValueError("state must be a mapping")
    prior_raw = raw_state.get("observations", [])
    if not isinstance(prior_raw, list):
        raise ValueError("state.observations must be a list")
    observations = [_validate_observation(item, i) for i, item in enumerate(prior_raw)]

    represented = {item["difficulty"] for item in observations}
    pattern_eligible = len(represented | {difficulty}) == 2
    adjustment = 0.0
    if pattern_eligible:
        # Hard-task confidence is pulled upward; easy-task confidence downward.
        # The distance to the relevant bound prevents out-of-range confidence.
        adjustment = strength * _ADJUSTMENT_COEFFICIENT * (
            (1.0 - reference) if difficulty == "hard" else -reference
        )
    confidence = min(1.0, max(0.0, reference + adjustment))
    observations.append({
        "difficulty": difficulty,
        "reference_confidence": reference,
        "outcome": outcome,
        "confidence": confidence,
    })

    by_difficulty: dict[str, list[float]] = {"hard": [], "easy": []}
    for item in observations:
        by_difficulty[item["difficulty"]].append(item["confidence"] - item["outcome"])
    if by_difficulty["hard"] and by_difficulty["easy"]:
        metric = (
            sum(by_difficulty["hard"]) / len(by_difficulty["hard"])
            - sum(by_difficulty["easy"]) / len(by_difficulty["easy"])
        )
    else:
        # A cross-difficulty contrast is zero until its necessary paired levels exist.
        metric = 0.0

    if not math.isfinite(metric):
        raise ValueError("computed metric is not finite")
    next_state = {
        "observations": observations,
        "last_confidence": confidence,
    }
    trace = [
        f"Reference confidence={reference:.6g}; outcome={outcome}; difficulty={difficulty}.",
        (
            f"Both difficulty levels represented={pattern_eligible}; adjustment="
            f"strength * 0.25 * {'(1-reference_confidence)' if difficulty == 'hard' else '-reference_confidence'} "
            f"= {adjustment:.6g}; resulting confidence={confidence:.6g}."
        ),
        (
            "Metric is mean(confidence-outcome) for hard observations minus the same mean for easy observations; "
            f"metric={metric:.6g}."
        ),
    ]
    return {
        "metric": float(metric),
        "active": bool(pattern_eligible and confidence != reference),
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0},
                {"difficulty": "easy", "reference_confidence": 0.5, "outcome": 1},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0},
                {"difficulty": "hard", "reference_confidence": 0.5, "outcome": 0},
            ],
            "expectation": "equal",
        },
    ]
