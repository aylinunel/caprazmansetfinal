import copy
import math

import pytest

from mechanisms import false_consensus_effect as mechanism


def _run(context, strength):
    """Call evaluate directly with the contract's reserved defaults."""
    prepared = copy.deepcopy(context)
    prepared.setdefault("state", {})
    prepared.setdefault("peer_states", [])
    prepared.setdefault("round_index", 0)
    prepared.setdefault("agent_index", 0)
    prepared.setdefault("uniform", 0.5)
    return mechanism.evaluate(prepared, strength)


def test_positive_projection_matches_numeric_pseudocount_oracle():
    context = {"own_position": "A", "peer_positions": ["A", "B", "B", "B", "B"]}
    result = _run(context, 0.8)
    # q=1/5 and projection mass=4*.8=3.2: (5*.2+3.2)/(5+3.2)=4.2/8.2.
    assert result["metric"] == pytest.approx(4.2 / 8.2)
    assert result["metric"] > 1 / 5
    assert result["active"] is True
    assert math.isfinite(result["metric"])


def test_boundary_without_owned_position_equals_strength_zero_reference():
    context = {"own_position": None, "peer_positions": ["A", "B", "B", "B", "B"]}
    biased = _run(context, 0.8)
    reference = _run(context, 0.0)
    assert biased["metric"] == reference["metric"] == 1 / 5
    assert biased["active"] is False


def test_zero_strength_reproduces_observed_own_agreement_reference():
    context = {"own_position": "B", "peer_positions": ["A", "B", "B", "A"]}
    result = _run(context, 0.0)
    assert result["metric"] == 1 / 2
    assert result["active"] is False
    assert result["state"]["reference_history"] == [1 / 2]


def test_missing_or_impossible_required_evidence_is_rejected():
    with pytest.raises(ValueError, match="required"):
        _run({"own_position": "A"}, 0.8)
    with pytest.raises(ValueError, match="non-empty"):
        _run({"own_position": "A", "peer_positions": []}, 0.8)
    with pytest.raises(ValueError, match="every peer"):
        _run({"own_position": "A", "peer_positions": ["A", "C"]}, 0.8)
    with pytest.raises(ValueError, match="own_position"):
        _run({"own_position": ["A"], "peer_positions": ["A"]}, 0.8)


def test_strength_validation_rejects_out_of_range_and_nonfinite_values():
    context = {"own_position": "A", "peer_positions": ["A", "B"]}
    for strength in (-0.1, 1.1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="strength"):
            _run(context, strength)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        "own_position": "A",
        "peer_positions": ["B", "B", "A"],
        "state": {"forecast_history": [0.25], "reference_history": [0.5], "memo": {"tag": "keep"}},
    }
    before = copy.deepcopy(context)
    first = _run(context, 0.8)
    second = _run(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["forecast_history"] == [0.25, first["metric"]]
    assert first["state"]["memo"] == {"tag": "keep"}
    assert first["state"] is not context["state"]
    assert first["trace"] and isinstance(first["trace"][0], str)
