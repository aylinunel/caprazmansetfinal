from copy import deepcopy

import pytest

from mechanisms import labeling


def context(labels=None):
    return {
        "actor_id": "actor-1",
        "factual_legitimacy": 0.5,
        "outlet_labels": labels or [
            {"outlet": "North", "label": "reform leader", "label_preset": 0.9},
            {"outlet": "South", "label": "power broker", "label_preset": 0.1},
        ],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_direction_and_task_specific_numeric_oracle():
    sample = context()
    baseline = labeling.evaluate(sample, 0.0)
    framed = labeling.evaluate(sample, 0.8)
    assert baseline["metric"] == 0.0
    # Shared evidence=.5; label presets=.9 and .1. At strength .8,
    # projected impressions=.82 and .18, hence spread=.64.
    assert framed["metric"] == pytest.approx(0.64)
    assert framed["metric"] > baseline["metric"]
    assert framed["active"] is True


def test_boundary_same_label_equals_strength_zero_reference():
    sample = context([
        {"outlet": "North", "label": "mayor", "label_preset": 0.6},
        {"outlet": "South", "label": "mayor", "label_preset": 0.6},
    ])
    assert labeling.evaluate(sample, 0.8)["metric"] == labeling.evaluate(sample, 0.0)["metric"] == 0.0
    assert labeling.evaluate(sample, 0.8)["active"] is False


def test_zero_strength_is_common_evidence_reference():
    result = labeling.evaluate(context(), 0.0)
    assert result["metric"] == 0.0
    assert result["active"] is False
    assert result["state"]["steps"] == 1
    assert "Strength-zero reference spread is 0" in result["trace"][0]


def test_missing_or_impossible_required_evidence_is_rejected():
    missing = context()
    del missing["factual_legitimacy"]
    with pytest.raises(ValueError, match="missing required evidence"):
        labeling.evaluate(missing, 0.8)
    impossible = context()
    impossible["outlet_labels"][0]["label_preset"] = 1.2
    with pytest.raises(ValueError, match="label_preset"):
        labeling.evaluate(impossible, 0.8)


def test_invalid_strength_and_insufficient_cross_outlet_evidence_rejected():
    with pytest.raises(ValueError, match="strength"):
        labeling.evaluate(context(), float("nan"))
    one_outlet = context()
    one_outlet["outlet_labels"] = one_outlet["outlet_labels"][:1]
    with pytest.raises(ValueError, match="at least two"):
        labeling.evaluate(one_outlet, 0.8)


def test_deterministic_nonmutating_and_state_is_carried_forward():
    sample = context()
    sample["state"] = {"steps": 4, "memo": {"keep": [1, 2]}}
    before = deepcopy(sample)
    first = labeling.evaluate(sample, 0.8)
    second = labeling.evaluate(sample, 0.8)
    assert sample == before
    assert first == second
    assert first["state"]["steps"] == 5
    assert first["state"]["memo"] == {"keep": [1, 2]}
    assert first["state"]["last_labels"] == ["reform leader", "power broker"]
