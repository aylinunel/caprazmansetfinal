from copy import deepcopy
import math

import pytest

from mechanisms import spin


def _context(forms=None):
    return {
        "evidence": [
            {"id": "gain", "direction": 0.8, "weight": 2.0},
            {"id": "gap", "direction": -0.6, "weight": 1.0},
        ],
        "presentation_forms": forms if forms is not None else [
            {"kind": "headline", "focus_id": "gain", "emphasis": 1.0},
            {"kind": "ordering", "focus_id": "gain", "emphasis": 0.5},
        ],
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.5,
    }


def test_positive_convergent_forms_shift_tone_up_with_numeric_oracle():
    result = spin.evaluate(_context(), 0.8)
    reference = (2.0 * 0.8 + 1.0 * -0.6) / 3.0
    # Two convergent forms give multiplier 1 + .8*(1.0 + .5) = 2.2.
    expected = (2.0 * 2.2 * 0.8 + 1.0 * -0.6) / (2.0 * 2.2 + 1.0)
    assert result["metric"] == pytest.approx(expected)
    assert result["metric"] > reference
    assert result["active"] is True
    assert result["state"]["last_framing_direction"] == 1


def test_boundary_without_two_form_convergence_matches_reference():
    context = _context([{"kind": "headline", "focus_id": "gain", "emphasis": 1.0}])
    result = spin.evaluate(context, 0.8)
    reference = (2.0 * 0.8 - 0.6) / 3.0
    assert result["metric"] == pytest.approx(reference)
    assert result["active"] is False


def test_zero_strength_reproduces_stated_reference_policy():
    result = spin.evaluate(_context(), 0.0)
    expected = (2.0 * 0.8 - 0.6) / 3.0
    assert result["metric"] == pytest.approx(expected)
    assert result["active"] is False
    assert result["state"]["step_count"] == 1


def test_missing_or_impossible_evidence_is_rejected_not_scored_as_zero():
    missing = _context()
    del missing["evidence"]
    with pytest.raises(ValueError, match="missing required input: evidence"):
        spin.evaluate(missing, 0.8)
    impossible = _context()
    impossible["evidence"][0]["direction"] = 1.2
    with pytest.raises(ValueError, match="direction must be in \\[-1, 1\\]"):
        spin.evaluate(impossible, 0.8)


def test_invalid_strength_is_rejected():
    with pytest.raises(ValueError, match="strength must be a finite number"):
        spin.evaluate(_context(), float("nan"))
    with pytest.raises(ValueError, match="strength must be in \\[0, 1\\]"):
        spin.evaluate(_context(), 1.1)


def test_evaluation_is_deterministic_and_does_not_mutate_nested_inputs():
    context = _context()
    context["state"] = {"step_count": 3, "custom": {"keep": [1, 2]}}
    before = deepcopy(context)
    first = spin.evaluate(context, 0.8)
    second = spin.evaluate(context, 0.8)
    assert first == second
    assert context == before
    assert first["state"]["step_count"] == 4
    assert first["state"]["custom"] == {"keep": [1, 2]}
    assert math.isfinite(first["metric"])
    assert isinstance(first["trace"], list) and first["trace"]
