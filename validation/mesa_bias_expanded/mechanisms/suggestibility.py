"""Illustrative, non-diagnostic model of suggestion influence on one recall estimate."""
from __future__ import annotations

import math


METADATA = {
    "id": "suggestibility",
    "name": "Suggestibility",
    "kind": "cognitive_bias",
    "description": (
        "An unsupported external quantity suggestion pulls a hypothetical recalled "
        "estimate away from unaided recall when independent appraisal is weak."
    ),
    # Each scenario phase supplies every listed task field; none is conditional.
    "required_inputs": [
        "target_quantity",
        "unaided_recall",
        "suggested_quantity",
        "suggestion_is_external",
        "suggestion_is_unsupported",
        "independent_appraisal",
    ],
    "state_fields": [],
    "metric_name": "absolute_recall_error",
    "metric_units": "absolute quantity-estimate units from the supplied target",
    "assumptions": [
        "All quantities describe one hypothetical recall task and are nonnegative.",
        "An external unsupported suggestion exerts a linear pull toward its value.",
        "Independent appraisal attenuates that pull linearly; strength scales the intervention.",
        "The strength parameter is an uncalibrated intervention setting, not a human effect size.",
    ],
    "limitations": [
        "This compact equation is an illustrative process model, not a validated account of memory.",
        "It does not infer source, support, appraisal, or a person's internal state; these are explicit task inputs.",
        "A quantity-estimate task omits richer recollection, source-monitoring, social, and contextual processes.",
        "The metric is task error only and cannot diagnose suggestibility or establish population effects.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _quantity(context: dict, field: str) -> float:
    value = context[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite nonnegative number")
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{field} must be a finite nonnegative number")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return one recall estimate and its absolute error without mutating inputs."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required task input {field}")

    if isinstance(strength, bool) or not isinstance(strength, (int, float)):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")

    target = _quantity(context, "target_quantity")
    unaided = _quantity(context, "unaided_recall")
    suggestion = _quantity(context, "suggested_quantity")
    external = context["suggestion_is_external"]
    unsupported = context["suggestion_is_unsupported"]
    if not isinstance(external, bool) or not isinstance(unsupported, bool):
        raise ValueError("suggestion source/support flags must be booleans")
    appraisal = context["independent_appraisal"]
    if isinstance(appraisal, bool) or not isinstance(appraisal, (int, float)):
        raise ValueError("independent_appraisal must be finite and in [0, 1]")
    appraisal = float(appraisal)
    if not math.isfinite(appraisal) or not 0.0 <= appraisal <= 1.0:
        raise ValueError("independent_appraisal must be finite and in [0, 1]")

    # The mechanism requires both an external source and unsupported content.
    # Appraisal attenuates the pull: R = U + s(1-a)(S-U).
    eligible = external and unsupported
    influence = strength * (1.0 - appraisal) if eligible else 0.0
    recalled = unaided + influence * (suggestion - unaided)
    error = abs(recalled - target)
    active = influence != 0.0 and suggestion != unaided
    trace = [
        "Recall estimate R = U + s(1-a)(S-U) only when suggestion is external and unsupported; "
        f"target={target:g}, unaided U={unaided:g}, suggestion S={suggestion:g}, "
        f"appraisal a={appraisal:g}, strength s={strength:g}, eligible={eligible}, "
        f"recalled R={recalled:g}, absolute error={error:g}.",
        "No influence is assigned to supported content or a non-external suggestion; "
        "this is not a model of evidence-based correction.",
    ]
    return {"metric": error, "active": active, "state": {}, "trace": trace}


def scenarios() -> list[dict]:
    common = {
        "target_quantity": 10.0,
        "unaided_recall": 10.0,
        "suggested_quantity": 18.0,
        "suggestion_is_external": True,
        "independent_appraisal": 0.25,
    }
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{**common, "suggestion_is_unsupported": True}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            # Removing the unsupported-content condition makes this an evidence-supported
            # suggestion, outside the defined suggestibility process.
            "contexts": [{**common, "suggestion_is_unsupported": False}],
            "expectation": "equal",
        },
    ]
