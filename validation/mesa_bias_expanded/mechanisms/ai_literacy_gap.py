"""Illustrative choice-process model for an AI literacy gap.

This is a synthetic mechanism, not a detector or empirically fitted model.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "ai_literacy_gap",
    "name": "AI Literacy Gap",
    "kind": "cognitive_bias",
    "description": (
        "Models a task-specific AI-use choice in which comfort can be mistaken "
        "for enough competence to verify an AI-assisted answer."
    ),
    "required_inputs": [
        "ai_comfort",
        "ai_competence",
        "task_ai_advantage",
        "validation_demand",
    ],
    "state_fields": [
        "rounds",
        "ai_selected",
        "unverified_reliance",
        "last_choice",
    ],
    "metric_name": "unverified_ai_reliance",
    "metric_units": "binary unverified AI selection in this task step (0 or 1)",
    "assumptions": [
        "Comfort and competence are explicit hypothetical 0-1 inputs; neither is inferred from use frequency or text.",
        "task_ai_advantage is the supplied utility difference for AI assistance over the non-AI option; positive values make AI worthwhile before validation is considered.",
        "validation_demand is the minimum competence needed to validate this task's AI output.",
        "Strength linearly mixes actual competence with the comfort-competence gap; it is an illustrative intervention setting, not a measured effect size.",
        "The reference policy selects AI only when its supplied advantage is positive and actual competence meets the task's validation demand.",
    ],
    "limitations": [
        "This is a one-step choice model, not an account of how literacy develops or persists over time.",
        "Self-report scales, utility differences, and validation thresholds are hypothetical and may be context-dependent.",
        "It does not infer competence from frequent use, identify real people, detect AI content, or establish empirical prevalence or accuracy.",
        "Actual users may rationally rely on external verification, expert review, or other safeguards not represented here.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_INPUT_RANGES = {
    "ai_comfort": (0.0, 1.0),
    "ai_competence": (0.0, 1.0),
    "task_ai_advantage": (-1.0, 1.0),
    "validation_demand": (0.0, 1.0),
}
_OPTIONAL_RANGES = {"use_frequency": (0.0, 1.0)}
_STATE_DEFAULTS = {
    "rounds": 0,
    "ai_selected": 0,
    "unverified_reliance": 0,
    "last_choice": None,
}


def _number(value: object, name: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    result = float(value)
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return result


def _counter(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"state.{name} must be a non-negative integer")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one task choice; missing competence evidence is an error, not zero."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    strength_value = _number(strength, "strength", 0.0, 1.0)
    values = {}
    for name, (low, high) in _INPUT_RANGES.items():
        if name not in context:
            raise ValueError(f"missing required input: {name}")
        values[name] = _number(context[name], name, low, high)
    # Frequency may be supplied as context, but is deliberately not evidence of literacy.
    for name, (low, high) in _OPTIONAL_RANGES.items():
        if name in context:
            _number(context[name], name, low, high)

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("context.state must be a dict")
    next_state = dict(prior)  # preserve unrelated caller state without mutating it
    old = {}
    for name, default in _STATE_DEFAULTS.items():
        value = prior.get(name, default)
        old[name] = _counter(value, name) if name != "last_choice" else value
    if old["last_choice"] not in (None, "ai", "non_ai"):
        raise ValueError("state.last_choice must be None, 'ai', or 'non_ai'")

    comfort = values["ai_comfort"]
    competence = values["ai_competence"]
    advantage = values["task_ai_advantage"]
    demand = values["validation_demand"]

    # The no-gap reference uses assessed competence, not comfort, to gate AI use.
    reference_selected = advantage > 0.0 and competence >= demand
    gap = max(0.0, comfort - competence)
    perceived_validation_capacity = min(1.0, competence + strength_value * gap)
    selected = advantage > 0.0 and perceived_validation_capacity >= demand
    unverified = int(selected and competence < demand)
    active = selected != reference_selected

    next_state.update({
        "rounds": old["rounds"] + 1,
        "ai_selected": old["ai_selected"] + int(selected),
        "unverified_reliance": old["unverified_reliance"] + unverified,
        "last_choice": "ai" if selected else "non_ai",
    })
    return {
        "metric": unverified,
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"Reference AI choice = (task_ai_advantage {advantage:g} > 0) and "
            f"(actual competence {competence:g} >= validation demand {demand:g}) "
            f"= {reference_selected}.",
            f"Gap=max(0, comfort {comfort:g} - competence {competence:g})={gap:g}; "
            f"perceived validation capacity=min(1, competence + strength*gap)="
            f"min(1, {competence:g} + {strength_value:g}*{gap:g})="
            f"{perceived_validation_capacity:g}.",
            f"AI selected={selected} because advantage>0 and perceived capacity "
            f"{'>=' if selected else '<'} demand; metric=selected and actual competence<demand={unverified}.",
            f"use_frequency is not used as evidence; active={active} means the choice differs from the reference.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"rounds": 0, "ai_selected": 0, "unverified_reliance": 0, "last_choice": None},
            "contexts": [{
                "ai_comfort": 0.9,
                "ai_competence": 0.4,
                "task_ai_advantage": 0.5,
                "validation_demand": 0.7,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"rounds": 0, "ai_selected": 0, "unverified_reliance": 0, "last_choice": None},
            "contexts": [{
                "ai_comfort": 0.6,
                "ai_competence": 0.6,
                "task_ai_advantage": 0.5,
                "validation_demand": 0.8,
                "use_frequency": 1.0,
            }],
            "expectation": "equal",
        },
    ]
