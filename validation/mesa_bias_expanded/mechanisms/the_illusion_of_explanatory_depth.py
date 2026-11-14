"""Illustrative explanation-depth gap process; not a detector or fitted psychology."""
from __future__ import annotations

import math


METADATA = {
    "id": "the_illusion_of_explanatory_depth",
    "name": "The Illusion of Explanatory Depth",
    "kind": "cognitive_bias",
    "description": (
        "Models excess perceived causal understanding when a pre-explanation "
        "self-assessment exceeds the parts demonstrated in a prompted explanation."
    ),
    # These fields are common to every scenario; validation of their values is phase-specific.
    "required_inputs": ["mechanism_parts", "explained_parts", "self_assessed_parts"],
    "state_fields": ["rounds", "cumulative_excess", "last_reported_depth", "last_demonstrated_depth"],
    "metric_name": "excess perceived explanatory depth",
    "metric_units": "fraction of the mechanism's causal parts (0 to 1)",
    "assumptions": [
        "A finite list of mechanism parts is a task-specific proxy for causal structure.",
        "The self-assessed count is elicited before an explanation prompt; explained count is observed afterward.",
        "Strength linearly interpolates the reported depth from demonstrated depth toward the prior self-assessment.",
        "Strength is an illustrative intervention setting, not a calibrated psychological effect size.",
    ],
    "limitations": [
        "The process is hypothetical and does not measure people or diagnose an individual.",
        "Part counts treat components as equally important and cannot represent explanation quality or dependencies.",
        "Low explanation coverage may reflect time, language, memory, motivation, or task design rather than an illusion.",
        "The model isolates an explanation-depth gap and makes no claim about general confidence or empirical prevalence.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _count(context: dict, key: str) -> int:
    value = context.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer count")
    return value


def _nonnegative_finite(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"state {name} must be a finite nonnegative number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"state {name} must be a finite nonnegative number")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Compare claimed pre-prompt depth with depth demonstrated in an explanation."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")

    total = _count(context, "mechanism_parts")
    explained = _count(context, "explained_parts")
    claimed = _count(context, "self_assessed_parts")
    if total <= 0:
        raise ValueError("mechanism_parts must be a positive integer")
    if not 0 <= explained <= total:
        raise ValueError("explained_parts must be between 0 and mechanism_parts")
    if not 0 <= claimed <= total:
        raise ValueError("self_assessed_parts must be between 0 and mechanism_parts")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be an object")
    rounds = prior.get("rounds", 0)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state rounds must be a nonnegative integer")
    cumulative = _nonnegative_finite(prior.get("cumulative_excess", 0.0), "cumulative_excess")

    demonstrated = explained / total
    claimed_depth = claimed / total
    gap = max(0.0, claimed_depth - demonstrated)
    reported = demonstrated + float(strength) * gap
    excess = reported - demonstrated

    next_state = dict(prior)
    next_state.update({
        "rounds": rounds + 1,
        "cumulative_excess": cumulative + excess,
        "last_reported_depth": reported,
        "last_demonstrated_depth": demonstrated,
    })
    return {
        "metric": excess,
        "active": bool(strength > 0 and gap > 0),
        "state": next_state,
        "trace": [
            f"Demonstrated depth={explained}/{total}={demonstrated:.6g}; "
            f"prior self-assessment={claimed}/{total}={claimed_depth:.6g}; "
            f"positive gap=max(0, self-assessment-demonstrated)={gap:.6g}; "
            f"reported depth=demonstrated+strength*gap={reported:.6g}; "
            f"metric=reported-demonstrated={excess:.6g}."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"rounds": 0, "cumulative_excess": 0.0},
            "contexts": [{"mechanism_parts": 8, "explained_parts": 2, "self_assessed_parts": 7}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"rounds": 0, "cumulative_excess": 0.0},
            # No positive self-assessment/explanation gap: the necessary condition is absent.
            "contexts": [{"mechanism_parts": 8, "explained_parts": 6, "self_assessed_parts": 3}],
            "expectation": "equal",
        },
    ]
