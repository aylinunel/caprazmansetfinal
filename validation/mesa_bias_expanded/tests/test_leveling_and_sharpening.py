from copy import deepcopy

import pytest

from mechanisms import leveling_and_sharpening as mechanism


DETAILS = [
    {"id": "minor", "intensity": 0.8, "salience": 0.2},
    {"id": "central", "intensity": 0.7, "salience": 0.8},
]


def call(context, strength):
    """Supply the runner's reserved inputs for a standalone evaluation."""
    full_context = {
        "state": {},
        "peer_states": [],
        "round_index": 0,
        "agent_index": 0,
        "uniform": 0.25,
        **deepcopy(context),
    }
    return mechanism.evaluate(full_context, strength)


def run(contexts, strength):
    state = {}
    result = None
    for round_index, task_context in enumerate(contexts):
        full_context = {
            **deepcopy(task_context),
            "state": deepcopy(state),
            "peer_states": [],
            "round_index": round_index,
            "agent_index": 0,
            "uniform": 0.25,
        }
        result = mechanism.evaluate(full_context, strength)
        state = result["state"]
    return result


def test_numeric_oracle_matches_salience_differential_and_task_metric():
    result = call({"details": DETAILS, "retention": 0.9}, 0.8)

    # Mean salience=.5. Multipliers are .9*(1-.12)=.792 and
    # .9*(1+.12)=1.008, applied to each detail's distance from neutral .5.
    assert result["state"]["memory"] == pytest.approx([0.7376, 0.7016])
    assert result["metric"] == pytest.approx((0.0624 + 0.0016) / 2)
    assert result["active"] is True
    assert result["trace"]


def test_strength_increases_distortion_in_positive_chronological_scenario():
    scenario = next(item for item in mechanism.scenarios() if item["name"] == "positive")
    reference = run(scenario["contexts"], 0.0)
    intervention = run(scenario["contexts"], 0.8)

    assert len(intervention["state"]["history"]) == len(scenario["contexts"]) == 2
    assert intervention["state"]["retell_count"] == 2
    assert intervention["metric"] > reference["metric"]


def test_equal_salience_boundary_removes_differential_condition():
    scenario = next(item for item in mechanism.scenarios() if item["name"] == "boundary")
    reference = run(scenario["contexts"], 0.0)
    intervention = run(scenario["contexts"], 0.8)

    assert len({d["salience"] for d in scenario["contexts"][0]["details"]}) == 1
    assert intervention["metric"] == pytest.approx(reference["metric"], abs=1e-12)
    assert intervention["state"]["memory"] == pytest.approx(reference["state"]["memory"])
    assert intervention["active"] is False


def test_zero_strength_is_uniform_retention_reference():
    result = call({"details": DETAILS, "retention": 0.5}, 0.0)

    assert result["state"]["memory"] == pytest.approx([0.65, 0.6])
    assert result["metric"] == pytest.approx(0.125)
    assert result["active"] is False
    assert result["state"]["history"] == [[0.65, 0.6]]


def test_missing_and_invalid_task_evidence_is_rejected():
    with pytest.raises(ValueError, match="details and retention"):
        call({"details": DETAILS}, 0.8)
    with pytest.raises(ValueError, match="salience"):
        call({"details": [{"id": "x", "intensity": 0.5, "salience": float("nan")}], "retention": 1.0}, 0.8)
    with pytest.raises(ValueError, match="retention"):
        call({"details": DETAILS, "retention": 1.1}, 0.8)
    with pytest.raises(ValueError, match="strength"):
        call({"details": DETAILS, "retention": 1.0}, float("inf"))


def test_deterministic_and_nonmutating_for_context_and_nested_prior_state():
    first = call({"details": DETAILS, "retention": 0.9}, 0.8)
    source_context = {
        "details": deepcopy(DETAILS),
        "retention": 0.9,
        "state": deepcopy(first["state"]),
        "peer_states": [{"unrelated": [1, 2]}],
        "round_index": 1,
        "agent_index": 3,
        "uniform": 0.75,
    }
    before = deepcopy(source_context)
    result_a = mechanism.evaluate(source_context, 0.8)
    result_b = mechanism.evaluate(source_context, 0.8)

    assert source_context == before
    assert result_a == result_b
    assert result_a["state"]["retell_count"] == 2
    assert len(result_a["state"]["history"]) == 2


def test_prior_state_must_match_the_source_and_history_shape():
    first = call({"details": DETAILS, "retention": 1.0}, 0.8)
    changed_details = deepcopy(DETAILS)
    changed_details[0]["salience"] = 0.3
    with pytest.raises(ValueError, match="remain unchanged"):
        mechanism.evaluate(
            {"details": changed_details, "retention": 1.0, "state": first["state"]}, 0.8
        )
    malformed = deepcopy(first["state"])
    malformed["history"].clear()
    with pytest.raises(ValueError, match="one snapshot"):
        mechanism.evaluate({"details": DETAILS, "retention": 1.0, "state": malformed}, 0.8)


def test_required_inputs_are_exact_unconditional_scenario_keys():
    assert mechanism.METADATA["required_inputs"] == ["details", "retention"]
    for scenario in mechanism.scenarios():
        for context in scenario["contexts"]:
            assert set(mechanism.METADATA["required_inputs"]).issubset(context)
            assert not ({"state", "peer_states", "uniform", "round_index", "agent_index"} & set(context))
