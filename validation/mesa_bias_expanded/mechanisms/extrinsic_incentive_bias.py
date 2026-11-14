"""Illustrative evidence-weighting process for extrinsic incentive bias.

This is a hypothetical mechanism, not an empirical model or detector.
"""

from math import isfinite


METADATA = {
    "id": "extrinsic_incentive_bias",
    "name": "Extrinsic Incentive Bias",
    "kind": "cognitive_bias",
    "description": (
        "Models an observer overweighting a documented reward cue when attributing "
        "another person's motivation, relative to the same evidence-weighting rule "
        "for self, when the other's motives are underdocumented."
    ),
    "required_inputs": [
        "self_reward_signal",
        "self_intrinsic_signal",
        "other_reward_signal",
        "other_intrinsic_signal",
        "other_motive_documentation",
    ],
    "state_fields": [
        "steps",
        "sum_self_extrinsic_share",
        "sum_other_extrinsic_share",
        "last_self_extrinsic_share",
        "last_other_extrinsic_share",
    ],
    "metric_name": "other_extrinsic_motivation_attribution",
    "metric_units": "proportion of attributed motivation (0 to 1)",
    "assumptions": [
        "Reward and intrinsic signals are explicit, normalized evidence values, not inferred from language.",
        "Motive documentation is a supplied completeness value: 0 means undocumented and 1 means fully documented.",
        "The illustrative strength scales how much an underdocumented reward cue is overweighted.",
        "At strength zero, both targets use the same reward-signal share of total reward and intrinsic signals.",
    ],
    "limitations": [
        "The formula and coefficients are illustrative assumptions, not empirically estimated or validated.",
        "A reward signal or incomplete documentation alone does not establish a person's actual motive.",
        "This compact model omits context, mixed motives, observer differences, and uncertainty calibration.",
        "It is not an NLP detector, diagnosis, or population-level claim.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(context: dict, field: str) -> float:
    if field not in context:
        raise ValueError(f"missing required input: {field}")
    value = context[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def _previous_state(context: dict) -> dict:
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    steps = state.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a nonnegative integer")
    result = {"steps": steps}
    for field in ("sum_self_extrinsic_share", "sum_other_extrinsic_share"):
        value = state.get(field, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or value < 0:
            raise ValueError(f"state.{field} must be a finite nonnegative number")
        result[field] = float(value)
    for field in ("last_self_extrinsic_share", "last_other_extrinsic_share"):
        value = state.get(field, 0.0)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)) or not 0.0 <= value <= 1.0:
            raise ValueError(f"state.{field} must be a finite number in [0, 1]")
        result[field] = float(value)
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one hypothetical attribution step without mutating ``context``."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    self_reward = _unit_interval(context, "self_reward_signal")
    self_intrinsic = _unit_interval(context, "self_intrinsic_signal")
    other_reward = _unit_interval(context, "other_reward_signal")
    other_intrinsic = _unit_interval(context, "other_intrinsic_signal")
    documentation = _unit_interval(context, "other_motive_documentation")
    if self_reward + self_intrinsic == 0:
        raise ValueError("self reward and intrinsic evidence cannot both be zero")
    if other_reward + other_intrinsic == 0:
        raise ValueError("other reward and intrinsic evidence cannot both be zero")

    # Reference rule: attribute each target's reward share proportionally to the
    # explicit reward and intrinsic evidence. The mechanism changes only the
    # other's reward-cue weight, scaled by underdocumentation.
    self_share = self_reward / (self_reward + self_intrinsic)
    baseline_other = other_reward / (other_reward + other_intrinsic)
    reward_weight = 1.0 + strength * (1.0 - documentation)
    weighted_reward = other_reward * reward_weight
    other_share = weighted_reward / (weighted_reward + other_intrinsic)
    active = other_share != baseline_other

    previous = _previous_state(context)
    next_state = {
        "steps": previous["steps"] + 1,
        "sum_self_extrinsic_share": previous["sum_self_extrinsic_share"] + self_share,
        "sum_other_extrinsic_share": previous["sum_other_extrinsic_share"] + other_share,
        "last_self_extrinsic_share": self_share,
        "last_other_extrinsic_share": other_share,
    }
    return {
        "metric": float(other_share),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"Reference self share = {self_reward}/({self_reward}+{self_intrinsic}) = {self_share:.6f}; ",
            f"reference other share = {baseline_other:.6f}.",
            f"Other reward weight = 1 + strength({strength}) * (1 - documentation({documentation})) = {reward_weight:.6f}; ",
            f"attributed other share = ({other_reward} * {reward_weight}) / ({other_reward} * {reward_weight} + {other_intrinsic}) = {other_share:.6f}.",
            "The differential cue-weighting condition requires a positive other reward signal and documentation below 1; a zero reward signal or complete documentation leaves the reference share unchanged.",
        ],
    }


def scenarios() -> list[dict]:
    common = {
        "self_reward_signal": 0.4,
        "self_intrinsic_signal": 0.6,
        "other_reward_signal": 0.4,
        "other_intrinsic_signal": 0.6,
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{**common, "other_motive_documentation": 0.0}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{**common, "other_motive_documentation": 1.0}],
            "expectation": "equal",
        },
    ]
