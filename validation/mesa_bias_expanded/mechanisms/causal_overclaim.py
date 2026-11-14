"""Illustrative editorial-process model for causal overclaim.

This is a structured scenario mechanism, not a language detector or an
empirically calibrated account of editorial behavior.
"""

from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "causal_overclaim",
    "name": "Causal overclaim (Kanıtsız nedensellik)",
    "kind": "media_practice",
    "description": (
        "Models how an explicit causal assertion based only on observed "
        "covariation or event order can be given extra rhetorical force "
        "when plausible alternative explanations remain unaddressed."
    ),
    "required_inputs": [
        "explicit_causal_statement",
        "evidence_kind",
        "claim_force",
        "plausible_alternatives",
        "addressed_alternatives",
    ],
    "conditional_inputs": {
        "covariation": ["paired_observations"],
        "time_order": ["event_sequence"],
    },
    "state_fields": ["last_causal_force", "steps_evaluated"],
    "metric_name": "reported_causal_force",
    "metric_units": "unit interval [0,1], a structured rhetorical-force score",
    "assumptions": [
        "The supplied structured claim and evidence facts are accurate; no text is inspected.",
        "At strength zero, the reference policy preserves the supplied causal-claim force (or reports zero when no causal statement is made).",
        "When a weak relation is asserted as causal, the mechanism allocates a fraction of remaining force headroom in proportion to the share of plausible alternatives left unaddressed.",
        "Strength is an illustrative intervention setting, not a prevalence, confidence, or measured effect size.",
    ],
    "limitations": [
        "Synthetic, hypothetical process only; not empirically validated and not a detector of real reporting.",
        "A supplied list of plausible alternatives is treated as complete and equally weighted.",
        "The model covers one structured editorial decision per call; it does not establish causation or model audience belief.",
        "A covariance check establishes co-movement in the supplied series only, not a causal relation or its absence.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    result = float(value)
    if not math.isfinite(result) or not lower <= result <= upper:
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    return result


def _validate_evidence(context: dict, evidence_kind: str) -> None:
    if evidence_kind == "covariation":
        observations = context.get("paired_observations")
        if not isinstance(observations, list) or len(observations) < 2:
            raise ValueError("covariation evidence requires at least two paired_observations")
        xs: list[float] = []
        ys: list[float] = []
        for index, pair in enumerate(observations):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError(f"paired_observations[{index}] must be an x/y pair")
            x = _finite_number(pair[0], f"paired_observations[{index}].x", -1e9, 1e9)
            y = _finite_number(pair[1], f"paired_observations[{index}].y", -1e9, 1e9)
            xs.append(x)
            ys.append(y)
        x_mean = math.fsum(xs) / len(xs)
        y_mean = math.fsum(ys) / len(ys)
        covariance = math.fsum(
            (x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)
        ) / len(xs)
        if covariance == 0.0:
            raise ValueError("paired_observations must show non-zero co-variation")
    else:
        sequence = context.get("event_sequence")
        if not isinstance(sequence, list) or len(sequence) < 2:
            raise ValueError("time_order evidence requires at least two ordered event_sequence entries")
        previous_time = -math.inf
        for index, entry in enumerate(sequence):
            if not isinstance(entry, dict) or not isinstance(entry.get("event"), str) or not entry["event"].strip():
                raise ValueError(f"event_sequence[{index}] must name an event")
            timestamp = entry.get("time")
            if isinstance(timestamp, bool) or not isinstance(timestamp, Real):
                raise ValueError(f"event_sequence[{index}].time must be a finite number")
            timestamp = float(timestamp)
            if not math.isfinite(timestamp) or timestamp <= previous_time:
                raise ValueError("event_sequence times must be finite and strictly increasing")
            previous_time = timestamp


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one structured editorial claim without mutating its context."""
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")

    if type(context.get("explicit_causal_statement")) is not bool:
        raise ValueError("explicit_causal_statement must be bool")
    evidence_kind = context.get("evidence_kind")
    if evidence_kind not in ("covariation", "time_order"):
        raise ValueError("evidence_kind must be 'covariation' or 'time_order'")
    claim_force = _finite_number(context.get("claim_force"), "claim_force", 0.0, 1.0)
    total = context.get("plausible_alternatives")
    addressed = context.get("addressed_alternatives")
    if isinstance(total, bool) or not isinstance(total, int) or total < 1:
        raise ValueError("plausible_alternatives must be an integer >= 1")
    if isinstance(addressed, bool) or not isinstance(addressed, int) or not 0 <= addressed <= total:
        raise ValueError("addressed_alternatives must be an integer from 0 to plausible_alternatives")
    _validate_evidence(context, evidence_kind)

    old_state = context.get("state")
    if not isinstance(old_state, dict):
        raise ValueError("state must be a dict")
    previous_force = old_state.get("last_causal_force", 0.0)
    _finite_number(previous_force, "state.last_causal_force", 0.0, 1.0)
    steps = old_state.get("steps_evaluated", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps_evaluated must be an integer >= 0")

    explicit = context["explicit_causal_statement"]
    unaddressed = total - addressed
    reference_force = claim_force if explicit else 0.0
    eligible = explicit and unaddressed > 0
    if eligible:
        unaddressed_share = unaddressed / total
        # Rhetorical force headroom is allocated in proportion to the
        # alternatives the explicit causal assertion leaves unexplained.
        metric = reference_force + (
            strength * (1.0 - reference_force) * unaddressed_share
        )
    else:
        unaddressed_share = 0.0
        metric = reference_force
    metric = float(metric)
    active = metric != reference_force

    next_state = dict(old_state)
    next_state["last_causal_force"] = metric
    next_state["steps_evaluated"] = steps + 1
    if not math.isfinite(metric):  # defensive invariant for the public interface
        raise ValueError("computed metric is not finite")

    trace = [
        f"Evidence kind={evidence_kind}; structured evidence validated; explicit_causal_statement={explicit}.",
        f"Reference force={reference_force:.6g}; unaddressed alternatives={unaddressed}/{total}.",
    ]
    if eligible:
        trace.append(
            "Applied force-allocation formula: reference + strength * (1 - reference) "
            f"* unaddressed_share = {reference_force:.6g} + {strength:.6g} * "
            f"(1 - {reference_force:.6g}) * {unaddressed_share:.6g} = {metric:.6g}."
        )
    else:
        trace.append("No eligible explicit causal assertion with an unaddressed alternative; reference force retained.")

    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"last_causal_force": 0.0, "steps_evaluated": 0},
            "contexts": [
                {
                    "explicit_causal_statement": True,
                    "evidence_kind": "covariation",
                    "paired_observations": [[1, 2], [2, 4], [3, 6]],
                    "claim_force": 0.4,
                    "plausible_alternatives": 4,
                    "addressed_alternatives": 1,
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"last_causal_force": 0.0, "steps_evaluated": 0},
            "contexts": [
                {
                    "explicit_causal_statement": False,
                    "evidence_kind": "time_order",
                    "event_sequence": [
                        {"event": "policy_change", "time": 1},
                        {"event": "outcome_change", "time": 2},
                    ],
                    "claim_force": 0.4,
                    "plausible_alternatives": 4,
                    "addressed_alternatives": 1,
                }
            ],
            "expectation": "equal",
        },
    ]
