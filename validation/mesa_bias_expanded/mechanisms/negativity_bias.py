"""Hypothetical structured-evidence model for negativity bias.

This is an illustrative weighting process, not a detector or an empirical model
of how people attend to or remember information.
"""
from copy import deepcopy
import math


# Illustrative coefficient, not an estimated or empirically validated effect.
COMPARABLE_NEGATIVE_GAIN = 0.5

METADATA = {
    "id": "negativity_bias",
    "name": "Negativity Bias",
    "kind": "cognitive_bias",
    "description": (
        "Models extra risk-priority weight for negative evidence only when a "
        "same-topic positive item is exactly comparable in supplied severity "
        "and relevance."
    ),
    "required_inputs": ["evidence"],
    "state_fields": [
        "rounds_evaluated",
        "last_reference_metric",
        "last_metric",
        "last_bias_increment",
        "last_matched_pairs",
    ],
    "metric_name": "net_risk_priority",
    "metric_units": "weighted risk-priority points: sum of negative severity×relevance less positive severity×relevance, plus the modeled comparable-negative increment",
    "assumptions": [
        "Evidence topic, valence, severity, and relevance are explicit scenario facts, not inferred from text.",
        "Severity and relevance are normalized to [0, 1], and ordinary reference scoring already weights each item by their product.",
        "Comparability is deliberately narrow: a positive and negative item match only when topic, supplied severity, and supplied relevance are exactly equal; items are paired one-to-one within those groups.",
        "When at least one comparable pair has positive severity×relevance, strength adds COMPARABLE_NEGATIVE_GAIN × strength times the matched negative evidence weight to the reference score.",
        "COMPARABLE_NEGATIVE_GAIN is an illustrative coefficient, not a published effect size; the model evaluates one evidence set per call and carries descriptive output state across calls.",
    ],
    "limitations": [
        "Explicitly hypothetical and not empirically validated; no population claim, fitted psychology, or detection accuracy is implied.",
        "This is a narrow risk-prioritization task proxy, not a general account of attention, memory, judgment, or negativity bias.",
        "Exact matching is conservative and misses genuinely comparable items represented with different topics or slightly different severity/relevance values; supplied classifications may also be wrong.",
        "Unequal weights can be justified by actual severity or relevance. The baseline reflects those differences; the extra mechanism only addresses exactly matched opposing evidence.",
        "A higher score does not establish error, irrationality, false evidence, or harmful media practice; useful caution toward negative evidence can be appropriate.",
        "Does not read natural language, assess evidence quality/truth, model audience effects, or infer motives; all inputs are structured synthetic facts.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _validate_context(context):
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    evidence = context["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise ValueError("evidence must be a non-empty list of records")
    normalized = []
    seen_ids = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise ValueError(f"evidence[{index}] must be a dict")
        for key in ("id", "topic", "valence", "severity", "relevance"):
            if key not in item:
                raise ValueError(f"evidence[{index}] is missing {key!r}")

        item_id = item["id"]
        topic = item["topic"]
        valence = item["valence"]
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError(f"evidence[{index}].id must be a non-empty string")
        if item_id in seen_ids:
            raise ValueError("evidence record ids must be unique")
        seen_ids.add(item_id)
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"evidence[{index}].topic must be a non-empty string")
        if valence not in ("negative", "positive"):
            raise ValueError(f"evidence[{index}].valence must be 'negative' or 'positive'")
        severity = _finite_number(item["severity"], f"evidence[{index}].severity")
        relevance = _finite_number(item["relevance"], f"evidence[{index}].relevance")
        if not 0.0 <= severity <= 1.0:
            raise ValueError(f"evidence[{index}].severity must be in [0, 1]")
        if not 0.0 <= relevance <= 1.0:
            raise ValueError(f"evidence[{index}].relevance must be in [0, 1]")
        normalized.append({
            "id": item_id,
            "topic": topic,
            "valence": valence,
            "severity": severity,
            "relevance": relevance,
        })
    return normalized


def evaluate(context: dict, strength: float) -> dict:
    """Score one evidence set, optionally overweighting matched negative items.

    The strength-zero reference is a transparent severity×relevance weighted
    balance: negative evidence adds and positive evidence subtracts. The extra
    term requires one-to-one same-topic positive/negative matches with exactly
    equal supplied severity and relevance; unmatched or incomparable evidence
    receives reference weighting only.
    """
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    evidence = _validate_context(context)

    old_state = context.get("state", {})
    if not isinstance(old_state, dict):
        raise ValueError("state must be a dict when supplied")
    next_state = deepcopy(old_state)

    reference_metric = sum(
        (1.0 if item["valence"] == "negative" else -1.0)
        * item["severity"] * item["relevance"]
        for item in evidence
    )

    grouped = {}
    for item in evidence:
        key = (item["topic"], item["severity"], item["relevance"])
        counts = grouped.setdefault(key, {"negative": 0, "positive": 0, "weight": item["severity"] * item["relevance"]})
        counts[item["valence"]] += 1

    matched_pairs = 0
    matched_negative_weight = 0.0
    for counts in grouped.values():
        pairs = min(counts["negative"], counts["positive"])
        matched_pairs += pairs
        matched_negative_weight += pairs * counts["weight"]

    increment = COMPARABLE_NEGATIVE_GAIN * strength * matched_negative_weight
    metric = reference_metric + increment
    active = increment > 0.0

    prior_rounds = old_state.get("rounds_evaluated", 0)
    if isinstance(prior_rounds, bool) or not isinstance(prior_rounds, int) or prior_rounds < 0:
        raise ValueError("state.rounds_evaluated must be a non-negative integer")
    next_state.update({
        "rounds_evaluated": prior_rounds + 1,
        "last_reference_metric": reference_metric,
        "last_metric": metric,
        "last_bias_increment": increment,
        "last_matched_pairs": matched_pairs,
    })

    trace = [
        "Strength-zero reference: add severity×relevance for each negative item and subtract it for each positive item.",
        f"Matched {matched_pairs} one-to-one same-topic pairs with exactly equal severity and relevance; added {COMPARABLE_NEGATIVE_GAIN:g} × strength({strength:g}) × matched negative weight({matched_negative_weight:g}) = {increment:g}.",
        f"Net risk-priority metric={metric:g} (reference={reference_metric:g}); active={active}.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "evidence": [
                    {"id": "upkeep-good", "topic": "upkeep", "valence": "positive", "severity": 0.6, "relevance": 0.5},
                    {"id": "upkeep-risk", "topic": "upkeep", "valence": "negative", "severity": 0.6, "relevance": 0.5},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "evidence": [
                    {"id": "unpaired-risk", "topic": "safety", "valence": "negative", "severity": 0.6, "relevance": 0.5},
                    {"id": "different-topic-good", "topic": "service", "valence": "positive", "severity": 0.6, "relevance": 0.5},
                    {"id": "different-severity-good", "topic": "safety", "valence": "positive", "severity": 0.7, "relevance": 0.5},
                ],
            }],
            "expectation": "equal",
        },
    ]
