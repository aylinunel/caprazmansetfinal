"""A hypothetical, task-level model of threat-linked information avoidance."""
import math


METADATA = {
    "id": "ostrich_effect",
    "name": "Ostrich Effect",
    "kind": "cognitive_bias",
    "description": (
        "When a report is explicitly marked threatening and reading it is expected "
        "to be uncomfortable, an illustrative discomfort term can raise the "
        "threshold for accessing it. This models a choice, not a belief or diagnosis."
    ),
    # This is the only phase-independent top-level task key. Its schema is checked below.
    "required_inputs": ["information"],
    "state_fields": ["information_value_accessed", "reports_read", "avoidance_choices"],
    "metric_name": "cumulative_task_relevant_information_accessed",
    "metric_units": "hypothetical task-utility points of report information accessed",
    "assumptions": [
        "decision_value, read_cost, and discomfort are commensurable hypothetical utility points",
        "the reference policy reads when decision value is at least reading cost",
        "strength scales only the discomfort-related threshold term and is not calibrated",
        "practical_delay means a delay is justified for reasons outside threat avoidance",
    ],
    "limitations": [
        "This compact choice model is illustrative and is not an empirical estimate or detector.",
        "Explicit scenario fields stand in for a hypothetical decision-maker's stated task inputs; no motive is inferred.",
        "It omits social context, alternative coping strategies, uncertainty, and downstream consequences.",
        "It distinguishes information access from beliefs about whether a threat exists.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}


def _finite_nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"information.{name} must be a finite nonnegative number")
    return float(value)


def _read_state(context):
    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be an object")
    unknown = set(state) - set(METADATA["state_fields"])
    if unknown:
        raise ValueError(f"unknown ostrich_effect state fields: {sorted(unknown)}")
    accessed = state.get("information_value_accessed", 0.0)
    if isinstance(accessed, bool) or not isinstance(accessed, (int, float)) or not math.isfinite(accessed) or accessed < 0:
        raise ValueError("state.information_value_accessed must be finite and nonnegative")
    counts = []
    for key in ("reports_read", "avoidance_choices"):
        value = state.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"state.{key} must be a nonnegative integer")
        counts.append(value)
    return float(accessed), counts[0], counts[1]


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one report without mutating the supplied context or its nested state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError("strength must be finite and in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    if "information" not in context:
        raise ValueError("missing required task input information")
    info = context["information"]
    if not isinstance(info, dict):
        raise ValueError("information must be an object")
    required = {"decision_value", "read_cost", "threatening", "discomfort", "practical_delay"}
    missing = required - set(info)
    if missing:
        raise ValueError(f"information missing fields: {sorted(missing)}")
    decision_value = _finite_nonnegative(info["decision_value"], "decision_value")
    read_cost = _finite_nonnegative(info["read_cost"], "read_cost")
    discomfort = _finite_nonnegative(info["discomfort"], "discomfort")
    if not isinstance(info["threatening"], bool):
        raise ValueError("information.threatening must be a boolean")
    if not isinstance(info["practical_delay"], bool):
        raise ValueError("information.practical_delay must be a boolean")

    prior_accessed, prior_read, prior_avoided = _read_state(context)
    reference_reads = decision_value >= read_cost
    effect_condition = info["threatening"] and not info["practical_delay"]
    avoidance_term = float(strength) * discomfort if effect_condition else 0.0
    # The only intervention is a threat- and discomfort-dependent increase in the
    # required value of reading. It is not a generic belief update or fixed penalty.
    reads = decision_value - avoidance_term >= read_cost
    active = bool(effect_condition and reference_reads and not reads)
    next_accessed = prior_accessed + (decision_value if reads else 0.0)
    next_read = prior_read + int(reads)
    next_avoided = prior_avoided + int(active)
    trace = [
        f"Reference: read iff decision_value ({decision_value:g}) >= read_cost ({read_cost:g}); "
        f"reference_reads={reference_reads}.",
        f"Threat-linked avoidance term={strength:g}*{discomfort:g}={avoidance_term:g} "
        f"(applied={effect_condition}); read iff decision_value - term >= read_cost; reads={reads}.",
        "Practical delay bypasses this mechanism; no inferred threat belief or motive is represented.",
    ]
    return {
        "metric": next_accessed,
        "active": active,
        "state": {
            "information_value_accessed": next_accessed,
            "reports_read": next_read,
            "avoidance_choices": next_avoided,
        },
        "trace": trace,
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"information_value_accessed": 0.0, "reports_read": 0, "avoidance_choices": 0},
            "contexts": [
                {"information": {"decision_value": 3.0, "read_cost": 1.0, "threatening": True, "discomfort": 4.0, "practical_delay": False}},
                {"information": {"decision_value": 2.5, "read_cost": 0.5, "threatening": True, "discomfort": 3.0, "practical_delay": False}},
                {"information": {"decision_value": 2.0, "read_cost": 0.5, "threatening": True, "discomfort": 2.5, "practical_delay": False}},
            ],
            "expectation": "decrease",
        },
        {
            "name": "boundary",
            "initial_state": {"information_value_accessed": 0.0, "reports_read": 0, "avoidance_choices": 0},
            # Nonthreatening information removes a necessary condition; discomfort alone is insufficient.
            "contexts": [
                {"information": {"decision_value": 3.0, "read_cost": 1.0, "threatening": False, "discomfort": 4.0, "practical_delay": False}},
                {"information": {"decision_value": 2.0, "read_cost": 0.5, "threatening": False, "discomfort": 2.5, "practical_delay": False}},
            ],
            "expectation": "equal",
        },
    ]
