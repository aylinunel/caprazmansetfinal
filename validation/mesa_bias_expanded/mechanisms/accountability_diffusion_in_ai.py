"""Illustrative ownership-routing model for accountability diffusion in AI.

This is a synthetic process model, not an empirical account or detector.
"""
from __future__ import annotations

import math
from copy import deepcopy
from numbers import Real


METADATA = {
    "id": "accountability_diffusion_in_ai",
    "name": "Accountability diffusion in AI",
    "kind": "cognitive_bias",
    "description": (
        "A required remediation task starts with a role-based lead; explicit "
        "disclaimers can route ownership onward as a strength-controlled cascade."
    ),
    "required_inputs": ["action_required", "stakeholders"],
    "state_fields": ["task_count", "unresolved_count", "owner_history", "last_owner"],
    "metric_name": "unowned_required_action",
    "metric_units": "Binary task-level indicator: 1 if no stakeholder owns the required action, else 0.",
    "assumptions": [
        "Stakeholder role_fit is a supplied hypothetical priority score, not measured responsibility.",
        "Stakeholder decisions and referral targets are explicit structured evidence, not inferred from text.",
        "At most one supplied uniform draw gates a whole task's disclaimer cascade.",
        "Strength is an illustrative cascade setting, not prevalence, confidence, or an effect size.",
    ],
    "limitations": [
        "The model abstracts complex institutional, legal, and organizational accountability to one action and one routing chain.",
        "The role-based reference can assign a lead who explicitly disclaims; it is a comparison policy, not a claim of ideal practice.",
        "The mechanism is hypothetical and has not been empirically validated; it is not an NLP detector.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value: object, label: str, low: float, high: float, *, high_open: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < low or (result >= high if high_open else result > high):
        bracket = f"[{low}, {high})" if high_open else f"[{low}, {high}]"
        raise ValueError(f"{label} must be in {bracket}")
    return result


def _validate_context(context: dict) -> tuple[list[dict], float, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for key in ("action_required", "stakeholders", "state", "peer_states", "round_index", "agent_index", "uniform"):
        if key not in context:
            raise ValueError(f"missing required context field: {key}")
    if context["action_required"] is not True:
        raise ValueError("action_required must be true; a required task is needed to measure ownership")
    stakeholders = context["stakeholders"]
    if not isinstance(stakeholders, list) or not stakeholders:
        raise ValueError("stakeholders must be a non-empty list of explicit evidence")
    if not isinstance(context["state"], dict):
        raise ValueError("state must be a dict")
    if not isinstance(context["peer_states"], list):
        raise ValueError("peer_states must be a list")
    for key in ("round_index", "agent_index"):
        value = context[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    uniform = _number(context["uniform"], "uniform", 0.0, 1.0, high_open=True)

    normalized = []
    seen = set()
    for i, person in enumerate(stakeholders):
        if not isinstance(person, dict):
            raise ValueError(f"stakeholders[{i}] must be a dict")
        for key in ("id", "role_fit", "decision"):
            if key not in person:
                raise ValueError(f"stakeholders[{i}] is missing {key}")
        person_id = person["id"]
        if not isinstance(person_id, str) or not person_id.strip() or person_id in seen:
            raise ValueError("stakeholder ids must be unique non-empty strings")
        seen.add(person_id)
        role_fit = _number(person["role_fit"], f"stakeholders[{i}].role_fit", 0.0, 1.0)
        if role_fit == 0:
            raise ValueError("each listed stakeholder must have positive role_fit evidence")
        decision = person["decision"]
        if decision not in ("accept", "disclaim"):
            raise ValueError(f"stakeholders[{i}].decision must be 'accept' or 'disclaim'")
        referral = person.get("refers_to")
        if decision == "disclaim":
            if "refers_to" not in person:
                raise ValueError(f"disclaiming stakeholder {person_id} must explicitly provide refers_to")
            if referral is not None and (not isinstance(referral, str) or not referral.strip()):
                raise ValueError(f"stakeholders[{i}].refers_to must be an id or null")
        elif referral is not None:
            raise ValueError(f"accepting stakeholder {person_id} cannot refer ownership onward")
        normalized.append({"id": person_id, "role_fit": role_fit, "decision": decision, "refers_to": referral})

    ids = {p["id"] for p in normalized}
    for person in normalized:
        if person["decision"] == "disclaim" and person["refers_to"] is not None and person["refers_to"] not in ids:
            raise ValueError(f"unknown referral target {person['refers_to']!r}")
    state = context["state"]
    if state:
        expected = set(METADATA["state_fields"])
        if set(state) != expected:
            raise ValueError("state must contain exactly the declared state fields")
        if isinstance(state["task_count"], bool) or not isinstance(state["task_count"], int) or state["task_count"] < 0:
            raise ValueError("state.task_count must be a non-negative integer")
        if isinstance(state["unresolved_count"], bool) or not isinstance(state["unresolved_count"], int) or not 0 <= state["unresolved_count"] <= state["task_count"]:
            raise ValueError("state.unresolved_count must be between zero and task_count")
        if not isinstance(state["owner_history"], list) or len(state["owner_history"]) != state["task_count"]:
            raise ValueError("state.owner_history must contain one entry per prior task")
        if any(x is not None and not isinstance(x, str) for x in state["owner_history"]):
            raise ValueError("state.owner_history entries must be stakeholder ids or null")
        if state["last_owner"] != (state["owner_history"][-1] if state["owner_history"] else None):
            raise ValueError("state.last_owner must match the last owner_history entry")
    return normalized, uniform, deepcopy(state)


def evaluate(context: dict, strength: float) -> dict:
    """Resolve a required action using role-based reference and explicit referrals."""
    s = _number(strength, "strength", 0.0, 1.0)
    people, uniform, prior = _validate_context(context)
    ranked = sorted(people, key=lambda p: (-p["role_fit"], p["id"]))
    reference_owner = ranked[0]["id"]
    owner = reference_owner
    traversed = []

    # A cascade needs distributed responsibility, an explicit disclaimer on the
    # lead's referral chain, and the supplied task-level draw to fall below s.
    # No disclaimer is never interpreted as diffusion.
    by_id = {p["id"]: p for p in people}
    lead = by_id[reference_owner]
    eligible_cascade = len(people) > 1 and lead["decision"] == "disclaim"
    cascade = eligible_cascade and uniform < s
    if cascade:
        current = reference_owner
        visited = set()
        owner = None
        while current is not None and current not in visited:
            visited.add(current)
            person = by_id[current]
            traversed.append(current)
            if person["decision"] == "accept":
                owner = current
                break
            current = person["refers_to"]
        # A cycle or a terminal explicit disclaimer leaves the task unowned.

    metric = 1.0 if owner is None else 0.0
    active = owner != reference_owner
    history = list(prior.get("owner_history", []))
    history.append(owner)
    unresolved = prior.get("unresolved_count", 0) + int(owner is None)
    next_state = {
        "task_count": prior.get("task_count", 0) + 1,
        "unresolved_count": unresolved,
        "owner_history": history,
        "last_owner": owner,
    }
    if cascade:
        decision_text = f"explicit referral chain {traversed!r} resolved owner={owner!r}"
    else:
        decision_text = f"role-based reference lead {reference_owner!r} retained"
    trace = [
        "Reference: assign the required action to argmax(role_fit), ties by stakeholder id; metric=1 iff no owner.",
        f"Diffusion gate: n={len(people)}; lead decision={lead['decision']!r}; uniform={uniform}; strength={s}; cascade={cascade}.",
        decision_text,
        f"Unowned required-action indicator={metric}; active={active} (owner differs from role-based reference).",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"task_count": 0, "unresolved_count": 0, "owner_history": [], "last_owner": None},
            "contexts": [{
                "action_required": True,
                "stakeholders": [
                    {"id": "model_team", "role_fit": 0.9, "decision": "disclaim", "refers_to": "deploy_team"},
                    {"id": "deploy_team", "role_fit": 0.7, "decision": "disclaim", "refers_to": None},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"task_count": 0, "unresolved_count": 0, "owner_history": [], "last_owner": None},
            "contexts": [{
                "action_required": True,
                "stakeholders": [
                    {"id": "model_team", "role_fit": 0.9, "decision": "accept"},
                    {"id": "deploy_team", "role_fit": 0.7, "decision": "accept"},
                ],
            }],
            "expectation": "equal",
        },
    ]
