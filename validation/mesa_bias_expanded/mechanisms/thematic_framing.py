"""Illustrative editorial allocation model for trend-based thematic framing.

This is a structured process model, not an NLP detector or an empirically fitted
account of editorial or audience behavior. It models one narrow form of the
specification's broader definition: allocating article space to a verified,
comparable multi-period trend around an incident.
"""

import math


METADATA = {
    "id": "thematic_framing",
    "name": "Thematic Framing (Bağlamsal çerçeveleme)",
    "kind": "media_practice",
    "description": (
        "An illustrative editorial space-allocation process: an author can add "
        "trend context to an incident when a verified, topic-matched sequence "
        "contains a directional pattern. Contextualization is a presentation "
        "choice, not inherently an error."
    ),
    "required_inputs": [
        "article_word_budget",
        "incident_word_reserve",
        "context_relevance",
        "source_verified",
        "topic_match",
        "trend_observations",
    ],
    "state_fields": ["context_words_total", "rounds", "allocation_history"],
    "metric_name": "trend_context_words_allocated",
    "metric_units": "whole words allocated to the trend-context passage this step",
    "assumptions": [
        "Strength is an illustrative editorial willingness to allocate space, not prevalence or a calibrated effect size.",
        "The trend signal is the absolute net change times directional consistency across supplied chronological observations.",
        "The word budget remaining after the incident reserve is the maximum space available for context.",
        "Verified source and topic match are explicit supplied facts; the model does not infer them.",
    ],
    "limitations": [
        "Covers only multi-period trend framing, not institutional/process framing or framing quality as a whole.",
        "Does not determine whether a context is fair, complete, useful, misleading, or causally explanatory.",
        "Uses synthetic structured inputs and has no empirical validation or detection-accuracy measurement.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return value


def _bounded_number(value, label, low, high):
    number = _finite_number(value, label)
    if not low <= number <= high:
        raise ValueError(f"{label} must be in [{low}, {high}]")
    return number


def _nonnegative_int(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return the current trend-context word allocation and complete next state."""
    s = _bounded_number(strength, "strength", 0.0, 1.0)
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    required = (
        "article_word_budget",
        "incident_word_reserve",
        "context_relevance",
        "source_verified",
        "topic_match",
        "trend_observations",
        "state",
    )
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")

    budget = _nonnegative_int(context["article_word_budget"], "article_word_budget")
    reserve = _nonnegative_int(context["incident_word_reserve"], "incident_word_reserve")
    if budget <= 0 or reserve <= 0 or reserve > budget:
        raise ValueError("article_word_budget must be positive and incident_word_reserve must be in [1, budget]")
    relevance = _bounded_number(context["context_relevance"], "context_relevance", 0.0, 1.0)
    if type(context["source_verified"]) is not bool:
        raise ValueError("source_verified must be bool")
    if type(context["topic_match"]) is not bool:
        raise ValueError("topic_match must be bool")

    observations = context["trend_observations"]
    if not isinstance(observations, list) or len(observations) < 3:
        raise ValueError("trend_observations must contain at least three chronological observations")
    periods = []
    rates = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict) or "period" not in observation or "rate" not in observation:
            raise ValueError(f"trend_observations[{index}] must contain period and rate")
        periods.append(_finite_number(observation["period"], f"trend_observations[{index}].period"))
        rates.append(_bounded_number(observation["rate"], f"trend_observations[{index}].rate", 0.0, 1.0))
    if any(later <= earlier for earlier, later in zip(periods, periods[1:])):
        raise ValueError("trend observation periods must be strictly increasing")

    prior = context["state"]
    if not isinstance(prior, dict):
        raise ValueError("state must be a dict")
    prior_total = _nonnegative_int(prior.get("context_words_total", 0), "state.context_words_total")
    prior_rounds = _nonnegative_int(prior.get("rounds", 0), "state.rounds")
    prior_history = prior.get("allocation_history", [])
    if not isinstance(prior_history, list):
        raise ValueError("state.allocation_history must be a list")

    # Directional consistency is zero for a flat series and is reduced by
    # reversals. The absolute endpoint change makes the signal dimensionless.
    net_change = rates[-1] - rates[0]
    path_length = sum(abs(right - left) for left, right in zip(rates, rates[1:]))
    consistency = abs(net_change) / path_length if path_length else 0.0
    trend_signal = abs(net_change) * consistency

    # Explicit incident-only reference policy: allocate no trend-context words.
    # Context is eligible only if its facts are verified, topically matched,
    # relevant, and support a non-flat directional sequence.
    eligible = (
        context["source_verified"]
        and context["topic_match"]
        and relevance > 0.0
        and path_length > 0.0
        and abs(net_change) > 0.0
    )
    capacity = budget - reserve
    if eligible:
        raw_words = capacity * s * relevance * trend_signal
        current_words = min(capacity, int(math.floor(raw_words + 1e-12)))
    else:
        current_words = 0

    record = {
        "round": prior_rounds,
        "words": current_words,
        "trend_signal": trend_signal,
        "eligible": eligible,
    }
    next_state = dict(prior)
    next_state["context_words_total"] = prior_total + current_words
    next_state["rounds"] = prior_rounds + 1
    next_state["allocation_history"] = list(prior_history) + [record]
    active = current_words > 0
    trace = [
        "Reference policy: incident-only copy allocates 0 trend-context words.",
        f"Trend signal = abs(last rate - first rate) * abs(net change) / total path length = {trend_signal:.6f}.",
        f"Eligibility = verified source AND topic match AND relevance > 0 AND non-flat chronological series: {eligible}.",
        f"Current allocation = floor((budget - incident reserve) * strength * relevance * trend signal) = {current_words} words (budget={budget}, reserve={reserve}, strength={s:.6f}, relevance={relevance:.6f}).",
    ]
    return {"metric": current_words, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    positive_context = {
        "article_word_budget": 240,
        "incident_word_reserve": 120,
        "context_relevance": 0.75,
        "source_verified": True,
        "topic_match": True,
        "trend_observations": [
            {"period": 1, "rate": 0.1},
            {"period": 2, "rate": 0.3},
            {"period": 3, "rate": 0.5},
            {"period": 4, "rate": 0.7},
        ],
    }
    boundary_context = {
        **positive_context,
        "topic_match": False,
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [positive_context],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [boundary_context],
            "expectation": "equal",
        },
    ]
