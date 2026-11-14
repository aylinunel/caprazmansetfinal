"""Illustrative, synthetic process model for naive realism; not a detector."""

from copy import deepcopy
import math


METADATA = {
    "id": "naive_realism",
    "name": "Naive Realism",
    "kind": "cognitive_bias",
    "description": (
        "A hypothetical agent discounts evidence aligned with an explicit dissenter "
        "when it treats its own view as neutral and attributes the disagreement to "
        "the dissenter's defect."
    ),
    "required_inputs": [
        "own_estimate",
        "evidence_target",
        "evidence_weight",
        "dissenting_estimate",
        "self_view_as_neutral",
        "dissent_defect_attribution",
    ],
    "state_fields": [
        "rounds_seen",
        "last_estimate",
        "cumulative_abs_movement",
        "cumulative_evidence_weight_discounted",
    ],
    "metric_name": "revised_estimate",
    "metric_units": "probability on the unit interval [0, 1]",
    "assumptions": [
        "Estimates and evidence targets are probabilities, and evidence_weight is a linear integration weight.",
        "dissent_defect_attribution is an explicit hypothetical input, not inferred from text or behavior.",
        "The 0.10 estimate gap is an illustrative threshold for a meaningful disagreement.",
        "strength and all coefficients are illustrative settings, not empirical effect sizes.",
    ],
    "limitations": [
        "This toy update rule is not empirically fitted, validated, or a psychological diagnosis.",
        "It does not infer beliefs, neutrality, bias, evidence quality, or motives from natural language.",
        "Evidence integration is linear and omits uncertainty, source reliability, social context, and learning dynamics.",
        "A dissenter may actually be misinformed, and discounting an argument can sometimes be reasonable; the model cannot adjudicate that.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_DISAGREEMENT_THRESHOLD = 0.10
_REQUIRED = tuple(METADATA["required_inputs"])
_STATE_DEFAULTS = {
    "rounds_seen": 0,
    "last_estimate": None,
    "cumulative_abs_movement": 0.0,
    "cumulative_evidence_weight_discounted": 0.0,
}


def _probability(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Apply one linear evidence update, conditionally discounted for dissent."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")
    missing = [key for key in _REQUIRED if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    own = _probability(context["own_estimate"], "own_estimate")
    target = _probability(context["evidence_target"], "evidence_target")
    weight = _probability(context["evidence_weight"], "evidence_weight")
    dissent = _probability(context["dissenting_estimate"], "dissenting_estimate")
    neutral = context["self_view_as_neutral"]
    if not isinstance(neutral, bool):
        raise ValueError("self_view_as_neutral must be a bool")
    attribution = _probability(
        context["dissent_defect_attribution"], "dissent_defect_attribution"
    )

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(prior_state)
    rounds = state.get("rounds_seen", _STATE_DEFAULTS["rounds_seen"])
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds_seen must be a non-negative integer")
    cumulative_movement = state.get(
        "cumulative_abs_movement", _STATE_DEFAULTS["cumulative_abs_movement"]
    )
    cumulative_discount = state.get(
        "cumulative_evidence_weight_discounted",
        _STATE_DEFAULTS["cumulative_evidence_weight_discounted"],
    )
    for name, value in (("cumulative_abs_movement", cumulative_movement),
                        ("cumulative_evidence_weight_discounted", cumulative_discount)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"state.{name} must be a finite non-negative number")

    # Reference policy: integrate the supplied evidence linearly, without
    # discounting, p_ref = p + w * (target - p).
    reference = own + weight * (target - own)

    # The modeled attribution pathway requires all three conditions:
    # a meaningful opposing estimate, explicitly neutral self-framing, and
    # explicit positive attribution of dissent to a defect. Evidence must point
    # in the same direction as the dissent for it to be discounted.
    gap = dissent - own
    evidence_direction = target - own
    has_disagreement = abs(gap) >= _DISAGREEMENT_THRESHOLD
    evidence_supports_dissent = gap * evidence_direction > 0.0
    condition = (
        has_disagreement
        and evidence_supports_dissent
        and neutral
        and attribution > 0.0
    )
    discount_fraction = float(strength) * attribution if condition else 0.0
    effective_weight = weight * (1.0 - discount_fraction)
    estimate = own + effective_weight * evidence_direction
    # Guard against tiny floating point excursions while retaining the defined
    # probability-domain result.
    estimate = min(1.0, max(0.0, estimate))
    active = estimate != reference

    state["rounds_seen"] = rounds + 1
    state["last_estimate"] = estimate
    state["cumulative_abs_movement"] = float(cumulative_movement) + abs(estimate - own)
    state["cumulative_evidence_weight_discounted"] = (
        float(cumulative_discount) + weight - effective_weight
    )
    trace = (
        f"Reference p+w*(target-p)={reference:.12g}; own={own:g}, target={target:g}, "
        f"weight={weight:g}. Necessary conditions: disagreement_gap>="
        f"{_DISAGREEMENT_THRESHOLD:g} ({has_disagreement}), evidence aligns with "
        f"dissent ({evidence_supports_dissent}), self_view_as_neutral={neutral}, "
        f"defect_attribution={attribution:g}. Applied discount_fraction="
        f"{discount_fraction:g}, effective_weight={effective_weight:g}; "
        f"revised_estimate={estimate:.12g}."
    )
    return {"metric": estimate, "active": bool(active), "state": state, "trace": [trace]}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "own_estimate": 0.8,
                    "evidence_target": 0.2,
                    "evidence_weight": 0.5,
                    "dissenting_estimate": 0.2,
                    "self_view_as_neutral": True,
                    "dissent_defect_attribution": 0.8,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "own_estimate": 0.8,
                    "evidence_target": 0.95,
                    "evidence_weight": 0.6,
                    "dissenting_estimate": 0.8,
                    "self_view_as_neutral": True,
                    "dissent_defect_attribution": 0.8,
                }
            ],
            "expectation": "equal",
        },
    ]
