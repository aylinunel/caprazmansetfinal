"""Hypothetical parasocially amplified AI disclosure choice; not a detector."""
from copy import deepcopy
import math
import numbers

METADATA = {
    "id": "parasocial_trust_in_ai",
    "name": "Parasocial Trust in AI",
    "kind": "psychological_state",
    "description": (
        "Models a sensitive-information disclosure choice in which explicit relational "
        "trust and humanlike interaction can outweigh an AI capability shortfall."
    ),
    "required_inputs": [
        "ai_capability",
        "task_requirement",
        "task_value",
        "disclosure_cost",
        "relational_trust",
        "interaction_warmth",
    ],
    "state_fields": [
        "steps",
        "sensitive_disclosures",
        "last_disclosed",
        "last_reference_disclosed",
        "last_capability_gap",
        "last_relational_bonus",
    ],
    "metric_name": "sensitive_disclosure_choice",
    "metric_units": "binary choice (1 = disclose; 0 = withhold) per simulated decision",
    "assumptions": [
        "All inputs are explicit hypothetical task/person values on a normalized 0-1 scale; none are inferred from language or behavior.",
        "Reference choice compares capability-adjusted task value with disclosure cost.",
        "A parasocial uplift requires both nonzero relational trust and interaction warmth, and is proportional to the unmet capability requirement.",
        "Strength controls only this illustrative uplift and is not a calibrated effect size, prevalence, or confidence estimate.",
    ],
    "limitations": [
        "This is a small synthetic decision model, not an NLP detector, diagnosis, or empirical claim about people or AI systems.",
        "Warmth alone is insufficient by construction; actual disclosure depends on many omitted factors, including consent, safeguards, context, and individual differences.",
        "The normalized scales, linear utility rule, and coefficients are hypothetical; a relational bond can be beneficial or appropriate, and trust is not inherently erroneous.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _unit(value, field):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{field} must be a finite number in [0, 1]")
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Choose whether to disclose using a reference utility plus conditional uplift.

    Reference utility is task_value * min(ai_capability/task_requirement, 1)
    minus disclosure_cost. The parasocial bonus is strength * trust * warmth *
    relative capability gap * task_value. Thus it cannot operate from warmth
    alone, or when actual capability meets task demand.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if isinstance(strength, bool) or not isinstance(strength, numbers.Real):
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    if not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be finite and in [0, 1]")
    values = {}
    for field in METADATA["required_inputs"]:
        if field not in context:
            raise ValueError(f"missing required input: {field}")
        values[field] = _unit(context[field], field)
    requirement = values["task_requirement"]
    if requirement <= 0.0:
        raise ValueError("task_requirement must be greater than zero")

    capability = values["ai_capability"]
    task_value = values["task_value"]
    cost = values["disclosure_cost"]
    trust = values["relational_trust"]
    warmth = values["interaction_warmth"]
    adequacy = min(capability / requirement, 1.0)
    gap = max(0.0, requirement - capability) / requirement
    reference_utility = task_value * adequacy - cost
    bonus = strength * trust * warmth * gap * task_value
    utility = reference_utility + bonus
    reference_disclose = reference_utility > 0.0
    disclose = utility > 0.0

    previous = context.get("state", {})
    if not isinstance(previous, dict):
        raise ValueError("state must be a dict")
    state = deepcopy(previous)
    steps = state.get("steps", 0)
    disclosures = state.get("sensitive_disclosures", 0)
    for name, value in (("steps", steps), ("sensitive_disclosures", disclosures)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{name} must be a nonnegative integer")
    state.update({
        "steps": steps + 1,
        "sensitive_disclosures": disclosures + int(disclose),
        "last_disclosed": disclose,
        "last_reference_disclosed": reference_disclose,
        "last_capability_gap": gap,
        "last_relational_bonus": bonus,
    })
    return {
        "metric": float(disclose),
        "active": disclose != reference_disclose,
        "state": state,
        "trace": [
            f"Capability adequacy=min({capability:g}/{requirement:g},1)={adequacy:.6g}; relative shortfall={gap:.6g}.",
            f"Reference utility={task_value:g}*{adequacy:.6g}-{cost:g}={reference_utility:.6g}; reference choice={'disclose' if reference_disclose else 'withhold'}.",
            f"Relational bonus={strength:g}*{trust:g}*{warmth:g}*{gap:.6g}*{task_value:g}={bonus:.6g}; utility={utility:.6g}; choice={'disclose' if disclose else 'withhold'}.",
        ],
    }


def scenarios() -> list[dict]:
    positive = {
        "ai_capability": 0.20,
        "task_requirement": 0.80,
        "task_value": 0.80,
        "disclosure_cost": 0.25,
        "relational_trust": 0.95,
        "interaction_warmth": 0.95,
    }
    boundary = dict(positive, relational_trust=0.0)
    return [
        {
            "name": "positive",
            "initial_state": {"steps": 0, "sensitive_disclosures": 0},
            "contexts": [positive],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"steps": 0, "sensitive_disclosures": 0},
            "contexts": [boundary],
            "expectation": "equal",
        },
    ]
