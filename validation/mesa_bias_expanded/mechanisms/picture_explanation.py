"""Illustrative structured model of caption-guided image interpretation.

This is a deterministic process model, not a caption/image detector or a
claim about how real readers behave.
"""
from copy import deepcopy
import math
from numbers import Real


METADATA = {
    "id": "picture_explanation",
    "name": "Picture explanation",
    "kind": "media_practice",
    "description": (
        "A supplied caption makes its explicitly named, image-compatible "
        "interpretation more salient during a structured interpretation choice."
    ),
    "required_inputs": ["interpretations", "caption_target", "caption_specificity"],
    "state_fields": ["last_interpretation", "last_caption_alignment", "last_visual_only_interpretation"],
    "metric_name": "caption_target_choice",
    "metric_units": "binary choice indicator (1 if the selected interpretation matches the caption target, else 0)",
    "assumptions": [
        "The candidate interpretations and visual-support scores are explicit scenario inputs, not inferred from pixels or language.",
        "Caption specificity is a supplied [0,1] salience parameter; strength scales its effect and is not calibrated.",
        "An absent caption target is not a candidate and receives no caption salience; the visual-only choice is retained.",
        "Ties are broken by candidate input order, making the reference rule deterministic.",
    ],
    "limitations": [
        "This toy choice rule omits real visual, linguistic, cultural, and reader differences.",
        "It cannot judge whether a caption is accurate, ethical, or misleading; caption-target compatibility is structured input.",
        "No human validation, effect-size estimation, or detection-accuracy measurement is claimed.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value, field):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    number = float(value)
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return number


def evaluate(context: dict, strength: float) -> dict:
    """Select one structured image interpretation with caption salience.

    Reference policy: choose the candidate with greatest supplied visual
    support. At nonzero strength, a candidate matching the supplied caption
    target receives the task-specific salience increment
    ``strength * caption_specificity``. First candidate wins exact ties.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    required = ("interpretations", "caption_target", "caption_specificity")
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    candidates = context["interpretations"]
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("interpretations must be a non-empty list")
    validated = []
    seen = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise ValueError(f"interpretations[{index}] must be a dict")
        identifier = candidate.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"interpretations[{index}].id must be a non-empty string")
        if identifier in seen:
            raise ValueError("interpretation ids must be unique")
        seen.add(identifier)
        support = _unit_interval(candidate.get("visual_support"), f"interpretations[{index}].visual_support")
        validated.append((identifier, support))

    target = context["caption_target"]
    if not isinstance(target, str) or not target.strip():
        raise ValueError("caption_target must be a non-empty string")
    specificity = _unit_interval(context["caption_specificity"], "caption_specificity")

    prior_state = context.get("state", {})
    if not isinstance(prior_state, dict):
        raise ValueError("state must be a dict")
    next_state = deepcopy(prior_state)

    # max() is stable: input order resolves equal visual support/utility.
    visual_only = max(validated, key=lambda item: item[1])[0]
    caption_is_candidate = any(identifier == target for identifier, _ in validated)
    utilities = [
        (identifier, support + (strength * specificity if identifier == target else 0.0))
        for identifier, support in validated
    ]
    chosen = max(utilities, key=lambda item: item[1])[0]
    aligned = float(chosen == target)
    active = chosen != visual_only

    next_state.update({
        "last_interpretation": chosen,
        "last_caption_alignment": aligned,
        "last_visual_only_interpretation": visual_only,
    })
    return {
        "metric": aligned,
        "active": bool(active),
        "state": next_state,
        "trace": [
            "Reference: choose argmax(visual_support), ties by input order. "
            "Caption policy: utility_i = visual_support_i + strength * "
            "caption_specificity * 1[id_i == caption_target]; choose maximum, "
            "ties by input order. Inputs: "
            f"strength={strength:g}, caption_specificity={specificity:g}, "
            f"caption_target={target!r}, target_is_candidate={caption_is_candidate}; "
            f"visual_only={visual_only!r}, selected={chosen!r}, metric=1[selected == target]={aligned:g}."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "interpretations": [
                    {"id": "person_waiting", "visual_support": 0.60},
                    {"id": "person_watching_departure", "visual_support": 0.45},
                ],
                "caption_target": "person_watching_departure",
                "caption_specificity": 1.0,
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "interpretations": [
                    {"id": "person_waiting", "visual_support": 0.60},
                    {"id": "person_watching_departure", "visual_support": 0.45},
                ],
                "caption_target": "storm_approaching",
                "caption_specificity": 1.0,
            }],
            "expectation": "equal",
        },
    ]
