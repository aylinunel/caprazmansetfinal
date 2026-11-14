import json
import subprocess
import sys

import numpy as np
import pytest

import legacy_mesa_model as sim


SMALL = sim.Config(n_agents=7, n_steps=3, signal_noise=0.12)


def test_same_seed_reproduces_exogenous_inputs_and_trajectory():
    policy = sim.policies(SMALL)[-1]
    first = sim.DecisionModel(SMALL, policy, seed=17)
    second = sim.DecisionModel(SMALL, policy, seed=17)

    np.testing.assert_array_equal(first.beliefs(), second.beliefs())
    np.testing.assert_array_equal(first.signals, second.signals)
    for _ in range(SMALL.n_steps):
        first.step()
        second.step()
        np.testing.assert_array_equal(first.beliefs(), second.beliefs())


def test_all_policies_receive_matched_initial_states_signals_and_susceptibilities():
    models = [sim.DecisionModel(SMALL, policy, seed=23) for policy in sim.policies(SMALL)]
    reference = models[0]
    for model in models[1:]:
        np.testing.assert_array_equal(model.beliefs(), reference.beliefs())
        np.testing.assert_array_equal(model.signals, reference.signals)
        np.testing.assert_array_equal(
            [agent.susceptibility for agent in model.agents],
            [agent.susceptibility for agent in reference.agents],
        )


def test_zero_bias_strengths_make_all_five_policies_equivalent():
    config = sim.Config(n_agents=7, n_steps=3, anchoring=0, confirmation=0, conformity=0)
    outputs = []
    for policy in sim.policies(config):
        model = sim.DecisionModel(config, policy, seed=31)
        for _ in range(config.n_steps):
            model.step()
        outputs.append(model.beliefs())
    for output in outputs[1:]:
        np.testing.assert_array_equal(output, outputs[0])


def test_beliefs_remain_in_unit_interval_during_simulation():
    model = sim.DecisionModel(SMALL, sim.policies(SMALL)[-1], seed=41)
    assert np.all((model.beliefs() >= 0) & (model.beliefs() <= 1))
    for _ in range(SMALL.n_steps):
        model.step()
        assert np.all((model.beliefs() >= 0) & (model.beliefs() <= 1))
    assert np.all((model.signals >= 0) & (model.signals <= 1))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_agents": 2},
        {"n_agents": True},
        {"n_steps": 0},
        {"n_steps": False},
    ],
)
def test_config_rejects_invalid_counts(kwargs):
    with pytest.raises(ValueError):
        sim.Config(**kwargs)


@pytest.mark.parametrize("kwargs", [{"truth": float("nan")}, {"anchor": float("nan")}, {"learning_rate": float("nan")}])
def test_config_rejects_nan_probability_or_score_fields(kwargs):
    with pytest.raises(ValueError):
        sim.Config(**kwargs)


def test_config_rejects_tie_truth_and_nonfinite_or_negative_noise():
    for kwargs in ({"truth": 0.5}, {"signal_noise": float("nan")}, {"signal_noise": -0.01}):
        with pytest.raises(ValueError):
            sim.Config(**kwargs)


def test_low_truth_correct_choice_uses_below_threshold_orientation():
    config = sim.Config(n_agents=3, n_steps=1, truth=0.3)
    model = sim.DecisionModel(config, sim.policies(config)[0], seed=7)
    for agent in model.agents:
        agent.belief = 0.4
    model.datacollector.collect(model)
    rows = model.datacollector.get_model_vars_dataframe()
    assert rows.iloc[-1]["correct_choice_fraction"] == 1.0
    assert rows.iloc[-1]["consensus_share"] == 1.0


def test_proposals_and_commits_are_independent_of_activation_order():
    model = sim.DecisionModel(SMALL, sim.policies(SMALL)[-1], seed=53)
    agents = list(model.agents)
    frozen_previous = model.beliefs().copy()
    model.previous = frozen_previous.copy()
    for agent in agents:
        agent.propose()
    forward = {agent.index: agent.next_belief for agent in agents}

    model.previous = frozen_previous.copy()
    for agent in agents:
        agent.next_belief = agent.belief
    for agent in reversed(agents):
        agent.propose()
    reverse = {agent.index: agent.next_belief for agent in agents}
    assert reverse == forward

    for agent in agents:
        agent.next_belief = forward[agent.index]
    for agent in agents:
        agent.commit()
    committed_forward = model.beliefs().copy()
    for agent in agents:
        agent.belief = frozen_previous[agent.index]
        agent.next_belief = forward[agent.index]
    for agent in reversed(agents):
        agent.commit()
    np.testing.assert_array_equal(model.beliefs(), committed_forward)


def test_confirmation_discounts_cross_choice_evidence_but_not_same_side_evidence():
    config = sim.Config(n_agents=3, n_steps=1, learning_rate=0.4)
    policy = sim.Policy("confirm", confirmation=0.5)
    model = sim.DecisionModel(config, policy, seed=61)
    agent = model.agents[0]
    agent.susceptibility = 1.0

    model.previous = model.beliefs().copy()
    model.previous[agent.index] = 0.8
    model.signals[0, agent.index] = 0.2
    agent.propose()
    expected_discounted = 0.8 + config.learning_rate * (1 - 0.5) * (0.2 - 0.8)
    assert agent.next_belief == pytest.approx(expected_discounted)
    assert agent.discounted is True

    model.previous[agent.index] = 0.8
    model.signals[0, agent.index] = 0.9
    agent.propose()
    expected_full = 0.8 + config.learning_rate * (0.9 - 0.8)
    assert agent.next_belief == pytest.approx(expected_full)
    assert agent.discounted is False


def test_anchoring_applies_one_step_pull_after_evidence_update():
    config = sim.Config(n_agents=3, n_steps=1, learning_rate=0.25, anchor=0.2)
    model = sim.DecisionModel(config, sim.Policy("anchor", anchoring=0.4), seed=71)
    agent = model.agents[0]
    agent.susceptibility = 0.5
    model.previous = model.beliefs().copy()
    old, signal = 0.8, 0.4
    model.previous[agent.index] = old
    model.signals[0, agent.index] = signal

    agent.propose()
    evidence_updated = old + config.learning_rate * (signal - old)
    effective_anchor = 0.4 * 0.5
    expected = (1 - effective_anchor) * evidence_updated + effective_anchor * config.anchor
    assert agent.next_belief == pytest.approx(expected)


def test_conformity_uses_frozen_previous_neighbor_beliefs_not_proposals():
    config = sim.Config(n_agents=7, n_steps=1, learning_rate=0.5)
    model = sim.DecisionModel(config, sim.Policy("conform", conformity=0.6), seed=83)
    focal = model.agents[0]
    focal.susceptibility = 1.0
    previous = np.full(config.n_agents, 0.1)
    previous[focal.index] = 0.6
    model.previous = previous.copy()
    model.signals[0, :] = 0.9
    model.signals[0, focal.index] = 0.6

    peer_mean = float(np.mean(previous[model.neighbors[focal.index]]))
    updated = 0.6 + config.learning_rate * (0.6 - 0.6)
    expected = (1 - 0.6) * updated + 0.6 * peer_mean
    focal.propose()
    assert focal.next_belief == pytest.approx(expected)
    assert focal.next_belief != pytest.approx(updated)


def test_experiment_trajectory_includes_round_zero_and_each_step():
    config = sim.Config(n_agents=3, n_steps=2)
    trajectories, _, _ = sim.run_experiment(config, replicates=1, seed=91)
    assert len(trajectories) == len(sim.policies(config)) * (config.n_steps + 1)
    for policy in sim.policies(config):
        rows = [row for row in trajectories if row["policy"] == policy.name]
        assert [row["round"] for row in rows] == [0, 1, 2]


def test_baseline_paired_deltas_are_zero():
    config = sim.Config(n_agents=3, n_steps=1)
    _, _, runs = sim.run_experiment(config, replicates=2, seed=101)
    baseline_rows = [row for row in runs if row["policy"] == "baseline"]
    assert len(baseline_rows) == 2
    for row in baseline_rows:
        assert row["paired_error_delta_vs_baseline"] == 0
        assert row["paired_accuracy_delta_vs_baseline"] == 0


def test_cli_no_plot_writes_csv_and_metadata_without_png(tmp_path):
    output = tmp_path / "cli-output"
    result = subprocess.run(
        [
            sys.executable,
            str(sim.__file__),
            "--agents",
            "3",
            "--steps",
            "1",
            "--replicates",
            "1",
            "--seed",
            "3",
            "--no-plot",
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for name in ("trajectories.csv", "final_agents.csv", "final_runs.csv"):
        assert (output / name).is_file()
        assert (output / name).stat().st_size > 0
    metadata = json.loads((output / "metadata.json").read_text())
    assert metadata["synthetic"] is True
    assert metadata["empirically_validated"] is False
    assert metadata["activation"] == "synchronous propose/commit"
    assert metadata["seed_sequence"] == [3]
    assert not (output / "dynamics.png").exists()
