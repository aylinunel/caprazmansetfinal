import copy
import math

import pytest

from mechanisms import metaphorical_framing as mf


def context(**overrides):
    value = {
        "event_id": "bridge-closure",
        "interpretations": [
            {"id": "routine-maintenance", "event_relation": "scheduled-care", "literal_support": 0.8, "response_priority": 0.2},
            {"id": "system-under-siege", "event_relation": "defensive-conflict", "literal_support": 0.65, "response_priority": 0.9},
        ],
        "metaphor": {
            "source_schema": "siege",
            "mapped_event_relation": "defensive-conflict",
            "mapping_note": "closure maps to defensive conflict in this hypothetical framing",
        },
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
    }
    value.update(overrides)
    return value


def run_sequence(inputs, strength):
    state = {}
    result = None
    for round_index, item in enumerate(inputs):
        current = copy.deepcopy(item)
        current.update(state=state, peer_states=[], round_index=round_index, agent_index=0)
        result = mf.evaluate(current, strength)
        state = result["state"]
    return result


def test_positive_frame_selects_mapped_relation_with_numeric_oracle():
    result = mf.evaluate(context(), 0.8)
    # Scores: routine=.2*.8 + .8*0=.16; siege=.2*.65 + .8*1=.93.
    assert result["state"]["last_interpretation"] == "system-under-siege"
    assert result["metric"] == pytest.approx(0.9)
    assert result["active"] is True
    assert math.isfinite(result["metric"])


def test_boundary_without_metaphor_matches_literal_reference_metric():
    no_frame = context(metaphor=None)
    framed = context()
    assert mf.evaluate(no_frame, 0.8)["metric"] == mf.evaluate(framed, 0.0)["metric"] == pytest.approx(0.2)
    assert mf.evaluate(no_frame, 0.8)["active"] is False


def test_zero_strength_is_literal_support_reference_even_with_frame():
    result = mf.evaluate(context(), 0)
    assert result["state"]["last_interpretation"] == "routine-maintenance"
    assert result["metric"] == pytest.approx(0.2)
    assert result["active"] is False


def test_invalid_missing_or_impossible_evidence_is_rejected():
    missing = context()
    del missing["interpretations"]
    with pytest.raises(ValueError, match="missing required input"):
        mf.evaluate(missing, 0.8)
    impossible = context(interpretations=[])
    with pytest.raises(ValueError, match="at least two"):
        mf.evaluate(impossible, 0.8)
    bad_support = context()
    bad_support["interpretations"][0]["literal_support"] = float("nan")
    with pytest.raises(ValueError, match="finite number"):
        mf.evaluate(bad_support, 0.8)
    with pytest.raises(ValueError, match="strength"):
        mf.evaluate(context(), 1.1)


def test_deterministic_and_nonmutating_for_nested_input_and_state():
    prior_state = {"history": [{"event_id": "earlier", "selected_interpretation": "routine-maintenance"}], "custom": {"keep": [1, 2]}}
    input_context = context(state=prior_state)
    before = copy.deepcopy(input_context)
    first = mf.evaluate(input_context, 0.8)
    second = mf.evaluate(input_context, 0.8)
    assert input_context == before
    assert first == second
    assert first["state"]["history"][0] == prior_state["history"][0]
    first["state"]["custom"]["keep"].append(3)
    assert input_context == before
    assert prior_state["custom"]["keep"] == [1, 2]


def test_chronological_calls_carry_complete_state():
    sequence = [context(), context(event_id="second-event", metaphor=None)]
    result = run_sequence(sequence, 0.8)
    assert len(result["state"]["history"]) == 2
    assert result["state"]["history"][0]["selected_interpretation"] == "system-under-siege"
    assert result["state"]["last_event_id"] == "second-event"
    assert result["state"]["last_interpretation"] == "routine-maintenance"
    assert result["state"]["frame_active"] is False


def test_scenarios_follow_contract_expectations():
    cases = {case["name"]: case for case in mf.scenarios()}
    positive, boundary = cases["positive"], cases["boundary"]
    assert positive["expectation"] == "increase"
    assert boundary["expectation"] == "equal"
    assert run_sequence(positive["contexts"], 0.8)["metric"] > run_sequence(positive["contexts"], 0)["metric"]
    assert run_sequence(boundary["contexts"], 0.8)["metric"] == run_sequence(boundary["contexts"], 0)["metric"]
