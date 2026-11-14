"""Illustrative sequential public-commitment decision process (not a detector)."""

import math
from numbers import Real


METADATA = {
    "id": "commitment_bias",
    "name": "Commitment Bias",
    "kind": "cognitive_bias",
    "description": (
        "A sequential stay/exit decision adds an illustrative public-consistency "
        "utility to staying after a prior public commitment, even when current "
        "prospective value favors exit."
    ),
    "required_inputs": [
        "stay_value",
        "exit_value",
        "public_visibility",
        "announce_commitment",
    ],
    "state_fields": ["choice", "publicly_committed_to_stay", "commitment_round"],
    "metric_name": "stay_choice",
    "metric_units": "Binary choice (1 = stay, 0 = exit); not a probability or accuracy score.",
    "assumptions": [
        "stay_value and exit_value are comparable prospective utility points for the current decision; prior expenditure is excluded.",
        "A public consistency credit of 3 illustrative utility points at full visibility is an assumed process parameter, not an estimated effect size.",
        "At equal adjusted values, the reference tie-break is to stay.",
    ],
    "limitations": [
        "This synthetic toy process represents maintenance of a public commitment only; it does not model escalation, real people, or detection from language.",
        "Public visibility and values are explicit scenario inputs; alternative explanations such as new information or legitimate switching costs are not inferred.",
        "Not empirically validated; no human validation or detection accuracy has been measured.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

# Explicitly illustrative utility scale, held fixed so strength remains the
# generic intervention setting rather than a fitted or calibrated quantity.
_FULL_VISIBILITY_CONSISTENCY_UTILITY = 3.0


def _finite_number(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number")
    return number


def _validate_state(state):
    if not isinstance(state, dict):
        raise ValueError("context['state'] must be a dict")
    choice = state.get("choice")
    if choice is not None and choice not in ("stay", "exit"):
        raise ValueError("state.choice must be 'stay', 'exit', or None")
    committed = state.get("publicly_committed_to_stay", False)
    if not isinstance(committed, bool):
        raise ValueError("state.publicly_committed_to_stay must be bool")
    commitment_round = state.get("commitment_round")
    if commitment_round is not None and (
        isinstance(commitment_round, bool)
        or not isinstance(commitment_round, int)
        or commitment_round < 0
    ):
        raise ValueError("state.commitment_round must be a nonnegative int or None")
    if committed and (choice != "stay" or commitment_round is None):
        raise ValueError("a public stay commitment requires a prior stay choice and round")


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one round without mutating the context or its nested state."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be finite and within [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and within [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    stay_value = _finite_number(context["stay_value"], "stay_value")
    exit_value = _finite_number(context["exit_value"], "exit_value")
    visibility = _finite_number(context["public_visibility"], "public_visibility")
    if not 0.0 <= visibility <= 1.0:
        raise ValueError("public_visibility must be in [0, 1]")
    announce = context["announce_commitment"]
    if not isinstance(announce, bool):
        raise ValueError("announce_commitment must be bool")
    if "state" not in context:
        raise ValueError("missing required state: context['state']")
    prior = context["state"]
    _validate_state(prior)

    # Strength zero is the explicit reference: choose the greater current
    # prospective value (tie -> stay), excluding sunk expenditure and history.
    reference_choice = "stay" if stay_value >= exit_value else "exit"
    has_prior_public_stay = prior.get("publicly_committed_to_stay", False)
    # The necessary concept-specific conjunction is a prior public stay
    # commitment, current evidence favoring exit, and nonzero visibility.
    consistency_credit = 0.0
    if has_prior_public_stay and stay_value < exit_value:
        consistency_credit = (
            strength * _FULL_VISIBILITY_CONSISTENCY_UTILITY * visibility
        )
    adjusted_stay_value = stay_value + consistency_credit
    choice = "stay" if adjusted_stay_value >= exit_value else "exit"
    metric = 1.0 if choice == "stay" else 0.0

    committed = has_prior_public_stay
    commitment_round = prior.get("commitment_round") if committed else None
    if announce and choice == "stay" and not committed:
        committed = True
        commitment_round = context.get("round_index", 0)
        if isinstance(commitment_round, bool) or not isinstance(commitment_round, int) or commitment_round < 0:
            raise ValueError("round_index must be a nonnegative int when recording a commitment")
    next_state = {
        "choice": choice,
        "publicly_committed_to_stay": committed,
        "commitment_round": commitment_round,
    }
    trace = [
        "Reference: stay iff stay_value >= exit_value (tie -> stay); "
        f"current values are {stay_value:g} vs {exit_value:g}, reference={reference_choice}.",
        "Consistency credit = strength * 3.0 * public_visibility only if a prior "
        "public stay commitment exists AND stay_value < exit_value; "
        f"inputs: prior_public_stay={has_prior_public_stay}, strength={strength:g}, "
        f"visibility={visibility:g}, credit={consistency_credit:g}.",
        f"Adjusted stay={adjusted_stay_value:g}, exit={exit_value:g}; choice={choice}; "
        f"new public commitment recorded={bool(announce and choice == 'stay')}.",
    ]
    return {
        "metric": metric,
        "active": choice != reference_choice,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    """Return one positive sequential case and its public-commitment boundary."""
    first = {
        "stay_value": 4.0,
        "exit_value": 2.0,
        "public_visibility": 0.0,
        "announce_commitment": True,
    }
    reconsider = {
        "stay_value": 3.0,
        "exit_value": 4.0,
        "public_visibility": 1.0,
        "announce_commitment": False,
    }
    no_public_commitment = dict(first, announce_commitment=False)
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [first, reconsider],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [no_public_commitment, reconsider],
            "expectation": "equal",
        },
    ]
