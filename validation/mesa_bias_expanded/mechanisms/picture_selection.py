"""Illustrative model of expression-framed picture selection.

This is a structured process model, not an image detector or empirical claim.
"""

from copy import deepcopy
import math


METADATA = {
    "id": "picture_selection",
    "name": "Picture selection",
    "kind": "media_practice",
    "description": (
        "Select among structured photos using production quality and, when the "
        "same person is available in contrasting expressions, an explicit "
        "authored expression-frame cue."
    ),
    "required_inputs": ["images", "editorial_frame"],
    "state_fields": ["steps", "selected_ids", "last_selected_id"],
    "metric_name": "selected_photo_is_angry",
    "metric_units": "binary indicator (1 if the selected photo is labeled angry, otherwise 0)",
    "assumptions": [
        "Each image record's person identity, expression, and quality are supplied structured facts.",
        "The editorial frame is an explicit authored presentation choice, not an inferred motive.",
        "A framing bonus of 0.5 quality units is an illustrative, user-settable assumption; strength scales it.",
        "The reference policy selects the highest-quality photo, breaking ties by image ID.",
    ],
    "limitations": [
        "Does not inspect images, infer authorship or intent, or estimate audience response.",
        "The scoring coefficient and process have not been empirically validated.",
        "Photo selection can be benign, including legitimate editorial illustration; no harm is presumed.",
        "Only the specified smiling/angry contrast and explicit structured inputs are modeled.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_FRAME_BONUS = 0.5
_VALID_EXPRESSIONS = {"smiling", "angry"}
_VALID_FRAMES = {"smiling", "angry"}


def _finite_number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    value = float(value)
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be a finite number in [{low}, {high}]")
    return value


def _validate_images(images):
    if not isinstance(images, list) or not images:
        raise ValueError("images must be a non-empty list of image records")
    normalized = []
    seen_ids = set()
    for index, image in enumerate(images):
        if not isinstance(image, dict):
            raise ValueError(f"images[{index}] must be a dictionary")
        image_id = image.get("id")
        person_id = image.get("person_id")
        expression = image.get("expression")
        if not isinstance(image_id, str) or not image_id.strip():
            raise ValueError(f"images[{index}].id must be a non-empty string")
        if image_id in seen_ids:
            raise ValueError("image IDs must be unique within a choice set")
        seen_ids.add(image_id)
        if not isinstance(person_id, str) or not person_id.strip():
            raise ValueError(f"images[{index}].person_id must be a non-empty string")
        if not isinstance(expression, str) or expression not in _VALID_EXPRESSIONS:
            raise ValueError(f"images[{index}].expression must be smiling or angry")
        quality = _finite_number(image.get("quality"), f"images[{index}].quality", 0.0, 1.0)
        normalized.append({
            "id": image_id,
            "person_id": person_id,
            "expression": expression,
            "quality": quality,
        })
    return normalized


def _select(images, frame, paired_contrast, strength):
    """Choose by quality, adding expression-frame match only for a same-person pair."""
    scored = []
    for image in images:
        frame_match = paired_contrast and image["expression"] == frame
        score = image["quality"] + (strength * _FRAME_BONUS if frame_match else 0.0)
        scored.append((score, image["id"], image))
    # Lexicographically smallest ID is the explicit deterministic tie-break.
    return min(scored, key=lambda item: (-item[0], item[1]))[2]


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate a single authored photo choice without mutating the supplied context."""
    strength = _finite_number(strength, "strength", 0.0, 1.0)
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    if "images" not in context or "editorial_frame" not in context:
        raise ValueError("required inputs images and editorial_frame must be supplied")
    images = _validate_images(context["images"])
    frame = context["editorial_frame"]
    if not isinstance(frame, str) or frame not in _VALID_FRAMES:
        raise ValueError("editorial_frame must be smiling or angry")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dictionary")
    steps = prior.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    selected_ids = prior.get("selected_ids", [])
    if not isinstance(selected_ids, list) or any(not isinstance(item, str) for item in selected_ids):
        raise ValueError("state.selected_ids must be a list of strings")

    # Necessary condition: both expressions for at least one explicitly identified
    # person must be present in this choice set. No unprovided identity is inferred.
    expressions_by_person = {}
    for image in images:
        expressions_by_person.setdefault(image["person_id"], set()).add(image["expression"])
    paired_contrast = any(
        _VALID_EXPRESSIONS.issubset(expressions)
        for expressions in expressions_by_person.values()
    )

    reference = _select(images, frame, paired_contrast=False, strength=0.0)
    chosen = _select(images, frame, paired_contrast=paired_contrast, strength=strength)
    next_state = deepcopy(prior)
    next_state.update({
        "steps": steps + 1,
        "selected_ids": [*selected_ids, chosen["id"]],
        "last_selected_id": chosen["id"],
    })
    metric = 1.0 if chosen["expression"] == "angry" else 0.0
    return {
        "metric": metric,
        "active": chosen["id"] != reference["id"],
        "state": next_state,
        "trace": [
            "Reference: maximize supplied photo quality; ties use the smallest image ID.",
            f"Same-person smiling/angry alternatives present: {paired_contrast}.",
            f"Choice score = quality + strength({strength:g}) * 0.5 * frame-match; "
            "the frame-match term is enabled only for a same-person contrast pair.",
            f"Selected {chosen['id']} ({chosen['expression']}, quality={chosen['quality']:g}); "
            f"reference selected {reference['id']}; metric is angry-indicator={metric:g}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"steps": 0, "selected_ids": []},
            "contexts": [{
                "images": [
                    {"id": "a-smile", "person_id": "person-1", "expression": "smiling", "quality": 0.7},
                    {"id": "z-angry", "person_id": "person-1", "expression": "angry", "quality": 0.7},
                ],
                "editorial_frame": "angry",
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"steps": 0, "selected_ids": []},
            "contexts": [{
                "images": [
                    {"id": "a-smile", "person_id": "person-1", "expression": "smiling", "quality": 0.7},
                    {"id": "z-angry", "person_id": "person-2", "expression": "angry", "quality": 0.7},
                ],
                "editorial_frame": "angry",
            }],
            "expectation": "equal",
        },
    ]
