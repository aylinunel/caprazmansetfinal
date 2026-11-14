"""Illustrative overjustification process; not a detector or fitted psychology."""
from __future__ import annotations

import math


METADATA = {
    "id": "overjustification_effect",
    "name": "Overjustification Effect",
    "kind": "motivational_mechanism",
    "description": (
        "An explicit hypothetical process in which contingent reward exposure "
        "reduces later voluntary allocation to an already intrinsically interesting activity."
    ),
    # These five scenario fields are supplied in every phase. Phase-specific
    # requirements are checked in evaluate rather than encoded as prose here.
    "required_inputs": [
        "phase", "intrinsic_interest", "reward_contingent",
        "reward_salience", "baseline_choice_minutes",
    ],
    "state_fields": [
        "baseline_seen", "baseline_interest", "baseline_minutes",
        "reward_dose", "completed",
    ],
    "metric_name": "predicted_unrewarded_free_choice_minutes",
    "metric_units": "minutes in a fixed optional, unrewarded activity probe",
    "assumptions": [
        "Interest, reward contingency, and salience are explicit hypothetical task inputs, not inferred from language or behavior.",
        "Illustrative fractional decline is strength × baseline interest × accumulated reward dose.",
        "Reward dose accumulates as 1 minus the product of one minus each contingent reward salience.",
        "Strength is an uncalibrated intervention setting; zero is the unchanged-baseline reference policy.",
    ],
    "limitations": [
        "This small state model omits task meaning, reward type, attribution, autonomy, social context, and individual differences.",
        "A post-reward change in voluntary time can have benign alternative explanations and is not evidence of a cognitive error or diagnosis.",
        "The coefficients and simulated outcomes are illustrative and have no empirical-validity claim.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_STATE_DEFAULTS = {
    "baseline_seen": False,
    "baseline_interest": None,
    "baseline_minutes": None,
    "reward_dose": 0.0,
    "completed": False,
}


def _number(value, name, low, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value) or value < low or (high is not None and value > high):
        bound = f" in [{low}, {high}]" if high is not None else f" >= {low}"
        raise ValueError(f"{name} must be finite and{bound}")
    return value


def _copy_state(context):
    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be an object")
    state = dict(_STATE_DEFAULTS)
    state.update(prior)
    if not isinstance(state["baseline_seen"], bool) or not isinstance(state["completed"], bool):
        raise ValueError("state baseline_seen and completed must be booleans")
    if not isinstance(state["reward_dose"], (int, float)) or isinstance(state["reward_dose"], bool):
        raise ValueError("state reward_dose must be numeric")
    dose = float(state["reward_dose"])
    if not math.isfinite(dose) or not 0.0 <= dose <= 1.0:
        raise ValueError("state reward_dose must be finite and in [0, 1]")
    state["reward_dose"] = dose
    if state["baseline_seen"]:
        state["baseline_interest"] = _number(state["baseline_interest"], "state baseline_interest", 0, 1)
        state["baseline_minutes"] = _number(state["baseline_minutes"], "state baseline_minutes", 0)
    elif state["baseline_interest"] is not None or state["baseline_minutes"] is not None:
        raise ValueError("unseen baseline cannot contain baseline observations")
    if state["completed"] and not state["baseline_seen"]:
        raise ValueError("completed state requires a baseline")
    return state


def evaluate(context: dict, strength: float) -> dict:
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError("missing required task input(s): " + ", ".join(missing))

    phase = context["phase"]
    if phase not in ("baseline", "reward", "post_reward"):
        raise ValueError("phase must be baseline, reward, or post_reward")
    interest = _number(context["intrinsic_interest"], "intrinsic_interest", 0, 1)
    salience = _number(context["reward_salience"], "reward_salience", 0, 1)
    minutes = _number(context["baseline_choice_minutes"], "baseline_choice_minutes", 0)
    contingent = context["reward_contingent"]
    if not isinstance(contingent, bool):
        raise ValueError("reward_contingent must be a boolean")

    state = _copy_state(context)
    if state["completed"]:
        raise ValueError("no task phase may follow completed post_reward")

    if phase == "baseline":
        if state["baseline_seen"]:
            raise ValueError("baseline may occur only once, before reward exposure")
        if contingent or salience != 0:
            raise ValueError("baseline phase must not contain a contingent reward")
        state.update(baseline_seen=True, baseline_interest=interest, baseline_minutes=minutes)
        metric = minutes
        active = False
        trace = [f"Baseline: stored explicit interest={interest:g} and voluntary-time reference={minutes:g} min."]
    else:
        if not state["baseline_seen"]:
            raise ValueError(f"{phase} requires a preceding baseline observation")
        if interest != state["baseline_interest"] or minutes != state["baseline_minutes"]:
            raise ValueError("interest and baseline_choice_minutes must match the stored baseline")
        if phase == "reward":
            if not contingent or salience <= 0:
                raise ValueError("reward phase requires a contingent reward with positive salience")
            state["reward_dose"] = 1.0 - (1.0 - state["reward_dose"]) * (1.0 - salience)
            metric = state["baseline_minutes"]
            active = False
            trace = [
                f"Reward history: dose=1−(1−prior dose)×(1−salience)={state['reward_dose']:.6g}; "
                "the unrewarded-probe prediction is not reduced before reward removal."
            ]
        else:
            if contingent or salience != 0:
                raise ValueError("post_reward phase must be an unrewarded probe")
            if state["reward_dose"] <= 0:
                raise ValueError("post_reward requires preceding contingent reward exposure")
            # Required conjunction: an observed positive-interest baseline and
            # accumulated contingent-reward exposure. Zero baseline interest
            # is the explicit no-overjustification boundary.
            fractional_decline = strength * state["baseline_interest"] * state["reward_dose"]
            metric = state["baseline_minutes"] * (1.0 - fractional_decline)
            state["completed"] = True
            active = strength > 0 and state["baseline_interest"] > 0 and state["reward_dose"] > 0
            trace = [
                "Post-reward probe: minutes=baseline_minutes×(1−strength×baseline_interest×reward_dose); "
                f"{state['baseline_minutes']:g}×(1−{strength:g}×{state['baseline_interest']:g}×{state['reward_dose']:.6g})={metric:.6g}."
            ]

    return {"metric": float(metric), "active": active, "state": state, "trace": trace}


def scenarios() -> list[dict]:
    interest, minutes = 0.8, 10.0
    return [
        {
            "name": "positive",
            "initial_state": dict(_STATE_DEFAULTS),
            "contexts": [
                {"phase": "baseline", "intrinsic_interest": interest, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": minutes},
                {"phase": "reward", "intrinsic_interest": interest, "reward_contingent": True, "reward_salience": 0.7, "baseline_choice_minutes": minutes},
                {"phase": "post_reward", "intrinsic_interest": interest, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": minutes},
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": dict(_STATE_DEFAULTS),
            "contexts": [
                {"phase": "baseline", "intrinsic_interest": 0.0, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": minutes},
                {"phase": "reward", "intrinsic_interest": 0.0, "reward_contingent": True, "reward_salience": 0.7, "baseline_choice_minutes": minutes},
                {"phase": "post_reward", "intrinsic_interest": 0.0, "reward_contingent": False, "reward_salience": 0.0, "baseline_choice_minutes": minutes},
            ],
            "expectation": "equal",
        },
    ]
