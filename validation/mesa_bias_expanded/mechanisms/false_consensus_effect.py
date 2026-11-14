"""Illustrative, synthetic-only false-consensus forecast mechanism.

This models an explicitly stated agent's projection into a forecast of peer
agreement. It is not a detector or an empirically fitted psychology model.
"""
from __future__ import annotations

import copy
import math
from numbers import Real


METADATA = {
    "id": "false_consensus_effect",
    "name": "False Consensus Effect",
    "kind": "cognitive_bias",
    "description": (
        "Forecast peer agreement by adding strength-scaled pseudo-observation "
        "mass to the agent's explicitly supplied own position."
    ),
    "required_inputs": ["own_position", "peer_positions"],
    "state_fields": ["forecast_history", "reference_history"],
    "metric_name": "forecast_own_position_agreement",
    "metric_units": "fraction of peers forecast to agree with the stated own position (0–1); without an own position, fraction forecast to choose A",
    "assumptions": [
        "Peer positions are supplied observations, not inferred from text or behavior.",
        "The illustrative projection mass is four peer-equivalent pseudo-observations at strength 1.",
        "The strength parameter scales this assumed projection mass linearly and is not a prevalence or calibrated confidence.",
        "The strength-zero reference forecast is the observed sample proportion.",
    ],
    "limitations": [
        "Synthetic process illustration only; not empirically validated or fitted.",
        "A small supplied peer sample may not represent the audience.",
        "No hidden beliefs, motives, pluralistic ignorance, or media framing are inferred.",
        "The metric is a forecast, not actual agreement or forecast accuracy.",
    ],
    "empirically_validated": False,
    "synthetic_only": True,
}

_CHOICES = {"A", "B"}
_PROJECTION_MASS_AT_FULL_STRENGTH = 4.0


def _valid_position(value: object) -> bool:
    return isinstance(value, str) and value in _CHOICES


def _finite_number(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(float(value))


def evaluate(context: dict, strength: float) -> dict:
    """Return one-round forecast and an updated, nonmutating history state.

    Let q be the observed fraction of peer positions matching the explicitly
    stated own position. At strength s, forecast agreement is
    (n*q + 4*s)/(n + 4*s): an own-position pseudo-count contribution. When no
    own position is supplied, that necessary condition is absent and the
    reference forecast for A is returned unchanged.
    """
    if not _finite_number(strength) or not 0.0 <= float(strength) <= 1.0:
        raise ValueError("strength must be a finite number in [0, 1]")
    if not isinstance(context, dict):
        raise ValueError("context must be a dict")
    if "own_position" not in context or "peer_positions" not in context:
        raise ValueError("own_position and peer_positions are required inputs")

    own_position = context["own_position"]
    if own_position is not None and not _valid_position(own_position):
        raise ValueError("own_position must be 'A', 'B', or None")
    peer_positions = context["peer_positions"]
    if not isinstance(peer_positions, (list, tuple)) or not peer_positions:
        raise ValueError("peer_positions must be a non-empty list or tuple")
    if any(not _valid_position(position) for position in peer_positions):
        raise ValueError("every peer position must be 'A' or 'B'")

    state = context.get("state", {})
    if not isinstance(state, dict):
        raise ValueError("state must be a dict")
    if "forecast_history" in state and (
        not isinstance(state["forecast_history"], list)
        or any(not _finite_number(x) or not 0.0 <= float(x) <= 1.0 for x in state["forecast_history"])
    ):
        raise ValueError("state.forecast_history must be a list of fractions in [0, 1]")
    if "reference_history" in state and (
        not isinstance(state["reference_history"], list)
        or any(not _finite_number(x) or not 0.0 <= float(x) <= 1.0 for x in state["reference_history"])
    ):
        raise ValueError("state.reference_history must be a list of fractions in [0, 1]")

    n = len(peer_positions)
    if own_position is None:
        # Boundary: without an owned position, agreement-with-self is undefined;
        # use the documented neutral A-share reference task instead.
        reference = sum(position == "A" for position in peer_positions) / n
        metric = reference
        active = False
        explanation = (
            "own_position=None removes the ownership condition; metric is the "
            "observed A share and equals the strength-zero reference."
        )
    else:
        matching = sum(position == own_position for position in peer_positions)
        reference = matching / n
        projection_mass = _PROJECTION_MASS_AT_FULL_STRENGTH * float(strength)
        metric = (n * reference + projection_mass) / (n + projection_mass)
        active = metric != reference
        explanation = (
            f"{matching}/{n} observed peers match own_position={own_position}; "
            f"metric=({n}*{reference:.12g}+4*{float(strength):.12g})/"
            f"({n}+4*{float(strength):.12g})={metric:.12g}."
        )

    next_state = copy.deepcopy(state)
    next_state.setdefault("forecast_history", [])
    next_state.setdefault("reference_history", [])
    next_state["forecast_history"].append(float(metric))
    next_state["reference_history"].append(float(reference))
    return {
        "metric": float(metric),
        "active": bool(active),
        "state": next_state,
        "trace": [explanation],
    }


def scenarios() -> list[dict]:
    return [
        {
            "name": "positive",
            "initial_state": {"forecast_history": [], "reference_history": []},
            "contexts": [{"own_position": "A", "peer_positions": ["A", "B", "B", "B", "B"]}],
            "expectation": "increase",
        },
        {
            "name": "boundary",
            "initial_state": {"forecast_history": [], "reference_history": []},
            "contexts": [{"own_position": None, "peer_positions": ["A", "B", "B", "B", "B"]}],
            "expectation": "equal",
        },
    ]
