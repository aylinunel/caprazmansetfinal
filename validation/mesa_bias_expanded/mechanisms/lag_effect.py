"""Illustrative spaced-practice lag effect process; not an empirical estimator."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping

METADATA = {
    "id": "lag_effect",
    "name": "Lag Effect",
    "kind": "learning_effect",
    "description": (
        "A suitable positive interval between study sessions increases the modeled "
        "encoding gain of the later session relative to a fixed-gain reference."
    ),
    # These task fields occur in every context. `state` is injected by the runner;
    # action-specific evidence (a prior study for tests) is checked in evaluate.
    "required_inputs": ["action", "day", "retention_horizon_days"],
    "state_fields": ["memory_strength", "last_study_day", "study_count"],
    "metric_name": "retention_score",
    "metric_units": "unitless modeled recall-strength score in [0, 1]",
    "assumptions": [
        "The strength-zero reference gives every study a fixed encoding gain of 0.20.",
        "Stored strength decays exponentially with the supplied retention horizon.",
        "A subsequent study after a positive interval no longer than the horizon gets gain 0.20*(1 + strength*2*interval/horizon).",
        "Practice saturates remaining headroom exponentially; a test reports decayed stored strength without sampling an outcome.",
        "All coefficients and equations are illustrative assumptions, not estimated effect sizes.",
    ],
    "limitations": [
        "The deterministic toy process omits item difficulty, retrieval success, encoding variability, interference, and individual differences.",
        "A single supplied horizon is treated as the applicable time constant; useful schedules depend on the later retention horizon and can exceed this toy boundary.",
        "This is not empirical validation, an individual learner prediction, a diagnosis, or a natural-language detector.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_BASE_GAIN = 0.20
_LAG_SENSITIVITY = 2.0
_STATE_FIELDS = ("memory_strength", "last_study_day", "study_count")


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _load_state(raw_state: object) -> dict:
    if not isinstance(raw_state, Mapping):
        raise ValueError("state must be a mapping (use {} for a new sequence)")
    if not raw_state:
        return {"memory_strength": 0.0, "last_study_day": None, "study_count": 0}
    missing = [field for field in _STATE_FIELDS if field not in raw_state]
    if missing:
        raise ValueError(f"state is incomplete; missing {', '.join(missing)}")

    memory = _finite_number(raw_state["memory_strength"], "state.memory_strength")
    if not 0.0 <= memory <= 1.0:
        raise ValueError("state.memory_strength must be within [0, 1]")
    count = raw_state["study_count"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.study_count must be a non-negative integer")
    last_day = raw_state["last_study_day"]
    if count == 0:
        if last_day is not None or memory != 0.0:
            raise ValueError("an unstudied state must have zero memory and no last study day")
    else:
        last_day = _finite_number(last_day, "state.last_study_day")
    return {"memory_strength": memory, "last_study_day": last_day, "study_count": count}


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate a chronological study/test event without mutating its inputs."""
    intensity = _finite_number(strength, "strength")
    if not 0.0 <= intensity <= 1.0:
        raise ValueError("strength must be within [0, 1]")
    if not isinstance(context, Mapping):
        raise ValueError("context must be a mapping")
    required = ("action", "day", "retention_horizon_days", "state")
    missing = [field for field in required if field not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    action = context["action"]
    if not isinstance(action, str) or action not in ("study", "test"):
        raise ValueError("action must be 'study' or 'test'")
    day = _finite_number(context["day"], "day")
    horizon = _finite_number(context["retention_horizon_days"], "retention_horizon_days")
    if day < 0.0:
        raise ValueError("day must be non-negative")
    if horizon <= 0.0:
        raise ValueError("retention_horizon_days must be positive")

    state = _load_state(context["state"])
    memory, count, last_day = state["memory_strength"], state["study_count"], state["last_study_day"]
    if count and day < last_day:
        raise ValueError("event day cannot precede the most recent study")

    trace: list[str] = []
    active = False
    if action == "study":
        gap = None if count == 0 else day - last_day
        decayed = memory if gap is None else memory * math.exp(-gap / horizon)
        suitable_lag = gap is not None and 0.0 < gap <= horizon
        gain = _BASE_GAIN
        if suitable_lag:
            ratio = gap / horizon
            gain *= 1.0 + intensity * _LAG_SENSITIVITY * ratio
            active = intensity > 0.0
            trace.append(
                f"Suitable spaced-practice interval: gap={gap:g} days, horizon={horizon:g}, "
                f"ratio={ratio:.6g}; encoding gain=0.20*(1+strength*2.0*ratio)={gain:.6g}."
            )
        else:
            reason = "first study" if gap is None else f"gap={gap:g} is not in (0, {horizon:g}]"
            trace.append(f"No lag enhancement ({reason}); fixed reference gain={gain:.6g}.")
        next_memory = 1.0 - (1.0 - decayed) * math.exp(-gain)
        next_state = {
            "memory_strength": next_memory,
            "last_study_day": day,
            "study_count": count + 1,
        }
        metric = next_memory
        trace.append(
            f"Retention state after forgetting and practice: 1-(1-{decayed:.6g})*exp(-{gain:.6g})={metric:.6g}."
        )
    else:
        if count == 0:
            raise ValueError("a test requires at least one prior study observation")
        elapsed = day - last_day
        metric = memory * math.exp(-elapsed / horizon)
        next_state = state
        trace.append(
            f"Test retention score=stored_strength*exp(-elapsed/horizon)="
            f"{memory:.6g}*exp(-{elapsed:.6g}/{horizon:.6g})={metric:.6g}; test leaves study state unchanged."
        )

    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"action": "study", "day": 0, "retention_horizon_days": 10},
                {"action": "study", "day": 5, "retention_horizon_days": 10},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"action": "study", "day": 0, "retention_horizon_days": 10},
                # A zero-day gap removes the necessary positive spaced interval.
                {"action": "study", "day": 0, "retention_horizon_days": 10},
            ],
            "expectation": "equal",
        },
    ]
