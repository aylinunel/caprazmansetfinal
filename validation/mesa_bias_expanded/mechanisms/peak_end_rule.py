"""Illustrative chronological peak-end weighting for completed episodes."""
from copy import deepcopy
import math


METADATA = {
    "id": "peak_end_rule",
    "name": "Peak-end Rule",
    "kind": "cognitive_bias",
    "description": (
        "At an explicitly marked episode ending, blend the experience mean with "
        "the equally weighted highest satisfaction and final satisfaction."
    ),
    "required_inputs": ["moment_score", "episode_end"],
    "state_fields": ["observed_scores", "episode_ended", "retrospective_rating"],
    "metric_name": "episode_satisfaction_rating",
    "metric_units": "Illustrative satisfaction points on a 0-10 scale",
    "assumptions": [
        "Moment scores are supplied, comparable satisfaction ratings, not inferred from text.",
        "Only an explicit episode_end=True marks a completed retrospective evaluation.",
        "The peak is the highest satisfaction score; the ending score is the final observation.",
        "At full strength, the peak/end summary receives an illustrative 0.6 mixture weight.",
        "Strength is an uncalibrated intervention parameter, not a confidence or prevalence estimate.",
    ],
    "limitations": [
        "This is a narrow hypothetical process model, not a detector, diagnosis, or empirical estimate.",
        "It treats satisfaction as a one-dimensional supplied score and does not model affect intensity, duration, or recall dynamics.",
        "The peak is defined as the maximum score; other operationalizations could differ.",
        "A marked ending is task evidence only and does not establish that a real person uses this rule.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _strength(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    strength = _strength(strength)
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required task input {field}")
    score = context["moment_score"]
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 10:
        raise ValueError("moment_score must be finite numeric satisfaction in [0, 10]")
    ending = context["episode_end"]
    if not isinstance(ending, bool):
        raise ValueError("episode_end must be a boolean")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be an object")
    scores = prior.get("observed_scores", [])
    completed = prior.get("episode_ended", False)
    if (not isinstance(scores, list) or any(isinstance(x, bool) or not isinstance(x, (int, float))
                                            or not math.isfinite(x) or not 0 <= x <= 10 for x in scores)):
        raise ValueError("state.observed_scores must contain finite scores in [0, 10]")
    if not isinstance(completed, bool):
        raise ValueError("state.episode_ended must be a boolean")
    if completed:
        raise ValueError("cannot add observations after the episode has ended")

    history = list(scores) + [float(score)]
    mean = sum(history) / len(history)
    metric = mean
    active = False
    rating = prior.get("retrospective_rating")
    if ending:
        if len(history) < 2:
            raise ValueError("a retrospective peak-end evaluation requires at least two moments")
        peak = max(history)
        end = history[-1]
        peak_end_summary = (peak + end) / 2.0
        weight = 0.6 * strength
        metric = (1.0 - weight) * mean + weight * peak_end_summary
        active = strength > 0 and not math.isclose(metric, mean, rel_tol=0.0, abs_tol=1e-12)
        rating = metric
        trace = (
            f"Completed episode: mean={mean:.6g}, peak=max(history)={peak:.6g}, "
            f"end={end:.6g}; rating=(1-0.6*strength)*mean + "
            f"0.6*strength*(peak+end)/2 = {metric:.6g}."
        )
    else:
        trace = f"Episode not marked complete: running arithmetic mean of {len(history)} supplied moments={mean:.6g}; no peak-end evaluation."

    # Keep nested auxiliary state independent of both the caller and this result.
    next_state = deepcopy(prior)
    next_state.update({
        "observed_scores": history,
        "episode_ended": ending,
        "retrospective_rating": rating,
    })
    return {"metric": float(metric), "active": active, "state": next_state, "trace": [trace]}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"moment_score": 2, "episode_end": False},
                {"moment_score": 4, "episode_end": False},
                {"moment_score": 10, "episode_end": False},
                {"moment_score": 8, "episode_end": True},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"moment_score": 2, "episode_end": False},
                {"moment_score": 4, "episode_end": False},
                {"moment_score": 10, "episode_end": False},
                {"moment_score": 8, "episode_end": False},
            ],
            "expectation": "equal",
        },
    ]
