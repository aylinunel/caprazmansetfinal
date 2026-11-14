"""Illustrative process model of base-rate neglect; not a detector or fitted theory."""
import math
from copy import deepcopy


METADATA = {
    "id": "base_rate_fallacy",
    "name": "Base Rate Fallacy",
    "kind": "cognitive_bias",
    "description": (
        "Models a decision-maker discounting relevant population prior odds while "
        "over-weighting supplied case-specific diagnostic evidence."
    ),
    "required_inputs": ["base_rate", "evidence_likelihood_ratio"],
    "state_fields": ["steps", "last_probability", "last_reference_probability"],
    "metric_name": "estimated_target_probability",
    "metric_units": "probability from 0 to 1 for the supplied hypothetical case",
    "assumptions": [
        "base_rate is the relevant population prevalence, and evidence_likelihood_ratio is the supplied case evidence's likelihood ratio for target versus non-target.",
        "The reference policy combines prior odds and the likelihood ratio by Bayes' rule.",
        "The illustrative bias gives diagnostic case evidence excess weight relative to prior odds: its log-likelihood ratio is multiplied by (1 + strength).",
        "Inputs describe an explicit hypothetical inference task and are not inferred from text or people.",
    ],
    "limitations": [
        "This is one stylized way to operationalize base-rate neglect, not an empirically validated cognitive model or a population claim.",
        "It treats the supplied likelihood ratio as known and omits uncertainty, costs, calibration, and the possibility that a chosen base rate is irrelevant or outdated.",
        "Strong case-specific evidence may rationally dominate a prior; the module cannot assess evidence quality or relevance beyond supplied inputs.",
        "It is not an NLP detector and cannot establish that any real person neglected a base rate.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _probability_from_log_odds(log_odds):
    # Stable logistic transform for finite log odds of either sign.
    if log_odds >= 0:
        return 1.0 / (1.0 + math.exp(-log_odds))
    exp_value = math.exp(log_odds)
    return exp_value / (1.0 + exp_value)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit prior-plus-evidence task without mutating inputs."""
    strength = _finite_number(strength, "strength")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    required = ("base_rate", "evidence_likelihood_ratio")
    missing = [field for field in required if field not in context]
    if missing:
        raise ValueError(f"missing required inputs: {', '.join(missing)}")

    base_rate = _finite_number(context["base_rate"], "base_rate")
    if not 0.0 < base_rate < 1.0:
        raise ValueError("base_rate must be strictly between 0 and 1")
    likelihood_ratio = _finite_number(
        context["evidence_likelihood_ratio"], "evidence_likelihood_ratio"
    )
    if likelihood_ratio <= 0.0:
        raise ValueError("evidence_likelihood_ratio must be greater than 0")

    prior = context.get("state", {})
    if not isinstance(prior, dict):
        raise ValueError("state must be a dictionary")
    steps = prior.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a non-negative integer")
    next_state = deepcopy(prior)

    prior_log_odds = math.log(base_rate) - math.log1p(-base_rate)
    evidence_log_likelihood = math.log(likelihood_ratio)
    reference_log_odds = prior_log_odds + evidence_log_likelihood
    # A neutral LR contributes no case-specific signal, so it cannot trigger
    # neglect. Diagnostic evidence instead receives excess weight relative to
    # the prior odds; at strength 1 its supplied log-LR is counted twice.
    biased_log_odds = prior_log_odds + (1.0 + strength) * evidence_log_likelihood
    reference_probability = _probability_from_log_odds(reference_log_odds)
    metric = _probability_from_log_odds(biased_log_odds)
    active = metric != reference_probability

    next_state.update({
        "steps": steps + 1,
        "last_probability": metric,
        "last_reference_probability": reference_probability,
    })
    return {
        "metric": metric,
        "active": active,
        "state": next_state,
        "trace": [
            "Reference rule: posterior log-odds = logit(base_rate) + "
            "log(evidence_likelihood_ratio); metric is the corresponding probability.",
            "Illustrative neglect rule: posterior log-odds = logit(base_rate) + "
            "(1 + strength) * log(evidence_likelihood_ratio).",
            f"Inputs: base_rate={base_rate:g}, evidence_likelihood_ratio="
            f"{likelihood_ratio:g}, strength={strength:g}; reference="
            f"{reference_probability:.12g}, metric={metric:.12g}, active={active}.",
        ],
    }


def scenarios() -> list[dict]:
    initial_state = {"steps": 0}
    return [
        {
            "name": "positive",
            "initial_state": initial_state,
            "contexts": [{"base_rate": 0.02, "evidence_likelihood_ratio": 9.0}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": initial_state,
            # LR=1 means no diagnostic case-specific information to favor over prevalence.
            "contexts": [{"base_rate": 0.02, "evidence_likelihood_ratio": 1.0}],
            "expectation": "equal",
        },
    ]
