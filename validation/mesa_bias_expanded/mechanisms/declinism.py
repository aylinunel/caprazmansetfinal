"""Illustrative process model for declinism; not an empirical detector."""

from copy import deepcopy
import math
from numbers import Real


METADATA = {
    "id": "declinism",
    "name": "Declinism",
    "kind": "cognitive_bias",
    "description": (
        "Models idealized historical recall by blending each domain's prior mean "
        "toward its observed peak, then counts generalized deterioration judgments "
        "only when at least two domains lack evidence of decline."
    ),
    "required_inputs": ["scores"],
    "state_fields": ["history", "last_metric", "last_supported_domains", "last_idealized_domains"],
    "metric_name": "share_of_domains_judged_deteriorating",
    "metric_units": "fraction of observed domains (0 to 1)",
    "assumptions": [
        "Each score is a comparable, directionally positive measure on a 0-100 scale.",
        "The supplied state history is an accurate sequence of prior observations.",
        "An illustrative memory retrieval blends the prior arithmetic mean toward the prior maximum in proportion to strength.",
        "A generalized unsupported-decline condition requires at least two domains whose current score is not below their prior mean but is below their prior maximum.",
        "Strength is a user-settable intervention parameter, not a measured psychological effect size.",
    ],
    "limitations": [
        "This is a hypothetical, explicit process model, not empirically validated psychology or a classifier.",
        "The mean and maximum are simplistic summaries; measurement noise, domain choice, changing scales, and legitimate peak-to-present changes are not modeled.",
        "The minimum-two-domain gate operationalizes generalization for this toy task and is not a clinical or population threshold.",
        "No natural-language claims, motives, or hidden mental states are inferred.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _score_map(value, label):
    if not isinstance(value, dict) or len(value) < 2:
        raise ValueError(f"{label} must be a mapping of at least two domain names to scores")
    clean = {}
    for key, score in value.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{label} domain names must be non-empty strings")
        if isinstance(score, bool) or not isinstance(score, Real):
            raise ValueError(f"{label}[{key!r}] must be a finite number")
        number = float(score)
        if not math.isfinite(number) or not 0.0 <= number <= 100.0:
            raise ValueError(f"{label}[{key!r}] must be finite and in [0, 100]")
        clean[key] = number
    return clean


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological score observation without mutating inputs."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a mapping")
    if "scores" not in context:
        raise ValueError("missing required input: scores")
    current = _score_map(context["scores"], "scores")
    state = context.get("state")
    if not isinstance(state, dict) or "history" not in state:
        raise ValueError("state must contain a history of prior score mappings")
    history = state["history"]
    if not isinstance(history, list) or len(history) < 2:
        raise ValueError("history must contain at least two chronological prior observations")

    checked_history = [_score_map(row, f"history[{index}]") for index, row in enumerate(history)]
    domains = set(current)
    if any(set(row) != domains for row in checked_history):
        raise ValueError("all historical and current observations must use the same domains")

    supported = []
    eligible = []
    remembered_past = {}
    for domain in current:
        observations = [row[domain] for row in checked_history]
        prior_mean = sum(observations) / len(observations)
        prior_peak = max(observations)
        now = current[domain]
        if now < prior_mean:
            supported.append(domain)
        elif prior_peak > now:
            # Current is not below the historical mean, so a peak-based
            # deterioration impression here is unsupported by the baseline.
            eligible.append(domain)
        remembered_past[domain] = prior_mean + strength * (prior_peak - prior_mean)

    baseline_domains = set(supported)
    judged_domains = set(baseline_domains)
    idealized = []
    # One supported decline is deliberately not generalized. Idealized recall
    # can add judgments only if at least two other domains have an unsupported
    # peak-versus-current contrast.
    if len(eligible) >= 2 and strength > 0.0:
        for domain in eligible:
            if remembered_past[domain] > current[domain]:
                judged_domains.add(domain)
                idealized.append(domain)

    metric = len(judged_domains) / len(domains)
    baseline_metric = len(baseline_domains) / len(domains)
    next_state = deepcopy(state)
    next_state["history"] = deepcopy(history) + [deepcopy(current)]
    next_state["last_metric"] = metric
    next_state["last_supported_domains"] = sorted(supported)
    next_state["last_idealized_domains"] = sorted(idealized)

    return {
        "metric": metric,
        "active": metric > baseline_metric,
        "state": next_state,
        "trace": [
            "For each domain, prior_mean=mean(history), prior_peak=max(history), and "
            "remembered_past=prior_mean+strength*(prior_peak-prior_mean).",
            "The strength-zero reference marks deterioration only where current < prior_mean.",
            "Peak-based judgments are added only when at least two domains have current >= prior_mean and prior_peak > current; the metric is judged-domain count / domain count.",
            f"Supported domains={sorted(supported)}; eligible unsupported domains={sorted(eligible)}; added idealized domains={sorted(idealized)}.",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {
                "history": [
                    {"health": 60, "safety": 70, "community": 50},
                    {"health": 100, "safety": 100, "community": 90},
                ]
            },
            "contexts": [
                {"scores": {"health": 80, "safety": 85, "community": 70}},
                {"scores": {"health": 80, "safety": 85, "community": 70}},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {
                "history": [
                    {"health": 100, "safety": 50, "community": 60},
                    {"health": 90, "safety": 50, "community": 60},
                ]
            },
            "contexts": [
                {"scores": {"health": 80, "safety": 50, "community": 60}},
                {"scores": {"health": 70, "safety": 50, "community": 60}},
            ],
            "expectation": "equal",
        },
    ]
