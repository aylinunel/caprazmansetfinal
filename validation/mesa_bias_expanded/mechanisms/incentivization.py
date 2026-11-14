"""Illustrative binary-task model of behavior under explicit incentives."""

from copy import deepcopy
import math


METADATA = {
    "id": "incentivization",
    "name": "Incentivization",
    "kind": "motivational_mechanism",
    "description": (
        "A completion reward and/or noncompletion penalty shifts the net-utility "
        "threshold for completing a specified task."
    ),
    "required_inputs": [
        "task_value",
        "effort_cost",
        "completion_reward",
        "noncompletion_penalty",
    ],
    "state_fields": [
        "decision_count",
        "last_completion",
        "last_intrinsic_surplus",
        "last_incentive_contribution",
        "last_effective_surplus",
    ],
    "metric_name": "task_completion",
    "metric_units": "Binary completion choice (0 = not completed, 1 = completed).",
    "assumptions": [
        "All four task amounts are expressed in comparable utility units.",
        "The participant chooses completion exactly when net modeled utility is nonnegative.",
        "The strength setting linearly scales only the explicit reward/penalty contingency.",
        "Rewards for completion and penalties for noncompletion are additive and salient.",
    ],
    "limitations": [
        "A deterministic single-agent choice illustration, not an empirical psychological model.",
        "Does not model crowding-out, fairness, social context, learning, or reward timing.",
        "A changed completion choice is not inherently beneficial, harmful, or manipulative.",
        "Coefficients and strength are illustrative assumptions, not fitted effect sizes.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, name, *, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    if nonnegative and number < 0:
        raise ValueError(f"{name} must be nonnegative")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one task decision without mutating the provided context.

    Reference policy (strength=0): complete when task_value - effort_cost >= 0.
    At nonzero strength, add strength * (completion_reward +
    noncompletion_penalty) to that same intrinsic surplus.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    strength_value = _finite_number(strength, "strength")
    if not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be within [0, 1]")

    amounts = {}
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required input: {field}")
        amounts[field] = _finite_number(context[field], field, nonnegative=True)

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(prior_state)
    previous_count = state.get("decision_count", 0)
    if isinstance(previous_count, bool) or not isinstance(previous_count, int) or previous_count < 0:
        raise ValueError("state.decision_count must be a nonnegative integer")

    intrinsic_surplus = amounts["task_value"] - amounts["effort_cost"]
    incentive_contribution = strength_value * (
        amounts["completion_reward"] + amounts["noncompletion_penalty"]
    )
    effective_surplus = intrinsic_surplus + incentive_contribution
    completion = effective_surplus >= 0.0
    reference_completion = intrinsic_surplus >= 0.0
    metric = 1.0 if completion else 0.0

    state.update(
        {
            "decision_count": previous_count + 1,
            "last_completion": completion,
            "last_intrinsic_surplus": intrinsic_surplus,
            "last_incentive_contribution": incentive_contribution,
            "last_effective_surplus": effective_surplus,
        }
    )
    return {
        "metric": metric,
        "active": completion != reference_completion,
        "state": state,
        "trace": [
            "intrinsic_surplus = task_value - effort_cost = "
            f"{amounts['task_value']} - {amounts['effort_cost']} = {intrinsic_surplus}.",
            "incentive_contribution = strength * (completion_reward + "
            "noncompletion_penalty) = "
            f"{strength_value} * ({amounts['completion_reward']} + "
            f"{amounts['noncompletion_penalty']}) = {incentive_contribution}.",
            "completion iff effective_surplus >= 0; "
            f"effective_surplus = {effective_surplus}, completion = {completion}; "
            f"strength-zero reference completion = {reference_completion}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "task_value": 2.0,
                    "effort_cost": 5.0,
                    "completion_reward": 3.5,
                    "noncompletion_penalty": 0.5,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "task_value": 2.0,
                    "effort_cost": 5.0,
                    "completion_reward": 0.0,
                    "noncompletion_penalty": 0.0,
                }
            ],
            "expectation": "equal",
        },
    ]
