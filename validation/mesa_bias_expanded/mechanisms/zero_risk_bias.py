"""Illustrative option-choice process for preference attached to zero-risk endpoints."""
from __future__ import annotations

import math


METADATA = {
    "id": "zero_risk_bias",
    "name": "Zero Risk Bias",
    "kind": "cognitive_bias",
    "description": (
        "Select among risk-reduction plans by expected-harm reduction less cost, "
        "with an additional salience premium only for a plan that truly removes "
        "a positive, severity-weighted risk to exactly zero while a rival offers "
        "a larger gross reduction and higher unadjusted net value."
    ),
    "required_inputs": ["baseline_risks", "harm_severities", "options", "plan_costs"],
    "state_fields": ["selected_option", "selected_expected_loss", "selected_gross_reduction"],
    "metric_name": "selected_plan_expected_harm_plus_cost",
    "metric_units": "illustrative expected-harm units per decision (severity × probability) plus cost in the same units",
    "assumptions": [
        "Risk probabilities and severity weights are supplied, hypothetical task facts; expected harm is their additive product.",
        "The zero-endpoint premium is strength × 2 × the severity-weighted baseline exposure actually eliminated; 2 is an illustrative choice coefficient, not an empirical estimate.",
        "The strength-zero reference selects the plan maximizing gross expected-harm reduction less supplied cost, with input order breaking exact ties.",
        "Only strictly positive baseline risks reduced to exactly zero can trigger the premium; a zero endpoint by itself is not treated as irrational.",
    ],
    "limitations": [
        "This compact deterministic choice model is hypothetical and is not a detector, diagnosis, population claim, or fitted account of human choice.",
        "Additive expected harm omits dependence, uncertainty, distributional effects, reversibility, implementation constraints, and other valid reasons to favor an endpoint.",
        "Costs must be expressed in the same illustrative units as expected harm; changing the coefficient or inputs can change choices.",
        "The boundary condition holds modeled severity, cost, and risk structure fixed and tests absence of an exactly eliminated positive risk; it does not settle real policy judgments.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _number(value, label, *, minimum=None, maximum=None, strict_minimum=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if minimum is not None and (value <= minimum if strict_minimum else value < minimum):
        op = ">" if strict_minimum else ">="
        raise ValueError(f"{label} must be {op} {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return value


def _validate(context):
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    missing = [key for key in METADATA["required_inputs"] if key not in context]
    if missing:
        raise ValueError("missing required task input(s): " + ", ".join(missing))

    baseline = context["baseline_risks"]
    severity = context["harm_severities"]
    options = context["options"]
    costs = context["plan_costs"]
    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("baseline_risks must be a nonempty risk-to-probability object")
    risks = set(baseline)
    if not all(isinstance(k, str) and k for k in risks):
        raise ValueError("risk names must be nonempty strings")
    if not isinstance(severity, dict) or set(severity) != risks:
        raise ValueError("harm_severities must have exactly the baseline risk keys")
    if not isinstance(options, dict) or len(options) < 2:
        raise ValueError("options must contain at least two named plans")
    if not all(isinstance(k, str) and k for k in options):
        raise ValueError("plan names must be nonempty strings")
    if not isinstance(costs, dict) or set(costs) != set(options):
        raise ValueError("plan_costs must have exactly the option names")

    base = {k: _number(v, f"baseline_risks[{k}]", minimum=0, maximum=1) for k, v in baseline.items()}
    harms = {k: _number(v, f"harm_severities[{k}]", minimum=0, strict_minimum=True) for k, v in severity.items()}
    residuals = {}
    for plan, profile in options.items():
        if not isinstance(profile, dict) or set(profile) != risks:
            raise ValueError(f"options[{plan}] must have exactly the baseline risk keys")
        residuals[plan] = {k: _number(v, f"options[{plan}][{k}]", minimum=0, maximum=1)
                           for k, v in profile.items()}
    plan_costs = {k: _number(v, f"plan_costs[{k}]", minimum=0) for k, v in costs.items()}
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be an object when supplied")
    return base, harms, residuals, plan_costs, state


def evaluate(context: dict, strength: float) -> dict:
    """Return one deterministic plan choice and its modeled expected loss."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    strength = float(strength)
    base, harms, residuals, costs, prior_state = _validate(context)
    baseline_loss = sum(base[risk] * harms[risk] for risk in base)
    gross = {
        plan: baseline_loss - sum(profile[risk] * harms[risk] for risk in base)
        for plan, profile in residuals.items()
    }
    net = {plan: gross[plan] - costs[plan] for plan in residuals}
    reference_choice = max(net, key=net.get)

    # Endpoint credit requires evidence of a genuine positive-to-exactly-zero
    # transition, plus a rival with both larger gross harm reduction and better
    # unadjusted net value. This isolates the defined preference from ordinary
    # cost/risk trade-offs and leaves rational zero endpoints unpenalized.
    endpoint_exposure = {}
    eligible = {}
    for plan, profile in residuals.items():
        eliminated = [risk for risk in base if base[risk] > 0 and profile[risk] == 0]
        endpoint_exposure[plan] = sum(base[risk] * harms[risk] for risk in eliminated)
        eligible[plan] = bool(eliminated) and any(
            gross[rival] > gross[plan] + 1e-12 and net[rival] > net[plan] + 1e-12
            for rival in residuals if rival != plan
        )
    scores = {
        plan: net[plan] + (strength * 2.0 * endpoint_exposure[plan] if eligible[plan] else 0.0)
        for plan in residuals
    }
    selected = max(scores, key=scores.get)
    residual_harm = sum(residuals[selected][risk] * harms[risk] for risk in base)
    metric = residual_harm + costs[selected]

    next_state = dict(prior_state)
    next_state.update({
        "selected_option": selected,
        "selected_expected_loss": metric,
        "selected_gross_reduction": gross[selected],
    })
    mechanism_active = selected != reference_choice
    trace = (
        f"Expected baseline harm={baseline_loss:.12g}; net reduction by plan="
        f"{net}; zero-endpoint exposures={endpoint_exposure}; eligible={eligible}; "
        f"adjusted choice scores={scores}. Selected {selected!r} with modeled "
        f"residual harm {residual_harm:.12g} plus cost {costs[selected]:.12g}; "
        f"strength-zero reference={reference_choice!r}; active={mechanism_active}.",
    )
    return {"metric": metric, "active": mechanism_active, "state": next_state, "trace": list(trace)}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {},
            "contexts": [{
                "baseline_risks": {"small_event": 0.10, "common_event": 0.40},
                "harm_severities": {"small_event": 1.0, "common_event": 1.0},
                "options": {
                    "eliminate_small_event": {"small_event": 0.0, "common_event": 0.39},
                    "reduce_total_harm_more": {"small_event": 0.05, "common_event": 0.20},
                },
                "plan_costs": {"eliminate_small_event": 0.0, "reduce_total_harm_more": 0.0},
            }],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {},
            "contexts": [{
                "baseline_risks": {"small_event": 0.10, "common_event": 0.40},
                "harm_severities": {"small_event": 1.0, "common_event": 1.0},
                # No option eliminates any positive risk to zero: the necessary
                # endpoint condition is absent, while the larger reduction wins.
                "options": {
                    "nearly_remove_small_event": {"small_event": 0.01, "common_event": 0.39},
                    "reduce_total_harm_more": {"small_event": 0.05, "common_event": 0.20},
                },
                "plan_costs": {"nearly_remove_small_event": 0.0, "reduce_total_harm_more": 0.0},
            }],
            "expectation": "equal",
        },
    ]
