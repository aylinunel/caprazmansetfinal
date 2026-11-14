"""Illustrative, synthetic process model for the Barnum effect.

This is not an empirical detector or a fitted model. It simulates a single
reader's attribution of a description as uniquely personal.
"""
from __future__ import annotations

import copy
import math
from numbers import Real


METADATA = {
    "id": "barnum_effect",
    "name": "Barnum Effect",
    "kind": "cognitive_bias",
    "description": (
        "Simulates increased unique-personal attribution when a reader agrees "
        "with a vague, widely applicable description and explicitly perceives "
        "it as personally specific."
    ),
    "required_inputs": [
        "agreement",
        "description_vagueness",
        "population_applicability",
        "perceived_personal_specificity",
        "verified_individual_fit",
    ],
    "state_fields": [
        "evaluations",
        "last_unique_attribution",
        "accepted_unique_count",
    ],
    "metric_name": "unique_personal_attribution",
    "metric_units": "unitless score from 0 (none) to 1 (maximal attribution)",
    "assumptions": [
        "All rating inputs are explicit hypothetical scenario data on [0, 1].",
        "Perceived personal specificity of at least 0.5 is a necessary condition.",
        "Vagueness and broad population applicability jointly strengthen the cue.",
        "Strength is an illustrative intervention setting, not an effect estimate.",
        "The reference policy scores agreement in proportion to independently verified individual fit.",
    ],
    "limitations": [
        "The equation is a compact toy process, not a validated account of human judgment.",
        "No text, population, or reader state is inferred; all relevant perceptions are supplied.",
        "The model omits social context, demand characteristics, and individual differences.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_REQUIRED = tuple(METADATA["required_inputs"])
_SPECIFICITY_GATE = 0.5


def _unit_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one description and return its attribution score and next state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    missing = [key for key in _REQUIRED if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    if not isinstance(context["agreement"], bool):
        raise ValueError("agreement must be a bool")
    agreement = context["agreement"]
    vagueness = _unit_interval(context["description_vagueness"], "description_vagueness")
    breadth = _unit_interval(context["population_applicability"], "population_applicability")
    perceived_specificity = _unit_interval(
        context["perceived_personal_specificity"], "perceived_personal_specificity"
    )
    verified_fit = _unit_interval(context["verified_individual_fit"], "verified_individual_fit")

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    state = copy.deepcopy(previous)
    evaluations = state.get("evaluations", 0)
    if isinstance(evaluations, bool) or not isinstance(evaluations, int) or evaluations < 0:
        raise ValueError("state.evaluations must be a non-negative integer")
    accepted_count = state.get("accepted_unique_count", 0)
    if isinstance(accepted_count, bool) or not isinstance(accepted_count, int) or accepted_count < 0:
        raise ValueError("state.accepted_unique_count must be a non-negative integer")
    prior_last = state.get("last_unique_attribution", 0.0)
    _unit_interval(prior_last, "state.last_unique_attribution")

    # Explicit reference rule: agreement alone is not uniqueness. Attribution
    # equals agreement times supplied independent, individual-specific fit.
    reference = verified_fit if agreement else 0.0

    # The Barnum pathway requires perceived specificity >= 0.5. Its cue is
    # multiplicative: agreement * vagueness * broad applicability * perceived
    # specificity. Verified fit limits only the room for cue-driven inflation.
    cue = 0.0
    if agreement and perceived_specificity >= _SPECIFICITY_GATE:
        cue = vagueness * breadth * perceived_specificity
    attribution = reference + strength * cue * (1.0 - reference)
    # Guard against negligible floating roundoff at the score bounds.
    attribution = min(1.0, max(0.0, attribution))
    changed = attribution != reference

    state["evaluations"] = evaluations + 1
    state["last_unique_attribution"] = attribution
    state["accepted_unique_count"] = accepted_count + int(attribution >= 0.5)
    trace = [
        f"Reference attribution = agreement({int(agreement)}) * verified_individual_fit({verified_fit:g}) = {reference:g}.",
        (
            f"Cue = agreement * vagueness({vagueness:g}) * applicability({breadth:g}) * "
            f"perceived_specificity({perceived_specificity:g}); specificity gate >= {_SPECIFICITY_GATE:g}."
        ),
        f"Score = reference + strength({strength:g}) * cue({cue:g}) * (1 - reference) = {attribution:g}.",
        "Agreement alone is insufficient; no cue is applied below the perceived-specificity gate.",
    ]
    return {
        "metric": attribution,
        "active": bool(changed),
        "state": state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "agreement": True,
                    "description_vagueness": 0.9,
                    "population_applicability": 0.9,
                    "perceived_personal_specificity": 0.9,
                    "verified_individual_fit": 0.2,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "agreement": True,
                    "description_vagueness": 0.9,
                    "population_applicability": 0.9,
                    "perceived_personal_specificity": 0.4,
                    "verified_individual_fit": 0.2,
                }
            ],
            "expectation": "equal",
        },
    ]
