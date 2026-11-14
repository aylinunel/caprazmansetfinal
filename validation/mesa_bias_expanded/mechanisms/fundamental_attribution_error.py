"""Illustrative fundamental-attribution-error attribution process.

This is a hypothetical process model, not a detector or fitted psychological model.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "fundamental_attribution_error",
    "name": "Fundamental Attribution Error",
    "kind": "cognitive_bias",
    "description": (
        "For an explicit character judgment, allocate causal weight between "
        "dispositional evidence and a documented relevant situational constraint; "
        "the mechanism discounts the latter."
    ),
    "required_inputs": [
        "dispositional_evidence",
        "situational_constraint",
        "context_evidence_observed",
        "constraint_relevant",
        "character_judgment",
    ],
    "state_fields": [
        "judgment_count",
        "cumulative_situational_share_sum",
        "last_situational_share",
    ],
    "metric_name": "situational_causal_attribution_share",
    "metric_units": "share of modeled causal attribution, from 0 to 1",
    "assumptions": [
        "Evidence magnitudes are explicit, nonnegative scenario inputs on a common additive scale.",
        "The reference policy allocates causal share in proportion to the two supplied evidence magnitudes.",
        "Mechanism strength linearly attenuates relevant situational evidence by the factor (1-strength).",
        "The model applies only to an explicit character judgment with documented context evidence and a relevant positive constraint.",
    ],
    "limitations": [
        "The evidence scale, proportional-allocation baseline, and attenuation rule are illustrative assumptions, not empirically estimated quantities.",
        "This mechanism does not infer context relevance, character judgments, motives, or evidence from text and does not establish that a person is biased.",
        "It omits interactions, uncertainty, alternative causes, and individual or cultural variation.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_nonnegative(context: dict, key: str) -> float:
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{key} must be a finite nonnegative number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{key} must be a finite nonnegative number")
    return value


def _bool(context: dict, key: str) -> bool:
    value = context[key]
    if type(value) is not bool:
        raise ValueError(f"{key} must be a bool")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit attribution task without mutating its inputs."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    required = METADATA["required_inputs"]
    missing = [key for key in required if key not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")
    disposition = _finite_nonnegative(context, "dispositional_evidence")
    situation = _finite_nonnegative(context, "situational_constraint")
    evidence_observed = _bool(context, "context_evidence_observed")
    relevant = _bool(context, "constraint_relevant")
    judgment = _bool(context, "character_judgment")
    if not evidence_observed:
        raise ValueError("context evidence must be observed explicitly; absence is not a zero metric")
    if relevant and situation <= 0:
        raise ValueError("a relevant situational constraint requires positive supplied evidence")
    if judgment and disposition + (situation if relevant else 0.0) <= 0:
        raise ValueError("a character judgment requires positive causal evidence")

    old_state = context.get("state", {})
    if not isinstance(old_state, dict):
        raise ValueError("state must be a dict")
    count = old_state.get("judgment_count", 0)
    total = old_state.get("cumulative_situational_share_sum", 0.0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("state.judgment_count must be a nonnegative integer")
    if isinstance(total, bool) or not isinstance(total, Real) or not math.isfinite(float(total)) or total < 0:
        raise ValueError("state.cumulative_situational_share_sum must be finite and nonnegative")
    total = float(total)

    # No character judgment means there is no attribution decision to distort.
    baseline_situation = situation if relevant else 0.0
    baseline_denominator = disposition + baseline_situation
    reference_share = (
        baseline_situation / baseline_denominator if judgment and baseline_denominator > 0 else 0.0
    )

    eligible = judgment and evidence_observed and relevant and situation > 0
    effective_situation = situation * (1.0 - strength) if eligible else baseline_situation
    denominator = disposition + effective_situation
    metric = effective_situation / denominator if judgment and denominator > 0 else 0.0
    # active means this step's primary observable differs from the strength-zero policy.
    active = bool(eligible and strength > 0 and not math.isclose(metric, reference_share, rel_tol=0.0, abs_tol=1e-15))

    next_count = count + (1 if judgment else 0)
    next_total = total + metric if judgment else total
    next_state = {
        "judgment_count": next_count,
        "cumulative_situational_share_sum": next_total,
        "last_situational_share": metric,
    }
    trace = [
        f"Reference: situational share = relevant situational_constraint / "
        f"(dispositional_evidence + relevant situational_constraint) = {reference_share:.12g}.",
        f"Inputs: character_judgment={judgment}, context_evidence_observed={evidence_observed}, "
        f"constraint_relevant={relevant}, disposition={disposition:.12g}, situation={situation:.12g}.",
        f"Effective situation={effective_situation:.12g} using factor (1-strength)={1.0-strength:.12g} "
        f"when eligible; resulting metric={metric:.12g}; active={active}.",
    ]
    return {"metric": float(metric), "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {
                    "dispositional_evidence": 2.0,
                    "situational_constraint": 8.0,
                    "context_evidence_observed": True,
                    "constraint_relevant": True,
                    "character_judgment": True,
                }
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "dispositional_evidence": 2.0,
                    "situational_constraint": 8.0,
                    "context_evidence_observed": True,
                    "constraint_relevant": False,
                    "character_judgment": True,
                }
            ],
            "expectation": "equal",
        },
    ]
