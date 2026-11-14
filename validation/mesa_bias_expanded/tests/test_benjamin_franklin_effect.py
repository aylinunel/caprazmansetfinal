from copy import deepcopy

import pytest

from mechanisms import benjamin_franklin_effect as mechanism


def run(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    result = None
    for round_index, source in enumerate(contexts):
        context = deepcopy(source)
        context.update(
            state=state,
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = mechanism.evaluate(context, strength)
        state = result["state"]
    return result


def test_positive_own_favor_has_numeric_effort_scaled_effect():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "positive")
    treated = run(scenario["contexts"], 0.8, scenario["initial_state"])
    reference = run(scenario["contexts"], 0.0, scenario["initial_state"])

    # 50 + 0.25 * 0.8 * 0.5 * (100 - 50) = 55.
    assert treated["metric"] == pytest.approx(55.0)
    assert reference["metric"] == pytest.approx(50.0)
    assert treated["metric"] > reference["metric"]
    assert treated["active"] is True
    assert treated["state"]["liking_by_person"]["colleague_A"] == pytest.approx(55.0)


def test_receiving_a_favor_is_boundary_and_matches_reference():
    scenario = next(s for s in mechanism.scenarios() if s["name"] == "boundary")
    treated = run(scenario["contexts"], 0.8, scenario["initial_state"])
    reference = run(scenario["contexts"], 0.0, scenario["initial_state"])

    assert treated["metric"] == reference["metric"] == pytest.approx(50.0)
    assert treated["active"] is False


def test_zero_strength_reproduces_explicit_retain_rating_reference_rule():
    result = mechanism.evaluate(
        {
            "direction": "given",
            "target_id": "person",
            "favor_effort": 1.0,
            "liking_before": 35.0,
            "favor_event_id": "e1",
            "state": {},
        },
        0.0,
    )
    assert result["metric"] == pytest.approx(35.0)
    assert result["active"] is False
    assert result["state"]["liking_by_person"]["person"] == pytest.approx(35.0)


def test_missing_or_impossible_evidence_and_invalid_strength_raise():
    base = {
        "direction": "given",
        "target_id": "person",
        "favor_effort": 0.5,
        "liking_before": 40.0,
        "favor_event_id": "e1",
        "state": {},
    }
    incomplete = dict(base)
    del incomplete["favor_effort"]
    with pytest.raises(ValueError, match="missing required inputs"):
        mechanism.evaluate(incomplete, 0.8)
    impossible = dict(base, liking_before=float("nan"))
    with pytest.raises(ValueError, match="liking_before"):
        mechanism.evaluate(impossible, 0.8)
    with pytest.raises(ValueError, match="strength"):
        mechanism.evaluate(base, 1.1)


def test_deterministic_and_nonmutating_with_nested_prior_state():
    context = {
        "direction": "given",
        "target_id": "person",
        "favor_effort": 0.4,
        "liking_before": 20.0,
        "favor_event_id": "e2",
        "state": {
            "liking_by_person": {"other": 33.0},
            "processed_favor_event_ids": ["old"],
            "retained_metadata": {"tag": ["keep"]},
        },
    }
    before = deepcopy(context)
    first = mechanism.evaluate(context, 0.8)
    second = mechanism.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["retained_metadata"] == {"tag": ["keep"]}
    assert first["state"]["liking_by_person"]["person"] == pytest.approx(26.4)


def test_chronological_state_carries_prior_liking_forward():
    first = mechanism.evaluate(
        {
            "direction": "given",
            "target_id": "person",
            "favor_effort": 0.5,
            "liking_before": 40.0,
            "favor_event_id": "first",
            "state": {},
        },
        0.8,
    )
    second = mechanism.evaluate(
        {
            "direction": "given",
            "target_id": "person",
            "favor_effort": 0.5,
            "liking_before": 40.0,
            "favor_event_id": "second",
            "state": first["state"],
        },
        0.8,
    )
    assert first["metric"] == pytest.approx(46.0)
    assert second["metric"] == pytest.approx(51.4)


def test_same_favor_event_id_is_not_applied_twice():
    context = {
        "direction": "given",
        "target_id": "person",
        "favor_effort": 0.5,
        "liking_before": 50.0,
        "favor_event_id": "unique-event",
        "state": {},
    }
    once = mechanism.evaluate(context, 0.8)
    repeated_context = dict(context, state=once["state"])
    repeated = mechanism.evaluate(repeated_context, 0.8)
    assert once["metric"] == pytest.approx(55.0)
    assert repeated["metric"] == pytest.approx(55.0)
    assert repeated["active"] is False
