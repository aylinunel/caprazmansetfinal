"""Hypothetical sequential memory-weighting model for illusory correlation.

This is an explicit structured-data process model, not a detector or an
empirically validated account of human memory or judgment.
"""

from __future__ import annotations

from copy import deepcopy
import math
from numbers import Real


_CELLS = ("00", "01", "10", "11")

METADATA = {
    "id": "illusory_correlation",
    "name": "Illusory Correlation",
    "kind": "cognitive_bias",
    "description": (
        "Models a hypothetical memory process in which the first observed "
        "co-occurrence of two binary events is encoded with extra salience, "
        "then perceived association is read from the memory-weighted table."
    ),
    "required_inputs": ["paired_observations"],
    "state_fields": ["observed_cells", "memory_cells", "steps_evaluated"],
    "metric_name": "memory_weighted_phi_association",
    "metric_units": "signed phi coefficient in [-1, 1] computed from memory-weighted binary contingency counts",
    "assumptions": [
        "Each supplied pair is one observation of two explicitly coded binary events; codes are not inferred.",
        "At strength zero, every observed pair contributes exactly one count to its contingency-table cell, and the metric is the ordinary phi coefficient.",
        "At positive strength, only the first observed joint occurrence (1,1) in the chronological history receives an extra strength-weighted memory count; later pairs are encoded once.",
        "The extra first-co-occurrence encoding is a task-specific illustration of disproportionate salience for a distinctive coincidence, not a measured psychological effect.",
        "A defined metric requires accumulated evidence with variation in both binary variables; it is not assigned zero when evidence is missing or degenerate.",
    ],
    "limitations": [
        "Explicitly hypothetical and synthetic; not empirically validated, fitted, or a population claim.",
        "Does not detect real-world correlations, infer event coding, model subjective belief directly, or establish causation.",
        "A rare coincidence can be memorable for benign reasons; the model does not infer error, intent, or harm from salience.",
        "It represents only one simplified memory-weighting process and does not cover other forms of illusory correlation or establish that actual data are representative.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value: object, label: str, lower: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number >= {lower}")
    result = float(value)
    if not math.isfinite(result) or result < lower:
        raise ValueError(f"{label} must be a finite number >= {lower}")
    return result


def _validate_state(context: dict) -> tuple[dict, dict, int]:
    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("state must be a dict")
    state = context["state"]
    observed_raw = state.get("observed_cells")
    memory_raw = state.get("memory_cells")
    if (observed_raw is None) != (memory_raw is None):
        raise ValueError("state must provide observed_cells and memory_cells together")
    if observed_raw is None:
        observed = {cell: 0 for cell in _CELLS}
        memory = {cell: 0.0 for cell in _CELLS}
    else:
        if not isinstance(observed_raw, dict) or set(observed_raw) != set(_CELLS):
            raise ValueError("state.observed_cells must contain exactly 00, 01, 10, and 11")
        if not isinstance(memory_raw, dict) or set(memory_raw) != set(_CELLS):
            raise ValueError("state.memory_cells must contain exactly 00, 01, 10, and 11")
        observed = {}
        memory = {}
        for cell in _CELLS:
            count = observed_raw[cell]
            if isinstance(count, bool) or not isinstance(count, int) or count < 0:
                raise ValueError("state.observed_cells values must be nonnegative integers")
            observed[cell] = count
            memory[cell] = _number(memory_raw[cell], f"state.memory_cells[{cell}]")
    steps = state.get("steps_evaluated", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps_evaluated must be a nonnegative integer")
    return observed, memory, steps


def _phi(cells: dict[str, float], label: str) -> float:
    n00, n01, n10, n11 = (float(cells[cell]) for cell in _CELLS)
    denominator_squared = (n10 + n11) * (n00 + n01) * (n01 + n11) * (n00 + n10)
    if not math.isfinite(denominator_squared) or denominator_squared <= 0.0:
        raise ValueError(
            f"{label} evidence is insufficient or degenerate: both binary variables must vary"
        )
    value = (n11 * n00 - n10 * n01) / math.sqrt(denominator_squared)
    if not math.isfinite(value):
        raise ValueError(f"{label} association metric is not finite")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Update memory counts for one chronological batch and compute weighted phi."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "paired_observations" not in context:
        raise ValueError("missing required input: paired_observations")

    batch = context["paired_observations"]
    if not isinstance(batch, list) or not batch:
        raise ValueError("paired_observations must be a non-empty list of binary pairs")
    normalized = []
    for index, pair in enumerate(batch):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(f"paired_observations[{index}] must be a pair")
        if any(type(value) is not int or value not in (0, 1) for value in pair):
            raise ValueError(f"paired_observations[{index}] values must be integer 0 or 1")
        normalized.append((pair[0], pair[1]))

    observed, memory, steps = _validate_state(context)
    for first, second in normalized:
        cell = f"{first}{second}"
        observed[cell] += 1
        # Novel, rare coincidence encoding: the first (1,1) event is stored
        # with an additional fractional count equal to strength.
        memory[cell] += 1.0
        if cell == "11" and observed[cell] == 1:
            memory[cell] += strength

    metric = _phi(memory, "memory-weighted")
    reference = _phi({cell: float(count) for cell, count in observed.items()}, "observed")
    active = metric != reference
    next_state = deepcopy(context["state"])
    next_state.update({
        "observed_cells": dict(observed),
        "memory_cells": dict(memory),
        "steps_evaluated": steps + 1,
    })
    trace = [
        f"Added {len(normalized)} chronological binary pair(s); observed contingency cells={observed}.",
        "The first-ever (1,1) co-occurrence contributes 1 + strength memory counts; all other observations contribute 1.",
        f"Memory-weighted phi=(n11*n00 - n10*n01)/sqrt((n10+n11)(n00+n01)(n01+n11)(n00+n10))={metric:.6g}; ordinary observed-data reference phi={reference:.6g}; active={active}.",
    ]
    return {"metric": float(metric), "active": bool(active), "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"paired_observations": [[1, 1], [1, 0], [0, 1], [0, 0]]},
                {"paired_observations": [[1, 0], [1, 0], [1, 0], [0, 1], [0, 1], [0, 1], [0, 0]]},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {"paired_observations": [[1, 0], [0, 1], [0, 0]]},
                {"paired_observations": [[1, 0], [0, 1], [0, 0]]},
            ],
            "expectation": "equal",
        },
    ]
