"""Illustrative bounded-rationality process for a finite option-choice task.

This is a hypothetical process model, not an empirical account or detector.
"""

from math import floor, isfinite
from numbers import Real

METADATA = {
    "id": "bounded_rationality",
    "name": "Bounded Rationality",
    "kind": "cognitive_bias",
    "description": (
        "A stated option-evaluation budget limits search; when the budget binds, "
        "an explicit aspiration threshold can stop search at a satisfactory option."
    ),
    "required_inputs": ["options", "evaluation_capacity", "aspiration_threshold"],
    "state_fields": [
        "decision_count",
        "last_choice",
        "last_evaluated_ids",
        "last_best_utility",
        "last_regret",
    ],
    "metric_name": "utility_regret",
    "metric_units": "best supplied utility minus chosen supplied utility (utility units)",
    "assumptions": [
        "Options are listed in the order in which the decision maker can inspect them.",
        "The finite evaluation_capacity is an explicit task constraint, not inferred.",
        "At strength zero the reference policy evaluates every option and maximizes supplied utility.",
        "At positive strength the effective inspection budget moves linearly toward evaluation_capacity, rounded down to a whole option.",
        "When the budget binds and an aspiration threshold is supplied, the first inspected option meeting it is selected; otherwise the best inspected option is selected.",
        "Strength is an illustrative setting, not prevalence, confidence, or a fitted effect size.",
    ],
    "limitations": [
        "Utilities, option order, evaluation capacity, and aspiration threshold are assumed inputs; the model does not infer them from text or behavior.",
        "A supplied threshold and constrained search may represent sensible adaptation rather than an error.",
        "The simple linear budget interpolation and first-satisfactory stopping rule are illustrative and not empirically validated.",
        "The metric is task utility regret, not a measure of irrationality or psychological diagnosis.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate a finite option choice without mutating the supplied context."""
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in ("options", "evaluation_capacity", "aspiration_threshold"):
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    options = context["options"]
    if not isinstance(options, list) or not options:
        raise ValueError("options must be a non-empty list")
    validated = []
    seen_ids = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict) or "id" not in option or "utility" not in option:
            raise ValueError(f"option {index} must contain id and utility")
        option_id = option["id"]
        if not isinstance(option_id, str) or not option_id:
            raise ValueError(f"option {index} id must be a non-empty string")
        if option_id in seen_ids:
            raise ValueError("option ids must be unique")
        seen_ids.add(option_id)
        validated.append((option_id, _finite_number(option["utility"], f"utility for {option_id}")))

    capacity = context["evaluation_capacity"]
    if isinstance(capacity, bool) or not isinstance(capacity, int) or not 1 <= capacity <= len(validated):
        raise ValueError("evaluation_capacity must be an integer from 1 through the number of options")
    threshold = context["aspiration_threshold"]
    if threshold is not None:
        threshold = _finite_number(threshold, "aspiration_threshold")

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    prior_count = prior_state.get("decision_count", 0)
    if isinstance(prior_count, bool) or not isinstance(prior_count, int) or prior_count < 0:
        raise ValueError("state.decision_count must be a non-negative integer")

    best_id, best_utility = max(validated, key=lambda item: item[1])
    count = len(validated)
    if strength == 0.0:
        # Explicit comparator: exhaustive maximum-utility choice.
        evaluated = validated
        chosen_id, chosen_utility = best_id, best_utility
        rule = "strength-zero reference: inspect all options and maximize supplied utility"
    else:
        # Linear interpolation represents how strongly the stated capacity binds.
        budget = max(1, min(count, floor(count - strength * (count - capacity))))
        evaluated = validated[:budget]
        binding = budget < count
        if binding and threshold is not None:
            satisfactory = next((item for item in evaluated if item[1] >= threshold), None)
        else:
            satisfactory = None
        if satisfactory is not None:
            chosen_id, chosen_utility = satisfactory
            rule = (
                f"binding budget {budget}/{count}; first inspected option meeting "
                f"aspiration threshold {threshold} stops search"
            )
        else:
            chosen_id, chosen_utility = max(evaluated, key=lambda item: item[1])
            if binding:
                rule = f"binding budget {budget}/{count}; choose highest utility among inspected options"
            else:
                rule = "non-binding budget; inspect all options and maximize supplied utility"

    metric = best_utility - chosen_utility
    # Suppress only floating-point negative zero/roundoff, not genuine regret.
    if metric < 0 and metric > -1e-12:
        metric = 0.0
    active = metric > 0.0
    next_state = {
        "decision_count": prior_count + 1,
        "last_choice": chosen_id,
        "last_evaluated_ids": [option_id for option_id, _ in evaluated],
        "last_best_utility": best_utility,
        "last_regret": metric,
    }
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            f"Options were inspected in supplied order; {rule}.",
            f"Chosen {chosen_id!r} at utility {chosen_utility}; global supplied maximum is {best_utility}; regret = {best_utility} - {chosen_utility} = {metric}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "options": [
                        {"id": "acceptable-first", "utility": 6.0},
                        {"id": "best-later", "utility": 10.0},
                        {"id": "middle", "utility": 8.0},
                    ],
                    "evaluation_capacity": 1,
                    "aspiration_threshold": 5.0,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "options": [
                        {"id": "acceptable-first", "utility": 6.0},
                        {"id": "best-later", "utility": 10.0},
                        {"id": "middle", "utility": 8.0},
                    ],
                    "evaluation_capacity": 3,
                    "aspiration_threshold": 5.0,
                }
            ],
            "expectation": "equal",
        },
    ]
