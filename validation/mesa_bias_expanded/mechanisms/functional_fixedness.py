"""Illustrative customary-use anchoring process for functional fixedness.

This is an explicit synthetic task model, not a detector or a fitted theory.
"""
from __future__ import annotations

import math
from numbers import Real


METADATA = {
    "id": "functional_fixedness",
    "name": "Functional Fixedness",
    "kind": "cognitive_bias",
    "description": (
        "When a feasible customary use is supplied, it becomes the default; "
        "an alternative use is selected only when its utility advantage clears "
        "a strength-scaled hurdle proportional to the customary-use utility."
    ),
    "required_inputs": ["uses"],
    "state_fields": ["last_choice_id", "last_metric", "step_count"],
    "metric_name": "utility_regret",
    "metric_units": "Feasible-use utility points lost versus the highest-utility supplied use (0–1 scale).",
    "assumptions": [
        "All listed uses are available and feasible for the task; utility and customary status are explicit task evidence.",
        "At strength zero the reference policy chooses the supplied use with maximum task utility, with input order breaking ties.",
        "At positive strength, the best customary use is the default; the best alternative must exceed it by more than strength times its utility to be selected.",
        "Strength and the relative-margin rule are illustrative user-settable assumptions, not empirical effect sizes.",
        "With no feasible customary-use candidate, there is no customary-purpose anchor and the reference choice is used.",
    ],
    "limitations": [
        "This compact task-specific selection rule is hypothetical and has not been empirically validated.",
        "It assumes the supplied uses and customary labels are accurate; it neither detects them from language nor infers a person's mental state.",
        "The model does not represent learning, object affordances, task history, or individual/population differences.",
        "Preferring a customary use is not inherently an error; regret is defined only relative to the supplied task utilities.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _validate(context: dict, strength: float) -> tuple[list[dict], float, dict]:
    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary")
    if isinstance(strength, bool) or not isinstance(strength, Real):
        raise ValueError("strength must be a finite number in [0, 1]")
    s = float(strength)
    if not math.isfinite(s) or not 0.0 <= s <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")

    if "uses" not in context:
        raise ValueError("uses are required; missing task evidence is not zero")
    raw_uses = context["uses"]
    if not isinstance(raw_uses, list) or len(raw_uses) < 2:
        raise ValueError("uses must be a list containing at least two supplied uses")
    uses: list[dict] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(raw_uses):
        if not isinstance(raw, dict):
            raise ValueError(f"uses[{index}] must be a dictionary")
        if not {"id", "utility", "customary"}.issubset(raw):
            raise ValueError(f"uses[{index}] requires id, utility, and customary")
        use_id = raw["id"]
        if not isinstance(use_id, str) or not use_id:
            raise ValueError(f"uses[{index}].id must be a nonempty string")
        if use_id in seen_ids:
            raise ValueError("use ids must be unique")
        seen_ids.add(use_id)
        utility = _finite_number(raw["utility"], f"uses[{index}].utility")
        if not 0.0 <= utility <= 1.0:
            raise ValueError(f"uses[{index}].utility must be within [0, 1]")
        customary = raw["customary"]
        if not isinstance(customary, bool):
            raise ValueError(f"uses[{index}].customary must be a boolean")
        uses.append({"id": use_id, "utility": utility, "customary": customary})

    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dictionary")
    steps = state.get("step_count", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.step_count must be a nonnegative integer")
    return uses, s, dict(state)


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit object-use task without mutating context."""
    uses, s, prior_state = _validate(context, strength)
    reference = max(uses, key=lambda use: use["utility"])
    customary_uses = [use for use in uses if use["customary"]]
    alternative_uses = [use for use in uses if not use["customary"]]

    if s == 0.0 or not customary_uses:
        chosen = reference
        hurdle = 0.0
        advantage = None
        rule = "exhaustive maximum-utility reference (no fixedness hurdle)"
    else:
        customary_default = max(customary_uses, key=lambda use: use["utility"])
        hurdle = s * customary_default["utility"]
        if alternative_uses:
            best_alternative = max(alternative_uses, key=lambda use: use["utility"])
            advantage = best_alternative["utility"] - customary_default["utility"]
            chosen = best_alternative if advantage > hurdle else customary_default
        else:
            advantage = None
            chosen = customary_default
        rule = (
            "best alternative is selected only if (alternative utility - customary utility) "
            "> strength * customary utility; otherwise retain customary default"
        )

    regret = max(0.0, reference["utility"] - chosen["utility"])
    next_state = dict(prior_state)
    next_state.update({
        "last_choice_id": chosen["id"],
        "last_metric": float(regret),
        "step_count": prior_state.get("step_count", 0) + 1,
    })
    active = chosen["id"] != reference["id"]
    detail = (
        f"uses={[(use['id'], use['utility'], use['customary']) for use in uses]}, "
        f"strength={s:g}, rule={rule}, hurdle={hurdle:g}, "
        f"best_customary_utility={max((u['utility'] for u in customary_uses), default=None)}, "
        f"best_alternative_advantage={advantage}, selected={chosen['id']} "
        f"(utility {chosen['utility']:g}), reference={reference['id']} "
        f"(utility {reference['utility']:g}), regret={regret:g}."
    )
    return {
        "metric": float(regret),
        "active": bool(active),
        "state": next_state,
        "trace": [detail],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "uses": [
                    {"id": "customary_container", "utility": 0.80, "customary": True},
                    {"id": "alternative_tool", "utility": 0.95, "customary": False},
                ],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "uses": [
                    {"id": "use_a", "utility": 0.45, "customary": False},
                    {"id": "use_b", "utility": 0.90, "customary": False},
                ],
            }],
            "expectation": "equal",
        },
    ]
