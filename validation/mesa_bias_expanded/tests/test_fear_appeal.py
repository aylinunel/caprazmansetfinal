from copy import deepcopy
import math

import pytest

from mechanisms import fear_appeal


POSITIVE = {
    "threat_language": True,
    "threat_salience": 0.8,
    "severity": 0.9,
    "stated_probability": 0.7,
    "evidence_supported_probability": 0.2,
    "response_capacity": 0.75,
}


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    results = []
    for index, item in enumerate(contexts):
        context = deepcopy(item)
        context.update(state=deepcopy(state), peer_states=[], round_index=index, agent_index=0, uniform=0.5)
        result = fear_appeal.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def test_positive_case_increases_precaution_with_exact_numeric_oracle():
    reference, amplified = [run_sequence([POSITIVE], s)[0] for s in (0.0, 0.8)]
    # Reference = .9*.2*.75 = .135; gap = .8*(.7-.2) = .4.
    # Added intensity = .8*.9*.75*.4 = .216.
    assert reference["metric"] == pytest.approx(0.135)
    assert amplified["metric"] == pytest.approx(0.351)
    assert amplified["metric"] > reference["metric"]
    assert amplified["active"] is True


def test_boundary_proportionate_probability_matches_reference_exactly():
    context = dict(POSITIVE, stated_probability=0.2)
    base = fear_appeal.evaluate({**context, "state": {}}, 0.0)
    at_strength = fear_appeal.evaluate({**context, "state": {}}, 0.8)
    assert base["metric"] == pytest.approx(0.135)
    assert at_strength["metric"] == base["metric"]
    assert at_strength["active"] is False


def test_zero_strength_is_stipulated_evidence_risk_reference_rule():
    result = fear_appeal.evaluate({**POSITIVE, "state": {}}, 0.0)
    assert result["metric"] == pytest.approx(
        POSITIVE["severity"]
        * POSITIVE["evidence_supported_probability"]
        * POSITIVE["response_capacity"]
    )
    assert result["active"] is False
    assert math.isfinite(result["metric"])


def test_missing_and_impossible_evidence_are_rejected():
    missing = dict(POSITIVE)
    del missing["evidence_supported_probability"]
    with pytest.raises(ValueError, match="missing required input"):
        fear_appeal.evaluate({**missing, "state": {}}, 0.8)
    impossible = dict(POSITIVE, stated_probability=1.01)
    with pytest.raises(ValueError, match="stated_probability"):
        fear_appeal.evaluate({**impossible, "state": {}}, 0.8)
    with pytest.raises(ValueError, match="threat_language"):
        fear_appeal.evaluate({**POSITIVE, "threat_language": 1, "state": {}}, 0.8)


def test_deterministic_and_nonmutating_with_chronological_state():
    context = {**POSITIVE, "state": {"cumulative_action_points": 0.25, "steps": 2, "tag": {"x": 1}}}
    before = deepcopy(context)
    first = fear_appeal.evaluate(context, 0.8)
    second = fear_appeal.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["steps"] == 3
    assert first["state"]["cumulative_action_points"] == pytest.approx(0.25 + 0.351)
    assert first["state"]["tag"] == {"x": 1}
    assert context["state"]["tag"] is not first["state"]["tag"]


def test_without_threat_language_discrepancy_does_not_change_action():
    context = dict(POSITIVE, threat_language=False)
    result = fear_appeal.evaluate({**context, "state": {}}, 0.8)
    assert result["metric"] == pytest.approx(0.135)
    assert result["active"] is False
