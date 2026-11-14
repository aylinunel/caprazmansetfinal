from copy import deepcopy
import math

import pytest

from mechanisms import responsibility_framing as mechanism


def context(**overrides):
    values = {
        "process_complete": False,
        "responsibility_claim_available": True,
        "evidence_support": 0.20,
        "attribution_salience": 0.90,
        "process_salience": 0.40,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    values.update(overrides)
    return values


def test_positive_incomplete_process_can_flip_to_attribution_at_point_eight():
    situation = context()
    reference = mechanism.evaluate(situation, 0.0)
    framed = mechanism.evaluate(situation, 0.8)

    assert reference["metric"] == 0.0  # .90 × .20 = .18 <= .40
    assert framed["metric"] == 1.0  # .18 + .8 × .9 × .8 × .8 = .6408 > .40
    assert framed["active"] is True
    assert "Premature pressure" in framed["trace"][1]


def test_boundary_completed_process_matches_zero_strength_reference():
    situation = context(process_complete=True)
    reference = mechanism.evaluate(situation, 0.0)
    boundary = mechanism.evaluate(situation, 0.8)

    assert reference["metric"] == boundary["metric"] == 0.0
    assert boundary["active"] is False
    assert "pressure=0" in boundary["trace"][2]


def test_zero_strength_uses_explicit_reference_choice_oracle():
    # A sufficiently supported claim wins when its support-weighted salience
    # exceeds process salience, even at the reference setting.
    situation = context(
        process_complete=True,
        evidence_support=0.90,
        attribution_salience=0.80,
        process_salience=0.50,
    )
    result = mechanism.evaluate(situation, 0.0)

    assert result["metric"] == 1.0  # .80 × .90 = .72 > .50
    assert result["active"] is False
    assert result["state"]["last_frame"] == "attribution"


def test_missing_or_impossible_evidence_is_rejected():
    missing = context()
    del missing["evidence_support"]
    with pytest.raises(ValueError, match="missing required"):
        mechanism.evaluate(missing, 0.8)

    with pytest.raises(ValueError, match="evidence_support"):
        mechanism.evaluate(context(evidence_support=1.01), 0.8)
    with pytest.raises(ValueError, match="process_complete"):
        mechanism.evaluate(context(process_complete=1), 0.8)


def test_strength_validation_rejects_nonfinite_and_out_of_range_values():
    for invalid in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="strength"):
            mechanism.evaluate(context(), invalid)


def test_repeatable_and_nonmutating_with_nested_prior_state():
    situation = context(state={"frame_history": ["process"], "last_frame": "process", "meta": {"tag": ["keep"]}})
    before = deepcopy(situation)
    first = mechanism.evaluate(situation, 0.8)
    second = mechanism.evaluate(situation, 0.8)

    assert situation == before
    assert first == second
    assert situation["state"]["frame_history"] == ["process"]
    assert first["state"]["frame_history"] == ["process", "attribution"]
    assert first["state"]["meta"] == {"tag": ["keep"]}
    assert isinstance(first["metric"], (int, float)) and math.isfinite(first["metric"])


def test_no_available_responsibility_claim_removes_mechanism_and_forces_process_frame():
    situation = context(responsibility_claim_available=False, process_salience=0.0)
    reference = mechanism.evaluate(situation, 0.0)
    result = mechanism.evaluate(situation, 0.8)

    assert result["metric"] == reference["metric"] == 0.0
    assert result["active"] is False


def test_scenarios_include_required_positive_and_boundary_cases():
    names = {scenario["name"] for scenario in mechanism.scenarios()}
    assert {"positive", "boundary"} <= names
