"""Illustrative, synthetic just-world attribution-choice mechanism.

This is an explicit toy process model, not a classifier or empirical claim.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "just_world_hypothesis",
    "name": "Just-world Hypothesis",
    "kind": "cognitive_bias",
    "description": (
        "When evaluating an outcome without supported action-specific causal evidence, "
        "an outcome-deserves-it prior can make a moral-desert attribution more competitive."
    ),
    "required_inputs": ["outcome_valence", "action_consequence_supported", "attributions"],
    "state_fields": ["decision_count", "desert_attribution_count", "last_choice"],
    "metric_name": "selected_desert_attribution",
    "metric_units": "Binary choice indicator (1 if the selected explanation says the outcome was deserved; otherwise 0).",
    "assumptions": [
        "The candidate explanations and their evidence_support values are supplied by the task; the mechanism does not infer them from text.",
        "The strength-scaled 0.6 prior weight is an illustrative setting, not an estimated effect size.",
        "At strength zero, the reference policy selects the candidate with greatest evidence support; ties use listed order.",
        "A supported action-specific consequence claim suppresses the just-world prior entirely, respecting the supplied boundary.",
    ],
    "limitations": [
        "This small choice model does not represent the many social, cultural, or situational causes of real judgments.",
        "It does not determine whether evidence is actually supported or whether an outcome is morally deserved.",
        "It is hypothetical, synthetic-only, and not empirically validated; no detection accuracy is claimed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_PRIOR_WEIGHT = 0.6
_ALLOWED_VALENCES = {"adverse", "beneficial"}


def _finite_unit(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return number


def _validated_state(raw: object) -> dict:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("state must be a dict")
    count = raw.get("decision_count", 0)
    desert_count = raw.get("desert_attribution_count", 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.decision_count must be a non-negative integer")
    if isinstance(desert_count, bool) or not isinstance(desert_count, int) or not 0 <= desert_count <= count:
        raise ValueError("state.desert_attribution_count must be an integer between zero and decision_count")
    last = raw.get("last_choice")
    if last is not None and not isinstance(last, str):
        raise ValueError("state.last_choice must be a string or None")
    return {"decision_count": count, "desert_attribution_count": desert_count, "last_choice": last}


def evaluate(context: dict, strength: float) -> dict:
    """Choose an attribution and return its binary desert metric plus complete task state."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    valence = context.get("outcome_valence")
    if valence not in _ALLOWED_VALENCES:
        raise ValueError("outcome_valence must be 'adverse' or 'beneficial'")
    supported = context.get("action_consequence_supported")
    if not isinstance(supported, bool):
        raise ValueError("action_consequence_supported must be a bool backed by supplied task evidence")
    candidates = context.get("attributions")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("attributions must contain at least two structured candidate explanations")

    checked = []
    seen = set()
    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"attributions[{i}] must be a dict")
        label = candidate.get("label")
        if not isinstance(label, str) or not label:
            raise ValueError(f"attributions[{i}].label must be a non-empty string")
        if label in seen:
            raise ValueError("attribution labels must be unique")
        seen.add(label)
        support = _finite_unit(candidate.get("evidence_support"), f"attributions[{i}].evidence_support")
        says_deserved = candidate.get("says_deserved")
        if not isinstance(says_deserved, bool):
            raise ValueError(f"attributions[{i}].says_deserved must be a bool")
        checked.append({"label": label, "evidence_support": support, "says_deserved": says_deserved})

    prior_state = _validated_state(context.get("state", {}))

    # Explicit strength-zero reference policy: choose the best-evidenced explanation;
    # Python's stable max preserves the supplied order on ties.
    baseline = max(checked, key=lambda item: item["evidence_support"])
    if supported:
        # Boundary: a supported claim linking a specific action to its consequence
        # uses exactly the reference choice and receives no outcome-deserves-it prior.
        selected = baseline
        reason = "supported action-specific consequence evidence: prior suppressed; reference choice used"
    else:
        # The task-specific prior represents the hypothesis that this observed fortune
        # should fit moral desert. It competes with evidence support, rather than
        # subtracting a generic penalty from any candidate.
        selected = max(
            checked,
            key=lambda item: item["evidence_support"]
            + (strength * _PRIOR_WEIGHT if item["says_deserved"] else 0.0),
        )
        reason = (
            f"no supported action-specific consequence claim: score = evidence_support + "
            f"{strength:g}*{_PRIOR_WEIGHT:g} for a says_deserved attribution"
        )

    metric = 1.0 if selected["says_deserved"] else 0.0
    baseline_metric = 1.0 if baseline["says_deserved"] else 0.0
    next_state = {
        "decision_count": prior_state["decision_count"] + 1,
        "desert_attribution_count": prior_state["desert_attribution_count"] + int(metric),
        "last_choice": selected["label"],
    }
    return {
        "metric": metric,
        "active": selected["label"] != baseline["label"],
        "state": next_state,
        "trace": [
            f"Outcome={valence}; action_consequence_supported={supported}.",
            f"Reference choice={baseline['label']!r} (evidence_support={baseline['evidence_support']:g}, metric={baseline_metric:g}); selected={selected['label']!r} (evidence_support={selected['evidence_support']:g}, metric={metric:g}).",
            reason,
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"decision_count": 0, "desert_attribution_count": 0, "last_choice": None},
            "contexts": [
                {
                    "outcome_valence": "adverse",
                    "action_consequence_supported": False,
                    "attributions": [
                        {"label": "structural_misfortune", "evidence_support": 0.4, "says_deserved": False},
                        {"label": "victim_deserved_outcome", "evidence_support": 0.1, "says_deserved": True},
                    ],
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"decision_count": 0, "desert_attribution_count": 0, "last_choice": None},
            "contexts": [
                {
                    "outcome_valence": "adverse",
                    "action_consequence_supported": True,
                    "attributions": [
                        {"label": "specific_action_consequence", "evidence_support": 0.8, "says_deserved": False},
                        {"label": "victim_deserved_outcome", "evidence_support": 0.1, "says_deserved": True},
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
