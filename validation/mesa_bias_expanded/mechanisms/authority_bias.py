"""Illustrative structured process model for authority-based claim acceptance.

This is a hypothetical mechanism, not a detector or empirically fitted model.
"""
from copy import deepcopy
import math

METADATA = {
    "id": "authority_bias",
    "name": "Authority Bias",
    "kind": "cognitive_bias",
    "description": (
        "Models acceptance of a claim when an authority-status cue substitutes "
        "for adequate evidence, only when the supplied expertise is not relevant."
    ),
    "required_inputs": [
        "claim_id", "direct_evidence", "expertise_relevance", "expert_testimony",
        "authority_status", "acceptance_threshold", "authority_sufficiency_threshold",
    ],
    "state_fields": ["steps", "reviewed_claim_ids", "accepted_claim_ids"],
    "metric_name": "claim_accepted",
    "metric_units": "binary indicator (1 accepted, 0 not accepted) for this claim review",
    "assumptions": [
        "All evidence, status, and relevance values are explicitly supplied structured facts.",
        "The reference rule accepts when direct evidence reaches threshold or a relevant expert's supplied testimony does.",
        "When relevance is false, authority status can independently satisfy the specified sufficiency cutoff; strength scales that cue.",
        "The strength and sufficiency cutoff are illustrative scenario settings, not empirical effect sizes.",
    ],
    "limitations": [
        "Does not inspect language, identify real authorities, or infer expertise/relevance or motives.",
        "A binary acceptance task omits uncertainty, source quality, and many rational uses of testimony.",
        "No human validation, detection accuracy, or empirical calibration is claimed.",
        "Relevant expert testimony can legitimately support acceptance and is not labeled bias here.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value, name, low=0.0, high=1.0, *, above_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    value = float(value)
    if not math.isfinite(value) or value < low or value > high or (above_zero and value <= 0):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return value


def _prior_state(value):
    if not isinstance(value, dict):
        raise ValueError("state must be a dictionary")
    steps = value.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    for field in ("reviewed_claim_ids", "accepted_claim_ids"):
        entries = value.get(field, [])
        if not isinstance(entries, list) or any(not isinstance(item, str) for item in entries):
            raise ValueError(f"state.{field} must be a list of strings")
    return deepcopy(value), steps, list(value.get("reviewed_claim_ids", [])), list(value.get("accepted_claim_ids", []))


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one claim-review step; input context and prior state are not mutated."""
    strength = _number(strength, "strength")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    fields = (
        "claim_id", "direct_evidence", "expertise_relevance", "expert_testimony",
        "authority_status", "acceptance_threshold", "authority_sufficiency_threshold",
    )
    missing = [field for field in fields if field not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")
    claim_id = context["claim_id"]
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError("claim_id must be a non-empty string")
    evidence = _number(context["direct_evidence"], "direct_evidence")
    testimony = _number(context["expert_testimony"], "expert_testimony")
    status = _number(context["authority_status"], "authority_status")
    threshold = _number(context["acceptance_threshold"], "acceptance_threshold")
    cutoff = _number(
        context["authority_sufficiency_threshold"],
        "authority_sufficiency_threshold", above_zero=True,
    )
    relevance = context["expertise_relevance"]
    if not isinstance(relevance, bool):
        raise ValueError("expertise_relevance must be a boolean")

    prior, steps, reviewed, accepted = _prior_state(context.get("state", {}))

    # Explicit reference policy: either direct evidence or relevant expert testimony
    # meeting the threshold is sufficient; irrelevant testimony contributes nothing.
    reference_accepts = evidence >= threshold or (relevance and testimony >= threshold)
    # Necessary condition from the concept boundary: status may substitute only when
    # expertise is explicitly irrelevant. Strength scales the supplied status cue.
    authority_route = (
        not relevance
        and strength > 0.0
        and strength * status >= cutoff
    )
    accepts = reference_accepts or authority_route
    metric = 1.0 if accepts else 0.0
    active = accepts != reference_accepts

    next_state = prior
    next_state.update({
        "steps": steps + 1,
        "reviewed_claim_ids": [*reviewed, claim_id],
        "accepted_claim_ids": [*accepted, claim_id] if accepts else accepted,
    })
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            "Reference: accept iff direct_evidence >= acceptance_threshold, or "
            "expertise_relevance is true and expert_testimony >= acceptance_threshold.",
            f"Status route: not expertise_relevance and strength({strength:g}) * "
            f"authority_status({status:g}) >= authority_sufficiency_threshold({cutoff:g}); "
            f"route={authority_route}.",
            f"Claim {claim_id!r}: reference_accepts={reference_accepts}; "
            f"accepted={accepts}; metric=claim_accepted={metric:g}; active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"steps": 0, "reviewed_claim_ids": [], "accepted_claim_ids": []},
            "contexts": [{
                "claim_id": "weak-evidence-high-status",
                "direct_evidence": 0.25,
                "expertise_relevance": False,
                "expert_testimony": 0.95,
                "authority_status": 0.95,
                "acceptance_threshold": 0.70,
                "authority_sufficiency_threshold": 0.65,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"steps": 0, "reviewed_claim_ids": [], "accepted_claim_ids": []},
            "contexts": [{
                "claim_id": "relevant-expert-testimony",
                "direct_evidence": 0.25,
                "expertise_relevance": True,
                "expert_testimony": 0.80,
                "authority_status": 0.95,
                "acceptance_threshold": 0.70,
                "authority_sufficiency_threshold": 0.65,
            }],
            "expectation": "equal",
        },
    ]
