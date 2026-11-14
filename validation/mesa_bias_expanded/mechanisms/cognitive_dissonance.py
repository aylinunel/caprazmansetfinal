"""Illustrative cognitive-dissonance resolution process; not a detector or diagnosis."""

from copy import deepcopy
import math
import numbers


METADATA = {
    "id": "cognitive_dissonance",
    "name": "Cognitive Dissonance",
    "kind": "psychological_state",
    "description": (
        "Models a hypothetical discomfort proxy from a committed belief/action "
        "conflict and a possible belief shift toward one's freely chosen action."
    ),
    "required_inputs": [
        "prior_belief",
        "action_position",
        "evidence_position",
        "evidence_weight",
        "commitment",
        "choice_freedom",
    ],
    "state_fields": [
        "rounds",
        "prior_belief",
        "reference_belief",
        "belief",
        "inconsistency",
        "discomfort",
        "resolution_shift",
    ],
    "metric_name": "post_resolution_belief_position",
    "metric_units": "normalized position on a 0-1 issue scale",
    "assumptions": [
        "Inputs explicitly describe a hypothetical person's prior position, action, evidence and commitment; none are inferred.",
        "The reference rule is a linear evidence-weighted update.",
        "A fraction of the belief/action inconsistency, scaled by commitment and choice freedom, represents a possible resolution pull toward the chosen action.",
        "Strength is an illustrative intervention setting, not prevalence, confidence or an empirical effect size.",
    ],
    "limitations": [
        "This is a toy process model and its discomfort proxy and coefficients are not empirically validated.",
        "Dissonance and resolution are not inherently biased or harmful; honest belief revision, changed behavior, or tolerating discomfort are omitted alternatives.",
        "It is not a psychological diagnosis, population claim, or detector of real-world motives.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value, field):
    """Return a finite float in [0, 1], rejecting bools and non-numbers."""
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit belief/action/evidence situation without mutation.

    The zero-strength reference is b_ref=(1-w)*b_prior+w*evidence. A
    hypothetical resolution pull is strength*D*(action-b_ref), where
    D=abs(b_prior-action)*commitment*choice_freedom. The resulting position
    remains a convex combination of two values in [0, 1].
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, numbers.Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    values = {}
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required input: {field}")
        values[field] = _unit_interval(context[field], field)

    prior = values["prior_belief"]
    action = values["action_position"]
    evidence = values["evidence_position"]
    evidence_weight = values["evidence_weight"]
    commitment = values["commitment"]
    choice_freedom = values["choice_freedom"]

    reference = (1.0 - evidence_weight) * prior + evidence_weight * evidence
    inconsistency = abs(prior - action)
    discomfort = inconsistency * commitment * choice_freedom
    shift = strength * discomfort * (action - reference)
    belief = reference + shift
    if not math.isfinite(belief):  # Defensive invariant for future formula edits.
        raise ValueError("computed belief is not finite")

    previous_state = context.get("state", {})
    if not isinstance(previous_state, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(previous_state)
    rounds = state.get("rounds", 0)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds must be a nonnegative integer")
    state.update(
        {
            "rounds": rounds + 1,
            "prior_belief": prior,
            "reference_belief": reference,
            "belief": belief,
            "inconsistency": inconsistency,
            "discomfort": discomfort,
            "resolution_shift": shift,
        }
    )

    return {
        "metric": belief,
        "active": not math.isclose(belief, reference, rel_tol=0.0, abs_tol=1e-15),
        "state": state,
        "trace": [
            f"Reference belief=(1-{evidence_weight:g})*{prior:g}+{evidence_weight:g}*{evidence:g}={reference:.12g}.",
            f"Discomfort proxy=|{prior:g}-{action:g}|*{commitment:g}*{choice_freedom:g}={discomfort:.12g}.",
            f"Resolution shift={strength:g}*discomfort*({action:g}-reference)={shift:.12g}; returned belief={belief:.12g}.",
        ],
    }


def scenarios() -> list[dict]:
    positive = {
        "prior_belief": 0.2,
        "action_position": 0.9,
        "evidence_position": 0.1,
        "evidence_weight": 0.8,
        "commitment": 0.9,
        "choice_freedom": 1.0,
    }
    boundary = dict(positive, choice_freedom=0.0)
    return [
        {
            "name": "positive",
            "initial_state": {"rounds": 0},
            "contexts": [positive],
            "expectation": "difference",
        },
        {
            "name": "boundary",
            "initial_state": {"rounds": 0},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
