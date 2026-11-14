"""Run a vendored Mesa mechanism and return what each agent actually did.

This is the only module that touches sys.path for the vendored package.
"""
from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

MESA = Path(__file__).resolve().parents[1] / "mesa_bias_expanded"
if str(MESA) not in sys.path:
    sys.path.insert(0, str(MESA))

import expanded_mesa  # noqa: E402  (vendored; needs the path insert above)


@dataclass(frozen=True)
class Realized:
    concept: str
    scenario: dict
    seed: int
    strength: float
    agent: int
    active: bool          # the mechanism changed the reference behaviour in at least one step
    metric: float
    reference_metric: float
    state: dict
    trace: tuple[str, ...]


def scenario(concept: str, name: str) -> dict:
    plugin = expanded_mesa.load_plugin(concept)
    for s in expanded_mesa.teaching_scenarios(plugin, 12):
        if s["name"] == name:
            return deepcopy(s)
    raise KeyError(f"{concept} has no scenario named {name!r}")


def realize(concept: str, scenario: dict, *, seed: int = 42, strength: float = 0.8,
            n_agents: int = 12) -> tuple[Realized, ...]:
    reference = expanded_mesa.ExpandedDecisionModel(concept, deepcopy(scenario), n_agents, 0.0, seed).run_task()
    model = expanded_mesa.ExpandedDecisionModel(concept, deepcopy(scenario), n_agents, strength, seed).run_task()
    base = {a.index: a.metric for a in reference.agents}
    out = []
    for a in sorted(model.agents, key=lambda a: a.index):
        steps = [t for t in model.traces if t["agent"] == a.index]
        out.append(Realized(concept, deepcopy(scenario), seed, float(strength), a.index,
                            any(t["active"] for t in steps), float(a.metric), float(base[a.index]),
                            deepcopy(a.state), tuple(line for t in steps for line in t["trace"])))
    return tuple(out)
