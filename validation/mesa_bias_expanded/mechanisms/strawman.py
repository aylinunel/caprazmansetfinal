"""Illustrative, structured strawman reconstruction process (not a detector)."""

from copy import deepcopy
import math


METADATA = {
    "id": "strawman",
    "name": "Strawman Fallacy (Korkuluk safsatası)",
    "kind": "cognitive_bias",
    "description": (
        "An authored critique reconstructs a stated position by increasing its "
        "commitment or removing qualifications, then targets that reconstruction."
    ),
    "required_inputs": [
        "actual_commitment",
        "actual_qualification",
        "reconstruction_commitment",
        "reconstruction_qualification",
    ],
    "state_fields": [
        "reconstructed_commitment",
        "reconstructed_qualification",
        "critique_target",
        "distortion",
    ],
    "metric_name": "reconstruction_distortion",
    "metric_units": "mean absolute difference in two normalized position coordinates (0–1)",
    "assumptions": [
        "Commitment is a normalized magnitude on a stated policy axis; qualification is the normalized degree of stated caveat/qualification.",
        "A caricature reconstruction is eligible only when it increases commitment or removes qualification; this is a deliberately narrow operational reading of the supplied definition.",
        "The strength parameter linearly controls how far the constructed critique target moves toward the supplied caricature; it is not prevalence or calibrated confidence.",
        "At strength zero, the reference policy criticizes the represented actual position without changing it.",
    ],
    "limitations": [
        "Structured inputs stand in for authored positions; the mechanism does not parse text or decide whether evidence supports an interpretation.",
        "It omits other ways a position may be weakened or misrepresented, including selective omission, attribution errors, and context-dependent meaning.",
        "A deliberate caricature, shorthand, honest misunderstanding, or fair criticism cannot be distinguished from these coordinates alone.",
        "The process and coefficients are hypothetical and have not been empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(context, field):
    if field not in context:
        raise ValueError(f"missing required input: {field}")
    value = context[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return a per-step constructed critique target and its distortion from the claim."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("context['state'] must be a dict")

    actual_commitment = _unit_interval(context, "actual_commitment")
    actual_qualification = _unit_interval(context, "actual_qualification")
    caricature_commitment = _unit_interval(context, "reconstruction_commitment")
    caricature_qualification = _unit_interval(context, "reconstruction_qualification")

    # Necessary condition: the proposed construction is more absolute or less qualified.
    eligible = (
        caricature_commitment > actual_commitment
        or caricature_qualification < actual_qualification
    )
    if eligible:
        target_commitment = actual_commitment + strength * (
            caricature_commitment - actual_commitment
        )
        target_qualification = actual_qualification + strength * (
            caricature_qualification - actual_qualification
        )
    else:
        # The supplied alternative is not a caricature under this operational boundary.
        target_commitment = actual_commitment
        target_qualification = actual_qualification

    distortion = (
        abs(target_commitment - actual_commitment)
        + abs(target_qualification - actual_qualification)
    ) / 2.0
    next_state = deepcopy(context["state"])
    next_state.update(
        {
            "reconstructed_commitment": target_commitment,
            "reconstructed_qualification": target_qualification,
            "critique_target": {
                "commitment": target_commitment,
                "qualification": target_qualification,
            },
            "distortion": distortion,
        }
    )
    active = bool(strength > 0.0 and eligible and distortion > 0.0)
    trace = [
        "Eligibility: reconstruction_commitment > actual_commitment OR "
        "reconstruction_qualification < actual_qualification; "
        f"actual=({actual_commitment:.6g}, {actual_qualification:.6g}), "
        f"proposed=({caricature_commitment:.6g}, {caricature_qualification:.6g}), "
        f"eligible={eligible}.",
        "When eligible, target = actual + strength*(proposed - actual) in both "
        "coordinates; otherwise target equals actual. Primary metric is "
        f"(|target commitment - actual commitment| + |target qualification - "
        f"actual qualification|)/2 = {distortion:.6g}; active={active}.",
    ]
    return {"metric": distortion, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "actual_commitment": 0.4,
                    "actual_qualification": 0.8,
                    "reconstruction_commitment": 0.9,
                    "reconstruction_qualification": 0.1,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "actual_commitment": 0.4,
                    "actual_qualification": 0.8,
                    "reconstruction_commitment": 0.4,
                    "reconstruction_qualification": 0.8,
                }
            ],
            "expectation": "equal",
        },
    ]
