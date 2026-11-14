"""Illustrative, synthetic action-bias choice process; not a detector."""
from __future__ import annotations

import math
from numbers import Real

METADATA = {
    "id": "action_bias",
    "name": "Action Bias",
    "kind": "cognitive_bias",
    "description": (
        "In a one-step act-versus-wait decision, explicit immediate-action pressure "
        "can tip an unsupported action choice despite a small expected-utility disadvantage."
    ),
    "required_inputs": [
        "action_utility",
        "wait_utility",
        "action_pressure",
        "evidence_supported",
    ],
    "state_fields": ["chosen_action", "unsupported_action_count", "decision_count", "last_utility_gap"],
    "metric_name": "action_chosen",
    "metric_units": "Binary choice indicator (1 = act, 0 = wait).",
    "assumptions": [
        "Utilities are comparable expected task values scaled to [0, 1].",
        "action_pressure is an explicit task-supplied, utility-equivalent pressure to resolve the decision by acting now; it is not inferred from wording.",
        "At strength zero the reference policy acts iff action_utility strictly exceeds wait_utility; ties go to waiting.",
        "Strength scales the action-pressure term linearly and is not a fitted effect size.",
    ],
    "limitations": [
        "This is a hypothetical one-decision process model, not an empirical psychological law, classifier, or population estimate.",
        "The supplied action_pressure and utility inputs are assumed rather than measured; their scales may not be comparable in real decisions.",
        "The binary evidence_supported flag is an explicit scenario fact, not inferred evidence quality; nuanced evidence and multi-option choices are not modeled.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _bounded_number(context: dict, key: str) -> float:
    if key not in context:
        raise ValueError(f"missing required input: {key}")
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one choice without modifying the supplied context or state."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    action_utility = _bounded_number(context, "action_utility")
    wait_utility = _bounded_number(context, "wait_utility")
    action_pressure = _bounded_number(context, "action_pressure")
    if "evidence_supported" not in context or not isinstance(context["evidence_supported"], bool):
        raise ValueError("evidence_supported must be supplied as a bool")
    evidence_supported = context["evidence_supported"]

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    unsupported_count = previous.get("unsupported_action_count", 0)
    decision_count = previous.get("decision_count", 0)
    for key, value in (("unsupported_action_count", unsupported_count), ("decision_count", decision_count)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{key} must be a nonnegative integer")

    gap = action_utility - wait_utility
    # The reference is a strict expected-value comparison: positive advantage acts,
    # a tie or disadvantage waits. Only unsupported immediate action receives pressure.
    reference_acts = gap > 0.0
    bias_eligible = not evidence_supported and action_pressure > 0.0
    biased_acts = reference_acts or (bias_eligible and gap + strength * action_pressure > 0.0)
    active = bool(biased_acts != reference_acts)
    unsupported_action = bool(biased_acts and gap <= 0.0 and not evidence_supported)
    next_state = {
        "chosen_action": "act" if biased_acts else "wait",
        "unsupported_action_count": unsupported_count + int(unsupported_action),
        "decision_count": decision_count + 1,
        "last_utility_gap": gap,
    }
    metric = 1.0 if biased_acts else 0.0
    if not math.isfinite(metric):  # defensive guarantee for the runner contract
        raise ArithmeticError("metric is not finite")
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            f"action_utility={action_utility:g}, wait_utility={wait_utility:g}, gap={gap:g}; "
            f"reference chooses {'act' if reference_acts else 'wait'} (act only for gap > 0).",
            f"evidence_supported={evidence_supported}, action_pressure={action_pressure:g}; "
            f"unsupported action term is {'enabled' if bias_eligible else 'suppressed'}.",
            f"biased decision condition: gap + strength*action_pressure > 0; strength={strength:g}; "
            f"choice={'act' if biased_acts else 'wait'}, active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "action_utility": 0.40,
                    "wait_utility": 0.50,
                    "action_pressure": 0.30,
                    "evidence_supported": False,
                }
            ],
            "expectation": "difference",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "action_utility": 0.70,
                    "wait_utility": 0.50,
                    "action_pressure": 0.30,
                    "evidence_supported": True,
                }
            ],
            "expectation": "equal",
        },
    ]
