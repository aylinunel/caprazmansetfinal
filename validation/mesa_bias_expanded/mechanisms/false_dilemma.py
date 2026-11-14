"""Illustrative false-dilemma choice process over an explicitly supplied menu."""

from __future__ import annotations

import copy
import math
from numbers import Real

METADATA = {
    "id": "false_dilemma",
    "name": "False Dilemma (Yanlış ikilem)",
    "kind": "cognitive_bias",
    "description": (
        "Models a reader who accepts an explicitly exhaustive two-option frame "
        "with probability strength, choosing only within that pair despite a "
        "larger supplied feasible menu."
    ),
    "required_inputs": ["options", "framed_pair", "frame_claims_exhaustive"],
    "state_fields": ["steps", "cumulative_expected_regret", "last_choice_probabilities"],
    "metric_name": "expected_utility_regret",
    "metric_units": "utility points on the supplied 0-to-1 scale per decision",
    "assumptions": [
        "Each feasible option has a supplied, comparable utility in [0, 1].",
        "The option list is the complete feasible menu for this decision.",
        "Strength is the probability of accepting the supplied exhaustive frame, not a measured psychological parameter.",
        "Within an accepted frame, and under the reference policy, choice is the highest-utility option; exact ties use listed order.",
    ],
    "limitations": [
        "This is a synthetic choice-process illustration, not a classifier, diagnosis, or fitted account of human choice.",
        "It assumes known utilities and does not model how frames are authored, noticed, or interpreted.",
        "A binary choice can be appropriate; the process applies only when a supplied exhaustive claim excludes other feasible options.",
        "The chosen utilities, policy mixture, and strength setting are illustrative and not empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_real(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _validate_context(context: dict) -> tuple[list[dict], list[dict], list[str], bool]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required input: {key}")

    options = context["options"]
    if not isinstance(options, list):
        raise ValueError("options must be a list")
    if len(options) < 2:
        raise ValueError("options must contain at least two alternatives")
    normalized: list[dict] = []
    seen: set[str] = set()
    feasible_ids: list[str] = []
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a dict")
        if not isinstance(option.get("id"), str) or not option["id"].strip():
            raise ValueError(f"options[{index}].id must be a non-empty string")
        option_id = option["id"]
        if option_id in seen:
            raise ValueError("option ids must be unique")
        seen.add(option_id)
        if "utility" not in option:
            raise ValueError(f"options[{index}] is missing utility evidence")
        utility = _finite_real(option["utility"], f"options[{index}].utility")
        if not 0.0 <= utility <= 1.0:
            raise ValueError(f"options[{index}].utility must be in [0, 1]")
        feasible = option.get("feasible")
        if type(feasible) is not bool:
            raise ValueError(f"options[{index}].feasible must be bool")
        normalized.append({"id": option_id, "utility": utility, "feasible": feasible})
        if feasible:
            feasible_ids.append(option_id)
    if len(feasible_ids) < 2:
        raise ValueError("at least two feasible options are required")

    framed_pair = context["framed_pair"]
    if not isinstance(framed_pair, list) or len(framed_pair) != 2:
        raise ValueError("framed_pair must be a list of exactly two option ids")
    if any(not isinstance(item, str) for item in framed_pair) or framed_pair[0] == framed_pair[1]:
        raise ValueError("framed_pair must contain two distinct string ids")
    by_id = {option["id"]: option for option in normalized}
    if any(item not in by_id or not by_id[item]["feasible"] for item in framed_pair):
        raise ValueError("both framed_pair options must exist and be feasible")

    exhaustive = context["frame_claims_exhaustive"]
    if type(exhaustive) is not bool:
        raise ValueError("frame_claims_exhaustive must be bool")
    return normalized, [by_id[item] for item in framed_pair], feasible_ids, exhaustive


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one decision, preserving a cumulative regret state without mutation."""
    strength_value = _finite_real(strength, "strength")
    if not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    options, pair, feasible_ids, exhaustive = _validate_context(context)

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    prior_steps = prior_state.get("steps", 0)
    if isinstance(prior_steps, bool) or not isinstance(prior_steps, int) or prior_steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    prior_regret = _finite_real(prior_state.get("cumulative_expected_regret", 0.0), "state.cumulative_expected_regret")
    if prior_regret < 0.0:
        raise ValueError("state.cumulative_expected_regret must be non-negative")

    by_id = {option["id"]: option for option in options}
    feasible = [by_id[item] for item in feasible_ids]
    reference = max(feasible, key=lambda option: option["utility"])
    framed_choice = max(pair, key=lambda option: option["utility"])
    frame_applies = exhaustive and len(feasible) > 2

    # Explicit policy mixture: strength is the mass assigned to choosing only
    # within the asserted exhaustive pair; the rest follows the full-menu rule.
    probabilities = {option["id"]: 0.0 for option in feasible}
    if frame_applies:
        probabilities[framed_choice["id"]] += strength_value
        probabilities[reference["id"]] += 1.0 - strength_value
        metric = strength_value * (reference["utility"] - framed_choice["utility"])
    else:
        probabilities[reference["id"]] = 1.0
        metric = 0.0

    expected_utility = sum(by_id[option_id]["utility"] * probability for option_id, probability in probabilities.items())
    active = any(
        probability != (1.0 if option["id"] == reference["id"] else 0.0)
        for option, probability in ((item, probabilities[item["id"]]) for item in feasible)
    )
    next_state = copy.deepcopy(prior_state)
    next_state.update(
        {
            "steps": prior_steps + 1,
            "cumulative_expected_regret": prior_regret + metric,
            "last_choice_probabilities": probabilities.copy(),
        }
    )
    next_state["last_expected_utility"] = expected_utility

    reason = (
        "exhaustive binary frame applies because more than two supplied options are feasible"
        if frame_applies
        else "no false-dilemma condition: the frame is not asserted exhaustive or no third feasible option exists"
    )
    return {
        "metric": float(metric),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"{reason}; full-menu reference selects {reference['id']} (utility {reference['utility']:.6g}), "
            f"framed-pair policy selects {framed_choice['id']} (utility {framed_choice['utility']:.6g}).",
            f"Expected regret = {strength_value:.6g} × (reference utility − framed-pair utility) when the condition applies; otherwise 0. Metric={metric:.6g} utility points.",
            f"Choice probabilities: {probabilities}.",
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
                        {"id": "accept", "utility": 0.55, "feasible": True},
                        {"id": "reject", "utility": 0.60, "feasible": True},
                        {"id": "revise", "utility": 0.90, "feasible": True},
                    ],
                    "framed_pair": ["accept", "reject"],
                    "frame_claims_exhaustive": True,
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
                        {"id": "accept", "utility": 0.55, "feasible": True},
                        {"id": "reject", "utility": 0.60, "feasible": True},
                    ],
                    "framed_pair": ["accept", "reject"],
                    "frame_claims_exhaustive": True,
                }
            ],
            "expectation": "equal",
        },
    ]
