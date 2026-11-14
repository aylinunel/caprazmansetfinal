"""Illustrative authored word-choice mechanism; not a language detector."""

from copy import deepcopy
import math

METADATA = {
    "id": "word_choice",
    "name": "Word choice",
    "kind": "media_practice",
    "description": (
        "Selects among equally fact-fitting labels for one explicitly identified fact; "
        "a supplied presentation tone can tilt selection toward labels with matching connotation."
    ),
    "required_inputs": ["options", "reference_fact_id", "presentation_tone"],
    "state_fields": ["decision_count", "last_term", "last_fact_id", "last_alignment"],
    "metric_name": "selected tone-connotation alignment",
    "metric_units": "normalized alignment points, presentation_tone × selected connotation, in [-1, 1]",
    "assumptions": [
        "The supplied fact IDs, factual-fit ratings, connotations, and presentation tone are explicit hypothetical inputs, not inferred from text.",
        "The strength parameter scales a deterministic editorial preference and is not a probability or calibrated effect size.",
        "Among equally fact-fitting alternatives the strength-zero reference selects the least connotative label, then the lexically earliest term.",
        "Only alternatives tied at the best supplied factual-fit score for the reference fact are considered for the tone tilt.",
    ],
    "limitations": [
        "This toy model does not determine whether two phrases really express the same fact or how audiences interpret them.",
        "Connotation and factual fit are supplied scales; the model has no empirical validation, fitted coefficients, or detection accuracy.",
        "Tone-aligned wording can be ordinary rhetoric or benign style, and is not inherently misinformation or harmful bias.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    fact_id = context["reference_fact_id"]
    if not isinstance(fact_id, str) or not fact_id.strip():
        raise ValueError("reference_fact_id must be a non-empty string")
    tone = _finite_number(context["presentation_tone"], "presentation_tone")
    if tone < -1.0 or tone > 1.0 or tone == 0.0:
        raise ValueError("presentation_tone must be in [-1, 1] and nonzero")

    options = context["options"]
    if not isinstance(options, list) or not options:
        raise ValueError("options must be a non-empty list")
    validated = []
    seen_terms = set()
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a dict")
        for field in ("term", "fact_id", "factual_fit", "connotation"):
            if field not in option:
                raise ValueError(f"options[{index}] is missing {field}")
        term = option["term"]
        option_fact = option["fact_id"]
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"options[{index}].term must be a non-empty string")
        if term in seen_terms:
            raise ValueError("option terms must be unique")
        seen_terms.add(term)
        if not isinstance(option_fact, str) or not option_fact.strip():
            raise ValueError(f"options[{index}].fact_id must be a non-empty string")
        fit = _finite_number(option["factual_fit"], f"options[{index}].factual_fit")
        valence = _finite_number(option["connotation"], f"options[{index}].connotation")
        if not 0.0 <= fit <= 1.0:
            raise ValueError(f"options[{index}].factual_fit must be in [0, 1]")
        if not -1.0 <= valence <= 1.0:
            raise ValueError(f"options[{index}].connotation must be in [-1, 1]")
        validated.append({"term": term, "fact_id": option_fact, "factual_fit": fit, "connotation": valence})

    candidates = [option for option in validated if option["fact_id"] == fact_id]
    if not candidates:
        raise ValueError("no supplied option supports reference_fact_id; required evidence is missing")
    return candidates, tone, fact_id


def _choose_reference(candidates):
    """Best supplied factual fit, then the least loaded label, then lexical tie-break."""
    best_fit = max(option["factual_fit"] for option in candidates)
    tied = [option for option in candidates if option["factual_fit"] == best_fit]
    return min(tied, key=lambda option: (abs(option["connotation"]), option["term"]))


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one editorial choice without modifying the provided context or state."""
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")

    candidates, tone, fact_id = _validate_context(context)
    state_in = context.get("state", {})
    if not isinstance(state_in, dict):
        raise ValueError("state must be a dict")
    prior_count = state_in.get("decision_count", 0)
    if isinstance(prior_count, bool) or not isinstance(prior_count, int) or prior_count < 0:
        raise ValueError("state.decision_count must be a non-negative integer")

    reference = _choose_reference(candidates)
    best_fit = max(option["factual_fit"] for option in candidates)
    tied = [option for option in candidates if option["factual_fit"] == best_fit]
    # At strength zero this reduces exactly to the reference tie-break. Positive strength
    # adds a tone × connotation preference only within the equally fact-fitting options.
    chosen = min(
        tied,
        key=lambda option: (
            -strength * tone * option["connotation"],
            abs(option["connotation"]),
            option["term"],
        ),
    )
    alignment = tone * chosen["connotation"]
    active = chosen["term"] != reference["term"]

    next_state = deepcopy(state_in)
    next_state.update(
        {
            "decision_count": prior_count + 1,
            "last_term": chosen["term"],
            "last_fact_id": fact_id,
            "last_alignment": alignment,
        }
    )
    return {
        "metric": float(alignment),
        "active": bool(active),
        "state": next_state,
        "trace": [
            f"For reference fact {fact_id!r}, retained options tied at best factual_fit={best_fit:g}.",
            "Reference policy: maximize factual_fit, then minimize absolute connotation, then choose lexical-first term.",
            f"Strength {strength:g} selects by maximizing strength × presentation_tone × connotation within that tie; selected {chosen['term']!r}.",
            f"Metric = presentation_tone ({tone:g}) × selected connotation ({chosen['connotation']:g}) = {alignment:g}; active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    positive_options = [
        {"term": "reported", "fact_id": "attendance_count", "factual_fit": 1.0, "connotation": 0.0},
        {"term": "welcomed", "fact_id": "attendance_count", "factual_fit": 1.0, "connotation": 0.8},
        {"term": "noted", "fact_id": "attendance_count", "factual_fit": 1.0, "connotation": 0.2},
    ]
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "options": positive_options,
                    "reference_fact_id": "attendance_count",
                    "presentation_tone": 1.0,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "options": [
                        {"term": "reported", "fact_id": "attendance_count", "factual_fit": 1.0, "connotation": 0.0},
                        {"term": "celebrated", "fact_id": "event_mood", "factual_fit": 1.0, "connotation": 0.9},
                    ],
                    "reference_fact_id": "attendance_count",
                    "presentation_tone": 1.0,
                }
            ],
            "expectation": "equal",
        },
    ]
