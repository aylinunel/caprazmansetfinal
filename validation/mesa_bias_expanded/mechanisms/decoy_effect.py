"""Illustrative asymmetric-dominance choice model; not a human-choice detector.
See specs/decoy_effect_implementation.md for the task and assumptions.
"""
from copy import deepcopy
import math


_ATTRACTION_SCALE = 1.2  # illustrative logit bonus, not an empirical estimate

METADATA = {
    "id": "decoy_effect",
    "name": "Decoy Effect",
    "kind": "cognitive_bias",
    "description": (
        "Models a choice share increase for an explicitly named option when it "
        "uniquely dominates a nearby third option on supplied attributes."
    ),
    "required_inputs": ["options", "target_id", "decoy_id"],
    "state_fields": ["last_target_probability", "last_decoy_similarity", "last_asymmetric_dominance"],
    "metric_name": "target_choice_probability",
    "metric_units": "probability (0–1) of choosing the designated target in the supplied three-option set",
    "assumptions": [
        "Exactly three options have explicit utilities and two higher-is-better attributes in [0, 1].",
        "The designated target and decoy are explicit; dominance is assessed coordinate-wise, not inferred.",
        "Reference choice follows softmax of supplied utility scores at unit temperature.",
        "When the target alone dominates the decoy, a similarity-weighted target logit bonus models attraction; the coefficient is illustrative and strength scales it linearly.",
    ],
    "limitations": [
        "This is a synthetic process illustration, not a fitted or empirically validated account of choice.",
        "Attribute direction, utility scores, decoy designation, and target are supplied rather than detected or inferred.",
        "A fixed bonus and simple mean absolute attribute distance omit choice-set, task, and individual differences; decoys may also be useful or irrelevant in real choices.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit_interval(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def _choice_task(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    options = context.get("options")
    if not isinstance(options, list) or len(options) != 3:
        raise ValueError("options must contain exactly three alternatives")
    parsed = {}
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a dictionary")
        option_id = option.get("id")
        if not isinstance(option_id, str) or not option_id:
            raise ValueError(f"options[{index}].id must be a non-empty string")
        if option_id in parsed:
            raise ValueError("option ids must be unique")
        utility = _unit_interval(option.get("utility"), f"options[{index}].utility")
        attributes = option.get("attributes")
        if not isinstance(attributes, list) or len(attributes) != 2:
            raise ValueError(f"options[{index}].attributes must contain two scores")
        attributes = [
            _unit_interval(value, f"options[{index}].attributes[{attr_index}]")
            for attr_index, value in enumerate(attributes)
        ]
        parsed[option_id] = {"utility": utility, "attributes": attributes}

    target_id = context.get("target_id")
    decoy_id = context.get("decoy_id")
    if not isinstance(target_id, str) or target_id not in parsed:
        raise ValueError("target_id must identify one supplied option")
    if not isinstance(decoy_id, str) or decoy_id not in parsed:
        raise ValueError("decoy_id must identify one supplied option")
    if target_id == decoy_id:
        raise ValueError("target_id and decoy_id must be distinct")
    competitor_ids = [key for key in parsed if key not in (target_id, decoy_id)]
    if len(competitor_ids) != 1:
        raise ValueError("the choice set must have exactly one competitor besides target and decoy")

    target = parsed[target_id]["attributes"]
    decoy = parsed[decoy_id]["attributes"]
    competitor = parsed[competitor_ids[0]]["attributes"]

    def dominates(left, right):
        return all(a >= b for a, b in zip(left, right)) and any(
            a > b for a, b in zip(left, right)
        )

    target_dominates = dominates(target, decoy)
    competitor_dominates = dominates(competitor, decoy)
    if not target_dominates:
        raise ValueError("required evidence absent: target must strictly dominate the named decoy")
    asymmetric = not competitor_dominates
    similarity = 1.0 - sum(abs(a - b) for a, b in zip(target, decoy)) / 2.0
    return parsed, target_id, decoy_id, asymmetric, similarity


def _softmax_target_probability(options, target_id, bonus):
    logits = {
        option_id: values["utility"] + (bonus if option_id == target_id else 0.0)
        for option_id, values in options.items()
    }
    peak = max(logits.values())
    weights = {option_id: math.exp(value - peak) for option_id, value in logits.items()}
    return weights[target_id] / sum(weights.values())


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicitly structured three-alternative choice task."""
    strength = _unit_interval(strength, "strength")
    options, target_id, decoy_id, asymmetric, similarity = _choice_task(context)
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")

    # Reference policy: softmax choice over supplied utilities. The attraction
    # process adds a target-specific logit increment only for unique dominance.
    bonus = strength * _ATTRACTION_SCALE * similarity if asymmetric else 0.0
    metric = _softmax_target_probability(options, target_id, bonus)
    if not math.isfinite(metric):
        raise ValueError("computed target choice probability is not finite")
    next_state = deepcopy(state)
    next_state.update({
        "last_target_probability": metric,
        "last_decoy_similarity": similarity,
        "last_asymmetric_dominance": asymmetric,
    })
    active = bool(strength > 0.0 and asymmetric and similarity > 0.0)
    condition = (
        "target uniquely dominates decoy" if asymmetric
        else "competitor also dominates decoy; asymmetry absent"
    )
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            f"Utilities={{{', '.join(f'{key}:{value['utility']:.12g}' for key, value in options.items())}}}; "
            f"target={target_id!r}, decoy={decoy_id!r}; {condition}; "
            f"target-decoy mean absolute attribute distance={1.0 - similarity:.12g}, "
            f"similarity={similarity:.12g}; reference=softmax(supplied utilities), "
            f"target logit bonus={strength:.12g}*{_ATTRACTION_SCALE:.12g}*"
            f"{similarity:.12g} when asymmetric (otherwise 0); "
            f"target choice probability={metric:.12g}.",
        ],
    }


def scenarios() -> list[dict]:
    positive = {
        "options": [
            {"id": "target", "utility": 0.55, "attributes": [0.8, 0.7]},
            {"id": "competitor", "utility": 0.62, "attributes": [0.5, 0.8]},
            {"id": "decoy", "utility": 0.40, "attributes": [0.6, 0.5]},
        ],
        "target_id": "target",
        "decoy_id": "decoy",
    }
    boundary = {
        "options": [
            {"id": "target", "utility": 0.55, "attributes": [0.8, 0.7]},
            {"id": "competitor", "utility": 0.62, "attributes": [0.9, 0.8]},
            {"id": "decoy", "utility": 0.40, "attributes": [0.6, 0.5]},
        ],
        "target_id": "target",
        "decoy_id": "decoy",
    }
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
