from copy import deepcopy
import math

import pytest

from mechanisms import cherry_picking


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
        result = cherry_picking.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def _base_context():
    return {
        "evidence": [
            {"id": "support-high", "date": "2025-01", "direction": "supports", "relevance": 0.80},
            {"id": "support-low", "date": "2025-02", "direction": "supports", "relevance": 0.70},
            {"id": "limit-high", "date": "2025-03", "direction": "limits", "relevance": 0.95},
            {"id": "limit-low", "date": "2025-04", "direction": "limits", "relevance": 0.85},
        ],
        "publication_slots": 2,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_strength_shifts_slots_and_numeric_support_share():
    positive = next(s for s in cherry_picking.scenarios() if s["name"] == "positive")
    reference = _run_sequence(positive, 0.0)[0]
    affected = _run_sequence(positive, 0.8)[0]
    assert reference["metric"] == 0.0
    assert reference["state"]["last_presented_ids"] == ["l-2024-03", "l-2024-04"]
    assert affected["metric"] == 1.0
    assert affected["state"]["last_presented_ids"] == ["s-2024-01", "s-2024-02"]
    assert affected["state"]["last_omitted_limiting_ids"] == ["l-2024-03", "l-2024-04"]
    assert affected["active"] is True
    assert math.isfinite(affected["metric"])


def test_boundary_without_limiting_evidence_matches_reference():
    boundary = next(s for s in cherry_picking.scenarios() if s["name"] == "boundary")
    baseline = _run_sequence(boundary, 0.0)[0]
    high_strength = _run_sequence(boundary, 0.8)[0]
    assert baseline["metric"] == high_strength["metric"] == 1.0
    assert baseline["state"]["last_presented_ids"] == high_strength["state"]["last_presented_ids"]
    assert high_strength["active"] is False


def test_zero_strength_is_relevance_only_reference_with_input_order_ties():
    context = _base_context()
    context["evidence"][0]["relevance"] = 0.95
    context["evidence"][2]["relevance"] = 0.95
    result = cherry_picking.evaluate(context, 0.0)
    assert result["state"]["last_presented_ids"] == ["support-high", "limit-high"]
    assert result["metric"] == 0.5
    assert result["active"] is False


def test_missing_or_impossible_evidence_is_rejected():
    context = _base_context()
    del context["evidence"][0]["direction"]
    with pytest.raises(ValueError, match="missing 'direction'"):
        cherry_picking.evaluate(context, 0.8)

    context = _base_context()
    context["evidence"][0]["relevance"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        cherry_picking.evaluate(context, 0.8)

    context = _base_context()
    context["publication_slots"] = 5
    with pytest.raises(ValueError, match="between 1 and the evidence count"):
        cherry_picking.evaluate(context, 0.8)


def test_deterministic_and_nonmutating_including_nested_state():
    context = _base_context()
    context["state"] = {"prior_note": {"tags": ["keep"]}}
    before = deepcopy(context)
    first = cherry_picking.evaluate(context, 0.8)
    second = cherry_picking.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["prior_note"] == {"tags": ["keep"]}
    assert first["state"]["prior_note"] is not context["state"]["prior_note"]


def test_invalid_strength_and_input_ranges_raise_value_error():
    for bad_strength in (-0.01, 1.01, float("inf"), float("nan"), True):
        with pytest.raises(ValueError):
            cherry_picking.evaluate(_base_context(), bad_strength)
    context = _base_context()
    context["evidence"][0]["relevance"] = 1.01
    with pytest.raises(ValueError, match=r"in \[0, 1\]"):
        cherry_picking.evaluate(context, 0.5)


def test_state_is_carried_across_chronological_contexts():
    first, = cherry_picking.scenarios()[0]["contexts"]
    second = deepcopy(first)
    second["publication_slots"] = 1
    contexts = {"initial_state": {}, "contexts": [first, second]}
    results = _run_sequence(contexts, 0.8)
    assert results[1]["state"]["last_presented_ids"] == ["s-2024-01"]
    assert results[1]["state"]["last_support_share"] == 1.0
    assert len(results) == 2
