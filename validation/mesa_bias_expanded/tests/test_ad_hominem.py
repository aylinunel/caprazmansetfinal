from copy import deepcopy

import pytest

from mechanisms import ad_hominem


def make_context(**overrides):
    context = {
        "claim_evidence_units": 3,
        "personal_attack_present": True,
        "attack_intensity": 0.6,
        "attack_claim_relevance": 0.0,
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }
    context.update(overrides)
    return context


def run_sequence(contexts, strength):
    state = {}
    outputs = []
    for i, task_context in enumerate(contexts):
        context = deepcopy(task_context)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=i,
            agent_index=0,
            uniform=0.5,
        )
        result = ad_hominem.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_irrelevant_personal_attack_diverts_evidence_review_with_numeric_oracle():
    context = make_context()
    biased = ad_hominem.evaluate(context, 0.8)
    reference = ad_hominem.evaluate(context, 0.0)

    # Diverted share = .8 * .6 * (1 - 0); reviewed evidence = 3 * (1 - .48).
    assert biased["metric"] == pytest.approx(1.56)
    assert reference["metric"] == pytest.approx(3.0)
    assert biased["metric"] < reference["metric"]
    assert biased["active"] is True
    assert biased["state"]["diverted_attention_total"] == pytest.approx(0.48)


def test_relevance_boundary_matches_strength_zero_reference():
    context = make_context(attack_claim_relevance=1.0)
    at_strength = ad_hominem.evaluate(context, 0.8)
    at_reference = ad_hominem.evaluate(context, 0.0)

    assert at_strength["metric"] == pytest.approx(3.0)
    assert at_strength["metric"] == pytest.approx(at_reference["metric"])
    assert at_strength["active"] is False


def test_zero_strength_is_explicit_full_evidence_review_reference():
    result = ad_hominem.evaluate(make_context(), 0.0)
    assert result["metric"] == pytest.approx(3.0)
    assert result["state"]["claim_evidence_units_reviewed_total"] == pytest.approx(3.0)
    assert result["state"]["turns_processed"] == 1
    assert result["active"] is False


def test_missing_or_invalid_required_evidence_is_rejected():
    incomplete = make_context()
    del incomplete["claim_evidence_units"]
    with pytest.raises(ValueError, match="missing required"):
        ad_hominem.evaluate(incomplete, 0.8)

    for invalid in (0, -1, float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="claim_evidence_units"):
            ad_hominem.evaluate(make_context(claim_evidence_units=invalid), 0.8)

    with pytest.raises(ValueError, match="personal_attack_present"):
        ad_hominem.evaluate(make_context(personal_attack_present=1), 0.8)
    with pytest.raises(ValueError, match="attack_claim_relevance"):
        ad_hominem.evaluate(make_context(attack_claim_relevance=1.2), 0.8)
    with pytest.raises(ValueError, match="strength"):
        ad_hominem.evaluate(make_context(), float("nan"))


def test_repeat_call_is_deterministic_and_does_not_mutate_context_or_nested_state():
    context = make_context(state={"memo": {"keep": [1, 2]}})
    before = deepcopy(context)
    result_one = ad_hominem.evaluate(context, 0.8)
    result_two = ad_hominem.evaluate(context, 0.8)

    assert context == before
    assert result_one == result_two
    assert result_one["state"] is not context["state"]
    assert result_one["state"]["memo"] is not context["state"]["memo"]


def test_chronological_calls_accumulate_state_without_fictitious_step():
    contexts = [make_context(), make_context(attack_intensity=0.2)]
    results = run_sequence(contexts, 0.8)

    assert [result["metric"] for result in results] == pytest.approx([1.56, 2.52])
    assert results[-1]["state"]["turns_processed"] == 2
    assert results[-1]["state"]["claim_evidence_units_reviewed_total"] == pytest.approx(4.08)
    assert results[-1]["state"]["diverted_attention_total"] == pytest.approx(0.64)


def test_nonpersonal_or_nonattack_content_does_not_trigger_diversion():
    result = ad_hominem.evaluate(
        make_context(personal_attack_present=False, attack_intensity=1.0), 0.8
    )
    assert result["metric"] == pytest.approx(3.0)
    assert result["active"] is False
