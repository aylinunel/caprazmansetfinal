#!/usr/bin/env python3
"""Synthetic offline boundary demo; mock outputs are NOT a real detector evaluation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import re
from typing import Literal, Protocol

import numpy as np

ROOT = Path(os.environ.get('MESA_BIAS_ROOT', '/home/ubuntu/mesa_bias_expanded')).expanduser()
TARGET = 'demo:media/presentation_denominator_mismatch'
# Explicit DEMO extension only; NOT an installed or validated BiasGuard crosswalk.
CROSSWALK = {'selective_statistics': TARGET}
HEADER = 'SYNTHETIC/DEMO — not real news. '
FAMILIES = {
    'denominator_claim_v1': ('dev', 'For the full comparison cohort, {count} events occurred among {used} members.'),
    'denominator_claim_v2': ('test', 'Within the full comparison cohort, {count} events were reported among {used} members.'),
}
Status = Literal['supported', 'not_supported', 'uncertain', 'unsupported', 'error']


def load(path: Path):
    spec = spec_from_file_location(path.stem, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class DetectorInput:
    text: str                         # Original, unnormalized source field.
    context: str | None = None         # Separate supplied documentary evidence.


@dataclass(frozen=True)
class Evidence:
    source: Literal['text', 'context']
    quote: str
    start: int                        # Python character index, inclusive.
    end: int                          # Exclusive, in the declared original field.


@dataclass(frozen=True)
class Assessment:
    category: str
    status: Status
    assessment_eligible: bool
    reason: str
    evidence: tuple[Evidence, ...] = ()
    contract_only: bool = True         # This example never produces real findings.


class Detector(Protocol):
    def assess(self, request: DetectorInput, target_id: str) -> Assessment: ...


def render(task: dict, process: dict, family_id: str) -> DetectorInput:
    """Whitelist observable prose and supplied facts; never forward process/state."""
    _, template = FAMILIES[family_id]
    text = HEADER + template.format(count=task['event_count'],
                                   used=process['state']['last_denominator_used'])
    context = (HEADER + f"The full comparison cohort contains {task['relevant_denominator']} members. "
               f"All {task['event_count']} counted events belong to both that cohort and "
               f"the {task['selected_denominator']}-member subgroup. "
               f"Evidence basis: {task['denominator_evidence']['basis']}.")
    return DetectorInput(text, context)


def span(request: DetectorInput, source: str, quote: str) -> Evidence:
    original = getattr(request, source)
    start = original.index(quote)
    return Evidence(source, quote, start, start + len(quote))


class MockContractDetector:
    """Fixture parser ONLY: no NLP accuracy, calibrated probability, or intent claim."""
    def assess(self, request: DetectorInput, target_id: str) -> Assessment:
        def result(status, eligible, reason, evidence=()):
            return Assessment(target_id, status, eligible, reason, evidence)
        if target_id != TARGET:
            return result('unsupported', False, 'Unknown/unmapped target; not a negative finding.')
        if not isinstance(request.text, str) or not request.text.strip():
            raise ValueError('Original text must be nonempty.')
        claim = re.search(r'(?:For|Within) the full comparison cohort, (\d+) events '
                          r'(?:occurred|were reported) among (\d+) members\.', request.text)
        if not claim:
            return result('uncertain', False, 'Outside this mock fixture grammar.')
        claim_evidence = (span(request, 'text', claim.group(0)),)
        if not request.context:
            return result('uncertain', False, 'Comparison evidence missing; not a negative finding.', claim_evidence)
        cohort = re.search(r'The full comparison cohort contains (\d+) members\.', request.context)
        membership = re.search(r'All (\d+) counted events belong to both that cohort and '
                               r'the (\d+)-member subgroup\.', request.context)
        basis = re.search(r'Evidence basis: (.+)\.', request.context)
        if not (cohort and membership and basis and basis.group(1).strip()):
            return result('uncertain', False, 'Needed cohort/membership/basis evidence missing.', claim_evidence)
        count, used = map(int, claim.groups())
        relevant = int(cohort.group(1))
        fact_count, subgroup = map(int, membership.groups())
        if min(used, relevant, subgroup) <= 0 or count != fact_count or count > min(relevant, subgroup) or used not in {relevant, subgroup}:
            return result('uncertain', False, 'Facts inconsistent or denominator unaccounted for.', claim_evidence)
        evidence = claim_evidence + tuple(span(request, 'context', match.group(0))
                                          for match in (cohort, membership, basis))
        return result('supported' if used != relevant else 'not_supported', True,
                      'Supplied facts support a presentation denominator mismatch.' if used != relevant
                      else 'Presented denominator matches the supplied comparison cohort.', evidence)


def safe_assess(detector: Detector, request: DetectorInput, target_id: str) -> Assessment:
    try:
        return detector.assess(request, target_id)
    except Exception as exc:
        return Assessment(target_id, 'error', False, f'Contract execution failed: {type(exc).__name__}')


def build_records():
    runner = load(ROOT / 'expanded_mesa.py')
    plugin = load(ROOT / 'mechanisms/selective_statistics.py')
    assert plugin.METADATA['kind'] == 'media_practice'
    records = []
    for scenario in plugin.scenarios():
        # Runner-compatible shape/seed; index 0 of three agents, same draw in each arm.
        uniform = float(np.random.default_rng(42).random((len(scenario['contexts']), 3))[0, 0])
        task = scenario['contexts'][0]
        for strength in (0.8, 0.0):
            private = dict(task, state=scenario['initial_state'].copy(), uniform=uniform)
            process = runner.checked_evaluate(plugin, private, strength)
            for family_id, (split, _) in FAMILIES.items():
                records.append({
                    'synthetic': True, 'demo': True, 'real_news': False,
                    'family_id': family_id, 'split': split, 'scenario': scenario['name'],
                    'private_simulation': {'strength': strength, 'uniform': uniform, **process},
                    'expected_observation': 'supported' if process['active'] else 'not_supported',
                    'input': render(task, process, family_id),
                })
    # Context ablations stay in the same reserved family as their originating pair.
    for record in records.copy():
        if record['scenario'] == 'positive' and record['private_simulation']['strength'] == 0.8:
            records.append({**record, 'control': 'context_removed', 'expected_observation': 'uncertain',
                            'input': replace(record['input'], context=None)})
    return records


def smoke_tests(records):
    detector = MockContractDetector()
    positive = next(r for r in records if r['scenario'] == 'positive' and r['private_simulation']['strength'] == 0.8)
    request = positive['input']
    outcome = safe_assess(detector, request, CROSSWALK['selective_statistics'])
    assert set(asdict(request)) == {'text', 'context'}
    assert not any(word in (request.text + request.context) for word in
                   ('strength', 'uniform', 'state', 'expected_observation', 'positive', 'boundary', 'family_id'))
    assert outcome.status == 'supported' and outcome.assessment_eligible
    assert {e.source for e in outcome.evidence} == {'text', 'context'}
    assert all(getattr(request, e.source)[e.start:e.end] == e.quote for e in outcome.evidence)
    assert outcome.evidence[0].start == len(HEADER)  # Includes original Unicode prefix.
    removed = safe_assess(detector, replace(request, context=None), TARGET)
    assert removed.status == 'uncertain' and not removed.assessment_eligible
    incomplete = replace(request, context=HEADER + 'The full comparison cohort contains 100 members.')
    assert safe_assess(detector, incomplete, TARGET).status == 'uncertain'
    assert safe_assess(detector, request, 'unmapped').status == 'unsupported'
    assert safe_assess(detector, DetectorInput(''), TARGET).status == 'error'
    for family_id, (split, _) in FAMILIES.items():
        group = [r for r in records if r['family_id'] == family_id and 'control' not in r]
        assert {r['split'] for r in records if r['family_id'] == family_id} == {split}
        for scenario in ('positive', 'boundary'):
            pair = [r for r in group if r['scenario'] == scenario]
            assert pair[0]['private_simulation']['uniform'] == pair[1]['private_simulation']['uniform']
            assert (pair[0]['input'] == pair[1]['input']) == (scenario == 'boundary')
            assert pair[0]['input'].context == pair[1]['input'].context
    for record in records:
        actual = safe_assess(detector, record['input'], TARGET)
        assert actual.status == record['expected_observation']
        assert actual.contract_only
    # State history cannot alter observable rendering when the used denominator is fixed.
    plugin = load(ROOT / 'mechanisms/selective_statistics.py')
    task = plugin.scenarios()[0]['contexts'][0]
    process = positive['private_simulation']
    changed = {**process, 'state': {**process['state'], 'steps_evaluated': 999, 'secret': 'LEAK_SENTINEL'}}
    assert render(task, process, positive['family_id']) == render(task, changed, positive['family_id'])
    return 'PASS: leakage, evidence, original spans, ablations, unsupported/error, matched pairs, family reservation, fixture outcomes'


def main():
    records = build_records()
    checks = smoke_tests(records)
    detector = MockContractDetector()
    output = [{**record, 'input': asdict(record['input']),
               'mock_assessment': asdict(safe_assess(detector, record['input'], TARGET))}
              for record in records]
    print(json.dumps({'notice': 'MOCK CONTRACT ONLY — NOT A REAL DETECTOR EVALUATION',
                      'smoke_tests': checks, 'records': output}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
