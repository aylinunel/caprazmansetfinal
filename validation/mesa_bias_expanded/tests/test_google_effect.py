import copy
import math

import pytest

from mechanisms import google_effect


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {"memory_traces": {}})
    results = []
    for round_index, item in enumerate(contexts):
        context = copy.deepcopy(item)
        context.update(
            state=copy.deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = google_effect.evaluate(context, strength)
        state = result["state"]
        results.append(result)
    return results


def study(expected=True, lookup=False, difficulty=0.0, item_id="x"):
    return {
        "action": "study",
        "items": [{
            "item_id": item_id,
            "difficulty": difficulty,
            "expected_external_access": expected,
            "external_lookup_used": lookup,
        }],
    }


def retrieve(item_id="x"):
    return {"action": "retrieve", "item_ids": [item_id]}


def test_positive_expected_access_reduces_numeric_recall_by_task_formula():
    base = run_sequence([study(expected=True), retrieve()], 0.0)[-1]["metric"]
    offloaded = run_sequence([study(expected=True), retrieve()], 0.8)[-1]["metric"]
    assert base == pytest.approx(1.0 - math.exp(-1.0))
    assert offloaded == pytest.approx(1.0 - math.exp(-0.52))
    assert offloaded < base
    assert run_sequence([study(expected=True), retrieve()], 0.8)[0]["active"] is True


def test_boundary_lookup_without_expected_access_matches_reference():
    contexts = [study(expected=False, lookup=True), retrieve()]
    reference = run_sequence(contexts, 0.0)[-1]["metric"]
    boundary = run_sequence(contexts, 0.8)[-1]["metric"]
    assert boundary == reference == pytest.approx(1.0 - math.exp(-1.0))
    assert run_sequence(contexts, 0.8)[0]["active"] is False


def test_zero_strength_is_explicit_unattenuated_reference_policy():
    contexts = [study(expected=True, difficulty=0.5), retrieve()]
    result = run_sequence(contexts, 0.0)[-1]
    assert result["metric"] == pytest.approx(1.0 - math.exp(-(1.0 / 1.5)))
    assert result["state"]["memory_traces"]["x"] == pytest.approx(1.0 / 1.5)


def test_invalid_strength_and_missing_required_inputs_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        google_effect.evaluate({"action": "retrieve", "item_ids": ["x"]}, 1.01)
    with pytest.raises(ValueError, match="study requires"):
        google_effect.evaluate({"action": "study"}, 0.5)
    with pytest.raises(ValueError, match="expected_external_access"):
        google_effect.evaluate({
            "action": "study",
            "items": [{"item_id": "x", "difficulty": 0.2, "external_lookup_used": True}],
        }, 0.5)


def test_retrieval_without_study_evidence_errors_instead_of_returning_zero():
    with pytest.raises(ValueError, match="without study evidence"):
        google_effect.evaluate({
            "action": "retrieve", "item_ids": ["unseen"], "state": {"memory_traces": {}}
        }, 0.8)


def test_deterministic_and_does_not_mutate_context_or_nested_state():
    context = {
        **study(expected=True, lookup=True, difficulty=0.25),
        "state": {"memory_traces": {"older": 0.2}},
        "peer_states": [{"memory_traces": {"peer": 0.4}}],
        "round_index": 3,
        "agent_index": 2,
        "uniform": 0.7,
    }
    before = copy.deepcopy(context)
    first = google_effect.evaluate(context, 0.8)
    second = google_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["memory_traces"] == pytest.approx({"older": 0.2, "x": 0.416})
    assert isinstance(first["trace"], list) and first["trace"]
    assert math.isfinite(first["metric"])
