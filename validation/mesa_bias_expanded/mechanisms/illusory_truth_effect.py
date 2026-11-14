"""Illustrative, non-empirically-validated illusory truth process model."""

import math
from numbers import Real


METADATA = {
    "id": "illusory_truth_effect",
    "name": "Illusory Truth Effect",
    "kind": "cognitive_bias",
    "description": (
        "Models a claim-specific familiarity contribution to a credibility index "
        "when a claim is encountered again without fresh independent evidence."
    ),
    "required_inputs": ["claim_id", "exposed", "evidence"],
    "state_fields": ["claim_memory"],
    "metric_name": "modeled_claim_credibility",
    "metric_units": "bounded index from 0 to 1 (not a calibrated probability)",
    "assumptions": [
        "The evidence-only reference is a logistic transform of a zero prior log-odds plus supplied, unique evidence log-likelihood ratios.",
        "A repeated unsupported exposure contributes 0.55 * strength * ln(1 + prior exposure count) to the credibility logit.",
        "The coefficient 0.55 is an illustrative user-settable assumption, not a measured effect size.",
        "Each evidence_id represents a genuinely independent evidence item; callers are responsible for that provenance.",
    ],
    "limitations": [
        "This is a transparent synthetic process model, not an NLP detector or empirically validated psychological model.",
        "The credibility index is not a calibrated probability, and the evidence likelihood ratios are assumed inputs.",
        "It does not model source quality, comprehension, forgetting, social context, or competing explanations for familiarity.",
        "Repeated exposure can be beneficial or neutral in real settings; this implementation only isolates the specified possible error.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_FAMILIARITY_LOGIT_COEFFICIENT = 0.55


def _is_finite_number(value):
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)


def _sigmoid(logit):
    """Overflow-safe logistic transform."""
    if logit >= 0:
        return 1.0 / (1.0 + math.exp(-logit))
    exp_value = math.exp(logit)
    return exp_value / (1.0 + exp_value)


def _validate_state(state):
    if not isinstance(state, dict):
        raise ValueError("context['state'] must be a dict")
    claim_memory = state.get("claim_memory", {})
    if not isinstance(claim_memory, dict):
        raise ValueError("state['claim_memory'] must be a dict")
    normalized = {}
    for claim_id, memory in claim_memory.items():
        if not isinstance(claim_id, str) or not claim_id.strip():
            raise ValueError("stored claim IDs must be non-empty strings")
        if not isinstance(memory, dict):
            raise ValueError("each stored claim memory must be a dict")
        count = memory.get("exposure_count", 0)
        log_odds = memory.get("evidence_log_odds", 0.0)
        evidence_ids = memory.get("seen_evidence_ids", [])
        if type(count) is not int or count < 0 or count > 1_000_000_000:
            raise ValueError("stored exposure_count must be an integer in [0, 1000000000]")
        if not _is_finite_number(log_odds):
            raise ValueError("stored evidence_log_odds must be finite")
        if not isinstance(evidence_ids, list) or any(
            not isinstance(item, str) or not item.strip() for item in evidence_ids
        ):
            raise ValueError("stored seen_evidence_ids must be a list of non-empty strings")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("stored seen_evidence_ids must be unique")
        normalized[claim_id] = {
            "exposure_count": count,
            "evidence_log_odds": float(log_odds),
            "seen_evidence_ids": list(evidence_ids),
        }
    return normalized


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one chronological claim observation without mutating its inputs.

    Required scenario inputs are claim_id (non-empty str), exposed (bool), and
    evidence (list of {evidence_id: non-empty str, log_likelihood_ratio: finite
    number in [-50, 50]}). Empty evidence is an explicit assertion that this
    step supplies no independent evidence; omitting it is an error.
    """
    if not _is_finite_number(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    for field in ("claim_id", "exposed", "evidence"):
        if field not in context:
            raise ValueError(f"missing required input: {field}")

    claim_id = context["claim_id"]
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError("claim_id must be a non-empty string")
    exposed = context["exposed"]
    if type(exposed) is not bool:
        raise ValueError("exposed must be a bool")
    evidence = context["evidence"]
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list; use [] to state there is no new evidence")

    prior_state = context.get("state", {})
    memories = _validate_state(prior_state)
    memory = memories.get(
        claim_id,
        {"exposure_count": 0, "evidence_log_odds": 0.0, "seen_evidence_ids": []},
    )
    seen_ids = set(memory["seen_evidence_ids"])
    new_evidence = []
    for item in evidence:
        if not isinstance(item, dict) or "evidence_id" not in item or "log_likelihood_ratio" not in item:
            raise ValueError("each evidence item needs evidence_id and log_likelihood_ratio")
        evidence_id = item["evidence_id"]
        llr = item["log_likelihood_ratio"]
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidence_id must be a non-empty string")
        if not _is_finite_number(llr) or not -50.0 <= llr <= 50.0:
            raise ValueError("log_likelihood_ratio must be finite and in [-50, 50]")
        if evidence_id not in seen_ids:
            new_evidence.append((evidence_id, float(llr)))
            seen_ids.add(evidence_id)

    evidence_delta = math.fsum(llr for _, llr in new_evidence)
    baseline_log_odds = memory["evidence_log_odds"] + evidence_delta
    if not math.isfinite(baseline_log_odds):
        raise ValueError("cumulative evidence log-odds must remain finite")
    baseline_metric = _sigmoid(baseline_log_odds)

    prior_exposures = memory["exposure_count"]
    familiarity_logit = 0.0
    if exposed and not new_evidence and prior_exposures >= 1:
        familiarity_logit = (
            _FAMILIARITY_LOGIT_COEFFICIENT
            * float(strength)
            * math.log1p(prior_exposures)
        )
    metric = _sigmoid(baseline_log_odds + familiarity_logit)

    next_memory = {
        "exposure_count": prior_exposures + int(exposed),
        "evidence_log_odds": baseline_log_odds,
        "seen_evidence_ids": sorted(seen_ids),
    }
    memories[claim_id] = next_memory
    next_state = dict(prior_state)
    next_state["claim_memory"] = memories
    active = familiarity_logit != 0.0 and metric != baseline_metric
    trace = [
        (
            f"Evidence reference: log_odds={baseline_log_odds:.12g} from prior claim log-odds "
            f"plus {len(new_evidence)} new independent evidence item(s); baseline index="
            f"{baseline_metric:.12g}."
        ),
        (
            f"Familiarity term={_FAMILIARITY_LOGIT_COEFFICIENT}*strength({float(strength):.12g})*"
            f"ln(1+prior_exposures({prior_exposures}))={familiarity_logit:.12g}; "
            f"applied only for an exposed claim with no new evidence and prior exposure."
        ),
        f"Returned credibility index={metric:.12g}; active={active}.",
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [
                {"claim_id": "water_claim", "exposed": True, "evidence": []},
                {"claim_id": "water_claim", "exposed": True, "evidence": []},
                {"claim_id": "water_claim", "exposed": True, "evidence": []},
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [
                {
                    "claim_id": "water_claim",
                    "exposed": True,
                    "evidence": [{"evidence_id": "study_1", "log_likelihood_ratio": 0.2}],
                },
                {
                    "claim_id": "water_claim",
                    "exposed": True,
                    "evidence": [{"evidence_id": "study_2", "log_likelihood_ratio": 0.3}],
                },
                {
                    "claim_id": "water_claim",
                    "exposed": True,
                    "evidence": [{"evidence_id": "study_3", "log_likelihood_ratio": 0.1}],
                },
            ],
            "expectation": "equal",
        },
    ]
