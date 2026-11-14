import copy

import pytest

from mechanisms import thematic_framing


def make_context(**changes):
    context = {
        "article_word_budget": 240,
        "incident_word_reserve": 120,
        "context_relevance": 0.75,
        "source_verified": True,
        "topic_match": True,
        "trend_observations": [
            {"period": 1, "rate": 0.1},
            {"period": 2, "rate": 0.3},
            {"period": 3, "rate": 0.5},
            {"period": 4, "rate": 0.7},
        ],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(changes)
    return context


def run_sequence(contexts, strength, initial_state=None):
    state = copy.deepcopy(initial_state or {})
    outputs = []
    for index, raw in enumerate(contexts):
        context = copy.deepcopy(raw)
        context.update(
            state=state,
            peer_states=[],
            round_index=index,
            agent_index=0,
            uniform=0.5,
        )
        result = thematic_framing.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_positive_direction_and_numeric_allocation_oracle():
    context = make_context()
    reference = thematic_framing.evaluate(context, 0.0)
    framed = thematic_framing.evaluate(context, 0.8)
    # Capacity=120; trend signal=.6; relevance=.75; strength=.8.
    # floor(120 * .6 * .75 * .8) = 43 contextual words.
    assert reference["metric"] == 0
    assert framed["metric"] == 43
    assert framed["active"] is True
    assert framed["state"]["context_words_total"] == 43


def test_boundary_missing_topic_match_equals_reference_at_strength_point_eight():
    boundary = make_context(topic_match=False)
    at_zero = thematic_framing.evaluate(boundary, 0.0)
    at_point_eight = thematic_framing.evaluate(boundary, 0.8)
    assert at_zero["metric"] == at_point_eight["metric"] == 0
    assert at_point_eight["active"] is False


def test_strength_zero_is_explicit_incident_only_reference():
    result = thematic_framing.evaluate(make_context(), 0.0)
    assert result["metric"] == 0
    assert result["state"]["rounds"] == 1
    assert "incident-only" in result["trace"][0]


def test_missing_observations_are_rejected_not_scored_as_zero():
    with pytest.raises(ValueError, match="trend_observations"):
        thematic_framing.evaluate(make_context(trend_observations=[]), 0.8)


def test_invalid_input_ranges_and_strength_are_rejected():
    with pytest.raises(ValueError, match="context_relevance"):
        thematic_framing.evaluate(make_context(context_relevance=1.1), 0.8)
    with pytest.raises(ValueError, match="strength"):
        thematic_framing.evaluate(make_context(), float("nan"))
    with pytest.raises(ValueError, match="strictly increasing"):
        thematic_framing.evaluate(
            make_context(trend_observations=[
                {"period": 1, "rate": 0.1},
                {"period": 1, "rate": 0.4},
                {"period": 3, "rate": 0.7},
            ]),
            0.8,
        )


def test_deterministic_and_does_not_mutate_context_or_nested_inputs():
    context = make_context()
    before = copy.deepcopy(context)
    first = thematic_framing.evaluate(context, 0.8)
    second = thematic_framing.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"] is not context["state"]
    assert first["state"]["allocation_history"] is not context["state"].get("allocation_history")


def test_chronological_calls_carry_complete_state_without_changing_prior_state():
    inputs = [make_context(), make_context(topic_match=False)]
    prior_state = {"context_words_total": 5, "rounds": 2, "allocation_history": [{"words": 5}]}
    prior_before = copy.deepcopy(prior_state)
    outputs = run_sequence(inputs, 0.8, prior_state)
    assert outputs[0]["metric"] == 43
    assert outputs[1]["metric"] == 0
    assert outputs[1]["state"]["context_words_total"] == 48
    assert outputs[1]["state"]["rounds"] == 4
    assert len(outputs[1]["state"]["allocation_history"]) == 3
    assert prior_state == prior_before
