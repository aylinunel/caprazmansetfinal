"""Illustrative choice process for an option with an unspecified probability.

This is a synthetic task mechanism, not a detector or empirically fitted account
of human decisions. See specs/ambiguity_effect_implementation.md.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "ambiguity_effect",
    "name": "Ambiguity Effect",
    "kind": "cognitive_bias",
    "description": (
        "Compares a known-probability option with an interval-probability option; "
        "ambiguity strength shifts the latter's decision probability from its "
        "midpoint toward its supplied lower bound."
    ),
    "required_inputs": [
        "known_probability",
        "ambiguous_probability_min",
        "ambiguous_probability_max",
        "success_payoff",
        "failure_payoff",
    ],
    "state_fields": [
        "last_choice",
        "last_reference_choice",
        "last_adjusted_ambiguous_probability",
        "last_known_expected_utility",
        "last_ambiguous_expected_utility",
    ],
    "metric_name": "ambiguous_option_chosen",
    "metric_units": "binary choice indicator (1 = ambiguous option; 0 = known-probability option)",
    "assumptions": [
        "Both options share the supplied success and failure payoffs; their success probabilities differ.",
        "The supplied interval [min, max] represents plausible success probabilities, not a known distribution over them.",
        "The reference policy uses the interval midpoint as the ambiguous option's probability and maximizes expected utility, breaking ties toward the known option.",
        "The illustrative mechanism linearly shifts the ambiguous option's decision probability from the midpoint toward the interval's lower endpoint as strength increases.",
        "Strength and the interval are scenario inputs, not calibrated psychological parameters or empirical claims.",
    ],
    "limitations": [
        "This narrow lower-bound process is one hypothetical representation of ambiguity aversion, not a general theory or classifier.",
        "A lower-bound preference may be legitimate risk management; the output alone cannot diagnose an error.",
        "Real people may use other priors, distributions, information, utilities, or ambiguity attitudes; none are inferred here.",
        "The model is synthetic and has not been empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return value


def _probability(value, field):
    value = _finite_number(value, field)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be in [0, 1]")
    return value


def _inputs(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    fields = (
        "known_probability",
        "ambiguous_probability_min",
        "ambiguous_probability_max",
        "success_payoff",
        "failure_payoff",
    )
    for field in fields:
        if field not in context:
            raise ValueError(f"{field} is required")
    known = _probability(context["known_probability"], "known_probability")
    lower = _probability(context["ambiguous_probability_min"], "ambiguous_probability_min")
    upper = _probability(context["ambiguous_probability_max"], "ambiguous_probability_max")
    if lower > upper:
        raise ValueError("ambiguous_probability_min must not exceed ambiguous_probability_max")
    success = _finite_number(context["success_payoff"], "success_payoff")
    failure = _finite_number(context["failure_payoff"], "failure_payoff")
    if success <= failure:
        raise ValueError("success_payoff must be greater than failure_payoff")
    return known, lower, upper, success, failure


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate a single binary-outcome choice under an ambiguity interval."""
    strength = _probability(strength, "strength")
    known_p, lower_p, upper_p, success, failure = _inputs(context)
    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dictionary")

    midpoint = (lower_p + upper_p) / 2.0
    # The strength-zero reference treats the interval midpoint as its probability.
    # Ambiguity aversion substitutes a lower-probability decision weight, not a
    # generic utility penalty: its effect depends on interval width and payoffs.
    adjusted_p = (1.0 - strength) * midpoint + strength * lower_p
    known_utility = known_p * success + (1.0 - known_p) * failure
    reference_ambiguous_utility = midpoint * success + (1.0 - midpoint) * failure
    adjusted_ambiguous_utility = adjusted_p * success + (1.0 - adjusted_p) * failure

    # Ties resolve to the known-probability option, consistently in both policies.
    reference_choice = int(reference_ambiguous_utility > known_utility)
    choice = int(adjusted_ambiguous_utility > known_utility)
    metric = float(choice)
    if not math.isfinite(metric):
        raise ValueError("computed choice metric is not finite")

    next_state = deepcopy(previous)
    next_state.update({
        "last_choice": choice,
        "last_reference_choice": reference_choice,
        "last_adjusted_ambiguous_probability": adjusted_p,
        "last_known_expected_utility": known_utility,
        "last_ambiguous_expected_utility": adjusted_ambiguous_utility,
    })
    active = strength > 0.0 and choice != reference_choice
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            (
                f"Known option EU={known_utility:.12g} using p={known_p:.12g}; "
                f"ambiguous interval=[{lower_p:.12g},{upper_p:.12g}], midpoint="
                f"{midpoint:.12g}, adjusted p=(1-{strength:.12g})*midpoint+"
                f"{strength:.12g}*lower={adjusted_p:.12g}, adjusted EU="
                f"{adjusted_ambiguous_utility:.12g}; reference choice="
                f"{'ambiguous' if reference_choice else 'known'}, current choice="
                f"{'ambiguous' if choice else 'known'}."
            )
        ],
    }


def scenarios() -> list[dict]:
    positive = {
        "known_probability": 0.55,
        "ambiguous_probability_min": 0.30,
        "ambiguous_probability_max": 0.90,
        "success_payoff": 10.0,
        "failure_payoff": 0.0,
    }
    boundary = {
        "known_probability": 0.55,
        "ambiguous_probability_min": 0.60,
        "ambiguous_probability_max": 0.60,
        "success_payoff": 10.0,
        "failure_payoff": 0.0,
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
