"""Illustrative comparison-budget process for choice overload.

This is a transparent synthetic task model, not a detector or a fitted theory.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "choice_overload_bias",
    "name": "Choice Overload",
    "kind": "cognitive_bias",
    "description": (
        "A bounded sequential comparison process can stop before later options "
        "are evaluated when their explicitly supplied comparison effort exceeds "
        "the available budget; this may reduce selected utility."
    ),
    "required_inputs": ["options", "comparison_budget"],
    "state_fields": ["last_choice", "last_metric", "last_examined_ids", "step_count"],
    "metric_name": "utility_regret",
    "metric_units": "Utility points lost versus the best supplied option (0–1 scale).",
    "assumptions": [
        "Options are scanned in the supplied order, starting with the first option as incumbent.",
        "Each later option has an explicit incremental comparison_difficulty cost.",
        "At strength zero, the reference policy examines all options and selects maximum utility.",
        "Strength linearly interpolates between exhaustive comparison and the supplied effort budget.",
        "Utilities, ordering, and effort costs are synthetic task inputs, not inferred psychology.",
    ],
    "limitations": [
        "The sequential scan and interpolation are illustrative assumptions, not an empirically validated model.",
        "The module does not infer choice difficulty or satisfaction from text and does not model population prevalence.",
        "An observed regret outcome is not evidence that a real person experienced overload.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _validate(context: dict, strength: float) -> tuple[list[dict], float, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength_value = float(strength)
    if not math.isfinite(strength_value) or not 0.0 <= strength_value <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    if "options" not in context or "comparison_budget" not in context:
        raise ValueError("options and comparison_budget are required; missing evidence is not zero")
    raw_options = context["options"]
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError("options must be a list containing at least two options")
    options: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_options):
        if not isinstance(raw, dict):
            raise ValueError(f"options[{index}] must be a dictionary")
        if not {"id", "utility", "comparison_difficulty"}.issubset(raw):
            raise ValueError(f"options[{index}] requires id, utility, and comparison_difficulty")
        option_id = raw["id"]
        if not isinstance(option_id, str) or not option_id:
            raise ValueError(f"options[{index}].id must be a nonempty string")
        if option_id in seen_ids:
            raise ValueError("option ids must be unique")
        seen_ids.add(option_id)
        utility = _finite_number(raw["utility"], f"options[{index}].utility")
        difficulty = _finite_number(raw["comparison_difficulty"], f"options[{index}].comparison_difficulty")
        if not 0.0 <= utility <= 1.0:
            raise ValueError(f"options[{index}].utility must be within [0, 1]")
        if difficulty < 0.0:
            raise ValueError(f"options[{index}].comparison_difficulty must be nonnegative")
        options.append({"id": option_id, "utility": utility, "comparison_difficulty": difficulty})

    budget = _finite_number(context["comparison_budget"], "comparison_budget")
    if budget <= 0.0:
        raise ValueError("comparison_budget must be positive")
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    old_steps = state.get("step_count", 0)
    if isinstance(old_steps, bool) or not isinstance(old_steps, int) or old_steps < 0:
        raise ValueError("state.step_count must be a nonnegative integer")
    return options, budget, dict(state)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one choice task without mutating context or its nested values."""
    options, budget, old_state = _validate(context, strength)
    s = float(strength)
    best = max(options, key=lambda option: option["utility"])
    total_effort = sum(option["comparison_difficulty"] for option in options[1:])

    # At s=0 this allowance equals all required effort: the explicit exhaustive
    # reference rule. At s=1 it equals the task's supplied comparison budget.
    allowance = (1.0 - s) * total_effort + s * budget
    examined = [options[0]]
    spent = 0.0
    for candidate in options[1:]:
        cost = candidate["comparison_difficulty"]
        if spent + cost > allowance:
            break
        spent += cost
        examined.append(candidate)

    # Sequential incumbent selection is the actual task process; stable ties
    # retain the earlier candidate, as they do in the exhaustive reference.
    chosen = examined[0]
    for option in examined[1:]:
        if option["utility"] > chosen["utility"]:
            chosen = option
    regret = max(0.0, best["utility"] - chosen["utility"])
    next_state = dict(old_state)
    next_state.update({
        "last_choice": chosen["id"],
        "last_metric": regret,
        "last_examined_ids": [option["id"] for option in examined],
        "step_count": old_state.get("step_count", 0) + 1,
    })
    active = chosen["id"] != best["id"]
    return {
        "metric": float(regret),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"Scanned options in supplied order; incremental comparison costs={ [o['comparison_difficulty'] for o in options[1:]] }, "
            f"total effort={total_effort:g}, supplied budget={budget:g}, strength={s:g}, allowance={allowance:g}; "
            f"examined={[o['id'] for o in examined]}, selected={chosen['id']} (utility {chosen['utility']:g}), "
            f"best full-set option={best['id']} (utility {best['utility']:g}), regret={regret:g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
        "name": "positive",
        "initial_state": {},
        "contexts": [{
            "options": [
                {"id": "basic", "utility": 0.20, "comparison_difficulty": 0.0},
                {"id": "standard", "utility": 0.70, "comparison_difficulty": 0.5},
                {"id": "premium", "utility": 0.95, "comparison_difficulty": 1.0},
            ],
            "comparison_budget": 0.5,
        }],
        "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "options": [
                    {"id": "a", "utility": 0.25, "comparison_difficulty": 0.0},
                    {"id": "b", "utility": 0.60, "comparison_difficulty": 0.0},
                    {"id": "c", "utility": 0.90, "comparison_difficulty": 0.0},
                ],
                "comparison_budget": 0.5,
            }],
            "expectation": "equal",
        },
    ]
