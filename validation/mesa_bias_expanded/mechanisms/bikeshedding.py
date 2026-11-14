"""Illustrative agenda-attention process for bikeshedding.

This is an assumed process model, not an empirical detector or psychology claim.
"""

from __future__ import annotations

import math
from typing import Any

METADATA = {
    "id": "bikeshedding",
    "name": "Bikeshedding",
    "kind": "cognitive_bias",
    "description": (
        "Allocates a fixed discussion budget across agenda issues. When an easier, "
        "lower-consequence issue competes with a harder, higher-consequence issue, "
        "ease disproportionately raises the attention weight of low-consequence items."
    ),
    "required_inputs": ["agenda", "discussion_budget"],
    "state_fields": ["rounds", "cumulative_budget", "cumulative_attention", "last_attention"],
    "metric_name": "attention_weighted_consequence",
    "metric_units": "0-1 attention-weighted mean of supplied issue consequence ratings; lower means more discussion went to lower-consequence issues.",
    "assumptions": [
        "Each agenda issue has an explicitly supplied consequence rating and discussion-ease rating, each on [0, 1]; consequence must be greater than zero.",
        "The reference policy allocates attention in proportion to consequence ratings.",
        "When an inverse ease/consequence pair exists, biased issue weights are consequence * exp(strength * ease * (1 - consequence)); this coefficient is illustrative, not fitted.",
        "Attention units are fungible within one agenda and discussion budget; the model does not infer issue importance from wording or appearance.",
    ],
    "limitations": [
        "Requires structured ratings and does not detect bikeshedding in natural discussion or infer motive.",
        "The inverse-pair condition and exponential weighting are illustrative choices, not empirically validated claims.",
        "Real discussion may appropriately focus on a small detail if its supplied consequence rating is high or if other relevant facts are absent.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number")
    return result


def _read_state(raw: Any) -> tuple[int, float, dict[str, float]]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError("state must be a dict")
    rounds = raw.get("rounds", 0)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds must be a nonnegative integer")
    cumulative_budget = _number(raw.get("cumulative_budget", 0.0), "state.cumulative_budget")
    if cumulative_budget < 0:
        raise ValueError("state.cumulative_budget must be nonnegative")
    raw_attention = raw.get("cumulative_attention", {})
    if not isinstance(raw_attention, dict):
        raise ValueError("state.cumulative_attention must be a dict")
    cumulative_attention: dict[str, float] = {}
    for key, value in raw_attention.items():
        if not isinstance(key, str) or not key:
            raise ValueError("cumulative_attention keys must be nonempty strings")
        amount = _number(value, f"state.cumulative_attention[{key!r}]")
        if amount < 0:
            raise ValueError("cumulative attention must be nonnegative")
        cumulative_attention[key] = amount
    return rounds, cumulative_budget, cumulative_attention


def evaluate(context: dict, strength: float) -> dict:
    """Allocate one round's discussion budget and return an independent next state."""
    strength = _number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "agenda" not in context or "discussion_budget" not in context:
        raise ValueError("context requires agenda and discussion_budget")

    agenda = context["agenda"]
    if not isinstance(agenda, list) or not agenda:
        raise ValueError("agenda must be a nonempty list")
    budget = _number(context["discussion_budget"], "discussion_budget")
    if budget <= 0:
        raise ValueError("discussion_budget must be greater than zero")

    issues: list[tuple[str, float, float]] = []
    seen: set[str] = set()
    for index, issue in enumerate(agenda):
        if not isinstance(issue, dict):
            raise ValueError(f"agenda[{index}] must be a dict")
        issue_id = issue.get("id")
        if not isinstance(issue_id, str) or not issue_id.strip() or issue_id in seen:
            raise ValueError("each agenda issue needs a unique nonempty string id")
        seen.add(issue_id)
        if "consequence" not in issue or "ease" not in issue:
            raise ValueError(f"agenda[{index}] requires consequence and ease")
        consequence = _number(issue["consequence"], f"agenda[{index}].consequence")
        ease = _number(issue["ease"], f"agenda[{index}].ease")
        if not 0.0 < consequence <= 1.0:
            raise ValueError("consequence must be in (0, 1]")
        if not 0.0 <= ease <= 1.0:
            raise ValueError("ease must be in [0, 1]")
        issues.append((issue_id, consequence, ease))

    # Necessary condition: at least one easier, lower-consequence issue competes
    # with a harder, higher-consequence issue. Otherwise use the reference rule.
    inverse_pair = any(
        low_consequence < high_consequence and low_ease > high_ease
        for _, low_consequence, low_ease in issues
        for _, high_consequence, high_ease in issues
    )
    reference_weights = [consequence for _, consequence, _ in issues]
    if strength > 0.0 and inverse_pair:
        weights = [
            consequence * math.exp(strength * ease * (1.0 - consequence))
            for _, consequence, ease in issues
        ]
    else:
        weights = reference_weights

    weight_sum = math.fsum(weights)
    attention = {
        issue_id: budget * weight / weight_sum
        for (issue_id, _, _), weight in zip(issues, weights)
    }
    # Use budget-normalized allocation to avoid rounding drift in the observable.
    metric = math.fsum(
        (attention[issue_id] / budget) * consequence
        for issue_id, consequence, _ in issues
    )
    baseline_weights = math.fsum(reference_weights)
    baseline_attention = {
        issue_id: budget * consequence / baseline_weights
        for issue_id, consequence, _ in issues
    }
    active = any(attention[key] != baseline_attention[key] for key in attention)

    rounds, cumulative_budget, cumulative_attention = _read_state(context.get("state", {}))
    next_cumulative = dict(cumulative_attention)
    for issue_id, amount in attention.items():
        next_cumulative[issue_id] = next_cumulative.get(issue_id, 0.0) + amount
    state = {
        "rounds": rounds + 1,
        "cumulative_budget": cumulative_budget + budget,
        "cumulative_attention": next_cumulative,
        "last_attention": dict(attention),
    }
    return {
        "metric": float(metric),
        "active": bool(active),
        "state": state,
        "trace": [
            "Reference attention is budget * consequence / sum(consequence). "
            "If strength > 0 and an issue pair has lower consequence but higher ease, "
            "weights become consequence * exp(strength * ease * (1 - consequence)); "
            "attention is the normalized weight times discussion_budget. "
            "Metric is sum(attention * consequence) / discussion_budget. "
            "Inputs used: agenda consequence/ease ratings and discussion_budget."
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "discussion_budget": 10.0,
                    "agenda": [
                        {"id": "easy_minor_format", "consequence": 0.15, "ease": 0.95},
                        {"id": "hard_safety_review", "consequence": 0.85, "ease": 0.15},
                    ],
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "discussion_budget": 10.0,
                    "agenda": [
                        {"id": "small_but_important_detail", "consequence": 0.7, "ease": 0.9},
                        {"id": "major_decision", "consequence": 0.9, "ease": 0.9},
                    ],
                }
            ],
            "expectation": "equal",
        },
    ]
