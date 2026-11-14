"""Illustrative distinction-bias process model; not a psychological detector."""

from math import isfinite


METADATA = {
    "id": "distinction_bias",
    "name": "Distinction Bias",
    "kind": "cognitive_bias",
    "description": (
        "In joint evaluation, inflate the judged gap between two options by a "
        "strength-scaled portion of their declared low-use-relevance feature gap."
    ),
    "required_inputs": ["options", "attribute_use_relevance", "evaluation_mode"],
    "state_fields": ["rounds", "cumulative_metric", "last_metric", "last_active"],
    "metric_name": "perceived_option_evaluation_gap",
    "metric_units": "evaluation-gap points on the supplied 0-100 compatible scales",
    "assumptions": [
        "Exactly two options are compared, each with a 0-100 use_value and a 0-100 comparison_value.",
        "attribute_use_relevance is an explicit task input in [0,1], not inferred from text.",
        "The comparison feature's contribution to the perceived gap is strength times its gap times its declared irrelevance, and applies only in joint evaluation.",
        "The strength-zero reference policy reports the absolute use-value gap; it is a comparator, not a claim of perfect rationality.",
    ],
    "limitations": [
        "This is an assumed, synthetic process equation, not an empirically fitted effect size or human-response model.",
        "The model uses one declared feature and cannot determine whether that feature truly matters in real use.",
        "Large comparison-feature differences can be genuinely useful information; only the explicitly declared low-relevance portion is treated as distortion here.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _bounded_number(value, label, lower, upper):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    number = float(value)
    if not isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{label} must be a finite number in [{lower}, {upper}]")
    return number


def _prior_state(context):
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    rounds = state.get("rounds", 0)
    cumulative = state.get("cumulative_metric", 0.0)
    if isinstance(rounds, bool) or not isinstance(rounds, int) or rounds < 0:
        raise ValueError("state.rounds must be a nonnegative integer")
    if isinstance(cumulative, bool) or not isinstance(cumulative, (int, float)):
        raise ValueError("state.cumulative_metric must be finite and nonnegative")
    cumulative = float(cumulative)
    if not isfinite(cumulative) or cumulative < 0:
        raise ValueError("state.cumulative_metric must be finite and nonnegative")
    last_metric = state.get("last_metric")
    if last_metric is not None:
        if isinstance(last_metric, bool) or not isinstance(last_metric, (int, float)):
            raise ValueError("state.last_metric must be finite and nonnegative or None")
        last_metric = float(last_metric)
        if not isfinite(last_metric) or last_metric < 0:
            raise ValueError("state.last_metric must be finite and nonnegative or None")
    last_active = state.get("last_active", False)
    if not isinstance(last_active, bool):
        raise ValueError("state.last_active must be a bool")
    return rounds, cumulative


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate a two-option task without mutating context or nested inputs."""
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    bias_strength = _bounded_number(strength, "strength", 0.0, 1.0)
    if "options" not in context:
        raise ValueError("missing required input: options")
    options = context["options"]
    if not isinstance(options, (list, tuple)) or len(options) != 2:
        raise ValueError("options must contain exactly two option dicts")

    use_values = []
    comparison_values = []
    for index, option in enumerate(options):
        if not isinstance(option, dict):
            raise ValueError(f"options[{index}] must be a dict")
        for field in ("use_value", "comparison_value"):
            if field not in option:
                raise ValueError(f"missing required input: options[{index}].{field}")
        use_values.append(_bounded_number(option["use_value"], f"options[{index}].use_value", 0.0, 100.0))
        comparison_values.append(
            _bounded_number(option["comparison_value"], f"options[{index}].comparison_value", 0.0, 100.0)
        )

    if "attribute_use_relevance" not in context:
        raise ValueError("missing required input: attribute_use_relevance")
    relevance = _bounded_number(context["attribute_use_relevance"], "attribute_use_relevance", 0.0, 1.0)
    if "evaluation_mode" not in context:
        raise ValueError("missing required input: evaluation_mode")
    mode = context["evaluation_mode"]
    if mode not in ("joint", "separate"):
        raise ValueError("evaluation_mode must be 'joint' or 'separate'")

    prior_rounds, prior_total = _prior_state(context)
    use_gap = abs(use_values[0] - use_values[1])
    feature_gap = abs(comparison_values[0] - comparison_values[1])
    irrelevant_fraction = 1.0 - relevance
    added_contrast = (
        bias_strength * irrelevant_fraction * feature_gap
        if mode == "joint"
        else 0.0
    )
    metric = use_gap + added_contrast
    active = bool(mode == "joint" and bias_strength > 0.0 and irrelevant_fraction > 0.0 and feature_gap > 0.0)
    next_state = {
        "rounds": prior_rounds + 1,
        "cumulative_metric": prior_total + metric,
        "last_metric": metric,
        "last_active": active,
    }
    trace = [
        "Reference gap=abs(use_value_1-use_value_2)="
        f"abs({use_values[0]:g}-{use_values[1]:g})={use_gap:g}; "
        f"feature_gap=abs(comparison_value_1-comparison_value_2)={feature_gap:g}; "
        f"added_contrast={bias_strength:g}*{irrelevant_fraction:g}*{feature_gap:g}"
        f"{(' (joint)' if mode == 'joint' else ' (zero: separate mode)')}={added_contrast:g}; "
        f"metric={metric:g}. Relevance={relevance:g}; mode={mode}; active={active}."
    ]
    return {"metric": metric, "active": active, "state": next_state, "trace": trace}


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"rounds": 0, "cumulative_metric": 0.0, "last_metric": None, "last_active": False},
            "contexts": [
                {
                    "options": [
                        {"use_value": 60, "comparison_value": 20},
                        {"use_value": 55, "comparison_value": 80},
                    ],
                    "attribute_use_relevance": 0.1,
                    "evaluation_mode": "joint",
                }
            ],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"rounds": 0, "cumulative_metric": 0.0, "last_metric": None, "last_active": False},
            "contexts": [
                {
                    "options": [
                        {"use_value": 60, "comparison_value": 20},
                        {"use_value": 55, "comparison_value": 80},
                    ],
                    "attribute_use_relevance": 0.1,
                    "evaluation_mode": "separate",
                }
            ],
            "expectation": "equal",
        },
    ]
