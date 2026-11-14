"""Illustrative projection of current option tastes into a future choice.

This is a synthetic decision process, not a detector or fitted psychological model.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "projection_bias",
    "name": "Projection Bias",
    "kind": "cognitive_bias",
    "description": (
        "For a future choice, blends each option's supplied future utility with "
        "the same option's current utility in proportion to intervention strength."
    ),
    "required_inputs": ["current_utilities", "future_utilities"],
    "state_fields": [
        "last_choice",
        "last_reference_choice",
        "last_projected_utilities",
        "last_future_satisfaction",
        "choice_count",
    ],
    "metric_name": "future_preference_satisfaction",
    "metric_units": "future utility of selected option, on a supplied 0-to-1 scale",
    "assumptions": [
        "Each decision supplies utilities on the same [0, 1] scale for the same named options, once from the explicit current state and once for the future task.",
        "At strength zero, the reference selects the option with the greatest supplied future utility; ties break by option name.",
        "The illustrative intervention weight equals strength: projected utility is (1-strength)*future utility + strength*current utility.",
        "The metric is the selected option's supplied future utility, so current/future preference divergence can reduce future-task fit.",
        "Strength is an uncalibrated intervention setting, not prevalence, confidence, or an estimated human effect size.",
    ],
    "limitations": [
        "The model assumes explicit, comparable utility estimates and does not infer hidden tastes or future states.",
        "A current preference can be stable and accurately predict the future; projection is not necessarily an error when the supplied profiles agree.",
        "The two-profile blend is one compact hypothetical process and omits learning, uncertainty, changing options, and legitimate reconsideration.",
        "This synthetic process has not been empirically validated and cannot diagnose a person or population.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _strength(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    return value


def _utilities(value, field):
    if not isinstance(value, dict) or len(value) < 2:
        raise ValueError(f"{field} must map at least two option names to utilities")
    result = {}
    for name, utility in value.items():
        if not isinstance(name, str) or not name:
            raise ValueError(f"{field} option names must be nonempty strings")
        if isinstance(utility, bool) or not isinstance(utility, (int, float)):
            raise ValueError(f"{field}[{name!r}] must be a finite utility in [0, 1]")
        utility = float(utility)
        if not math.isfinite(utility) or not 0.0 <= utility <= 1.0:
            raise ValueError(f"{field}[{name!r}] must be a finite utility in [0, 1]")
        result[name] = utility
    return result


def _task_inputs(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"{field} is required")
    current = _utilities(context["current_utilities"], "current_utilities")
    future = _utilities(context["future_utilities"], "future_utilities")
    if current.keys() != future.keys():
        raise ValueError("current_utilities and future_utilities must name identical options")
    return current, future


def evaluate(context: dict, strength: float) -> dict:
    """Choose a future option after projecting present utility into its estimate."""
    strength = _strength(strength)
    current, future = _task_inputs(context)
    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dictionary")

    projected = {
        option: (1.0 - strength) * future[option] + strength * current[option]
        for option in future
    }
    # Stable, explicit tie rules: higher future utility, then lexical option name.
    reference_choice = max(future, key=lambda option: (future[option], option))
    choice = max(projected, key=lambda option: (projected[option], future[option], option))
    metric = future[choice]
    if not math.isfinite(metric):
        raise ValueError("computed future-preference metric is not finite")

    next_state = deepcopy(previous)
    next_state.update({
        "last_choice": choice,
        "last_reference_choice": reference_choice,
        "last_projected_utilities": projected,
        "last_future_satisfaction": metric,
        "choice_count": int(previous.get("choice_count", 0)) + 1,
    })
    active = strength > 0.0 and choice != reference_choice
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            (
                f"Future choice among {len(future)} options: projected_i="
                f"(1-{strength:.12g})*future_i+{strength:.12g}*current_i; "
                f"projected utilities={projected}; selected={choice!r} "
                f"(future utility={metric:.12g}); strength-zero future-only "
                f"reference={reference_choice!r}."
            )
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "current_utilities": {"present_favorite": 1.0, "future_favorite": 0.0},
                "future_utilities": {"present_favorite": 0.0, "future_favorite": 1.0},
            }],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "current_utilities": {"tea": 1.0, "coffee": 0.2},
                "future_utilities": {"tea": 1.0, "coffee": 0.2},
            }],
            "expectation": "equal",
        },
    ]
