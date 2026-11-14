"""Illustrative loss-aversion choice process for explicit two-or-more option lotteries.

This is a synthetic process model, not a detector or an empirically fitted account.
"""

from copy import deepcopy
import math
from numbers import Real


METADATA = {
    "id": "loss_aversion",
    "name": "Loss Aversion",
    "kind": "cognitive_bias",
    "description": (
        "Chooses among explicit lotteries by weighting each outcome below a supplied "
        "reference point more heavily than an equal-sized outcome above it."
    ),
    "required_inputs": ["options", "reference_point"],
    "state_fields": [],
    "metric_name": "chosen expected reference-relative payoff",
    "metric_units": "payoff points relative to the supplied reference point",
    "assumptions": [
        "The agent evaluates supplied outcomes and probabilities rather than estimating them.",
        "Strength s in [0, 1] sets the illustrative loss multiplier lambda = 1 + 2s.",
        "At strength zero, the reference rule selects the option with the highest expected payoff.",
        "Ties are resolved by choosing the first listed option.",
    ],
    "limitations": [
        "Linear payoff evaluation at strength zero is only a reference policy, not a claim of perfect rationality.",
        "The multiplier is an illustrative assumption, not an empirically estimated effect size.",
        "The process requires explicit reference points and complete structured lotteries; it is not an NLP detector.",
        "Risk aversion or financial inability to absorb losses is not inferred or modeled.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _prepare(context, strength):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    if "reference_point" not in context:
        raise ValueError("missing required input: reference_point")
    reference = _finite_number(context["reference_point"], "reference_point")
    options = context.get("options")
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError("options must be a list containing at least two lotteries")

    prepared = []
    identifiers = set()
    for option_index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{option_index}] must be a dict")
        identifier = option.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f"options[{option_index}].id must be a nonempty string")
        if identifier in identifiers:
            raise ValueError("option ids must be unique")
        identifiers.add(identifier)
        outcomes = option.get("outcomes")
        if not isinstance(outcomes, list) or not outcomes:
            raise ValueError(f"options[{option_index}].outcomes must be a nonempty list")
        parsed = []
        probability_sum = 0.0
        for outcome_index, outcome in enumerate(outcomes):
            label = f"options[{option_index}].outcomes[{outcome_index}]"
            if not isinstance(outcome, dict) or "value" not in outcome or "probability" not in outcome:
                raise ValueError(f"{label} must provide value and probability")
            value = _finite_number(outcome["value"], f"{label}.value")
            probability = _finite_number(outcome["probability"], f"{label}.probability")
            if probability < 0.0 or probability > 1.0:
                raise ValueError(f"{label}.probability must be in [0, 1]")
            parsed.append((value, probability))
            probability_sum += probability
        if not math.isfinite(probability_sum) or not math.isclose(probability_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"probabilities for options[{option_index}] must sum to 1")
        prepared.append((identifier, parsed))

    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("state must be a dict (use {} when there is no prior task state)")
    return reference, prepared, strength


def _expected_payoff(outcomes, reference):
    return math.fsum(probability * (value - reference) for value, probability in outcomes)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one choice step without mutating the supplied context or state."""
    reference, options, strength = _prepare(context, strength)
    baseline_scores = [_expected_payoff(outcomes, reference) for _, outcomes in options]
    multiplier = 1.0 + 2.0 * strength

    loss_weighted_scores = []
    expected_payoffs = []
    loss_mass = []
    for _, outcomes in options:
        weighted_terms = []
        losses = []
        for value, probability in outcomes:
            delta = value - reference
            if delta < 0.0:
                weighted_terms.append(probability * multiplier * delta)
                losses.append(probability * -delta)
            else:
                weighted_terms.append(probability * delta)
        loss_weighted_scores.append(math.fsum(weighted_terms))
        expected_payoffs.append(_expected_payoff(outcomes, reference))
        loss_mass.append(math.fsum(losses))

    if any(not math.isfinite(x) for x in baseline_scores + loss_weighted_scores + expected_payoffs + loss_mass):
        raise ValueError("lottery values produce a non-finite derived quantity")
    baseline_index = max(range(len(options)), key=lambda i: baseline_scores[i])
    selected_index = max(range(len(options)), key=lambda i: loss_weighted_scores[i])
    metric = expected_payoffs[selected_index]
    if not math.isfinite(metric):
        raise ValueError("selected expected payoff is non-finite")

    trace = [
        f"Reference point={reference:g}; expected payoff is sum(p*(value-reference)).",
        f"Strength={strength:g} gives loss multiplier lambda=1+2s={multiplier:g}; gains retain weight 1.",
        "Loss-weighted option score is sum(p*delta) for delta>=0 and sum(p*lambda*delta) for delta<0; ties use first listed option.",
        f"Reference choice={options[baseline_index][0]} (score {baseline_scores[baseline_index]:g}); "
        f"selected choice={options[selected_index][0]} (weighted score {loss_weighted_scores[selected_index]:g}).",
    ]
    if all(mass == 0.0 for mass in loss_mass):
        trace.append("No outcome falls below the reference point, so the necessary loss condition is absent and both choice rules coincide.")
    else:
        trace.append("Reference-relative downside exists; the loss-weighted comparison is applied, without inferring risk aversion or inability to bear a loss.")

    return {
        "metric": metric,
        "active": selected_index != baseline_index,
        "state": deepcopy(context["state"]),
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "reference_point": 0,
                    "options": [
                        {"id": "volatile", "outcomes": [{"value": 10, "probability": 0.5}, {"value": -8, "probability": 0.5}]},
                        {"id": "sure_zero", "outcomes": [{"value": 0, "probability": 1.0}]},
                    ],
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "reference_point": 0,
                    "options": [
                        {"id": "mixed_nonnegative", "outcomes": [{"value": 10, "probability": 0.5}, {"value": 0, "probability": 0.5}]},
                        {"id": "sure_four", "outcomes": [{"value": 4, "probability": 1.0}]},
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
