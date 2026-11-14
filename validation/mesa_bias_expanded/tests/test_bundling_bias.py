from copy import deepcopy

import pytest

from mechanisms import bundling_bias


BUNDLE = {
    "bundle_purchased": True,
    "component_in_bundle": True,
    "bundle_component_count": 3,
    "bundle_price": 8.0,
    "component_marginal_price": 2.0,
    "component_use_value": 4.0,
}


def run_sequence(contexts, strength, initial_state=None):
    state = deepcopy(initial_state or {})
    outputs = []
    for round_index, fields in enumerate(contexts):
        context = deepcopy(fields)
        context.update(
            state=deepcopy(state),
            peer_states=[],
            round_index=round_index,
            agent_index=0,
            uniform=0.5,
        )
        result = bundling_bias.evaluate(context, strength)
        state = result["state"]
        outputs.append(result)
    return outputs


def test_positive_underuse_numeric_choice_oracle():
    # At .8, perceived cost = 2 + .8 * (8 - 2) = 6.8; value 4 misses it.
    # The explicit marginal-price reference (2) would use the component.
    out = bundling_bias.evaluate(BUNDLE, 0.8)
    assert out["state"]["last_perceived_cost"] == pytest.approx(6.8)
    assert out["state"]["last_reference_use"] == 1
    assert out["metric"] == 0.0
    assert out["active"] is True


def test_boundary_without_included_component_matches_reference():
    boundary = {**BUNDLE, "component_in_bundle": False}
    at_strength = bundling_bias.evaluate(boundary, 0.8)
    reference = bundling_bias.evaluate(boundary, 0.0)
    assert at_strength["metric"] == reference["metric"] == 1.0
    assert at_strength["state"]["last_perceived_cost"] == 2.0
    assert at_strength["active"] is False


def test_zero_strength_is_explicit_marginal_price_reference_rule():
    out = bundling_bias.evaluate(BUNDLE, 0.0)
    assert out["state"]["last_perceived_cost"] == 2.0
    assert out["metric"] == 1.0  # use iff value >= marginal component price
    assert out["state"]["last_reference_use"] == out["metric"]
    assert out["active"] is False


def test_bundle_purchase_alone_does_not_activate_mechanism():
    not_a_multi_component_bundle = {**BUNDLE, "bundle_component_count": 1}
    out = bundling_bias.evaluate(not_a_multi_component_bundle, 0.8)
    assert out["metric"] == 1.0
    assert out["active"] is False
    assert "eligibility condition false" in out["trace"][0]


def test_missing_or_impossible_evidence_is_rejected():
    missing = dict(BUNDLE)
    del missing["component_use_value"]
    with pytest.raises(ValueError, match="missing required"):
        bundling_bias.evaluate(missing, 0.8)
    impossible = {**BUNDLE, "bundle_price": 1.0}
    with pytest.raises(ValueError, match="cannot be below"):
        bundling_bias.evaluate(impossible, 0.8)
    malformed = {**BUNDLE, "component_in_bundle": 1}
    with pytest.raises(ValueError, match="must be a bool"):
        bundling_bias.evaluate(malformed, 0.8)


def test_strength_and_numeric_ranges_are_validated():
    for invalid in (-0.01, 1.01, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            bundling_bias.evaluate(BUNDLE, invalid)
    with pytest.raises(ValueError, match="finite nonnegative"):
        bundling_bias.evaluate({**BUNDLE, "component_use_value": float("nan")}, 0.8)


def test_deterministic_and_nonmutating_with_nested_prior_state():
    context = {**BUNDLE, "state": {"history": ["kept"], "other": {"x": 1}}}
    original = deepcopy(context)
    first = bundling_bias.evaluate(context, 0.8)
    second = bundling_bias.evaluate(context, 0.8)
    assert context == original
    assert first == second
    assert first["state"]["history"] == ["kept"]
    assert first["state"]["last_use"] == 0
    first["state"]["history"].append("output change")
    assert context == original


def test_scenario_contract_has_positive_and_boundary_effects():
    scenarios = {scenario["name"]: scenario for scenario in bundling_bias.scenarios()}
    assert set(("positive", "boundary")).issubset(scenarios)
    positive = scenarios["positive"]
    boundary = scenarios["boundary"]
    assert positive["expectation"] == "decrease"
    assert boundary["expectation"] == "equal"
    positive_effect = run_sequence(positive["contexts"], 0.8)[-1]["metric"]
    positive_reference = run_sequence(positive["contexts"], 0.0)[-1]["metric"]
    assert positive_effect < positive_reference
    boundary_effect = run_sequence(boundary["contexts"], 0.8)[-1]["metric"]
    boundary_reference = run_sequence(boundary["contexts"], 0.0)[-1]["metric"]
    assert boundary_effect == boundary_reference
