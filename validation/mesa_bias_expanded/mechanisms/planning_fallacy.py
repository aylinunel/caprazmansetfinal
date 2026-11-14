"""Illustrative planning-fallacy process for hypothetical task-duration estimates."""
from __future__ import annotations

import math
from statistics import median


METADATA = {
    "id": "planning_fallacy",
    "name": "Planning Fallacy",
    "kind": "cognitive_bias",
    "description": (
        "Discounts demonstrated duration overruns on prior completed tasks of the "
        "same explicit class when producing a new duration forecast."
    ),
    "required_inputs": ["task_class", "planned_hours", "actual_hours"],
    "state_fields": ["history", "last_forecast_hours", "last_task_class"],
    "metric_name": "duration_underestimate",
    "metric_units": "hours by which the forecast is below the supplied realized duration (floored at zero)",
    "assumptions": [
        "The supplied task class defines an adequate comparison group.",
        "Completed prior tasks are available to this hypothetical planner.",
        "Strength controls the degree of discounting, not prevalence or calibrated confidence.",
        "Prior same-class median actual/planned duration ratio is a simple reference forecast.",
    ],
    "limitations": [
        "Synthetic structured inputs only; this is not a language detector, diagnosis, or population claim.",
        "Task classes may be too broad or narrow, and the median may not predict a new task.",
        "Realized duration is used only to score the forecast and update experience after the task.",
        "The illustrative coefficient and strength setting are not empirically calibrated.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _positive_finite(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite positive number")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a finite positive number")
    return float(value)


def _history(context):
    state = context.get("state")
    if not isinstance(state, dict):
        raise ValueError("state must be an object containing chronological history")
    history = state.get("history")
    if not isinstance(history, list):
        raise ValueError("state.history must be a list")
    clean = []
    for item in history:
        if not isinstance(item, dict) or not isinstance(item.get("task_class"), str) or not item["task_class"].strip():
            raise ValueError("each history item requires a nonempty task_class")
        planned = _positive_finite(item.get("planned_hours"), "history planned_hours")
        actual = _positive_finite(item.get("actual_hours"), "history actual_hours")
        clean.append({"task_class": item["task_class"], "planned_hours": planned, "actual_hours": actual})
    return clean


def evaluate(context: dict, strength: float) -> dict:
    """Forecast from explicit task inputs without mutating context or its state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    task_class = context.get("task_class")
    if not isinstance(task_class, str) or not task_class.strip():
        raise ValueError("task_class must be a nonempty string")
    planned = _positive_finite(context.get("planned_hours"), "planned_hours")
    actual = _positive_finite(context.get("actual_hours"), "actual_hours")
    history = _history(context)

    comparable = [h for h in history if h["task_class"] == task_class]
    ratios = [h["actual_hours"] / h["planned_hours"] for h in comparable]
    historical_ratio = median(ratios) if ratios else 1.0
    # Require sustained comparable underestimation evidence; a short plan alone
    # or unrelated overrun is insufficient under the annotation boundary.
    active = bool(ratios) and historical_ratio > 1.0
    if active:
        # Strength attenuates the outside-view correction: 0 uses the reference
        # ratio fully, while 1 retains only the current inside-view plan.
        forecast = planned * (1.0 + (1.0 - float(strength)) * (historical_ratio - 1.0))
    else:
        forecast = planned
    underestimation = max(0.0, actual - forecast)

    next_history = history + [{"task_class": task_class, "planned_hours": planned, "actual_hours": actual}]
    return {
        "metric": underestimation,
        "active": active,
        "state": {
            "history": next_history,
            "last_forecast_hours": forecast,
            "last_task_class": task_class,
        },
        "trace": [
            f"Matched {len(comparable)} prior same-class task(s); median actual/planned ratio={historical_ratio:.6g}.",
            f"Active only when comparable median ratio > 1; forecast={planned:g} * (1 + (1 - {float(strength):g}) * ({historical_ratio:.6g} - 1)) when active, otherwise the plan; undershoot=max(0, {actual:g} - {forecast:.6g}) hours.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"history": []},
            "contexts": [
                {"task_class": "small-software-change", "planned_hours": 8, "actual_hours": 12},
                {"task_class": "small-software-change", "planned_hours": 20, "actual_hours": 30},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"history": []},
            "contexts": [
                {"task_class": "routine-maintenance", "planned_hours": 8, "actual_hours": 12},
                {"task_class": "small-software-change", "planned_hours": 20, "actual_hours": 30},
            ],
            "expectation": "equal",
        },
    ]
