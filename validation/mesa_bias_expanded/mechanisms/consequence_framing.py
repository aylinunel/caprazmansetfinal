"""Illustrative structured model of consequence-led headline framing.

This models an editorial emphasis choice, not a detector or a claim that the
choice is biased or misleading.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "consequence_framing",
    "name": "Consequence Framing (Sonuç çerçevelemesi)",
    "kind": "media_practice",
    "description": (
        "Models an editor choosing a consequence-led rather than event-led "
        "headline when a supplied, supported consequence competes successfully "
        "for limited headline emphasis."
    ),
    "required_inputs": [
        "event_label",
        "event_salience",
        "consequence_label",
        "consequence_salience",
        "consequence_supported",
    ],
    "state_fields": ["last_focus", "steps", "consequence_led_count"],
    "metric_name": "consequence_led_headline",
    "metric_units": "Binary per-step choice indicator (1.0 consequence-led; 0.0 event-led).",
    "assumptions": [
        "The supplied [0,1] salience values are task inputs, not measured psychological quantities.",
        "The event-led headline is the explicit strength-zero reference policy.",
        "At positive strength, consequence emphasis competes with event emphasis as strength × consequence salience versus event salience; ties remain event-led.",
        "A consequence can lead only when its support status is explicitly true.",
        "Strength is an illustrative control setting, not prevalence or a calibrated effect size.",
    ],
    "limitations": [
        "This structured-choice model does not inspect natural-language headlines or establish whether a real consequence is supported.",
        "The salience values and competition rule are hypothetical assumptions, not empirically fitted or validated.",
        "Consequence-led emphasis can be useful or appropriate; this module does not label it an error.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


_REQUIRED = METADATA["required_inputs"]


def _unit_interval(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{name} must be a finite number in [0, 1]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one headline-emphasis choice without mutating the context."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    missing = [key for key in _REQUIRED if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    for key in ("event_label", "consequence_label"):
        if not isinstance(context[key], str) or not context[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    event_salience = _unit_interval("event_salience", context["event_salience"])
    consequence_salience = _unit_interval(
        "consequence_salience", context["consequence_salience"]
    )
    supported = context["consequence_supported"]
    if not isinstance(supported, bool):
        raise ValueError("consequence_supported must be an explicit bool")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    steps = prior.get("steps", 0)
    led_count = prior.get("consequence_led_count", 0)
    for field, value in (("steps", steps), ("consequence_led_count", led_count)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{field} must be a non-negative integer")

    # The reference policy is event-led. The modeled alternative can win only
    # with explicit support and when weighted consequence salience exceeds the
    # event's supplied salience. Equal scores preserve the reference choice.
    weighted_consequence = strength * consequence_salience
    consequence_led = supported and weighted_consequence > event_salience
    focus = "consequence" if consequence_led else "event"
    metric = 1.0 if consequence_led else 0.0

    next_state = dict(prior)
    next_state.update(
        {
            "last_focus": focus,
            "steps": steps + 1,
            "consequence_led_count": led_count + int(consequence_led),
        }
    )
    trace = (
        f"event_salience={event_salience:.6g}; consequence_salience="
        f"{consequence_salience:.6g}; strength={strength:.6g}; "
        f"weighted_consequence=strength*consequence_salience="
        f"{weighted_consequence:.6g}; consequence_supported={supported}; "
        f"strictly greater than event salience and supported => {consequence_led}; "
        f"selected {focus}-led headline (metric={metric:.1f})."
    )
    return {
        "metric": metric,
        "active": consequence_led,
        "state": next_state,
        "trace": [trace],
    }


def scenarios() -> list[dict]:
    """Return required positive and necessary-condition boundary cases."""
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "event_label": "City approves transit plan",
                    "event_salience": 0.40,
                    "consequence_label": "Commute times expected to fall",
                    "consequence_salience": 0.70,
                    "consequence_supported": True,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "event_label": "City approves transit plan",
                    "event_salience": 0.40,
                    "consequence_label": "Commute times expected to fall",
                    "consequence_salience": 0.70,
                    "consequence_supported": False,
                }
            ],
            "expectation": "equal",
        },
    ]
