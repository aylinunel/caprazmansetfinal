"""Illustrative, non-empirical model of a cue-based decision heuristic."""

from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "heuristics",
    "name": "Heuristics",
    "kind": "heuristic",
    "description": (
        "When the ordered first attribute has a unique leader and the cue budget "
        "permits a shortcut, select that option after evaluating only that cue; "
        "otherwise use the full mean-utility reference policy."
    ),
    "required_inputs": ["options"],
    "state_fields": ["last_choice", "decisions", "cumulative_attribute_evaluations"],
    "metric_name": "attribute_evaluations",
    "metric_units": "Count of option-attribute values inspected in this decision.",
    "assumptions": [
        "Each option has the same ordered list of normalized attribute values.",
        "The first listed attribute is the currently most accessible cue.",
        "The supplied strength controls a maximum cue-depth budget, not accuracy or prevalence.",
        "The reference policy selects the highest arithmetic mean across all attributes.",
    ],
    "limitations": [
        "This is a synthetic choice-process illustration, not an empirical model or detector.",
        "Cue accessibility, attribute scales, and mean utility are stipulated by the scenario.",
        "A shortcut may be useful or may select a lower-mean option; neither outcome is presumed harmful.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(float(value))


def _options_from(context: dict) -> tuple[list[str], list[list[float]]]:
    if "options" not in context:
        raise ValueError("missing required input: options")
    options = context["options"]
    if not isinstance(options, list) or len(options) < 2:
        raise ValueError("options must be a list containing at least two alternatives")
    names: list[str] = []
    rows: list[list[float]] = []
    width: int | None = None
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a mapping")
        name = option.get("name")
        values = option.get("attributes")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"options[{index}].name must be a non-empty string")
        if name in names:
            raise ValueError("option names must be unique")
        if not isinstance(values, list) or len(values) < 2:
            raise ValueError(f"options[{index}].attributes must contain at least two values")
        if width is None:
            width = len(values)
        elif len(values) != width:
            raise ValueError("all alternatives must provide the same number of attributes")
        if any(not _finite_number(value) or not 0.0 <= float(value) <= 1.0 for value in values):
            raise ValueError("attribute values must be finite numbers in [0, 1]")
        names.append(name)
        rows.append([float(value) for value in values])
    return names, rows


def _read_state(context: dict) -> tuple[dict, int, int]:
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a mapping")
    decisions = state.get("decisions", 0)
    cumulative = state.get("cumulative_attribute_evaluations", 0)
    if (not isinstance(decisions, int) or isinstance(decisions, bool) or decisions < 0
            or not isinstance(cumulative, int) or isinstance(cumulative, bool) or cumulative < 0):
        raise ValueError("state counters must be non-negative integers")
    last_choice = state.get("last_choice")
    if last_choice is not None and not isinstance(last_choice, str):
        raise ValueError("state.last_choice must be a string or None")
    return dict(state), decisions, cumulative


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one choice without mutating context or nested values.

    The full-information reference chooses the first maximum of the options'
    mean attribute values and inspects every value. For positive strength, the
    available cue depth is ceil((1-strength) * attribute_count), bounded below
    by one. If that budget is narrower than the full attribute list and the
    first cue has a unique maximum, the model stops after that cue and chooses
    its leader. Otherwise it evaluates the full reference policy.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a mapping")
    if not _finite_number(strength) or not 0.0 <= float(strength) <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    names, rows = _options_from(context)
    prior_state, decisions, cumulative = _read_state(context)
    n_options = len(rows)
    n_attributes = len(rows[0])
    cue_budget = max(1, math.ceil((1.0 - float(strength)) * n_attributes))
    first_cue = [row[0] for row in rows]
    max_first_cue = max(first_cue)
    leaders = [i for i, value in enumerate(first_cue) if value == max_first_cue]

    shortcut = cue_budget < n_attributes and len(leaders) == 1
    if shortcut:
        chosen_index = leaders[0]
        inspected = n_options
        method = "unique first-cue leader; inspected only the first attribute"
    else:
        means = [sum(row) / n_attributes for row in rows]
        chosen_index = max(range(n_options), key=lambda i: means[i])
        inspected = n_options * n_attributes
        if cue_budget >= n_attributes:
            method = "cue budget covers all attributes; applied full mean-utility reference"
        else:
            method = "first cue has a tied leader; fell back to full mean-utility reference"

    choice = names[chosen_index]
    next_state = dict(prior_state)
    next_state.update(
        last_choice=choice,
        decisions=decisions + 1,
        cumulative_attribute_evaluations=cumulative + inspected,
    )
    return {
        "metric": float(inspected),
        "active": bool(shortcut),
        "state": next_state,
        "trace": [
            f"strength={float(strength):g}; cue_budget=max(1, ceil((1-strength)*{n_attributes}))={cue_budget}.",
            f"{method}; chosen={choice!r}; inspected={inspected} of {n_options * n_attributes} possible option-attribute values.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "options": [
                        {"name": "quick-leader", "attributes": [0.9, 0.0, 0.0]},
                        {"name": "balanced", "attributes": [0.7, 0.9, 0.9]},
                    ]
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "options": [
                        {"name": "lower-mean", "attributes": [0.8, 0.2]},
                        {"name": "higher-mean", "attributes": [0.8, 0.8]},
                    ]
                }
            ],
            "expectation": "equal",
        },
    ]
