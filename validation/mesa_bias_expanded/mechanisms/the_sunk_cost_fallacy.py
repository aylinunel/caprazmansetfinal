"""Illustrative, non-empirical sunk-cost choice mechanism.

The modeled error is counting irrecoverable past expenditure as extra value for
continuing. This module is a transparent process model, not a detector.
"""

import math
from numbers import Real


METADATA = {
    "id": "the_sunk_cost_fallacy",
    "name": "The Sunk Cost Fallacy",
    "kind": "cognitive_bias",
    "description": (
        "Adds a strength-scaled amount of irrecoverable past expenditure to the "
        "continue-choice score, while reporting the selected option's actual "
        "future utility."
    ),
    "required_inputs": [
        "past_expenditure",
        "recoverable_amount",
        "future_value_continue",
        "future_value_exit",
    ],
    "state_fields": ["round_count", "choices", "actual_utilities", "cumulative_utility", "last_choice"],
    "metric_name": "selected_option_actual_future_utility",
    "metric_units": "same utility units as both supplied future-value inputs",
    "assumptions": [
        "Future option values are comparable, already account for future contractual costs/benefits, and use a common decision horizon.",
        "Past expenditure and recoverable amount use the same units as future utility; only their unrecoverable difference is modeled.",
        "Strength linearly controls how much unrecoverable past expenditure is mistakenly added to continuing's score; this is an illustrative parameter, not an estimated effect size.",
        "The reference policy chooses the option with greater future value and exits on an exact tie.",
    ],
    "limitations": [
        "Synthetic process model only; no empirical validation, calibration, population claim, or detection accuracy is provided.",
        "The model requires explicit structured inputs and cannot infer sunk costs, motives, or option values from text.",
        "A lower selected future utility is a consequence of this constructed choice task, not a claim about real-world decision makers.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_STATE_DEFAULTS = {
    "round_count": 0,
    "choices": [],
    "actual_utilities": [],
    "cumulative_utility": 0.0,
    "last_choice": None,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _read_state(state):
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    if not state:
        return {**_STATE_DEFAULTS, "choices": [], "actual_utilities": []}
    required = set(_STATE_DEFAULTS)
    if set(state) != required:
        raise ValueError(f"state must contain exactly {sorted(required)}")
    count = state["round_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.round_count must be a nonnegative integer")
    choices = state["choices"]
    utilities = state["actual_utilities"]
    if not isinstance(choices, list) or any(x not in ("continue", "exit") for x in choices):
        raise ValueError("state.choices must be a list of continue/exit choices")
    if not isinstance(utilities, list):
        raise ValueError("state.actual_utilities must be a list")
    utilities = [_finite_number(x, "state.actual_utilities item") for x in utilities]
    if len(choices) != count or len(utilities) != count:
        raise ValueError("state history lengths must equal round_count")
    cumulative = _finite_number(state["cumulative_utility"], "state.cumulative_utility")
    if not math.isclose(sum(utilities), cumulative, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError("state.cumulative_utility must equal the sum of actual_utilities")
    last = state["last_choice"]
    if last not in (None, "continue", "exit") or last != (choices[-1] if choices else None):
        raise ValueError("state.last_choice must match the last recorded choice")
    return {
        "round_count": count,
        "choices": list(choices),
        "actual_utilities": list(utilities),
        "cumulative_utility": cumulative,
        "last_choice": last,
    }


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit continue-or-exit task step without mutating inputs."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required input: {field}")

    past = _finite_number(context["past_expenditure"], "past_expenditure")
    recoverable = _finite_number(context["recoverable_amount"], "recoverable_amount")
    continue_value = _finite_number(context["future_value_continue"], "future_value_continue")
    exit_value = _finite_number(context["future_value_exit"], "future_value_exit")
    if past < 0:
        raise ValueError("past_expenditure must be nonnegative")
    if recoverable < 0 or recoverable > past:
        raise ValueError("recoverable_amount must be between zero and past_expenditure")
    sunk = past - recoverable

    prior = _read_state(context.get("state", {}))
    reference_choice = "continue" if continue_value > exit_value else "exit"
    continue_score = continue_value + strength * sunk
    choice = "continue" if continue_score > exit_value else "exit"
    actual_utility = continue_value if choice == "continue" else exit_value

    choices = prior["choices"] + [choice]
    utilities = prior["actual_utilities"] + [actual_utility]
    next_state = {
        "round_count": prior["round_count"] + 1,
        "choices": choices,
        "actual_utilities": utilities,
        "cumulative_utility": prior["cumulative_utility"] + actual_utility,
        "last_choice": choice,
    }
    return {
        "metric": float(actual_utility),
        "active": choice != reference_choice,
        "state": next_state,
        "trace": [
            f"Unrecoverable expenditure = past_expenditure - recoverable_amount = {past:g} - {recoverable:g} = {sunk:g}.",
            f"Reference choice compares future values only: continue={continue_value:g}, exit={exit_value:g}; reference={reference_choice} (ties exit).",
            f"Mechanism score: continue={continue_value:g} + strength({strength:g}) * sunk({sunk:g}) = {continue_score:g}; exit={exit_value:g}; selected={choice}.",
            f"Primary metric is selected option's actual future utility, not its biased score: {actual_utility:g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "past_expenditure": 5.0,
                "recoverable_amount": 0.0,
                "future_value_continue": -2.0,
                "future_value_exit": 0.0,
            }],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "past_expenditure": 5.0,
                "recoverable_amount": 5.0,
                "future_value_continue": -2.0,
                "future_value_exit": 0.0,
            }],
            "expectation": "equal",
        },
    ]
