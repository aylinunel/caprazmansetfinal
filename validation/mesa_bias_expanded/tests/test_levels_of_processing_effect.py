"""Direct contract and numeric-oracle tests for the illustrative memory model."""
from copy import deepcopy
import math

import pytest

from mechanisms import levels_of_processing_effect as lop


def step(context, state=None, strength=0.8):
    supplied = deepcopy(context)
    supplied.update({
        "state": deepcopy({} if state is None else state),
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.25,
    })
    return lop.evaluate(supplied, strength)


def sigmoid(value):
    return 1.0 / (1.0 + math.exp(-value))


def study_then_probe(depth, strength=0.8, exposure=1.0):
    studied = step({
        "action": "study", "item_id": "item-A",
        "exposure_units": exposure, "processing_depth": depth,
    }, strength=strength)
    probed = step({"action": "probe", "item_id": "item-A"},
                  state=studied["state"], strength=strength)
    return studied, probed


def test_numeric_oracle_matches_exposure_plus_elaboration_logistic_readout():
    studied, probed = study_then_probe(depth=1.0, strength=0.8, exposure=1.0)
    # trace = 1 * (1 + 1.5 * .8 * 1) = 2.2; criterion = 1.5.
    assert studied["state"]["items"]["item-A"]["trace"] == pytest.approx(2.2)
    assert probed["metric"] == pytest.approx(sigmoid(2.2 - 1.5))
    assert probed["active"] is True
    assert probed["state"]["events"] == 2


def test_positive_scenario_recall_exceeds_strength_zero_with_exposure_controlled():
    _, intervention = study_then_probe(depth=1.0, strength=0.8)
    _, reference = study_then_probe(depth=1.0, strength=0.0)
    assert intervention["metric"] > reference["metric"]
    assert reference["metric"] == pytest.approx(sigmoid(1.0 - 1.5))


def test_zero_semantic_depth_removes_necessary_condition_and_matches_reference():
    study, probe = study_then_probe(depth=0.0, strength=0.8)
    _, reference = study_then_probe(depth=0.0, strength=0.0)
    assert study["state"]["items"]["item-A"]["trace"] == pytest.approx(1.0)
    assert study["active"] is False
    assert probe["metric"] == pytest.approx(reference["metric"])
    assert probe["metric"] == pytest.approx(sigmoid(1.0 - 1.5))
    assert probe["active"] is False


def test_strength_zero_is_the_exposure_only_reference_policy():
    study, probe = study_then_probe(depth=0.75, strength=0.0, exposure=2.0)
    item = study["state"]["items"]["item-A"]
    assert item["reference_trace"] == pytest.approx(2.0)
    assert item["trace"] == pytest.approx(item["reference_trace"])
    assert probe["metric"] == pytest.approx(sigmoid(2.0 - 1.5))


def test_missing_or_invalid_phase_specific_evidence_is_rejected():
    with pytest.raises(ValueError, match="action"):
        lop.evaluate({"item_id": "x"}, 0.8)
    with pytest.raises(ValueError, match="item_id"):
        lop.evaluate({"action": "study", "exposure_units": 1, "processing_depth": 1}, 0.8)
    with pytest.raises(ValueError, match="exposure_units"):
        step({"action": "study", "item_id": "x", "processing_depth": 1})
    with pytest.raises(ValueError, match="processing_depth"):
        step({"action": "study", "item_id": "x", "exposure_units": 1})
    with pytest.raises(ValueError, match="cannot probe"):
        step({"action": "probe", "item_id": "unseen"})
    with pytest.raises(ValueError, match="processing_depth"):
        step({"action": "study", "item_id": "x", "exposure_units": 1, "processing_depth": 1.1})
    with pytest.raises(ValueError, match="strength"):
        step({"action": "study", "item_id": "x", "exposure_units": 1, "processing_depth": 1}, strength=float("nan"))


def test_repeated_chronological_study_events_accumulate_separate_exposure_and_elaboration():
    first = step({"action": "study", "item_id": "item-A", "exposure_units": 0.5, "processing_depth": 0.5})
    second = step({"action": "study", "item_id": "item-A", "exposure_units": 0.5, "processing_depth": 1.0}, state=first["state"])
    probed = step({"action": "probe", "item_id": "item-A"}, state=second["state"])
    item = probed["state"]["items"]["item-A"]
    assert item["reference_trace"] == pytest.approx(1.0)
    assert item["elaboration_dose"] == pytest.approx(0.75)
    assert item["trace"] == pytest.approx(1.0 + 1.5 * 0.8 * 0.75)
    assert probed["metric"] == pytest.approx(sigmoid(1.9 - 1.5))
    assert probed["state"]["events"] == 3


def test_evaluation_is_deterministic_and_does_not_mutate_context_or_nested_state():
    original_state = {"items": {}, "events": 0}
    context = {"action": "study", "item_id": "item-A", "exposure_units": 1.0,
               "processing_depth": 0.6, "state": original_state,
               "peer_states": [{"nested": [1, 2]}], "round_index": 3,
               "agent_index": 1, "uniform": 0.9}
    before = deepcopy(context)
    a = lop.evaluate(context, 0.8)
    b = lop.evaluate(context, 0.8)
    assert context == before
    assert a == b
    assert original_state == {"items": {}, "events": 0}
    assert a["state"] is not original_state
    assert a["trace"] and isinstance(a["active"], bool)


def test_metadata_and_scenarios_keep_conditional_fields_phase_specific():
    assert lop.METADATA["required_inputs"] == ["action", "item_id"]
    scenarios = {scenario["name"]: scenario for scenario in lop.scenarios()}
    assert {"positive", "boundary"}.issubset(scenarios)
    reserved = {"state", "peer_states", "uniform", "round_index", "agent_index"}
    for scenario in scenarios.values():
        assert scenario["contexts"]
        assert not any(reserved.intersection(context) for context in scenario["contexts"])
    assert scenarios["positive"]["contexts"][0]["processing_depth"] > 0
    assert scenarios["boundary"]["contexts"][0]["processing_depth"] == 0
