"""Illustrative affect-substitution choice process; not an empirical detector.

The process is deliberately explicit: supplied affect can displace supplied
benefit/risk evaluation in a factual-evaluation frame. See the implementation
note for the task, baseline, boundary, and limitations.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "affect_heuristic",
    "name": "Affect Heuristic",
    "kind": "cognitive_bias",
    "description": (
        "In factual option evaluation, linearly blends each option's supplied "
        "benefit-minus-risk value with its explicit affect signal, then selects "
        "the highest blended score. Stated subjective-preference choices use "
        "preference scores instead, without treating affect as factual error."
    ),
    "required_inputs": ["decision_frame", "options"],
    "state_fields": ["last_choice", "last_metric", "last_frame", "decision_history"],
    "metric_name": "selected_option_value",
    "metric_units": (
        "benefit-minus-risk units (-1 to 1) in factual_evaluation; stated "
        "preference-score units (0 to 1) in subjective_preference"
    ),
    "assumptions": [
        "Options contain explicit, hypothetical benefit, risk, affect, and preference values; none are inferred from text.",
        "Factual utility is benefit minus risk, with both inputs on [0, 1].",
        "Strength linearly sets the weight of affect in a factual-evaluation choice score; it is not a population parameter.",
        "A subjective-preference frame has an explicit preference score that is the relevant choice criterion, so affect is not labeled a factual distortion there.",
        "Ties are resolved by the earlier option in the supplied list.",
    ],
    "limitations": [
        "The linear blend, scales, and examples are illustrative assumptions and have not been empirically validated.",
        "The model requires structured affect and task-value inputs; it is not an NLP detector and does not estimate hidden emotion.",
        "Affect can be informative or preference-relevant in real decisions; the model only demonstrates a possible substitution in its stipulated factual-evaluation task.",
        "Selected task value is not a comprehensive measure of decision quality or welfare.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value, field, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [{low}, {high}]")
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{field} must be a finite number in [{low}, {high}]")
    return value


def _validated_task(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    frame = context.get("decision_frame")
    if frame not in ("factual_evaluation", "subjective_preference"):
        raise ValueError(
            "decision_frame must be 'factual_evaluation' or 'subjective_preference'"
        )
    options = context.get("options")
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError("options must be a list containing at least two alternatives")

    normalized = []
    ids = set()
    for index, option in enumerate(options):
        prefix = f"options[{index}]"
        if not isinstance(option, dict):
            raise ValueError(f"{prefix} must be a dictionary")
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id.strip():
            raise ValueError(f"{prefix}.id must be a non-empty string")
        if option_id in ids:
            raise ValueError("option ids must be unique")
        ids.add(option_id)
        benefit = _number(option.get("benefit"), f"{prefix}.benefit", 0.0, 1.0)
        risk = _number(option.get("risk"), f"{prefix}.risk", 0.0, 1.0)
        affect = _number(option.get("affect"), f"{prefix}.affect", -1.0, 1.0)
        preference = _number(
            option.get("preference_score"), f"{prefix}.preference_score", 0.0, 1.0
        )
        normalized.append(
            {
                "id": option_id,
                "benefit": benefit,
                "risk": risk,
                "utility": benefit - risk,
                "affect": affect,
                "preference_score": preference,
            }
        )
    return frame, normalized


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one structured choice and return its task value and next state."""
    strength = _number(strength, "strength", 0.0, 1.0)
    frame, options = _validated_task(context)
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    prior_history = state.get("decision_history", [])
    if not isinstance(prior_history, list):
        raise ValueError("state.decision_history must be a list")

    if frame == "factual_evaluation":
        # Reference: select maximum supplied benefit-minus-risk utility.
        # Affect substitutes for that evaluation in proportion to strength.
        scored = [
            {
                **option,
                "score": (1.0 - strength) * option["utility"]
                + strength * option["affect"],
            }
            for option in options
        ]
        metric_key = "utility"
        score_description = "(1-strength)*(benefit-risk)+strength*affect"
    else:
        # Boundary: an explicit subjective preference is not a factual claim.
        scored = [{**option, "score": option["preference_score"]} for option in options]
        metric_key = "preference_score"
        score_description = "stated preference_score (affect substitution not applicable)"

    chosen = max(scored, key=lambda option: option["score"])
    metric = chosen[metric_key]
    if not math.isfinite(metric):
        raise ValueError("computed selected option value is not finite")

    next_state = deepcopy(state)
    history = deepcopy(prior_history)
    history.append({"frame": frame, "choice": chosen["id"], "metric": metric})
    next_state.update(
        {
            "last_choice": chosen["id"],
            "last_metric": metric,
            "last_frame": frame,
            "decision_history": history,
        }
    )
    reference = max(
        options,
        key=lambda option: option["utility"]
        if frame == "factual_evaluation"
        else option["preference_score"],
    )
    active = frame == "factual_evaluation" and chosen["id"] != reference["id"]
    trace = (
        f"Frame={frame}; selected {chosen['id']!r} by maximizing {score_description}; "
        f"selected score={chosen['score']:.12g}, benefit={chosen['benefit']:.12g}, "
        f"risk={chosen['risk']:.12g}, utility=benefit-risk={chosen['utility']:.12g}, "
        f"affect={chosen['affect']:.12g}, preference_score="
        f"{chosen['preference_score']:.12g}; task metric={metric:.12g}."
    )
    return {"metric": metric, "active": active, "state": next_state, "trace": [trace]}


def scenarios() -> list[dict]:
    positive = {
        "decision_frame": "factual_evaluation",
        "options": [
            {"id": "steady", "benefit": 0.7, "risk": 0.1, "affect": -0.8, "preference_score": 0.4},
            {"id": "thrilling", "benefit": 0.5, "risk": 0.4, "affect": 0.9, "preference_score": 0.8},
        ],
    }
    boundary = {
        "decision_frame": "subjective_preference",
        "options": [
            {"id": "calm", "benefit": 0.7, "risk": 0.1, "affect": -0.9, "preference_score": 0.9},
            {"id": "thrilling", "benefit": 0.5, "risk": 0.4, "affect": 0.9, "preference_score": 0.2},
        ],
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [positive],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
