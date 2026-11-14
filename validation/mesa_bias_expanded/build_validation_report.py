#!/usr/bin/env python3
"""Summarize actual execution, keeping synthetic coverage distinct from validity."""
from collections import Counter
from pathlib import Path
import csv
import json
import xml.etree.ElementTree as ET
import expanded_mesa as engine

ROOT=Path(__file__).resolve().parent


def main():
    coverage=json.loads((ROOT/'results/coverage.json').read_text())
    summary=json.loads((ROOT/'results/sweep/summary.json').read_text())
    run=json.loads((ROOT/'results/sweep/run_metadata.json').read_text())
    errors=json.loads((ROOT/'results/sweep/failures.json').read_text())
    initial_path=ROOT/'results/sweep_first_attempt/failures.json'
    initial_errors=json.loads(initial_path.read_text()) if initial_path.exists() else []
    checks=[]
    expected_keys=set()
    for concept in engine.expected_ids():
        scenarios=engine.teaching_scenarios(engine.load_plugin(concept),run['agents'])
        expected_keys.update((concept,s['name']) for s in scenarios)
    for row in summary:
        scenarios={s['name']:s for s in engine.teaching_scenarios(engine.load_plugin(row['concept']),run['agents'])}
        expectation=scenarios[row['scenario']]['expectation']
        checks.append({'concept':row['concept'],'scenario':row['scenario'],
                       'expectation':expectation,'mean_paired_delta':row['mean_paired_delta'],
                       'passed':engine.expectation_holds(row['mean_paired_delta'],expectation)})
    expectation_report={'checked_scenarios':len(checks),
                        'passed_scenarios':sum(c['passed'] for c in checks),
                        'failed_scenarios':sum(not c['passed'] for c in checks),'checks':checks,
                        'note':'Synthetic task-level means across matched seeds; not independent empirical validation.'}
    (ROOT/'results/sweep/expectation_checks.json').write_text(json.dumps(expectation_report,indent=2)+'\n')
    with (ROOT/'results/sweep/paired_agents.csv').open() as file:
        paired_rows=sum(1 for _ in csv.DictReader(file))
    with (ROOT/'results/sweep/traces.jsonl').open() as file:
        trace_rows=sum(1 for _ in file)
    suites=list(ET.parse(ROOT/'results/pytest_results.xml').getroot().iter('testsuite'))
    tests=sum(int(s.attrib.get('tests',0)) for s in suites)
    failures=sum(int(s.attrib.get('failures',0))+int(s.attrib.get('errors',0)) for s in suites)
    skipped=sum(int(s.attrib.get('skipped',0)) for s in suites)
    passed=tests-failures-skipped
    kinds=dict(Counter(r.get('kind','ERROR') for r in coverage['results']))
    ids={r['concept'] for r in summary}
    status={'expected_new_modules':138,'passing_executable_contracts':coverage['passing_contracts'],
            'pytest_passed':passed,'pytest_failed_or_error':failures,'pytest_skipped':skipped,
            'sweep_completed_concepts':len(ids),'sweep_completed_scenarios':len(summary),
            'sweep_execution_failures':len(errors),'module_kinds':kinds,
            'empirically_validated':False,'synthetic_only':True,
            'sweep_expectation_checks_passed':expectation_report['passed_scenarios'],
            'sweep_expectation_checks_failed':expectation_report['failed_scenarios'],
            'paired_agent_rows':paired_rows,'agent_step_trace_rows':trace_rows,
            'first_sweep_execution_failures':initial_errors,
            'legacy_direct_rules_retained':coverage['legacy_direct_rules_retained'],
            'legacy_partial_proxies_not_upgraded':coverage['legacy_partial_proxies_not_upgraded']}
    status['software_scope_complete']=(coverage['passing_contracts']==138 and failures==0 and
                                       skipped==0 and len(ids)==138 and len(errors)==0 and
                                       expectation_report['failed_scenarios']==0 and
                                       {(r['concept'],r['scenario']) for r in summary}==expected_keys)
    (ROOT/'results/FINAL_STATUS.json').write_text(json.dumps(status,indent=2)+'\n')
    text=f'''# Executed validation of the 138-module Mesa expansion

**Executable scope complete: {status['software_scope_complete']}.** The run reports {coverage['passing_contracts']}/138 passing process contracts, {passed} passed pytest cases, {failures} failed/error cases, and {skipped} skips. The paired sweep completed {len(ids)} concepts and {len(summary)} named task scenarios with {len(errors)} execution failures.

All {expectation_report['passed_scenarios']}/{len(checks)} larger-sweep scenario means met their declared directional or boundary-equality expectations. This includes {paired_rows} paired-agent observations and {trace_rows} agent-step trace records. The pytest suite includes a complete standalone-script contract check in a temporary folder without the modular source directory.

The exact missing scope comprises 138 canonical entries: 112 from the attachment's cognitive-concept layer and 26 from its other source layers. Source-layer labels are not psychological classifications; the implemented registry distinguishes biases, heuristics, learning/motivational effects, psychological states and media practices. Each entry has distinct source metadata, executable process code, task inputs/state, an explicit reference policy, positive and boundary scenarios, a module-specific test file, and an implementation note. Source labels, source variants and annotation boundaries are retained in `missing_concepts.json`.

The paired sweep used {run['agents']} agents per condition, {run['replicates']} seeds, and strength {run['strength']} versus strength zero. Agent conditions received matched input scenarios and uniform random draws. Scenarios run their own number of chronological contexts; a one-step choice is not presented as longitudinal evidence. Metrics have concept-specific units and are never reduced to one global bias score.

`coverage.json` contains every contract's actual directional comparison. `pytest_results.xml` and `pytest_results.txt` retain executed software cases. `sweep/paired_agents.csv` and `sweep/traces.jsonl` preserve numeric observables, paired differences and per-agent process traces. `sweep/summary.json` reports seed-level comparisons and between-seed variation. No dropped or failed output is replaced with a fabricated negative result.

The unchanged original anchoring/confirmation demonstration is retained in `legacy_mesa_model.py`, with its regression cases. The original bandwagon/social-norms peer averaging remains explicitly partial and is not silently declared a full implementation by this expansion.

## First larger sweep and repair

The first 12-agent sweep had {len(initial_errors)} recorded execution failure(s). Its raw outputs are retained in `results/sweep_first_attempt`, not discarded. The pluralistic-ignorance teaching fixture described three people and therefore rejected larger agent indexes. An opt-in built-in population factory now creates complete hypothetical group vectors for the chosen agent count under the same teaching assumptions. Custom group data are never resized or inferred. New 12- and 50-agent tests preserve private-expression reference behavior, the no-misperception boundary, and strict rejection of mismatched custom groups. The final sweep above was executed again after this integration repair.

## What passing these checks does not establish

These are implementation-authored, synthetic task models. Passing a positive example, a boundary control, and an equation oracle establishes code behavior under those assumptions. It does not independently establish expert validity, human-population behavior, effect size, construct identification, causal inference, model calibration or detection accuracy. The model has no natural-language/image detector and cannot diagnose bias in an actual person or newsroom.

Heuristics and learning/motivational effects are preserved as potentially useful processes rather than blanket errors. Media practices are structured presentation-process models, not evidence that a publisher acted deceptively. Narrow or uncertain effects are only hypothesized rules, not universal empirical facts.

Models use explicit task state and freeze peer snapshots before proposals. Default agent populations share the teaching scenario; deterministic effects can be identical across agents/seeds. More copies of a synthetic rule are not independent human observations. Combining incompatible units or automatically layering all 138 mechanisms into one decision is unsupported; joint modeling requires a separately designed, compatible task and update policy.

## Reproduce

```bash
python -m pip install -r requirements.txt
python -m pytest -q --junitxml=results/pytest_results.xml
python expanded_mesa.py validate --output results/coverage.json
python expanded_mesa.py sweep --agents 12 --replicates 3 --output results/sweep
python build_validation_report.py
python export_single_file.py
```

The standalone `expanded_mesa_biases.py` embeds the exact same source code, definitions and scenarios. It requires Mesa 3.5.2 and NumPy at runtime, not the module directory or pytest. The source package includes tests and implementation notes for inspectability.
'''
    (ROOT/'VALIDATION.md').write_text(text,encoding='utf-8')
    print(json.dumps(status,indent=2))
    if not status['software_scope_complete']:
        raise SystemExit(2)


if __name__=='__main__':
    main()
