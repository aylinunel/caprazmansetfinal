"""Illustrative, task-bounded exposure priming process; not a detector."""
from __future__ import annotations

import math


_DECAY = 0.75
_ACTIVATION_GAIN = 0.8

METADATA = {
    "id": "priming",
    "name": "Priming",
    "kind": "learning_effect",
    "description": (
        "A category explicitly paired with an earlier exposure temporarily gains "
        "processing activation and can influence a later, unrelated choice."
    ),
    "required_inputs": ["exposures", "options"],
    "state_fields": ["activation", "last_choice", "last_baseline_choice", "last_metric"],
    "metric_name": "exposed-category choice indicator",
    "metric_units": "binary indicator (1 if the selected option's category was activated; otherwise 0)",
    "assumptions": [
        "Exposure records supply a hypothetical cue-category association; the plugin does not infer one from words.",
        "Category activation decays by 25% per simulated context and each exposure adds one activation unit.",
        "Choice options have supplied baseline scores; activation adds 0.8 times activation and intervention strength.",
        "The task has no deliberate inferential link between exposure and the later choice.",
    ],
    "limitations": [
        "This compact category-choice process is a hypothetical illustration, not a fitted cognitive model or effect-size estimate.",
        "It cannot establish priming from text co-occurrence or infer an individual's hidden state, motive, or response.",
        "Strength is an uncalibrated intervention setting; category labels and scores are synthetic task inputs.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_inputs(context):
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    for key in METADATA["required_inputs"]:
        if key not in context:
            raise ValueError(f"missing required task input {key}")
    exposures, options = context["exposures"], context["options"]
    if not isinstance(exposures, list) or not isinstance(options, list):
        raise ValueError("exposures and options must be lists")
    for item in exposures:
        if not isinstance(item, dict) or not isinstance(item.get("cue"), str) or not item["cue"].strip():
            raise ValueError("each exposure requires a nonempty cue string")
        if not isinstance(item.get("category"), str) or not item["category"].strip():
            raise ValueError("each exposure requires an explicit nonempty category")
    seen = set()
    for option in options:
        if not isinstance(option, dict):
            raise ValueError("each option must be an object")
        option_id, category = option.get("id"), option.get("category")
        if not isinstance(option_id, str) or not option_id.strip() or option_id in seen:
            raise ValueError("option ids must be unique nonempty strings")
        if not isinstance(category, str) or not category.strip():
            raise ValueError("each option requires a nonempty category")
        _finite_number(option.get("score"), "option score")
        seen.add(option_id)


def _previous_activation(state):
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    activation = state.get("activation", {})
    if not isinstance(activation, dict):
        raise ValueError("state.activation must be an object")
    result = {}
    for category, amount in activation.items():
        if not isinstance(category, str) or not category:
            raise ValueError("state activation categories must be nonempty strings")
        amount = _finite_number(amount, "state activation")
        if amount < 0:
            raise ValueError("state activation cannot be negative")
        result[category] = amount
    return result


def evaluate(context: dict, strength: float) -> dict:
    """Apply decay, add explicit exposure activation, then select an option."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    _validate_inputs(context)
    prior = _previous_activation(context.get("state", {}))

    activation = {category: amount * _DECAY for category, amount in prior.items()}
    for exposure in context["exposures"]:
        category = exposure["category"].strip()
        activation[category] = activation.get(category, 0.0) + 1.0

    options = context["options"]
    if options:
        baseline = max(options, key=lambda option: _finite_number(option["score"], "option score"))
        chosen = max(
            options,
            key=lambda option: _finite_number(option["score"], "option score")
            + float(strength) * _ACTIVATION_GAIN * activation.get(option["category"], 0.0),
        )
        baseline_id, chosen_id = baseline["id"], chosen["id"]
        activated_categories = {category for category, amount in activation.items() if amount > 0}
        metric = float(chosen["category"] in activated_categories)
        active = chosen_id != baseline_id
    else:
        baseline_id = chosen_id = None
        metric = 0.0
        active = False

    next_state = {
        "activation": activation,
        "last_choice": chosen_id,
        "last_baseline_choice": baseline_id,
        "last_metric": metric,
    }
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            f"Decay prior category activations by {_DECAY}; add 1 per explicit exposure; "
            f"score each option as baseline score + strength*{_ACTIVATION_GAIN}*category activation. "
            f"Baseline choice={baseline_id!r}, selected={chosen_id!r}, activated categories={sorted(k for k, v in activation.items() if v > 0)!r}."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"activation": {}},
            "contexts": [
                {"exposures": [{"cue": "cedar", "category": "nature"}], "options": []},
                {
                    "exposures": [],
                    "options": [
                        {"id": "routine", "category": "routine", "score": 0.30},
                        {"id": "nature", "category": "nature", "score": 0.00},
                    ],
                },
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"activation": {}},
            "contexts": [
                {"exposures": [{"cue": "cedar", "category": "nature"}], "options": []},
                {
                    "exposures": [],
                    "options": [
                        {"id": "routine", "category": "routine", "score": 0.30},
                        {"id": "work", "category": "work", "score": 0.00},
                    ],
                },
            ],
            "expectation": "equal",
        },
    ]
