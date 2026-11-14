"""Illustrative finite-slot editorial event-selection process.

This is an assumed structured process model, not a detector or empirical claim.
"""

from copy import deepcopy
from math import isfinite
from numbers import Real

METADATA = {
    "id": "event_selection",
    "name": "Event selection",
    "kind": "media_practice",
    "description": (
        "Ranks a supplied day's candidate events for a limited number of coverage slots; "
        "strength blends public-value ranking with an explicitly supplied editorial-salience criterion."
    ),
    "required_inputs": ["candidates", "capacity"],
    "state_fields": ["last_selected_ids", "last_selection_divergence", "selection_count"],
    "metric_name": "selection_divergence_from_public_value_reference",
    "metric_units": "fraction of coverage slots occupied by a different event than the strength-zero reference",
    "assumptions": [
        "Candidate public_value and editorial_salience are supplied, hypothetical scores on [0, 1].",
        "The strength setting linearly blends those scores; it is illustrative, not calibrated.",
        "Events are ranked independently and ties are broken by ascending event ID.",
        "The strength-zero reference fills the same capacity by descending public_value.",
    ],
    "limitations": [
        "This models a structured editorial choice only; it does not infer newsworthiness or detect bias in real media.",
        "Editorial salience is not inherently harmful and may reflect legitimate audience, format, or resource needs.",
        "No empirical validation, human validation, or measured detection accuracy is claimed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _score(value, label):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    value = float(value)
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{label} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Select up to ``capacity`` candidates and report divergence from reference.

    The returned metric is a task outcome (slot-level choice difference), not a
    belief or a judgment that the selected items are wrong.
    """
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    candidates = context.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty list")
    capacity = context.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int):
        raise ValueError("capacity must be an integer")
    if not 1 <= capacity <= len(candidates):
        raise ValueError("capacity must be between 1 and the number of candidates")

    normalized = []
    seen = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"candidate {index} must be a dict")
        event_id = candidate.get("id")
        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError(f"candidate {index} must have a non-empty string id")
        if event_id in seen:
            raise ValueError(f"candidate id {event_id!r} is duplicated")
        seen.add(event_id)
        public_value = _score(candidate.get("public_value"), f"{event_id}.public_value")
        editorial_salience = _score(
            candidate.get("editorial_salience"), f"{event_id}.editorial_salience"
        )
        normalized.append((event_id, public_value, editorial_salience))

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    selection_count = prior_state.get("selection_count", 0)
    if (
        isinstance(selection_count, bool)
        or not isinstance(selection_count, int)
        or selection_count < 0
    ):
        raise ValueError("state.selection_count must be a non-negative integer")

    reference = sorted(normalized, key=lambda item: (-item[1], item[0]))[:capacity]
    ranked = sorted(
        normalized,
        key=lambda item: (
            -((1.0 - strength) * item[1] + strength * item[2]),
            item[0],
        ),
    )[:capacity]
    reference_ids = [item[0] for item in reference]
    selected_ids = [item[0] for item in ranked]
    changed_slots = sum(event_id not in reference_ids for event_id in selected_ids)
    metric = changed_slots / capacity

    next_state = deepcopy(prior_state)
    next_state.update(
        {
            "last_selected_ids": list(selected_ids),
            "last_selection_divergence": float(metric),
            "selection_count": selection_count + 1,
        }
    )
    return {
        "metric": float(metric),
        "active": metric > 0.0,
        "state": next_state,
        "trace": [
            "Reference: rank by public_value descending, then id ascending; "
            f"reference={reference_ids}.",
            "Mechanism: rank by (1-strength)*public_value + "
            "strength*editorial_salience, descending, then id ascending; "
            f"strength={strength}, capacity={capacity}, selected={selected_ids}.",
            f"Metric: {changed_slots}/{capacity} selected slots differ from reference; "
            "this records a choice difference, not an error judgment.",
        ],
    }


def scenarios() -> list[dict]:
    """Minimal contract scenarios with a competing choice and a no-scarcity boundary."""
    competing = [
        {"id": "A", "public_value": 0.9, "editorial_salience": 0.0},
        {"id": "B", "public_value": 0.8, "editorial_salience": 0.1},
        {"id": "C", "public_value": 0.2, "editorial_salience": 1.0},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{"candidates": competing, "capacity": 1}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{"candidates": competing, "capacity": 3}],
            "expectation": "equal",
        },
    ]
