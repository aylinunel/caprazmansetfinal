"""Illustrative model of outlet-specific labels that preset actor legitimacy.

This models supplied structured presentation choices, not language detection.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import Any


METADATA = {
    "id": "labeling",
    "name": "Labeling",
    "kind": "media_practice",
    "description": (
        "Models how explicitly supplied outlet-specific epithets/titles can pull "
        "a reader's legitimacy impression away from a shared factual baseline."
    ),
    "required_inputs": ["actor_id", "factual_legitimacy", "outlet_labels"],
    "state_fields": ["steps", "last_actor_id", "last_metric", "last_labels"],
    "metric_name": "cross-outlet legitimacy spread attributable to labels",
    "metric_units": "legitimacy points on a 0–1 scale",
    "assumptions": [
        "The caller has established that all supplied outlets refer to the same actor.",
        "factual_legitimacy is a common evidence-based reference, not a claim of truth.",
        "Each label_preset is an explicit hypothetical legitimacy impression in [0,1].",
        "Strength linearly controls adoption of the supplied label preset; it is not an effect estimate.",
    ],
    "limitations": [
        "No natural-language detection or inference about author intent is performed.",
        "This is a synthetic media-presentation/reader-response relation, not empirical validation.",
        "Outlet, audience, context, label familiarity, and non-label causes of impressions are omitted.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def _validate(context: dict) -> tuple[str, float, list[dict], dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required evidence: {', '.join(missing)}")
    actor_id = context["actor_id"]
    if not isinstance(actor_id, str) or not actor_id.strip():
        raise ValueError("actor_id must be a non-empty string identifying the same actor")
    factual = _unit_interval(context["factual_legitimacy"], "factual_legitimacy")
    raw = context["outlet_labels"]
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("outlet_labels must contain at least two outlet observations")
    observations: list[dict] = []
    outlets: set[str] = set()
    presets: dict[str, float] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"outlet_labels[{index}] must be a dict")
        outlet, label = item.get("outlet"), item.get("label")
        if not isinstance(outlet, str) or not outlet.strip():
            raise ValueError(f"outlet_labels[{index}].outlet must be a non-empty string")
        if outlet in outlets:
            raise ValueError("each outlet must appear exactly once")
        outlets.add(outlet)
        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"outlet_labels[{index}].label must be a non-empty string")
        if "label_preset" not in item:
            raise ValueError(f"outlet_labels[{index}] lacks label_preset evidence")
        preset = _unit_interval(item["label_preset"], f"outlet_labels[{index}].label_preset")
        # A given epithet/title must have one explicit preset in a scenario.
        if label in presets and not math.isclose(presets[label], preset, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("the same label cannot have conflicting label_preset values")
        presets[label] = preset
        observations.append({"outlet": outlet, "label": label, "label_preset": preset})
    state = context.get("state")
    if not isinstance(state, dict):
        raise ValueError("state must be a dict (use {} for an initial state)")
    steps = state.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    return actor_id, factual, observations, state


def evaluate(context: dict, strength: float) -> dict:
    """Return label-induced cross-outlet legitimacy spread and next state."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    actor_id, factual, observations, previous = _validate(context)
    # Necessary condition: outlets use different epithets/titles for the actor.
    # Supplied label presets determine how those authored labels frame legitimacy;
    # no meaning is inferred from the text itself.
    labels_differ = len({item["label"] for item in observations}) > 1
    impressions = [
        factual + strength * (item["label_preset"] - factual)
        for item in observations
    ]
    metric = max(impressions) - min(impressions) if labels_differ else 0.0
    # The strength-zero reference presents the common evidence baseline at every outlet,
    # whose cross-outlet spread is zero. Numerical clipping guards floating-point noise.
    metric = min(1.0, max(0.0, metric))
    next_state = dict(previous)
    next_state.update({
        "steps": previous.get("steps", 0) + 1,
        "last_actor_id": actor_id,
        "last_metric": metric,
        "last_labels": [item["label"] for item in observations],
    })
    active = bool(strength > 0.0 and labels_differ and metric > 0.0)
    trace = [
        "For each outlet, impression = factual_legitimacy + strength * "
        "(label_preset - factual_legitimacy); metric is max(impression)-min(impression). "
        f"Same actor={actor_id!r}; labels_differ={labels_differ}; strength={strength:g}; "
        f"label presets={[item['label_preset'] for item in observations]!r}; "
        f"metric={metric:.12g}. Strength-zero reference spread is 0."
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "actor_id": "actor-1",
                "factual_legitimacy": 0.5,
                "outlet_labels": [
                    {"outlet": "North", "label": "reform leader", "label_preset": 0.9},
                    {"outlet": "South", "label": "power broker", "label_preset": 0.1},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "actor_id": "actor-1",
                "factual_legitimacy": 0.5,
                "outlet_labels": [
                    {"outlet": "North", "label": "mayor", "label_preset": 0.6},
                    {"outlet": "South", "label": "mayor", "label_preset": 0.6},
                ],
            }],
            "expectation": "equal",
        },
    ]
