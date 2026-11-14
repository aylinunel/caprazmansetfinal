"""Illustrative paired-presentation framing mechanism (not an empirical model)."""

from __future__ import annotations

import math
from typing import Any


METADATA = {
    "id": "framing_effect",
    "name": "Framing Effect",
    "kind": "cognitive_bias",
    "description": (
        "For numerically identical gain/loss presentations of risky options, an "
        "illustrative frame-dependent variance premium changes which option is chosen."
    ),
    "required_inputs": ["frame", "presentations"],
    "state_fields": ["last_frame", "last_choice", "reference_choice", "eligible"],
    "metric_name": "chosen_option_index",
    "metric_units": "zero-based option index in the selected presentation",
    "assumptions": [
        "Each presentation contains the same named options and exact canonical outcome distributions; only the gain/loss wording differs.",
        "Strength scales a hypothetical risk premium of 0.002 score-points per outcome-point-squared.",
        "Gain framing applies a variance premium with a negative sign; loss framing uses a positive sign.",
        "At strength zero, the reference policy chooses the option with greatest expected outcome, with first-listed tie breaking.",
    ],
    "limitations": [
        "This is a small synthetic choice process, not a fitted or validated account of human decisions.",
        "The variance premium and coefficient are illustrative and depend on the arbitrary outcome-point scale.",
        "Structured paired distributions establish numeric equivalence only; the module does not inspect natural language or establish substantive equivalence in real communications.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

# Illustrative coefficient, in inverse outcome-points, so coefficient * variance
# has the same units as the expected-outcome score.
_VARIANCE_COEFFICIENT = 0.002
_EQUIVALENCE_TOLERANCE = 1e-9


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def _parse_presentation(raw: Any, expected_frame: str) -> tuple[dict[str, list[tuple[float, float]]], dict[str, tuple[float, float]]]:
    if not isinstance(raw, dict) or raw.get("frame") != expected_frame:
        raise ValueError("presentations must contain one 'gain' and one 'loss' presentation")
    options = raw.get("options")
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError("each presentation needs at least two options")
    distributions: dict[str, list[tuple[float, float]]] = {}
    stats: dict[str, tuple[float, float]] = {}
    for option in options:
        if not isinstance(option, dict):
            raise ValueError("each option must be an object")
        name = option.get("id")
        if not isinstance(name, str) or not name:
            raise ValueError("each option needs a nonempty string id")
        if name in distributions:
            raise ValueError("option ids must be unique within a presentation")
        outcomes = option.get("outcomes")
        if not isinstance(outcomes, list) or not outcomes:
            raise ValueError(f"option {name!r} needs at least one outcome")
        distribution: list[tuple[float, float]] = []
        total_probability = 0.0
        expected = 0.0
        second_moment = 0.0
        for outcome in outcomes:
            if not isinstance(outcome, dict) or "probability" not in outcome or "value" not in outcome:
                raise ValueError(f"each outcome for {name!r} needs probability and value")
            probability = _number(outcome["probability"], "outcome probability")
            value = _number(outcome["value"], "outcome value")
            if not (0.0 <= probability <= 1.0):
                raise ValueError("outcome probabilities must lie in [0, 1]")
            if not (-1_000_000.0 <= value <= 1_000_000.0):
                raise ValueError("outcome values must lie in [-1,000,000, 1,000,000]")
            distribution.append((probability, value))
            total_probability += probability
            expected += probability * value
            second_moment += probability * value * value
        if not math.isclose(total_probability, 1.0, rel_tol=0.0, abs_tol=_EQUIVALENCE_TOLERANCE):
            raise ValueError(f"outcome probabilities for {name!r} must sum to 1")
        variance = max(0.0, second_moment - expected * expected)
        distributions[name] = sorted(distribution)
        stats[name] = (expected, variance)
    return distributions, stats


def _equivalent(
    left: dict[str, list[tuple[float, float]]], right: dict[str, list[tuple[float, float]]]
) -> bool:
    if left.keys() != right.keys():
        return False
    for option_id in left:
        a, b = left[option_id], right[option_id]
        if len(a) != len(b):
            return False
        if any(
            not math.isclose(pa, pb, rel_tol=0.0, abs_tol=_EQUIVALENCE_TOLERANCE)
            or not math.isclose(va, vb, rel_tol=0.0, abs_tol=_EQUIVALENCE_TOLERANCE)
            for (pa, va), (pb, vb) in zip(a, b)
        ):
            return False
    return True


def _winner(option_ids: list[str], scores: dict[str, float]) -> int:
    # max() retains the first listed item on ties: this is also the reference rule.
    return max(range(len(option_ids)), key=lambda index: scores[option_ids[index]])


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicitly structured gain/loss choice pair without mutation."""
    setting = _number(strength, "strength")
    if not 0.0 <= setting <= 1.0:
        raise ValueError("strength must lie in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    frame = context.get("frame")
    if frame not in ("gain", "loss"):
        raise ValueError("frame must be 'gain' or 'loss'")
    raw_presentations = context.get("presentations")
    if not isinstance(raw_presentations, list) or len(raw_presentations) != 2:
        raise ValueError("presentations must provide the matched gain and loss versions")
    by_frame = {item.get("frame"): item for item in raw_presentations if isinstance(item, dict)}
    if set(by_frame) != {"gain", "loss"}:
        raise ValueError("presentations must contain exactly one gain and one loss version")
    parsed = {key: _parse_presentation(by_frame[key], key) for key in ("gain", "loss")}
    equivalent = _equivalent(parsed["gain"][0], parsed["loss"][0])
    selected_raw = by_frame[frame]
    selected_options = selected_raw["options"]
    option_ids = [option["id"] for option in selected_options]
    selected_stats = parsed[frame][1]
    reference_scores = {name: selected_stats[name][0] for name in option_ids}
    reference_choice = _winner(option_ids, reference_scores)

    if equivalent:
        # Risk preference is frame-specific: a gain frame discounts variance;
        # a loss frame rewards it. This applies only to identical distributions.
        frame_sign = -1.0 if frame == "gain" else 1.0
        scores = {
            name: selected_stats[name][0]
            + frame_sign * setting * _VARIANCE_COEFFICIENT * selected_stats[name][1]
            for name in option_ids
        }
        choice = _winner(option_ids, scores)
        active = setting > 0.0 and choice != reference_choice
        reason = "matched outcome distributions; frame-dependent variance scoring applied"
    else:
        # Non-equivalent information is not classified as framing: use the
        # same expected-value reference rule regardless of strength.
        scores = reference_scores
        choice = reference_choice
        active = False
        reason = "paired outcome distributions differ; framing condition is absent"

    if not all(math.isfinite(value) for value in scores.values()):
        raise ValueError("computed option scores must be finite")
    previous_state = context.get("state", {})
    if not isinstance(previous_state, dict):
        raise ValueError("state must be a dictionary when provided")
    next_state = dict(previous_state)
    next_state.update(
        {
            "last_frame": frame,
            "last_choice": option_ids[choice],
            "reference_choice": option_ids[reference_choice],
            "eligible": equivalent,
        }
    )
    score_trace = ", ".join(f"{name}={scores[name]:.6g}" for name in option_ids)
    return {
        "metric": float(choice),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"Selected frame={frame}; matched distributions equivalent={equivalent}.",
            f"{reason}; scores by listed option [{score_trace}].",
            "Reference chooses highest expected outcome (first-listed tie wins); "
            "eligible score = expected outcome + sign(frame)*strength*0.002*variance, "
            "with sign(gain)=-1 and sign(loss)=+1. Metric is the chosen zero-based option index.",
        ],
    }


def scenarios() -> list[dict]:
    paired = [
        {
            "frame": "gain",
            "options": [
                {"id": "certain", "outcomes": [{"probability": 1.0, "value": 90.0}]},
                {"id": "lottery", "outcomes": [
                    {"probability": 0.5, "value": 0.0},
                    {"probability": 0.5, "value": 200.0},
                ]},
            ],
        },
        {
            "frame": "loss",
            "options": [
                {"id": "certain", "outcomes": [{"probability": 1.0, "value": 90.0}]},
                {"id": "lottery", "outcomes": [
                    {"probability": 0.5, "value": 0.0},
                    {"probability": 0.5, "value": 200.0},
                ]},
            ],
        },
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{"frame": "gain", "presentations": paired}],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "frame": "gain",
                    "presentations": [
                        paired[0],
                        {
                            "frame": "loss",
                            "options": [
                                {"id": "certain", "outcomes": [{"probability": 1.0, "value": 90.0}]},
                                {"id": "lottery", "outcomes": [
                                    {"probability": 0.5, "value": 0.0},
                                    {"probability": 0.5, "value": 180.0},
                                ]},
                            ],
                        },
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
