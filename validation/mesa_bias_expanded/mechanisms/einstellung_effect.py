"""Illustrative task-specific model of learned-procedure fixation.

This is a synthetic process model, not a detector or empirically fitted account.
"""
from __future__ import annotations

import copy
import math
from typing import Any


METADATA = {
    "id": "einstellung_effect",
    "name": "Einstellung Effect",
    "kind": "cognitive_bias",
    "description": (
        "Repeated successful use of a learned procedure consumes modeled search "
        "capacity, potentially preventing retrieval of a lower-action alternative "
        "for a matching task family."
    ),
    "required_inputs": [
        "task_family",
        "learned_solution_id",
        "solutions",
        "search_budget",
    ],
    "state_fields": [
        "learned_successes_by_key",
        "last_choice_id",
        "last_action_count",
        "last_effective_search_budget",
    ],
    "metric_name": "selected_solution_action_count",
    "metric_units": "number of actions in the selected supplied solution",
    "assumptions": [
        "Each supplied solution is valid and completes the same task; action_count is a comparable task cost.",
        "A completed use of the designated learned solution in a task family adds one unit of learned activation for later rounds.",
        "Search effort and budget are task-specific supplied quantities; remaining alternative-search capacity is search_budget / (1 + strength * prior successful uses).",
        "The learned procedure is directly retrievable once learned, while alternatives must fit within remaining search capacity.",
        "Strength and coefficients are illustrative settings, not estimates of human effects.",
    ],
    "limitations": [
        "This is an abstract structured choice simulation, not a model of human cognition or an NLP detector.",
        "It assumes the supplied action counts, retrieval costs, task-family labels, and history are accurate and comparable.",
        "It omits partial discovery, noisy retrieval, insight, feedback, and strategic or beneficial reasons to reuse a familiar procedure.",
        "It is explicitly hypothetical and has not been empirically validated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: Any, name: str, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number >= {minimum}")
    result = float(value)
    if not math.isfinite(result) or result < minimum:
        raise ValueError(f"{name} must be a finite number >= {minimum}")
    return result


def _validated(context: dict, strength: float) -> tuple[str, str, list[dict], float, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    family = context.get("task_family")
    learned_id = context.get("learned_solution_id")
    if not isinstance(family, str) or not family.strip():
        raise ValueError("task_family must be a non-empty string")
    if not isinstance(learned_id, str) or not learned_id.strip():
        raise ValueError("learned_solution_id must be a non-empty string")
    budget = _finite_number(context.get("search_budget"), "search_budget")
    raw_solutions = context.get("solutions")
    if not isinstance(raw_solutions, list) or not raw_solutions:
        raise ValueError("solutions must be a non-empty list")

    solutions: list[dict] = []
    ids: set[str] = set()
    for index, solution in enumerate(raw_solutions):
        if not isinstance(solution, dict):
            raise ValueError(f"solutions[{index}] must be a dict")
        solution_id = solution.get("id")
        if not isinstance(solution_id, str) or not solution_id.strip():
            raise ValueError(f"solutions[{index}].id must be a non-empty string")
        if solution_id in ids:
            raise ValueError("solution ids must be unique within a task")
        ids.add(solution_id)
        actions = solution.get("action_count")
        if isinstance(actions, bool) or not isinstance(actions, int) or actions <= 0:
            raise ValueError(f"solutions[{index}].action_count must be a positive integer")
        retrieval = _finite_number(solution.get("retrieval_cost"), f"solutions[{index}].retrieval_cost")
        solutions.append({"id": solution_id, "action_count": actions, "retrieval_cost": retrieval})
    if learned_id not in ids:
        raise ValueError("learned_solution_id must identify a supplied solution")

    raw_state = context.get("state", {})
    if not isinstance(raw_state, dict):
        raise ValueError("state must be a dict")
    state = copy.deepcopy(raw_state)
    histories = state.get("learned_successes_by_key", {})
    if not isinstance(histories, dict):
        raise ValueError("state.learned_successes_by_key must be a dict")
    for key, count in histories.items():
        if not isinstance(key, str) or isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("learned-success history must map strings to non-negative integers")
    state["learned_successes_by_key"] = copy.deepcopy(histories)
    return family, learned_id, solutions, budget, state


def evaluate(context: dict, strength: float) -> dict:
    family, learned_id, solutions, budget, state = _validated(context, strength)
    strength = float(strength)
    history = state["learned_successes_by_key"]
    key = f"{family}\u241f{learned_id}"
    prior_uses = history.get(key, 0)
    learned = next(option for option in solutions if option["id"] == learned_id)

    # Reference rule: retrieve every supplied solution within the full task search
    # budget, then choose the one requiring the fewest actions (stable ID tie-break).
    reference_options = [option for option in solutions if option["retrieval_cost"] <= budget]
    if learned not in reference_options:
        raise ValueError("the learned solution must be retrievable within the full search_budget")
    reference_choice = min(reference_options, key=lambda option: (option["action_count"], option["id"]))

    # The learned routine is primed/retrievable. Prior successful repetition
    # consumes capacity for searching alternatives in this same task family.
    effective_budget = budget / (1.0 + strength * prior_uses)
    eligible = [learned] + [
        option for option in solutions
        if option["id"] != learned_id and option["retrieval_cost"] <= effective_budget
    ]
    choice = min(eligible, key=lambda option: (option["action_count"], option["id"]))

    # Update history only after the current choice; thus only prior rounds cause
    # fixation in the current round. Supplied options are assumed valid completions.
    if choice["id"] == learned_id:
        history[key] = prior_uses + 1
    state["last_choice_id"] = choice["id"]
    state["last_action_count"] = choice["action_count"]
    state["last_effective_search_budget"] = effective_budget
    return {
        "metric": float(choice["action_count"]),
        "active": choice["id"] != reference_choice["id"],
        "state": state,
        "trace": [
            f"Prior successful uses for matching family/rule={prior_uses}; remaining alternative-search budget = "
            f"{budget:g} / (1 + {strength:g} * {prior_uses}) = {effective_budget:g}.",
            f"Reference chooses minimum action_count among solutions with retrieval_cost <= full budget ({budget:g}): "
            f"{reference_choice['id']} ({reference_choice['action_count']} actions).",
            f"Mechanism retains the learned solution as retrievable and admits alternatives with retrieval_cost <= "
            f"{effective_budget:g}; selected {choice['id']} ({choice['action_count']} actions).",
        ],
    }


def scenarios() -> list[dict]:
    practice = {
        "task_family": "measure-vessel",
        "learned_solution_id": "learned-sequence",
        "search_budget": 5,
        "solutions": [
            {"id": "learned-sequence", "action_count": 8, "retrieval_cost": 1},
        ],
    }
    target = {
        "task_family": "measure-vessel",
        "learned_solution_id": "learned-sequence",
        "search_budget": 5,
        "solutions": [
            {"id": "learned-sequence", "action_count": 8, "retrieval_cost": 1},
            {"id": "short-alternative", "action_count": 2, "retrieval_cost": 4},
        ],
    }
    boundary = {
        **target,
        # A practiced procedure in a different task family is not evidence of
        # fixation on this task's learned solution.
        "task_family": "different-task-family",
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [dict(practice), dict(practice), dict(target)],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [dict(practice), dict(practice), dict(boundary)],
            "expectation": "equal",
        },
    ]
