from copy import deepcopy

import pytest

from mechanisms import commitment_bias


def _run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, raw in enumerate(contexts):
        context = deepcopy(raw)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = commitment_bias.evaluate(context, strength)
        outputs.append(result)
        state = deepcopy(result["state"])
    return outputs


def test_positive_sequential_scenario_changes_final_choice():
    case = commitment_bias.scenarios()[0]
    biased = _run(case["contexts"], 0.8, case["initial_state"])
    reference = _run(case["contexts"], 0.0, case["initial_state"])
    assert biased[-1]["metric"] == 1.0
    assert reference[-1]["metric"] == 0.0
    assert biased[-1]["active"] is True
    assert biased[0]["state"]["publicly_committed_to_stay"] is True


def test_numeric_oracle_for_commitment_credit_and_choice():
    outputs = _run(commitment_bias.scenarios()[0]["contexts"], 0.8)
    step = outputs[1]
    assert step["metric"] == 1.0  # stay, despite current 3 < 4 values
    assert step["active"] is True
    assert any("credit=2.4" in line for line in step["trace"])
    assert any("Adjusted stay=5.4, exit=4" in line for line in step["trace"])


def test_boundary_without_prior_public_commitment_matches_reference():
    case = commitment_bias.scenarios()[1]
    biased = _run(case["contexts"], 0.8, case["initial_state"])
    reference = _run(case["contexts"], 0.0, case["initial_state"])
    assert biased[-1]["metric"] == reference[-1]["metric"] == 0.0
    assert biased[-1]["active"] is False


def test_strength_zero_is_prospective_value_reference():
    context = {
        "stay_value": -2,
        "exit_value": 1,
        "public_visibility": 1,
        "announce_commitment": False,
        "state": {
            "choice": "stay",
            "publicly_committed_to_stay": True,
            "commitment_round": 0,
        },
    }
    result = commitment_bias.evaluate(context, 0.0)
    assert result["metric"] == 0.0
    assert result["state"]["choice"] == "exit"
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    incomplete = {
        "stay_value": 2,
        "exit_value": 1,
        "public_visibility": 1,
        "state": {},
    }
    with pytest.raises(ValueError, match="announce_commitment"):
        commitment_bias.evaluate(incomplete, 0.5)
    impossible = {
        "stay_value": float("nan"),
        "exit_value": 1,
        "public_visibility": 1,
        "announce_commitment": False,
        "state": {},
    }
    with pytest.raises(ValueError, match="stay_value"):
        commitment_bias.evaluate(impossible, 0.5)
    out_of_range = dict(impossible, stay_value=2, public_visibility=1.1)
    with pytest.raises(ValueError, match="public_visibility"):
        commitment_bias.evaluate(out_of_range, 0.5)


def test_deterministic_and_nonmutating_with_nested_state():
    context = {
        "stay_value": 3,
        "exit_value": 4,
        "public_visibility": 1,
        "announce_commitment": False,
        "state": {
            "choice": "stay",
            "publicly_committed_to_stay": True,
            "commitment_round": 0,
            "extra_history": {"note": ["kept"]},
        },
        "peer_states": [{"nested": [1, 2]}],
        "round_index": 1,
        "agent_index": 3,
        "uniform": 0.25,
    }
    before = deepcopy(context)
    first = commitment_bias.evaluate(context, 0.8)
    second = commitment_bias.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] == {
        "choice": "stay",
        "publicly_committed_to_stay": True,
        "commitment_round": 0,
    }


def test_zero_visibility_removes_consistency_effect():
    context = {
        "stay_value": 3,
        "exit_value": 4,
        "public_visibility": 0,
        "announce_commitment": False,
        "state": {
            "choice": "stay",
            "publicly_committed_to_stay": True,
            "commitment_round": 0,
        },
    }
    assert commitment_bias.evaluate(context, 0.8)["metric"] == 0.0


def test_strength_and_visibility_validation():
    context = {
        "stay_value": 1,
        "exit_value": 2,
        "public_visibility": 0.5,
        "announce_commitment": False,
        "state": {},
    }
    for strength in (-0.01, 1.01, float("inf"), float("nan")):
        with pytest.raises(ValueError):
            commitment_bias.evaluate(context, strength)
