from copy import deepcopy
import math

import pytest

from mechanisms import strawman


POSITIVE = {
    "actual_commitment": 0.4,
    "actual_qualification": 0.8,
    "reconstruction_commitment": 0.9,
    "reconstruction_qualification": 0.1,
}


def run_step(inputs, strength, state=None):
    context = deepcopy(inputs)
    context.update(
        {
            "state": {} if state is None else deepcopy(state),
            "peer_states": [],
            "round_index": 0,
            "agent_index": 0,
            "uniform": 0.5,
        }
    )
    return strawman.evaluate(context, strength)


def test_positive_numeric_oracle_and_reconstructed_critique_target():
    result = run_step(POSITIVE, 0.8)
    # target=(.4,.8)+.8*((.9,.1)-(.4,.8))=(.8,.24); mean L1 distortion=.48
    assert result["metric"] == pytest.approx(0.48)
    assert result["active"] is True
    assert result["state"]["critique_target"] == pytest.approx(
        {"commitment": 0.8, "qualification": 0.24}
    )
    assert len(result["trace"]) >= 1


def test_boundary_without_either_necessary_caricature_condition_matches_reference():
    context = {
        "actual_commitment": 0.4,
        "actual_qualification": 0.8,
        "reconstruction_commitment": 0.4,
        "reconstruction_qualification": 0.8,
    }
    baseline = run_step(context, 0.0)
    treated = run_step(context, 0.8)
    assert treated["metric"] == pytest.approx(baseline["metric"])
    assert treated["metric"] == 0.0
    assert treated["active"] is False
    assert treated["state"]["critique_target"] == baseline["state"]["critique_target"]


def test_strength_zero_is_explicit_fair_reference_even_with_caricature_candidate():
    result = run_step(POSITIVE, 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["reconstructed_commitment"] == pytest.approx(0.4)
    assert result["state"]["reconstructed_qualification"] == pytest.approx(0.8)
    assert result["active"] is False


def test_missing_or_impossible_required_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required"):
        run_step({k: v for k, v in POSITIVE.items() if k != "actual_qualification"}, 0.8)
    invalid = dict(POSITIVE, reconstruction_commitment=1.1)
    with pytest.raises(ValueError, match="finite number"):
        run_step(invalid, 0.8)
    with pytest.raises(ValueError, match="strength"):
        run_step(POSITIVE, math.nan)


def test_determinism_and_nonmutation_of_context_and_nested_state():
    initial = {"memo": {"labels": ["keep"]}}
    context = deepcopy(POSITIVE)
    context["state"] = deepcopy(initial)
    context["peer_states"] = [{"opaque": [1, 2]}]
    before = deepcopy(context)
    first = strawman.evaluate(context, 0.8)
    second = strawman.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["memo"] == initial["memo"]
    first["state"]["memo"]["labels"].append("changed")
    assert context["state"] == initial
    assert second["state"]["memo"] == initial["memo"]


def test_qualification_removal_alone_is_a_concept_specific_trigger():
    context = {
        "actual_commitment": 0.6,
        "actual_qualification": 0.9,
        "reconstruction_commitment": 0.6,
        "reconstruction_qualification": 0.4,
    }
    result = run_step(context, 0.5)
    assert result["state"]["critique_target"]["qualification"] == pytest.approx(0.65)
    assert result["metric"] == pytest.approx(0.125)
    assert result["active"] is True
