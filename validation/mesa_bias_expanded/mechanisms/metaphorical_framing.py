"""Illustrative, structured reader-response model of metaphorical framing.

This is a synthetic process model, not a language detector or empirical claim.
"""
from __future__ import annotations

import copy
import math
from typing import Any


METADATA = {
    "id": "metaphorical_framing",
    "name": "Metaphorical Framing (Mecazi çerçeveleme)",
    "kind": "media_practice",
    "description": (
        "A supplied source-schema-to-event-relation mapping can reorganize which "
        "structured interpretation a reader selects, competing with literal support."
    ),
    "required_inputs": ["event_id", "interpretations", "metaphor"],
    "state_fields": ["last_event_id", "last_interpretation", "last_metric", "frame_active", "history"],
    "metric_name": "selected_response_priority",
    "metric_units": "Unitless response-priority score in [0, 1] attached to the selected interpretation.",
    "assumptions": [
        "The caller supplies a genuine metaphor and its structural source-to-event mapping; this module does not detect metaphors.",
        "Literal support, response priority, and mapping fit are hypothetical structured task facts, not measured reader data.",
        "At zero strength the reference reader selects the option with greatest literal support; ties break by option id.",
        "Strength linearly interpolates choice scores between literal support and structural mapping fit.",
    ],
    "limitations": [
        "A deliberately small choice-task abstraction cannot represent the range, ambiguity, or cultural variation of metaphorical understanding.",
        "The mapping and its numerical intervention strength are illustrative, not empirically validated or calibrated.",
        "A changed interpretation is not inherently harmful: a metaphor may clarify, obscure, or simply redirect attention.",
        "No natural-language detection, causal inference, or population claim is made.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return number


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate(context: Any, strength: Any) -> tuple[dict, dict, list, dict | None, float]:
    if not isinstance(strength, (int, float)) or isinstance(strength, bool):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    for field in ("event_id", "interpretations", "metaphor"):
        if field not in context:
            raise ValueError(f"missing required input: {field}")
    event_id = _nonempty_string(context["event_id"], "event_id")
    raw_options = context["interpretations"]
    if not isinstance(raw_options, list) or len(raw_options) < 2:
        raise ValueError("interpretations must contain at least two options")
    options = []
    seen = set()
    for index, raw in enumerate(raw_options):
        if not isinstance(raw, dict):
            raise ValueError(f"interpretations[{index}] must be a dictionary")
        for field in ("id", "event_relation", "literal_support", "response_priority"):
            if field not in raw:
                raise ValueError(f"interpretations[{index}] missing {field}")
        option_id = _nonempty_string(raw["id"], f"interpretations[{index}].id")
        if option_id in seen:
            raise ValueError("interpretation ids must be unique")
        seen.add(option_id)
        option = {
            "id": option_id,
            "event_relation": _nonempty_string(raw["event_relation"], f"interpretations[{index}].event_relation"),
            "literal_support": _unit_interval(raw["literal_support"], f"interpretations[{index}].literal_support"),
            "response_priority": _unit_interval(raw["response_priority"], f"interpretations[{index}].response_priority"),
        }
        options.append(option)
    raw_metaphor = context["metaphor"]
    metaphor = None
    if raw_metaphor is not None:
        if not isinstance(raw_metaphor, dict):
            raise ValueError("metaphor must be None or a mapping dictionary")
        for field in ("source_schema", "mapped_event_relation", "mapping_note"):
            if field not in raw_metaphor:
                raise ValueError(f"metaphor missing {field}")
        metaphor = {
            "source_schema": _nonempty_string(raw_metaphor["source_schema"], "metaphor.source_schema"),
            "mapped_event_relation": _nonempty_string(raw_metaphor["mapped_event_relation"], "metaphor.mapped_event_relation"),
            "mapping_note": _nonempty_string(raw_metaphor["mapping_note"], "metaphor.mapping_note"),
        }

    # The standard runner supplies these fields. This process is deterministic and
    # does not consume uniform, but checks and carries an independent task state.
    if "state" not in context or not isinstance(context["state"], dict):
        raise ValueError("state must be a dictionary")
    if "peer_states" not in context or not isinstance(context["peer_states"], list):
        raise ValueError("peer_states must be a list")
    for field in ("round_index", "agent_index"):
        if field not in context or isinstance(context[field], bool) or not isinstance(context[field], int) or context[field] < 0:
            raise ValueError(f"{field} must be a non-negative integer")
    prior = context["state"]
    if "history" in prior and not isinstance(prior["history"], list):
        raise ValueError("state.history must be a list")
    return {"event_id": event_id}, prior, options, metaphor, strength


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one event without mutating the input or any nested values."""
    event, prior, options, metaphor, strength = _validate(context, strength)

    # The reference policy follows supplied literal evidence. A mapped metaphor
    # contributes exact structural congruence (1 iff relation matches; else 0).
    literal_scores = {o["id"]: o["literal_support"] for o in options}
    alignments = {
        o["id"]: float(metaphor is not None and o["event_relation"] == metaphor["mapped_event_relation"])
        for o in options
    }
    choice_scores = {
        o["id"]: (1.0 - strength) * literal_scores[o["id"]] + strength * alignments[o["id"]]
        for o in options
    }
    # Lexical tie-break is explicit and independent of option input order.
    selected_id = min(choice_scores, key=lambda option_id: (-choice_scores[option_id], option_id))
    baseline_id = min(literal_scores, key=lambda option_id: (-literal_scores[option_id], option_id))
    selected = next(o for o in options if o["id"] == selected_id)
    metric = selected["response_priority"]
    active = bool(metaphor is not None and strength > 0.0 and selected_id != baseline_id)

    next_state = copy.deepcopy(prior)
    history = copy.deepcopy(prior.get("history", []))
    record = {
        "event_id": event["event_id"],
        "selected_interpretation": selected_id,
        "reference_interpretation": baseline_id,
        "frame_active": active,
        "metric": metric,
    }
    history.append(record)
    next_state.update({
        "last_event_id": event["event_id"],
        "last_interpretation": selected_id,
        "last_metric": metric,
        "frame_active": active,
        "history": history,
    })

    if metaphor is None:
        mapping_description = "no metaphor mapping supplied; all structural alignments are 0"
    else:
        mapping_description = (
            f"source schema {metaphor['source_schema']!r} maps to event relation "
            f"{metaphor['mapped_event_relation']!r}; exact relation matches have alignment 1"
        )
    trace = [
        f"Reference selects max literal_support; scores used: (1-{strength})*literal_support + {strength}*structural_alignment.",
        f"Mapping: {mapping_description}; option scores={choice_scores!r}.",
        f"Selected {selected_id!r} (reference {baseline_id!r}); metric=response_priority={metric}; active={active}.",
    ]
    return {"metric": float(metric), "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    positive = {
        "event_id": "bridge-closure",
        "interpretations": [
            {"id": "routine-maintenance", "event_relation": "scheduled-care", "literal_support": 0.8, "response_priority": 0.2},
            {"id": "system-under-siege", "event_relation": "defensive-conflict", "literal_support": 0.65, "response_priority": 0.9},
        ],
        "metaphor": {
            "source_schema": "siege",
            "mapped_event_relation": "defensive-conflict",
            "mapping_note": "closure is explicitly mapped to defense against an attack in this hypothetical authored frame",
        },
    }
    boundary = copy.deepcopy(positive)
    boundary["event_id"] = "bridge-closure-without-metaphor"
    boundary["metaphor"] = None
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [positive],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
