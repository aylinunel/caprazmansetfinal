#!/usr/bin/env python3
"""Task-specific Mesa extension for 138 missing concepts from the user attachment.

Illustrative process models, not fitted human psychology or news/clinical detectors.
Use --help. No model APIs, credentials, web access, or paid services at runtime.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from functools import lru_cache
import hashlib
import importlib
from importlib import metadata as distribution_metadata
import json
import math
from pathlib import Path
import sys
import types

import mesa
import numpy as np

ROOT = Path(__file__).resolve().parent
# The single-file exporter supplies these constants before this runner's source.
EMBEDDED_MANIFEST = globals().get('EMBEDDED_MANIFEST', None)
EMBEDDED_SOURCES = globals().get('EMBEDDED_SOURCES', None)


def manifest():
    if EMBEDDED_MANIFEST is not None:
        return deepcopy(EMBEDDED_MANIFEST)
    return json.loads((ROOT / 'missing_concepts.json').read_text(encoding='utf-8'))


def expected_ids():
    return [item['id'] for item in manifest()]


def json_safe(value):
    """Forbid NaN/Infinity, unserializable objects and non-JSON state."""
    return json.loads(json.dumps(value, allow_nan=False, ensure_ascii=False))


def valid_strength(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    return float(value)


def positive_integer(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


@lru_cache(maxsize=150)
def load_plugin(concept_id):
    if concept_id not in expected_ids():
        raise ValueError(f'Unknown or out-of-scope concept: {concept_id}')
    if EMBEDDED_SOURCES is not None:
        # Only fixed source text embedded by our exporter is executed. User JSON
        # is always data, never executable code. Plugins have no external imports.
        if concept_id not in EMBEDDED_SOURCES:
            raise RuntimeError(f'Missing embedded implementation: {concept_id}')
        module = types.ModuleType('mechanisms.' + concept_id)
        module.__file__ = f'<embedded:{concept_id}>'
        if 'mechanisms' not in sys.modules:
            package = types.ModuleType('mechanisms')
            package.__path__ = []
            sys.modules['mechanisms'] = package
        sys.modules[module.__name__] = module
        exec(compile(EMBEDDED_SOURCES[concept_id], f'<embedded:{concept_id}>', 'exec'), module.__dict__)
    else:
        module = importlib.import_module('mechanisms.' + concept_id)
    required = ('id', 'name', 'kind', 'description', 'required_inputs', 'state_fields',
                'metric_name', 'metric_units', 'assumptions', 'limitations',
                'empirically_validated', 'synthetic_only')
    md = getattr(module, 'METADATA', None)
    if not isinstance(md, dict) or any(key not in md for key in required):
        raise ValueError(f'{concept_id}: incomplete mechanism metadata')
    if md['id'] != concept_id or md['empirically_validated'] is not False or md['synthetic_only'] is not True:
        raise ValueError(f'{concept_id}: incorrect scope or unsupported validation claim')
    allowed_kinds = {'cognitive_bias', 'media_practice', 'heuristic', 'learning_effect',
                     'motivational_mechanism', 'psychological_state'}
    if md['kind'] not in allowed_kinds:
        raise ValueError(f'{concept_id}: unrecognized mechanism kind')
    for key in ('required_inputs', 'state_fields', 'assumptions', 'limitations'):
        if not isinstance(md[key], list) or not all(isinstance(x, str) for x in md[key]):
            raise ValueError(f'{concept_id}: {key} must be a list of strings')
    if not callable(getattr(module, 'evaluate', None)) or not callable(getattr(module, 'scenarios', None)):
        raise ValueError(f'{concept_id}: missing executable process or scenarios')
    return module


def teaching_scenarios(plugin, n_agents):
    """Build teaching inputs for the requested population, only when opted in.

    Explicit user-supplied scenarios are never resized or rewritten. Factories
    are authored toy-task generators, not estimates of population distributions.
    """
    positive_integer(n_agents, 'n_agents', minimum=2)
    factory = getattr(plugin, 'scenarios_for_population', None)
    return factory(n_agents) if callable(factory) else plugin.scenarios()


def checked_evaluate(plugin, context, strength):
    strength = valid_strength(strength)
    before = json_safe(context)
    for key in plugin.METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f"{plugin.METADATA['id']}: missing required task input {key}")
    result = plugin.evaluate(context, strength)
    if json_safe(context) != before:
        raise ValueError(f"{plugin.METADATA['id']}: plugin mutated the input context")
    if not isinstance(result, dict) or any(key not in result for key in ('metric', 'state', 'trace', 'active')):
        raise ValueError(f"{plugin.METADATA['id']}: invalid process result")
    metric = result['metric']
    if isinstance(metric, bool) or not isinstance(metric, (int, float)) or not math.isfinite(metric):
        raise ValueError(f"{plugin.METADATA['id']}: non-finite or non-numeric metric")
    if not isinstance(result['state'], dict) or not isinstance(result['active'], bool):
        raise ValueError(f"{plugin.METADATA['id']}: invalid state or active flag")
    if not isinstance(result['trace'], list) or not result['trace'] or not all(isinstance(t, str) for t in result['trace']):
        raise ValueError(f"{plugin.METADATA['id']}: trace must be a nonempty list of strings")
    return json_safe(result)


def check_scenario(scenario):
    if not isinstance(scenario, dict) or not isinstance(scenario.get('name'), str):
        raise ValueError('Scenario must include a name')
    if not isinstance(scenario.get('initial_state'), dict):
        raise ValueError('Scenario requires an explicit initial_state object')
    contexts = scenario.get('contexts')
    if not isinstance(contexts, list) or not contexts or not all(isinstance(c, dict) for c in contexts):
        raise ValueError('Scenario contexts must be a nonempty chronological list of objects')
    reserved = {'state', 'peer_states', 'round_index', 'agent_index', 'uniform'}
    if any(reserved.intersection(c) for c in contexts):
        raise ValueError('Task contexts cannot override reserved runner state or random inputs')
    if scenario.get('expectation') not in ('increase', 'decrease', 'difference', 'equal'):
        raise ValueError('Scenario needs an explicit expected comparison')
    return json_safe(scenario)


class TaskAgent(mesa.Agent):
    """An agent has concept-specific task state, not one universal belief scalar."""
    def __init__(self, model, index):
        super().__init__(model)
        self.index = index
        self.state = deepcopy(model.scenario_data['initial_state'])
        self.metric = None
        self.active = False
        self.proposed = None

    def propose(self):
        m = self.model
        context = deepcopy(m.scenario_data['contexts'][m.round_index])
        context.update({'state': deepcopy(m.previous_states[self.index]),
                        'peer_states': [deepcopy(m.previous_states[i]) for i in m.neighbors[self.index]],
                        'round_index': m.round_index, 'agent_index': self.index,
                        'uniform': float(m.uniforms[m.round_index, self.index])})
        self.proposed = checked_evaluate(m.plugin, context, m.strength)

    def commit(self):
        self.state = deepcopy(self.proposed['state'])
        self.metric = float(self.proposed['metric'])
        self.active = self.proposed['active']
        self.model.traces.append({'concept': self.model.concept_id,
                                  'scenario': self.model.scenario_data['name'],
                                  'seed': self.model.run_seed,
                                  'strength': self.model.strength,
                                  'round': self.model.round_index + 1,
                                  'agent': self.index, **deepcopy(self.proposed)})


class ExpandedDecisionModel(mesa.Model):
    """Run one justified task model at a time; incompatible tasks are not combined."""
    def __init__(self, concept_id, scenario=None, n_agents=12, strength=0.8, seed=42):
        positive_integer(n_agents, 'n_agents', minimum=2)
        positive_integer(seed, 'seed', minimum=0)
        self.strength = valid_strength(strength)
        super().__init__(rng=seed)
        self.concept_id = concept_id
        self.plugin = load_plugin(concept_id)
        supplied = teaching_scenarios(self.plugin, n_agents)[0] if scenario is None else scenario
        self.scenario_data = check_scenario(supplied)
        self.run_seed = seed
        self.round_index = 0
        self.traces = []
        # Common random inputs are exogenous and independent of strength or actions.
        self.uniforms = self.rng.random((len(self.scenario_data['contexts']), n_agents))
        self.neighbors = [sorted({(i-1) % n_agents, (i+1) % n_agents} - {i}) for i in range(n_agents)]
        for index in range(n_agents):
            TaskAgent(self, index)
        self.previous_states = self.snapshot()
        self.datacollector = mesa.DataCollector(model_reporters={
            'round': lambda m: m.round_index,
            'mean_metric': lambda m: float(np.mean([a.metric for a in m.agents])) if m.round_index else None,
            'metric_sd': lambda m: float(np.std([a.metric for a in m.agents])) if m.round_index else None,
            'active_fraction': lambda m: float(np.mean([a.active for a in m.agents])),
        })
        self.datacollector.collect(self)

    def snapshot(self):
        result = [None] * len(self.agents)
        for agent in self.agents:
            result[agent.index] = deepcopy(agent.state)
        return result

    def step(self):
        if self.round_index >= len(self.scenario_data['contexts']):
            self.running = False
            return
        self.previous_states = self.snapshot()
        self.agents.do('propose')
        self.agents.do('commit')
        self.round_index += 1
        self.datacollector.collect(self)
        self.running = self.round_index < len(self.scenario_data['contexts'])

    def run_task(self):
        for _ in self.scenario_data['contexts']:
            self.step()
        return self


def paired_run(concept_id, scenario, n_agents, strength, seed):
    reference = ExpandedDecisionModel(concept_id, scenario, n_agents, 0.0, seed).run_task()
    intervention = ExpandedDecisionModel(concept_id, scenario, n_agents, strength, seed).run_task()
    rows = []
    reference_by_index = {a.index: a for a in reference.agents}
    for a in intervention.agents:
        base = reference_by_index[a.index]
        rows.append({'concept': concept_id, 'scenario': scenario['name'], 'seed': seed,
                     'agent': a.index, 'strength': strength, 'reference_metric': base.metric,
                     'intervention_metric': a.metric, 'paired_delta': a.metric-base.metric,
                     'active': a.active, 'metric_name': intervention.plugin.METADATA['metric_name'],
                     'metric_units': intervention.plugin.METADATA['metric_units']})
    return rows, reference.traces + intervention.traces


def summarize_pairs(rows):
    grouped = {}
    for row in rows:
        key = (row['concept'], row['scenario'])
        grouped.setdefault(key, []).append(row)
    summaries = []
    for (concept, scenario), group in grouped.items():
        # Sampling unit is the seed, NOT every synthetic agent as an independent subject.
        seeds = sorted({r['seed'] for r in group})
        per_seed = [float(np.mean([r['paired_delta'] for r in group if r['seed'] == s])) for s in seeds]
        summaries.append({'concept': concept, 'scenario': scenario, 'replicates': len(seeds),
                          'paired_agent_rows': len(group), 'metric_name': group[0]['metric_name'],
                          'metric_units': group[0]['metric_units'],
                          'mean_reference_metric': float(np.mean([r['reference_metric'] for r in group])),
                          'mean_intervention_metric': float(np.mean([r['intervention_metric'] for r in group])),
                          'mean_paired_delta': float(np.mean(per_seed)),
                          'sd_paired_delta_across_seeds': float(np.std(per_seed, ddof=1)) if len(seeds)>1 else None})
    return summaries


def expectation_holds(delta, expectation, tolerance=1e-9):
    return {'increase': delta > tolerance, 'decrease': delta < -tolerance,
            'difference': abs(delta) > tolerance, 'equal': abs(delta) <= tolerance}[expectation]


def validate_one(concept_id):
    """Executable-contract check only; not expert or empirical validation."""
    plugin = load_plugin(concept_id)
    scenarios = plugin.scenarios()
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError('Missing scenarios')
    names = [s.get('name') for s in scenarios]
    if len(set(names)) != len(names) or not {'positive','boundary'}.issubset(names):
        raise ValueError('Need unique positive and boundary scenarios')
    checks = []
    for scenario in scenarios:
        scenario = check_scenario(scenario)
        if scenario['name']=='boundary' and scenario['expectation']!='equal':
            raise ValueError('Boundary scenario must use equal expectation')
        if scenario['name']=='positive' and scenario['expectation']=='equal':
            raise ValueError('Positive scenario needs a nonzero process effect')
        rows, _ = paired_run(concept_id, scenario, 3, 0.8, 42)
        delta = float(np.mean([r['paired_delta'] for r in rows]))
        passed = expectation_holds(delta, scenario['expectation'])
        checks.append({'name':scenario['name'],'expected':scenario['expectation'],
                       'delta':delta,'passed':passed})
    return {'id': concept_id, 'kind': plugin.METADATA['kind'],
            'status': 'PASS' if all(c['passed'] for c in checks) else 'FAIL',
            'checks': checks, 'empirically_validated': False}


def coverage():
    rows = []
    for concept in expected_ids():
        try:
            rows.append(validate_one(concept))
        except Exception as exc:
            rows.append({'id':concept,'status':'ERROR','error_type':type(exc).__name__,
                         'error':str(exc),'empirically_validated':False})
    return {'expected_new_mechanisms':len(expected_ids()),
            'passing_contracts':sum(r['status']=='PASS' for r in rows),
            'failed_or_missing_contracts':sum(r['status']!='PASS' for r in rows),
            'synthetic_only':True,'empirically_validated':False,'results':rows,
            'legacy_direct_rules_retained':['anchoring_bias','confirmation_bias'],
            'legacy_partial_proxies_not_upgraded':['bandwagon_effect','social_norms']}


def save_csv(path, rows):
    if not rows:
        path.write_text('', encoding='utf-8')
        return
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list', help='List exact scope and source layers')
    describe = sub.add_parser('describe', help='Inspect assumptions, fields and scenarios')
    describe.add_argument('concept')
    validate = sub.add_parser('validate', help='Fail unless every plugin passes its executable contract')
    validate.add_argument('--output', type=Path, default=Path('expanded_results/coverage.json'))
    for name in ('run','sweep'):
        cmd = sub.add_parser(name, help='Run paired task-specific agents against strength-zero references')
        if name=='run':
            cmd.add_argument('concept')
            cmd.add_argument('--scenario', default='positive')
            cmd.add_argument('--scenario-file', type=Path, help='JSON scenario; data only, never evaluated as code')
        cmd.add_argument('--agents', type=int, default=12)
        cmd.add_argument('--replicates', type=int, default=3)
        cmd.add_argument('--seed', type=int, default=42)
        cmd.add_argument('--strength', type=float, default=0.8)
        cmd.add_argument('--output', type=Path, default=Path('expanded_results'))
    args = parser.parse_args(argv)
    if args.command=='list':
        print(json.dumps([{'id':i['id'],'name':i['name'],'source_layer':i['layer']} for i in manifest()], indent=2, ensure_ascii=False))
        return 0
    if args.command=='describe':
        p = load_plugin(args.concept)
        print(json.dumps({'metadata':p.METADATA,'scenarios':p.scenarios()},indent=2,ensure_ascii=False,allow_nan=False))
        return 0
    if args.command=='validate':
        result = coverage()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        save_json(args.output,result)
        print(f"{result['passing_contracts']}/{result['expected_new_mechanisms']} executable contracts passed; {result['failed_or_missing_contracts']} failed/missing. Not empirical validation.")
        return 0 if result['failed_or_missing_contracts']==0 else 2
    try:
        positive_integer(args.agents,'agents',2)
        positive_integer(args.replicates,'replicates')
        positive_integer(args.seed,'seed',0)
        valid_strength(args.strength)
    except ValueError as exc:
        parser.error(str(exc))
    ids = [args.concept] if args.command=='run' else expected_ids()
    all_rows, all_traces, errors = [], [], []
    args.output.mkdir(parents=True,exist_ok=True)
    for concept in ids:
        try:
            p=load_plugin(concept)
            if args.command=='run' and args.scenario_file:
                scenarios=[check_scenario(json.loads(args.scenario_file.read_text(encoding='utf-8')))]
            else:
                scenarios=[check_scenario(s) for s in teaching_scenarios(p, args.agents)
                           if args.command=='sweep' or s['name']==args.scenario]
            if not scenarios:
                raise ValueError('Requested scenario not found')
            for scenario in scenarios:
                for seed in range(args.seed,args.seed+args.replicates):
                    rows,traces=paired_run(concept,scenario,args.agents,args.strength,seed)
                    all_rows.extend(rows);all_traces.extend(traces)
            print(f'Completed {concept}: {len(scenarios)} task scenarios',flush=True)
        except Exception as exc:
            errors.append({'concept':concept,'error_type':type(exc).__name__,'error':str(exc)})
            print(f'FAILED {concept}: {exc}',file=sys.stderr,flush=True)
    save_csv(args.output/'paired_agents.csv',all_rows)
    save_json(args.output/'summary.json',summarize_pairs(all_rows))
    with (args.output/'traces.jsonl').open('w',encoding='utf-8') as f:
        for row in all_traces:
            f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
    save_json(args.output/'failures.json',errors)
    save_json(args.output/'run_metadata.json',{
        'synthetic_only':True,'empirically_validated':False,'requested_concepts':ids,
        'failed_concepts':len(errors),'agents':args.agents,'replicates':args.replicates,
        'seeds':list(range(args.seed,args.seed+args.replicates)), 'strength':args.strength,
        'activation':'synchronous propose/commit','paired_exogenous_inputs':True,
        'python':sys.version,'mesa':distribution_metadata.version('mesa'),
        'numpy':distribution_metadata.version('numpy'),
        'note':'Metrics are task-specific and must not be averaged across incompatible units. Default populations are homogeneous unless task inputs or matched uniforms generate differences.'})
    return 2 if errors else 0


if __name__=='__main__':
    raise SystemExit(main())
