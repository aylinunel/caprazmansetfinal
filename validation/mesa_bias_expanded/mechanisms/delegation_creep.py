"""Illustrative temporal process model for delegation creep; not a detector."""

from copy import deepcopy
import math


METADATA = {
    "id": "delegation_creep",
    "name": "Delegation Creep",
    "kind": "cognitive_bias",
    "description": (
        "Models reliance momentum allocating a growing share of a new-domain or "
        "consequential task without a task-specific suitability review."
    ),
    "required_inputs": [
        "task_domain",
        "consequence",
        "suitability_reviewed",
        "suitability_approved",
    ],
    "state_fields": [
        "seen_domains",
        "approved_delegations",
        "total_opportunities",
        "delegated_work",
        "unreviewed_expansion_work",
    ],
    "metric_name": "cumulative delegated task-equivalents",
    "metric_units": "fractional task-equivalents across this agent's sequence",
    "assumptions": [
        "The scope is novel if its domain has not previously received an AI delegation.",
        "Consequence >= 0.5 is an illustrative threshold for consequential work.",
        "Reliance momentum is the share of prior opportunities that were reviewed and approved for delegation.",
        "At nonzero strength, an unreviewed expansion receives a fractional allocation equal to strength times prior reliance momentum.",
        "A reference policy delegates only tasks with an affirmative suitability review; strength controls deviation from that rule.",
    ],
    "limitations": [
        "This is a synthetic process assumption, not a validated psychological mechanism or empirical effect estimate.",
        "Task domains and consequence are supplied structured facts; this is not an NLP detector.",
        "The model cannot establish actual suitability, harm, or a person's motive from delegation behavior.",
        "Fractional task allocation is an illustrative workload abstraction; strength is not prevalence or calibrated confidence.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_CONSEQUENTIAL_THRESHOLD = 0.5
_STATE_DEFAULTS = {
    "seen_domains": [],
    "approved_delegations": 0,
    "total_opportunities": 0,
    "delegated_work": 0.0,
    "unreviewed_expansion_work": 0.0,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validated_state(context):
    raw = context.get("state", {})
    if not isinstance(raw, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(_STATE_DEFAULTS)
    state.update(deepcopy(raw))

    domains = state["seen_domains"]
    if not isinstance(domains, list) or any(not isinstance(x, str) or not x for x in domains):
        raise ValueError("state.seen_domains must be a list of nonempty strings")
    if len(domains) != len(set(domains)):
        raise ValueError("state.seen_domains cannot contain duplicates")
    for key in ("approved_delegations", "total_opportunities"):
        value = state[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{key} must be a nonnegative integer")
    if state["approved_delegations"] > state["total_opportunities"]:
        raise ValueError("approved_delegations cannot exceed total_opportunities")
    for key in ("delegated_work", "unreviewed_expansion_work"):
        value = _finite_number(state[key], f"state.{key}")
        if value < 0:
            raise ValueError(f"state.{key} must be nonnegative")
        state[key] = value
    if state["delegated_work"] > state["total_opportunities"]:
        raise ValueError("delegated_work cannot exceed total_opportunities")
    if state["unreviewed_expansion_work"] > state["delegated_work"]:
        raise ValueError("unreviewed_expansion_work cannot exceed delegated_work")
    return state


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological task opportunity without mutating its context."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")
    domain = context["task_domain"]
    if not isinstance(domain, str) or not domain.strip():
        raise ValueError("task_domain must be a nonempty string")
    consequence = _finite_number(context["consequence"], "consequence")
    if not 0.0 <= consequence <= 1.0:
        raise ValueError("consequence must be in [0, 1]")
    reviewed = context["suitability_reviewed"]
    approved = context["suitability_approved"]
    if not isinstance(reviewed, bool):
        raise ValueError("suitability_reviewed must be bool")
    if reviewed and not isinstance(approved, bool):
        raise ValueError("suitability_approved must be bool when a review occurred")
    if not reviewed and approved is not None:
        raise ValueError("suitability_approved must be None when no review occurred")

    state = _validated_state(context)
    is_new_domain = domain not in state["seen_domains"]
    is_expansion = is_new_domain or consequence >= _CONSEQUENTIAL_THRESHOLD
    # The explicit reference policy is always review-gated, independent of strength.
    reference_fraction = 1.0 if reviewed and approved else 0.0
    prior_momentum = (
        state["approved_delegations"] / state["total_opportunities"]
        if state["total_opportunities"]
        else 0.0
    )
    if reference_fraction:
        delegated_fraction = 1.0
        approved_increment = 1
        unreviewed_expansion_increment = 0.0
    elif not reviewed and is_expansion:
        delegated_fraction = strength * prior_momentum
        approved_increment = 0
        unreviewed_expansion_increment = delegated_fraction
    else:
        delegated_fraction = 0.0
        approved_increment = 0
        unreviewed_expansion_increment = 0.0

    # Retain only actually delegated domains: an unreviewed partial allocation is
    # the modeled scope expansion, while a rejected/nondelegated task is not.
    if delegated_fraction > 0.0 and domain not in state["seen_domains"]:
        state["seen_domains"].append(domain)
    state["approved_delegations"] += approved_increment
    state["total_opportunities"] += 1
    state["delegated_work"] += delegated_fraction
    state["unreviewed_expansion_work"] += unreviewed_expansion_increment

    trace = [
        f"new_domain={is_new_domain}; consequential={consequence >= _CONSEQUENTIAL_THRESHOLD} "
        f"(consequence={consequence:.6g}, threshold={_CONSEQUENTIAL_THRESHOLD}); "
        f"unreviewed_expansion={not reviewed and is_expansion}.",
        f"reference_fraction={reference_fraction:.6g}; prior_approved_share="
        f"{prior_momentum:.6g}; chosen_delegated_fraction={delegated_fraction:.6g} "
        f"(strength × prior_approved_share for unreviewed expansion, else review-gated reference).",
    ]
    return {
        "metric": float(state["delegated_work"]),
        "active": delegated_fraction != reference_fraction,
        "state": state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"task_domain": "scheduling", "consequence": 0.2, "suitability_reviewed": True, "suitability_approved": True},
                {"task_domain": "scheduling", "consequence": 0.2, "suitability_reviewed": True, "suitability_approved": True},
                {"task_domain": "case_triage", "consequence": 0.9, "suitability_reviewed": False, "suitability_approved": None},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"seen_domains": ["scheduling"], "approved_delegations": 1, "total_opportunities": 1, "delegated_work": 1.0, "unreviewed_expansion_work": 0.0},
            "contexts": [
                {"task_domain": "scheduling", "consequence": 0.2, "suitability_reviewed": True, "suitability_approved": True},
            ],
            "expectation": "equal",
        },
    ]
