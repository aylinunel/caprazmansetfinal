#!/usr/bin/env python3
"""Illustrative cognitive-bias dynamics using Mesa 3.5.2.

No LLM/API calls or human data. The rules are modeling assumptions, not a
validated psychological theory. Compare five policies on the SAME initial
agents, signals, peer network and seeds. See README.md for the equations.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict, dataclass
from importlib import metadata
import json
import math
from pathlib import Path
import sys

import mesa
import numpy as np


@dataclass(frozen=True)
class Config:
    n_agents: int = 60
    n_steps: int = 50
    truth: float = 0.70
    anchor: float = 0.20
    learning_rate: float = 0.25
    signal_noise: float = 0.18
    anchoring: float = 0.10
    confirmation: float = 0.75
    conformity: float = 0.35

    def __post_init__(self):
        for name in ('n_agents', 'n_steps'):
            value = getattr(self, name)
            minimum = 3 if name == 'n_agents' else 1
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f'{name} must be an integer >= {minimum}')
        for name in ('truth', 'anchor', 'learning_rate', 'anchoring', 'confirmation', 'conformity'):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'{name} must be finite and in [0, 1]')
        if self.truth == 0.5:
            raise ValueError('truth=0.5 is a tie: this example requires a uniquely better option')
        if not math.isfinite(self.signal_noise) or self.signal_noise < 0:
            raise ValueError('signal_noise must be finite and nonnegative')


@dataclass(frozen=True)
class Policy:
    name: str
    anchoring: float = 0.0
    confirmation: float = 0.0
    conformity: float = 0.0

    def __post_init__(self):
        for name in ('anchoring', 'confirmation', 'conformity'):
            value = getattr(self, name)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f'policy {name} must be finite and in [0, 1]')


def policies(config: Config) -> list[Policy]:
    return [
        Policy('baseline'),
        Policy('anchoring_only', anchoring=config.anchoring),
        Policy('confirmation_only', confirmation=config.confirmation),
        Policy('conformity_only', conformity=config.conformity),
        Policy('combined', config.anchoring, config.confirmation, config.conformity),
    ]


class DecisionAgent(mesa.Agent):
    def __init__(self, model: 'DecisionModel', index: int, belief: float,
                 susceptibility: float):
        super().__init__(model)  # Mesa automatically registers this agent.
        self.index = index
        self.belief = float(belief)
        self.next_belief = self.belief
        self.susceptibility = float(susceptibility)
        self.discounted = False

    def propose(self):
        """Read only last-round state; never read another agent's proposed state."""
        model = self.model
        old = float(model.previous[self.index])
        signal = float(model.signals[model.round_index, self.index])
        contradictory = (old - 0.5) * (signal - 0.5) < 0
        c = min(1.0, model.policy.confirmation * self.susceptibility)
        evidence_weight = 1.0 - c if contradictory else 1.0
        self.discounted = contradictory and c > 0

        # Evidence update, followed by persistent pull to a fixed anchor.
        updated = old + model.config.learning_rate * evidence_weight * (signal - old)
        a = min(1.0, model.policy.anchoring * self.susceptibility)
        updated = (1.0 - a) * updated + a * model.config.anchor

        # Conformity to local peers' LAST-round beliefs, not new private signals.
        neighbors = model.neighbors[self.index]
        peer_mean = float(np.mean(model.previous[neighbors]))
        k = min(1.0, model.policy.conformity * self.susceptibility)
        self.next_belief = float(np.clip((1.0 - k) * updated + k * peer_mean, 0, 1))

    def commit(self):
        self.belief = self.next_belief


class DecisionModel(mesa.Model):
    def __init__(self, config: Config, policy: Policy, seed: int = 42):
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError('seed must be a nonnegative integer')
        super().__init__(rng=seed)
        self.config, self.policy = config, policy
        self.round_index = 0
        n = config.n_agents
        # Draw ALL exogenous inputs before activating agents. Every policy with
        # the same seed therefore sees identical agents and evidence.
        initial = self.rng.uniform(0.30, 0.70, n)
        susceptibility = self.rng.uniform(0.6, 1.4, n)
        common = self.rng.normal(0, config.signal_noise * 0.25, (config.n_steps, 1))
        private = self.rng.normal(0, config.signal_noise * math.sqrt(1 - 0.25**2),
                                  (config.n_steps, n))
        self.signals = np.clip(config.truth + common + private, 0, 1)
        # Ring network: up to six nearest peers, excluding self and duplicates.
        self.neighbors = [sorted({(i + offset) % n for offset in (-3, -2, -1, 1, 2, 3)}
                                 - {i}) for i in range(n)]
        for i in range(n):
            DecisionAgent(self, i, initial[i], susceptibility[i])
        self.previous = self.beliefs()
        self.datacollector = mesa.DataCollector(model_reporters={
            'round': lambda m: m.round_index,
            'mean_belief': lambda m: float(np.mean(m.beliefs())),
            'belief_sd': lambda m: float(np.std(m.beliefs())),
            'mean_absolute_error': lambda m: float(np.mean(np.abs(m.beliefs() - m.config.truth))),
            'correct_choice_fraction': lambda m: float(np.mean((m.beliefs() >= 0.5) == (m.config.truth > 0.5))),
            'consensus_share': lambda m: max(float(np.mean(m.beliefs() >= 0.5)),
                                             float(np.mean(m.beliefs() < 0.5))),
            'discounted_signal_fraction': lambda m: float(np.mean([a.discounted for a in m.agents])),
        })
        self.datacollector.collect(self)  # round zero is included.

    def beliefs(self) -> np.ndarray:
        # Explicit indices keep signal/evidence alignment independent of AgentSet order.
        values = np.empty(self.config.n_agents)
        for agent in self.agents:
            values[agent.index] = agent.belief
        return values

    def step(self):
        if self.round_index >= self.config.n_steps:
            self.running = False
            return
        self.previous = self.beliefs()
        self.agents.do('propose')  # All proposals before any commit: synchronous.
        self.agents.do('commit')
        self.round_index += 1
        self.datacollector.collect(self)
        self.running = self.round_index < self.config.n_steps


def write_csv(path: Path, rows: list[dict]):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_experiment(config: Config, replicates: int = 10, seed: int = 42):
    """Return full trajectories, final agent states and seed-level paired metrics."""
    if isinstance(replicates, bool) or not isinstance(replicates, int) or replicates < 1:
        raise ValueError('replicates must be a positive integer')
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError('seed must be a nonnegative integer')
    trajectories, final_agents, final_runs = [], [], []
    for replicate in range(replicates):
        run_seed = seed + replicate
        baseline = None
        for policy in policies(config):
            model = DecisionModel(config, policy, run_seed)
            for _ in range(config.n_steps):
                model.step()
            records = model.datacollector.get_model_vars_dataframe().to_dict('records')
            trajectories.extend({'policy': policy.name, 'replicate': replicate,
                                 'seed': run_seed, **record} for record in records)
            for agent in model.agents:
                final_agents.append({'policy': policy.name, 'replicate': replicate,
                                     'seed': run_seed, 'agent_index': agent.index,
                                     'belief': agent.belief, 'susceptibility': agent.susceptibility,
                                     'choice': 'B' if agent.belief >= 0.5 else 'A'})
            final = records[-1]
            if policy.name == 'baseline':
                baseline = final
            final_runs.append({'policy': policy.name, 'replicate': replicate,
                               'seed': run_seed, **final,
                               'paired_error_delta_vs_baseline': final['mean_absolute_error'] - baseline['mean_absolute_error'],
                               'paired_accuracy_delta_vs_baseline': final['correct_choice_fraction'] - baseline['correct_choice_fraction']})
    return trajectories, final_agents, final_runs


def summarize(final_runs: list[dict]) -> dict:
    result = {}
    metrics = ('mean_belief', 'belief_sd', 'mean_absolute_error', 'correct_choice_fraction',
               'consensus_share', 'paired_error_delta_vs_baseline', 'paired_accuracy_delta_vs_baseline')
    for name in dict.fromkeys(row['policy'] for row in final_runs):
        group = [row for row in final_runs if row['policy'] == name]
        result[name] = {'replicates': len(group)}
        for metric in metrics:
            values = [row[metric] for row in group]
            result[name][metric] = {'mean': float(np.mean(values)),
                                    'sd_across_seeds': float(np.std(values, ddof=1)) if len(values) > 1 else None}
    return result


def plot_trajectories(rows: list[dict], truth: float, path: Path):
    import matplotlib
    matplotlib.use('Agg')  # Works without a display or resident server.
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for name in dict.fromkeys(row['policy'] for row in rows):
        selected = [row for row in rows if row['policy'] == name]
        rounds = sorted({row['round'] for row in selected})
        for axis, metric in zip(axes, ('mean_belief', 'correct_choice_fraction')):
            means = [np.mean([row[metric] for row in selected if row['round'] == t]) for t in rounds]
            axis.plot(rounds, means, label=name.replace('_', ' '))
    axes[0].axhline(truth, color='black', linestyle='--', label='known simulated score')
    axes[0].axhline(0.5, color='gray', linestyle=':', label='A/B choice threshold')
    for axis, title, ylabel in zip(axes, ('Estimated score', 'Choice agreement with oracle'),
                                  ('Mean agent belief', 'Correct-choice fraction')):
        axis.set(title=title, xlabel='Round', ylabel=ylabel, ylim=(0, 1))
        axis.grid(alpha=0.2)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc='lower center', ncol=3, fontsize=9)
    figure.suptitle('Mesa toy simulation — mean trajectories across matched seeds')
    figure.tight_layout(rect=(0, 0.19, 1, 0.94))
    figure.savefig(path, dpi=160)
    plt.close(figure)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agents', type=int, default=60)
    parser.add_argument('--steps', type=int, default=50)
    parser.add_argument('--replicates', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--truth', type=float, default=0.70)
    parser.add_argument('--anchor', type=float, default=0.20)
    parser.add_argument('--learning-rate', type=float, default=0.25)
    parser.add_argument('--signal-noise', type=float, default=0.18)
    parser.add_argument('--anchoring', type=float, default=0.10)
    parser.add_argument('--confirmation', type=float, default=0.75)
    parser.add_argument('--conformity', type=float, default=0.35)
    parser.add_argument('--output', type=Path, default=Path('simulation_output'))
    parser.add_argument('--no-plot', action='store_true', help='Do not import matplotlib or generate PNG.')
    args = parser.parse_args(argv)
    try:
        config = Config(args.agents, args.steps, args.truth, args.anchor, args.learning_rate,
                        args.signal_noise, args.anchoring, args.confirmation, args.conformity)
        trajectories, agents, runs = run_experiment(config, args.replicates, args.seed)
    except ValueError as exc:
        parser.error(str(exc))
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / 'trajectories.csv', trajectories)
    write_csv(args.output / 'final_agents.csv', agents)
    write_csv(args.output / 'final_runs.csv', runs)
    summary = summarize(runs)
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    provenance = {'synthetic': True, 'empirically_validated': False, 'config': asdict(config),
                  'policies': [asdict(p) for p in policies(config)], 'replicates': args.replicates,
                  'seed_sequence': list(range(args.seed, args.seed + args.replicates)),
                  'python': sys.version, 'mesa': metadata.version('mesa'), 'numpy': metadata.version('numpy'),
                  'activation': 'synchronous propose/commit', 'paired_exogenous_inputs': True,
                  'note': 'No human data, psychological diagnosis, LLM calls or external services.'}
    (args.output / 'metadata.json').write_text(json.dumps(provenance, indent=2) + '\n')
    if not args.no_plot:
        plot_trajectories(trajectories, config.truth, args.output / 'dynamics.png')
    print('Illustrative simulation only; not a validated human behavioral model.')
    for name, values in summary.items():
        print(f"{name:19s} mean_belief={values['mean_belief']['mean']:.3f} "
              f"MAE={values['mean_absolute_error']['mean']:.3f} "
              f"correct_choice={values['correct_choice_fraction']['mean']:.1%}")
    print(f'Outputs: {args.output.resolve()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
