import copy
import math

import pytest

from mechanisms import fundamental_attribution_error as fae


def context(**overrides):
    result = {
        "dispositional_evidence": 2.0,
        "situational_constraint": 8.0,
        "context_evidence_observed": True,
        "constraint_relevant": True,
        "character_judgment": True,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    result.update(overrides)
    return result


def test_positive_scenario_reduces_situational_attribution_and_matches_numeric_oracle():
    data = fae.scenarios()[0]["contexts"][0]
    baseline = fae.evaluate({**data, "state": {}}, 0.0)
    result = fae.evaluate({**data, "state": {}}, 0.8)
    assert baseline["metric"] == pytest.approx(8 / 10)
    # S is attenuated to 8*(1-.8)=1.6, so the share is 1.6/(2+1.6)=4/9.
    assert result["metric"] == pytest.approx(4 / 9)
    assert result["metric"] < baseline["metric"]
    assert result["active"] is True


def test_boundary_without_relevant_context_matches_reference_at_strength_point_eight():
    data = fae.scenarios()[1]["contexts"][0]
    at_zero = fae.evaluate({**data, "state": {}}, 0.0)
    at_point_eight = fae.evaluate({**data, "state": {}}, 0.8)
    assert at_zero["metric"] == 0.0
    assert at_point_eight["metric"] == at_zero["metric"]
    assert at_point_eight["active"] is False


def test_zero_strength_reproduces_proportional_reference_rule():
    result = fae.evaluate(context(), 0.0)
    assert result["metric"] == pytest.approx(8.0 / (2.0 + 8.0))
    assert result["active"] is False
    assert result["state"]["judgment_count"] == 1


def test_missing_required_evidence_is_rejected_not_scored_as_zero():
    data = context()
    del data["situational_constraint"]
    with pytest.raises(ValueError, match="missing required input"):
        fae.evaluate(data, 0.8)


def test_unobserved_context_evidence_is_rejected():
    with pytest.raises(ValueError, match="must be observed explicitly"):
        fae.evaluate(context(context_evidence_observed=False), 0.8)


def test_invalid_values_and_strength_are_rejected():
    with pytest.raises(ValueError, match="finite nonnegative"):
        fae.evaluate(context(dispositional_evidence=float("nan")), 0.8)
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        fae.evaluate(context(), 1.01)
    with pytest.raises(ValueError, match="must be a bool"):
        fae.evaluate(context(constraint_relevant=1), 0.8)


def test_deterministic_and_nonmutating_with_nested_prior_state():
    data = context(state={"judgment_count": 2, "cumulative_situational_share_sum": 1.25,
                          "last_situational_share": 0.5}, peer_states=[{"nested": [1, 2]}])
    before = copy.deepcopy(data)
    first = fae.evaluate(data, 0.8)
    second = fae.evaluate(data, 0.8)
    assert first == second
    assert data == before
    assert first["state"] == {
        "judgment_count": 3,
        "cumulative_situational_share_sum": pytest.approx(1.25 + 4 / 9),
        "last_situational_share": pytest.approx(4 / 9),
    }
    assert math.isfinite(first["metric"])
