"""Illustrative effort-allocation model for illusion of control.

This is a synthetic decision process, not an empirical model or detector.
"""
from copy import deepcopy
import math


METADATA = {
    "id": "illusion_of_control",
    "name": "Illusion of Control",
    "kind": "cognitive_bias",
    "description": (
        "Allocates effort among control actions by maximizing expected net value; "
        "only when the action has no causal influence, an explicit positive control "
        "belief can raise its estimated return above the objective reference."
    ),
    "required_inputs": [
        "actual_effect_per_effort",
        "perceived_effect_per_effort",
        "outcome_value",
        "effort_cost",
        "effort_levels",
    ],
    "state_fields": [
        "steps",
        "cumulative_effort",
        "effort_history",
        "last_effort",
        "last_objective_net_utility",
        "last_decision_score",
    ],
    "metric_name": "selected_control_effort",
    "metric_units": "effort units selected in this decision step",
    "assumptions": [
        "Effects are per-effort increases in the target-outcome probability, and the listed effort levels keep each supplied probability within [0, 1].",
        "Outcome value and linear effort cost are commensurable utility units; candidate effort levels are the available actions.",
        "At strength zero the reference policy chooses the available effort with greatest objective expected net value, breaking ties toward lower effort.",
        "The illustrative illusion applies only to a truly ineffective action with an explicitly overstated positive perceived effect; strength interpolates that false efficacy into the action's decision estimate.",
    ],
    "limitations": [
        "This highly simplified, user-settable process is synthetic and explicitly not empirically validated.",
        "It does not infer beliefs or causal structure from behavior, estimate real-world prevalence, or detect the concept in text or people.",
        "Real control beliefs may be rational, partially accurate, contextual, or based on omitted causal pathways; the model cannot resolve those alternatives.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


_REQUIRED = METADATA["required_inputs"]


def _finite_number(value, name, *, minimum=None, maximum=None, strictly_positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    if strictly_positive and number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    if minimum is not None and number < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and number > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return number


def _validate_state(state):
    if not isinstance(state, dict):
        raise ValueError("context['state'] must be a dict")
    steps = state.get("steps", 0)
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 0:
        raise ValueError("state.steps must be a nonnegative integer")
    cumulative = _finite_number(state.get("cumulative_effort", 0), "state.cumulative_effort", minimum=0)
    history = state.get("effort_history", [])
    if not isinstance(history, list):
        raise ValueError("state.effort_history must be a list")
    for index, value in enumerate(history):
        _finite_number(value, f"state.effort_history[{index}]", minimum=0)
    for key in ("last_effort", "last_objective_net_utility", "last_decision_score"):
        if key in state:
            _finite_number(state[key], f"state.{key}")
    return steps, cumulative, history


def evaluate(context: dict, strength: float) -> dict:
    """Choose effort using objective returns plus gated false efficacy.

    The primary observable is the chosen effort level. A positive, explicit
    perceived effect changes the selected action only if objective efficacy is
    exactly zero; actual influence is therefore outside the concept's boundary.
    """
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    s = _finite_number(strength, "strength", minimum=0, maximum=1)
    missing = [field for field in _REQUIRED if field not in context]
    if missing:
        raise ValueError(f"missing required input(s): {', '.join(missing)}")

    actual = _finite_number(context["actual_effect_per_effort"], "actual_effect_per_effort", minimum=0, maximum=1)
    perceived = _finite_number(context["perceived_effect_per_effort"], "perceived_effect_per_effort", minimum=0, maximum=1)
    value = _finite_number(context["outcome_value"], "outcome_value", strictly_positive=True)
    cost = _finite_number(context["effort_cost"], "effort_cost", minimum=0)
    levels = context["effort_levels"]
    if not isinstance(levels, (list, tuple)) or not levels:
        raise ValueError("effort_levels must be a nonempty list or tuple")
    efforts = [_finite_number(level, f"effort_levels[{i}]", minimum=0) for i, level in enumerate(levels)]
    if efforts[0] != 0 or any(right <= left for left, right in zip(efforts, efforts[1:])):
        raise ValueError("effort_levels must start at zero and be strictly increasing")
    if actual * efforts[-1] > 1 or perceived * efforts[-1] > 1:
        raise ValueError("effect per effort times maximum effort must not exceed 1")

    state = context.get("state", {})
    steps, cumulative, history = _validate_state(state)
    # The deliberate necessary-condition gate enforces the annotation boundary:
    # if actual efficacy is nonzero, the mechanism contributes no false efficacy.
    false_control_belief = actual == 0 and perceived > actual
    effective_efficacy = actual + (s * (perceived - actual) if false_control_belief else 0.0)

    def utility(effort, efficacy):
        return value * efficacy * effort - cost * effort

    reference_effort = max(efforts, key=lambda effort: (utility(effort, actual), -effort))
    selected_effort = max(efforts, key=lambda effort: (utility(effort, effective_efficacy), -effort))
    objective_net = utility(selected_effort, actual)
    decision_score = utility(selected_effort, effective_efficacy)
    active = selected_effort != reference_effort

    next_state = deepcopy(state)
    next_state.update({
        "steps": steps + 1,
        "cumulative_effort": cumulative + selected_effort,
        "effort_history": deepcopy(history) + [selected_effort],
        "last_effort": selected_effort,
        "last_objective_net_utility": objective_net,
        "last_decision_score": decision_score,
    })
    trace = [
        f"Candidate effort levels: {efforts}; objective efficacy={actual:g}, perceived efficacy={perceived:g}, outcome value={value:g}, linear effort cost={cost:g} per unit.",
        f"Reference maximizes value*actual_efficacy*effort - cost*effort; reference effort={reference_effort:g}.",
        (
            f"False-control condition={false_control_belief}; decision efficacy={effective_efficacy:g} "
            f"(actual + strength*max(perceived-actual, 0) only when actual efficacy is zero); "
            f"selected effort={selected_effort:g}, objective net utility={objective_net:g}, "
            f"decision score={decision_score:g}."
        ),
    ]
    return {
        "metric": selected_effort,
        "active": active,
        "state": next_state,
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "actual_effect_per_effort": 0.0,
                "perceived_effect_per_effort": 0.4,
                "outcome_value": 100.0,
                "effort_cost": 30.0,
                "effort_levels": [0, 1, 2],
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "actual_effect_per_effort": 0.4,
                "perceived_effect_per_effort": 0.5,
                "outcome_value": 100.0,
                "effort_cost": 30.0,
                "effort_levels": [0, 1, 2],
            }],
            "expectation": "equal",
        },
    ]
