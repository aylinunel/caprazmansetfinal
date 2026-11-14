from copy import deepcopy
import math

import pytest

from mechanisms import base_rate_fallacy


def _context(**overrides):
    context = {
        "base_rate": 0.02,
        "evidence_likelihood_ratio": 9.0,
        "state": {"steps": 3, "memo": {"seen": ["prior"]}},
    }
    context.update(overrides)
    return context


def _bayes_posterior(base_rate, likelihood_ratio):
    return (base_rate * likelihood_ratio) / (
        (1.0 - base_rate) + base_rate * likelihood_ratio
    )


def test_positive_case_specific_evidence_overweights_low_prevalence_with_numeric_oracle():
    context = _context()
    reference = base_rate_fallacy.evaluate(context, 0.0)
    result = base_rate_fallacy.evaluate(context, 0.8)
    expected_reference = (0.02 * 9.0) / (0.98 + 0.02 * 9.0)
    # At strength .8 the case-specific log-likelihood ratio is weighted 1.8x.
    expected_biased = 1.0 / (
        1.0 + math.exp(-(math.log(0.02 / 0.98) + (1.0 + 0.8) * math.log(9.0)))
    )
    assert reference["metric"] == pytest.approx(expected_reference)
    assert result["metric"] == pytest.approx(expected_biased)
    assert result["metric"] > reference["metric"]
    assert result["active"] is True
    assert result["state"]["steps"] == 4


def test_uninformative_case_evidence_boundary_equals_reference_at_strength_point_eight():
    context = _context(evidence_likelihood_ratio=1.0)
    reference = base_rate_fallacy.evaluate(context, 0.0)
    result = base_rate_fallacy.evaluate(context, 0.8)
    assert result["metric"] == pytest.approx(reference["metric"], abs=1e-15)
    assert result["metric"] == pytest.approx(0.02)
    assert result["active"] is False


def test_zero_strength_reproduces_explicit_bayes_reference_policy():
    context = _context(base_rate=0.13, evidence_likelihood_ratio=2.7)
    result = base_rate_fallacy.evaluate(context, 0.0)
    assert result["metric"] == pytest.approx(_bayes_posterior(0.13, 2.7))
    assert result["active"] is False
    assert "Reference rule" in result["trace"][0]


def test_required_evidence_and_ranges_are_validated_not_silently_zeroed():
    with pytest.raises(ValueError, match="missing required inputs"):
        base_rate_fallacy.evaluate({"base_rate": 0.1}, 0.5)
    with pytest.raises(ValueError, match="base_rate"):
        base_rate_fallacy.evaluate(_context(base_rate=0.0), 0.5)
    with pytest.raises(ValueError, match="evidence_likelihood_ratio"):
        base_rate_fallacy.evaluate(_context(evidence_likelihood_ratio=float("nan")), 0.5)
    with pytest.raises(ValueError, match="evidence_likelihood_ratio"):
        base_rate_fallacy.evaluate(_context(evidence_likelihood_ratio=0), 0.5)
    with pytest.raises(ValueError, match="strength"):
        base_rate_fallacy.evaluate(_context(), 1.1)


def test_deterministic_nonmutating_and_complete_next_state():
    context = _context()
    before = deepcopy(context)
    first = base_rate_fallacy.evaluate(context, 0.8)
    second = base_rate_fallacy.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["memo"] == {"seen": ["prior"]}
    assert first["state"]["steps"] == 4
    assert first["state"]["last_probability"] == first["metric"]
    assert first["state"]["last_reference_probability"] == pytest.approx(
        base_rate_fallacy.evaluate(context, 0.0)["metric"]
    )
    first["state"]["memo"]["seen"].append("mutation")
    assert context["state"]["memo"]["seen"] == ["prior"]
    assert second["state"]["memo"]["seen"] == ["prior"]


def test_required_scenarios_show_effect_and_boundary_equivalence():
    cases = {item["name"]: item for item in base_rate_fallacy.scenarios()}
    assert {"positive", "boundary"}.issubset(cases)
    positive = cases["positive"]["contexts"][0]
    boundary = cases["boundary"]["contexts"][0]
    assert base_rate_fallacy.evaluate(positive, 0.8)["metric"] > base_rate_fallacy.evaluate(positive, 0.0)["metric"]
    assert base_rate_fallacy.evaluate(boundary, 0.8)["metric"] == pytest.approx(
        base_rate_fallacy.evaluate(boundary, 0.0)["metric"]
    )
