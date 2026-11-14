"""Illustrative sequential warning-response model for normalcy bias.

This is a hypothetical task process, not a detector or fitted psychological model.
"""
import math


METADATA = {
    "id": "normalcy_bias",
    "name": "Normalcy Bias",
    "kind": "cognitive_bias",
    "description": (
        "When credible disruption warnings arrive, intervention strength selectively "
        "reduces the log-evidence weight used to update perceived disruption odds; "
        "preparation is chosen by comparing perceived expected loss with its cost."
    ),
    # This field is common to every phase; other per-phase evidence is checked below.
    "required_inputs": ["base_disruption_probability"],
    "state_fields": [
        "initialized", "objective_log_odds", "perceived_log_odds", "prepared",
        "cumulative_task_loss", "credible_warning_count",
    ],
    "metric_name": "cumulative_expected_task_loss",
    "metric_units": "hypothetical task-loss units across warning phases; preparation cost or unprepared objective expected loss",
    "assumptions": [
        "Each credible warning supplies a likelihood ratio multiplying disruption odds.",
        "At strength s, only credible warning log-evidence is attenuated by factor 1 - 0.8*s.",
        "The reference uses full supplied credible evidence and the same preparation-cost decision rule.",
        "Preparation is persistent and incurs its cost once; otherwise each phase accrues objective expected disruption loss.",
        "All coefficients and scenario values are illustrative, not calibrated effect sizes.",
    ],
    "limitations": [
        "A stylized binary-hazard decision task omits social, institutional, and practical response constraints.",
        "Likelihood ratios, losses, preparation costs, and the attenuation coefficient are hypothetical inputs.",
        "The model does not diagnose people, detect real warnings, or establish empirical validity.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(context, name, *, minimum=None, maximum=1e12):
    value = context.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if value > maximum or (minimum is not None and value < minimum):
        raise ValueError(f"{name} is outside the allowed task range")
    return value


def _probability(value, name):
    if not 0.0 < value < 1.0:
        raise ValueError(f"{name} must be strictly between 0 and 1")
    return value


def _sigmoid(log_odds):
    if log_odds >= 0:
        z = math.exp(-log_odds) if log_odds < 746 else 0.0
        return 1.0 / (1.0 + z)
    z = math.exp(log_odds) if log_odds > -746 else 0.0
    return z / (1.0 + z)


def _initial_state(state, base_probability):
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    if not state.get("initialized", False):
        log_odds = math.log(base_probability) - math.log1p(-base_probability)
        return {
            "initialized": True,
            "objective_log_odds": log_odds,
            "perceived_log_odds": log_odds,
            "prepared": False,
            "cumulative_task_loss": 0.0,
            "credible_warning_count": 0,
        }
    needed = METADATA["state_fields"]
    if any(key not in state for key in needed):
        raise ValueError("initialized state is incomplete")
    objective = state["objective_log_odds"]
    perceived = state["perceived_log_odds"]
    loss = state["cumulative_task_loss"]
    count = state["credible_warning_count"]
    if (isinstance(objective, bool) or not isinstance(objective, (int, float)) or not math.isfinite(objective)
            or isinstance(perceived, bool) or not isinstance(perceived, (int, float)) or not math.isfinite(perceived)
            or isinstance(loss, bool) or not isinstance(loss, (int, float)) or not math.isfinite(loss) or loss < 0
            or isinstance(count, bool) or not isinstance(count, int) or count < 0
            or not isinstance(state["prepared"], bool) or state["initialized"] is not True):
        raise ValueError("initialized state contains invalid task values")
    return {
        "initialized": True,
        "objective_log_odds": float(objective),
        "perceived_log_odds": float(perceived),
        "prepared": state["prepared"],
        "cumulative_task_loss": float(loss),
        "credible_warning_count": count,
    }


def evaluate(context: dict, strength: float) -> dict:
    """Advance one warning phase; all phase-specific evidence is explicit in context."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    base = _probability(_number(context, "base_disruption_probability", minimum=0.0), "base_disruption_probability")
    ratio = _number(context, "warning_likelihood_ratio", minimum=1.0)
    damage = _number(context, "disruption_loss", minimum=0.0)
    prep_cost = _number(context, "precaution_cost", minimum=0.0)
    credible = context.get("warning_credible")
    if not isinstance(credible, bool):
        raise ValueError("warning_credible must be a boolean")
    next_state = _initial_state(context.get("state", {}), base)

    # A non-credible alert is not evidence in either policy. For a credible alert,
    # the reference adds log(LR); the bias adds only (1 - .8*strength)*log(LR).
    log_evidence = math.log(ratio) if credible else 0.0
    next_state["objective_log_odds"] += log_evidence
    attenuation = 1.0 - 0.8 * float(strength)
    next_state["perceived_log_odds"] += attenuation * log_evidence
    if credible and ratio > 1.0:
        next_state["credible_warning_count"] += 1

    objective_probability = _sigmoid(next_state["objective_log_odds"])
    perceived_probability = _sigmoid(next_state["perceived_log_odds"])
    expected_precautionary_saving = perceived_probability * damage
    chose_preparation = (not next_state["prepared"] and expected_precautionary_saving >= prep_cost)
    if chose_preparation:
        next_state["prepared"] = True
        phase_loss = prep_cost
    elif next_state["prepared"]:
        phase_loss = 0.0
    else:
        phase_loss = objective_probability * damage
    next_state["cumulative_task_loss"] += phase_loss
    if not math.isfinite(next_state["cumulative_task_loss"]):
        raise ValueError("task loss overflowed the supported finite range")

    active = bool(float(strength) > 0 and credible and ratio > 1.0)
    trace = (
        f"credible={credible}; LR={ratio:g}; objective log-odds += {log_evidence:.6g}; "
        f"perceived log-odds += {attenuation:.6g}*{log_evidence:.6g}; "
        f"objective_p={objective_probability:.6g}, perceived_p={perceived_probability:.6g}; "
        f"prepare={next_state['prepared']} (threshold compares perceived_p*loss with cost); "
        f"phase_loss={phase_loss:.6g}."
    )
    return {
        "metric": next_state["cumulative_task_loss"],
        "active": active,
        "state": next_state,
        "trace": [trace],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"base_disruption_probability": 0.05, "warning_credible": True,
                 "warning_likelihood_ratio": 8.0, "disruption_loss": 100.0, "precaution_cost": 55.0},
                {"base_disruption_probability": 0.05, "warning_credible": True,
                 "warning_likelihood_ratio": 8.0, "disruption_loss": 100.0, "precaution_cost": 55.0},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            # An alert is present but explicitly lacks credibility: no qualifying
            # warning evidence, so neither policy updates odds from its LR.
            "contexts": [
                {"base_disruption_probability": 0.05, "warning_credible": False,
                 "warning_likelihood_ratio": 8.0, "disruption_loss": 100.0, "precaution_cost": 55.0},
                {"base_disruption_probability": 0.05, "warning_credible": False,
                 "warning_likelihood_ratio": 8.0, "disruption_loss": 100.0, "precaution_cost": 55.0},
            ],
            "expectation": "equal",
        },
    ]
