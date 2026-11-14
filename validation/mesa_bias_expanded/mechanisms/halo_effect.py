"""Illustrative structured process model for cross-attribute halo spillover.

This is a hypothetical mechanism, not a detector or empirically fitted model.
"""
from copy import deepcopy
import math


METADATA = {
    "id": "halo_effect",
    "name": "Halo Effect",
    "kind": "cognitive_bias",
    "description": (
        "Models a favorable rating on one explicitly unrelated attribute pulling "
        "an insufficiently supported target-attribute judgment upward."
    ),
    "required_inputs": [
        "donor_attribute", "target_attribute", "attributes_related",
        "donor_rating", "target_reference_rating", "target_evidence_support",
    ],
    "state_fields": [
        "steps", "last_target_judgment", "last_reference_rating", "last_spillover_points",
    ],
    "metric_name": "target_attribute_judgment",
    "metric_units": "rating points on the supplied 0–10 target-attribute scale",
    "assumptions": [
        "Structured ratings and the relatedness flag are supplied facts, not inferred from text.",
        "The strength-zero reference reports the target_reference_rating without cross-attribute transfer.",
        "When attributes are explicitly unrelated, the favorable donor-target gap is blended into the target rating in proportion to strength and unsupported share (1 - target_evidence_support).",
        "All ratings, support, and strength are illustrative scenario inputs, not calibrated psychological effect sizes.",
    ],
    "limitations": [
        "Does not detect attributes, judge whether they are truly related, or infer evidence support from prose.",
        "The linear blend is a compact hypothetical process assumption and omits uncertainty, context, and individual differences.",
        "No human validation, detection accuracy, or empirical calibration is claimed.",
        "A favorable judgment based on relevant performance is not treated as halo spillover.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    value = float(value)
    if not math.isfinite(value) or value < low or value > high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return value


def _state(value):
    if not isinstance(value, dict):
        raise ValueError("state must be a dictionary")
    prior = deepcopy(value)
    steps = prior.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    for field in ("last_target_judgment", "last_reference_rating", "last_spillover_points"):
        if field in prior and prior[field] is not None:
            _number(prior[field], f"state.{field}", 0.0, 10.0)
    return prior, steps


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one structured target-attribute judgment without mutating inputs."""
    strength = _number(strength, "strength", 0.0, 1.0)
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    fields = (
        "donor_attribute", "target_attribute", "attributes_related",
        "donor_rating", "target_reference_rating", "target_evidence_support",
    )
    missing = [field for field in fields if field not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")

    donor_attribute = context["donor_attribute"]
    target_attribute = context["target_attribute"]
    for field, value in (("donor_attribute", donor_attribute), ("target_attribute", target_attribute)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a non-empty string")
    if donor_attribute.strip().casefold() == target_attribute.strip().casefold():
        raise ValueError("donor_attribute and target_attribute must be distinct")
    related = context["attributes_related"]
    if not isinstance(related, bool):
        raise ValueError("attributes_related must be a boolean")

    donor = _number(context["donor_rating"], "donor_rating", 0.0, 10.0)
    reference = _number(context["target_reference_rating"], "target_reference_rating", 0.0, 10.0)
    support = _number(context["target_evidence_support"], "target_evidence_support", 0.0, 1.0)
    prior, steps = _state(context.get("state", {}))

    # Strength-zero reference: retain the target's own supplied reference rating.
    # Necessary halo conditions: distinct, explicitly unrelated attributes; a
    # favorable donor rating above the target reference; and some unsupported share.
    necessary_conditions = (
        not related and donor > reference and support < 1.0
    )
    spillover = (
        strength * (1.0 - support) * (donor - reference)
        if necessary_conditions else 0.0
    )
    judgment = reference + spillover
    # Algebraically bounded by donor_rating <= 10 and the support/strength factors.
    next_state = prior
    next_state.update({
        "steps": steps + 1,
        "last_target_judgment": judgment,
        "last_reference_rating": reference,
        "last_spillover_points": spillover,
    })
    active = judgment != reference
    return {
        "metric": judgment,
        "active": active,
        "state": next_state,
        "trace": [
            f"Reference target judgment = target_reference_rating({reference:g}) points.",
            "Spillover points = strength * (1 - target_evidence_support) * "
            "max(0, donor_rating - target_reference_rating), only when attributes are "
            f"explicitly unrelated; related={related}, conditions_met={necessary_conditions}.",
            f"Inputs: donor={donor_attribute!r} ({donor:g}), target={target_attribute!r}, "
            f"support={support:g}, strength={strength:g}; spillover={spillover:g}, "
            f"judgment={judgment:g}/10, active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "donor_attribute": "presentation_polish",
                "target_attribute": "analytical_accuracy",
                "attributes_related": False,
                "donor_rating": 9.0,
                "target_reference_rating": 4.0,
                "target_evidence_support": 0.2,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "donor_attribute": "task_performance",
                "target_attribute": "task_competence",
                "attributes_related": True,
                "donor_rating": 9.0,
                "target_reference_rating": 4.0,
                "target_evidence_support": 0.2,
            }],
            "expectation": "equal",
        },
    ]
