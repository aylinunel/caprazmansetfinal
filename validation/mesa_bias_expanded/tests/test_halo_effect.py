from copy import deepcopy

import pytest

from mechanisms import halo_effect


def _context(**overrides):
    context = {
        "donor_attribute": "presentation_polish",
        "target_attribute": "analytical_accuracy",
        "attributes_related": False,
        "donor_rating": 9.0,
        "target_reference_rating": 4.0,
        "target_evidence_support": 0.2,
        "state": {"steps": 2, "last_target_judgment": 3.0, "custom": {"prior": ["kept"]}},
    }
    context.update(overrides)
    return context


def test_positive_cross_attribute_spillover_has_numeric_oracle():
    context = _context()
    reference = halo_effect.evaluate(context, 0.0)
    result = halo_effect.evaluate(context, 0.8)
    # Oracle: 4 + .8 * (1-.2) * (9-4) = 7.2 target-rating points.
    assert reference["metric"] == 4.0
    assert result["metric"] == pytest.approx(7.2)
    assert result["active"] is True
    assert result["state"]["last_spillover_points"] == pytest.approx(3.2)


def test_relevant_performance_boundary_matches_reference_at_strength_point_eight():
    context = _context(
        donor_attribute="task_performance",
        target_attribute="task_competence",
        attributes_related=True,
        donor_rating=9.0,
    )
    reference = halo_effect.evaluate(context, 0.0)
    result = halo_effect.evaluate(context, 0.8)
    assert reference["metric"] == result["metric"] == 4.0
    assert result["active"] is False
    assert result["state"]["last_spillover_points"] == 0.0


def test_zero_strength_reproduces_explicit_target_reference_policy():
    result = halo_effect.evaluate(_context(target_reference_rating=6.25), 0.0)
    assert result["metric"] == 6.25
    assert result["active"] is False
    assert result["state"]["last_target_judgment"] == 6.25


def test_full_target_support_and_non_favorable_cue_do_not_spill_over():
    fully_supported = halo_effect.evaluate(_context(target_evidence_support=1.0), 0.8)
    non_favorable = halo_effect.evaluate(_context(donor_rating=3.0), 0.8)
    assert fully_supported["metric"] == 4.0
    assert non_favorable["metric"] == 4.0
    assert not fully_supported["active"]
    assert not non_favorable["active"]


def test_missing_or_impossible_required_evidence_is_rejected():
    with pytest.raises(ValueError, match="missing required inputs"):
        halo_effect.evaluate({"donor_attribute": "style"}, 0.5)
    with pytest.raises(ValueError, match="target_reference_rating"):
        halo_effect.evaluate(_context(target_reference_rating=float("nan")), 0.5)
    with pytest.raises(ValueError, match="target_evidence_support"):
        halo_effect.evaluate(_context(target_evidence_support=1.1), 0.5)
    with pytest.raises(ValueError, match="attributes_related"):
        halo_effect.evaluate(_context(attributes_related=0), 0.5)


def test_invalid_strength_and_same_attribute_are_rejected():
    with pytest.raises(ValueError, match="strength"):
        halo_effect.evaluate(_context(), float("inf"))
    with pytest.raises(ValueError, match="strength"):
        halo_effect.evaluate(_context(), -0.01)
    with pytest.raises(ValueError, match="distinct"):
        halo_effect.evaluate(_context(target_attribute="PRESENTATION_POLISH"), 0.8)


def test_determinism_and_input_state_nonmutation():
    context = _context(metadata={"nested": [1, 2]})
    before = deepcopy(context)
    first = halo_effect.evaluate(context, 0.8)
    second = halo_effect.evaluate(context, 0.8)
    assert context == before
    assert first == second
    assert first["state"]["steps"] == 3
    assert first["state"]["custom"] == {"prior": ["kept"]}
    first["state"]["custom"]["prior"].append("changed")
    assert context["state"]["custom"] == {"prior": ["kept"]}
    assert second["state"]["custom"] == {"prior": ["kept"]}


def test_scenarios_include_required_positive_and_boundary_comparisons():
    items = {scenario["name"]: scenario for scenario in halo_effect.scenarios()}
    assert {"positive", "boundary"}.issubset(items)
    positive = items["positive"]["contexts"][0]
    boundary = items["boundary"]["contexts"][0]
    assert halo_effect.evaluate(positive, 0.8)["metric"] > halo_effect.evaluate(positive, 0.0)["metric"]
    assert halo_effect.evaluate(boundary, 0.8)["metric"] == halo_effect.evaluate(boundary, 0.0)["metric"]
