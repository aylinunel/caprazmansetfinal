from copy import deepcopy
import math

import pytest

from mechanisms import negativity_bias


def _run_sequence(scenario, strength):
    state = deepcopy(scenario["initial_state"])
    results = []
    for round_index, raw in enumerate(scenario["contexts"]):
        context = deepcopy(raw)
        context.update({
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.5,
        })
        result = negativity_bias.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def _context(evidence=None):
    return {
        "evidence": evidence if evidence is not None else [
            {"id": "pro", "topic": "service", "valence": "positive", "severity": 0.6, "relevance": 0.5},
            {"id": "con", "topic": "service", "valence": "negative", "severity": 0.6, "relevance": 0.5},
        ],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_strength_has_exact_task_specific_numeric_effect():
    scenario = next(item for item in negativity_bias.scenarios() if item["name"] == "positive")
    reference = _run_sequence(scenario, 0.0)[0]
    affected = _run_sequence(scenario, 0.8)[0]
    assert reference["metric"] == pytest.approx(0.0)
    # 0.8 strength × 0.5 illustrative gain × (0.6 severity × 0.5 relevance).
    assert affected["metric"] == pytest.approx(0.12)
    assert affected["state"]["last_matched_pairs"] == 1
    assert affected["state"]["last_bias_increment"] == pytest.approx(0.12)
    assert affected["active"] is True
    assert math.isfinite(affected["metric"])


def test_boundary_without_comparable_opposing_pair_matches_reference_metric():
    scenario = next(item for item in negativity_bias.scenarios() if item["name"] == "boundary")
    baseline = _run_sequence(scenario, 0.0)[0]
    high_strength = _run_sequence(scenario, 0.8)[0]
    assert baseline["metric"] == high_strength["metric"] == pytest.approx(-0.35)
    assert high_strength["state"]["last_matched_pairs"] == 0
    assert high_strength["active"] is False


def test_zero_strength_is_explicit_severity_relevance_weighted_reference():
    context = _context([
        {"id": "n1", "topic": "a", "valence": "negative", "severity": 0.8, "relevance": 0.5},
        {"id": "p1", "topic": "b", "valence": "positive", "severity": 0.4, "relevance": 0.5},
    ])
    result = negativity_bias.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(0.2)  # 0.8×0.5 - 0.4×0.5
    assert result["state"]["last_reference_metric"] == pytest.approx(0.2)
    assert result["state"]["last_bias_increment"] == 0.0
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected_not_scored_as_zero():
    with pytest.raises(ValueError, match="missing required input"):
        negativity_bias.evaluate({"state": {}}, 0.8)
    with pytest.raises(ValueError, match="non-empty list"):
        negativity_bias.evaluate(_context([]), 0.8)
    invalid = _context()
    del invalid["evidence"][0]["severity"]
    with pytest.raises(ValueError, match="missing 'severity'"):
        negativity_bias.evaluate(invalid, 0.8)
    invalid = _context()
    invalid["evidence"][0]["relevance"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        negativity_bias.evaluate(invalid, 0.8)
    invalid = _context()
    invalid["evidence"][0]["severity"] = 1.01
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        negativity_bias.evaluate(invalid, 0.8)


def test_deterministic_and_nonmutating_even_for_nested_state_and_evidence():
    context = _context()
    context["evidence"][0]["metadata"] = {"labels": ["supplied"]}
    context["state"] = {"memo": {"tags": ["keep"]}}
    before = deepcopy(context)
    first = negativity_bias.evaluate(context, 0.8)
    second = negativity_bias.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["memo"] == {"tags": ["keep"]}
    assert first["state"]["memo"] is not context["state"]["memo"]
    assert first["state"]["rounds_evaluated"] == 1


def test_strength_validation_and_one_to_one_pairing():
    for bad_strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            negativity_bias.evaluate(_context(), bad_strength)
    evidence = [
        {"id": "n1", "topic": "x", "valence": "negative", "severity": 0.5, "relevance": 0.8},
        {"id": "n2", "topic": "x", "valence": "negative", "severity": 0.5, "relevance": 0.8},
        {"id": "p1", "topic": "x", "valence": "positive", "severity": 0.5, "relevance": 0.8},
    ]
    result = negativity_bias.evaluate(_context(evidence), 0.8)
    assert result["state"]["last_matched_pairs"] == 1
    assert result["state"]["last_bias_increment"] == pytest.approx(0.16)
    assert result["metric"] == pytest.approx(0.56)


def test_state_is_carried_across_calls_without_inventing_extra_steps():
    scenario = next(item for item in negativity_bias.scenarios() if item["name"] == "positive")
    two_rounds = {"initial_state": {}, "contexts": [scenario["contexts"][0], scenario["contexts"][0]]}
    results = _run_sequence(two_rounds, 0.8)
    assert len(results) == 2
    assert results[-1]["state"]["rounds_evaluated"] == 2
    assert results[-1]["metric"] == pytest.approx(0.12)
