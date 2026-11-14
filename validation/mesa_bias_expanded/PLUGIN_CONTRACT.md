# Contract for illustrative Mesa mechanism plugins

Implement exactly your assigned concept from `specs/<id>.json`. Do not edit the shared engine or another plugin. Modules are task-specific, assumed process models, not classifiers, diagnoses, population claims, or fitted psychology. No external LLM/API access or paid calls are required.

Write `mechanisms/<id>.py`, `tests/test_<id>.py`, and `specs/<id>_implementation.md`. Use only Python standard library inside plugins; pytest is available for tests. Import as `from mechanisms import <id>`. Test with `/home/ubuntu/mesa_bias_sample/.venv/bin/python -m pytest -q tests/test_<id>.py` from `/home/ubuntu/mesa_bias_expanded`.

## Required module interface

```python
METADATA = {
    'id': '<id>',
    'name': '...',
    'kind': 'cognitive_bias',  # or media_practice, heuristic, learning_effect,
                              # motivational_mechanism, psychological_state
    'description': 'The explicit task-specific process being simulated.',
    'required_inputs': ['...'],  # scenario fields, excluding reserved runner fields
    'state_fields': ['...'],
    'metric_name': '...',
    'metric_units': '...',
    'assumptions': ['...'],
    'limitations': ['...'],
    'empirically_validated': False,
    'synthetic_only': True,
}

def evaluate(context: dict, strength: float) -> dict:
    # Do not mutate context or nested values. Do not use random/time/network/files.
    # Reject non-finite strengths or strengths outside [0,1] with ValueError.
    # Validate required inputs: missing/impossible evidence is an error, not a zero.
    # context['state'] is an independent copy of this agent's previous task state.
    # context['peer_states'] are copies of neighbors' prior states, not live objects.
    # context['round_index'], context['agent_index'], context['uniform'] are available.
    # Use supplied uniform only if a stochastic choice is needed.
    return {
        'metric': 0.0,  # finite numeric primary task observable, NOT always belief
        'active': False,  # bool: mechanism changes baseline in this specific step
        'state': {},  # complete next task state; preserve relevant prior fields
        'trace': ['Explain the actual equation/condition and inputs used.'],
    }

def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{'field': 'task-specific data'}],
            'expectation': 'increase',  # increase, decrease, or difference
            # compare final metric at strength=.8 against strength=0 on same inputs
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{'field': 'data removing a NECESSARY condition'}],
            'expectation': 'equal',
        },
    ]
```

Both scenario names are required. Extra named scenarios are allowed. Contexts are chronological per-round task inputs. At least one context per scenario. Temporal concepts must provide multiple contexts and explicitly carry or evaluate relevant history, not replace chronology with a scalar “bias score”. Runner injects reserved state, peer_states, round_index, agent_index and matched uniform draws; do not put those reserved keys inside scenario contexts. Supply initial_state to initialize agents. Simulation runs exactly the length of contexts; no fictitious extra steps.

The strength-zero comparator must be an explicit, justified reference policy on the same task, not a guarantee of perfect rationality. Positive scenarios must yield a measurable concept-specific effect at .8; boundary scenarios remove a necessary concept condition and yield the same primary metric as strength zero. If a heuristic is helpful, its positive effect can be reduced computation or improved recall, not an error. State can include extra observations/choices to retain the mechanism. Metric_units must explain any primary task measure.

## Implementation requirements

1. A real concept-specific formula, selection/allocation process, or state transition. No placeholders, pass/TODO, generic constant metric offset, “if concept then add 0.1”, shared arbitrary penalty, or a boolean that simply turns a label on without the underlying task relation.
2. Explicit distinguishable input/state requirements. Use actual option utilities/dominance relations, base rates, sequential observations, budgets, ownership, attribution, memory/retention or full-text/source facts as the concept requires. Media concepts simulate authored presentation choices or reader effects using supplied structured facts; they are NOT natural-language/image detectors.
3. Respect the provided annotation boundary. Do not infer hidden states or motives from a keyword. Simulated internal states may be explicit inputs, clearly hypothetical. Require the mechanism's evidence/condition; absence cannot be a positive.
4. Coefficients are illustrative user-settable assumptions, not published effect sizes. Strength is a generic intervention setting, not prevalence or calibrated confidence. Document scope, weaknesses and benign alternative explanations.
5. Preserve non-error concepts as such. Heuristics, learning effects, incentives and psychological states must not be declared harmful by default. Proposed/narrow effects require especially clear caution about empirical uncertainty.
6. Maintain conceptual distinctions in the source: ownership vs construction; omission bias vs contextual omission; recall vs judgment; hindsight vs outcome; current-state projection vs different-state empathy; survivor selection vs general response bias; primacy/recency vs serial-position umbrella; persistence vs backfire. Implement only your assigned concept.
7. Write at least 5 genuine tests: positive direction, boundary equivalence, zero-strength/reference behavior, invalid required input rejection, deterministic/nonmutating behavior. Include a task-specific numeric/choice oracle so tests are more than registry checks. For stochastic mechanisms fix context uniform, never call random inside evaluate.
8. Test directly by calling evaluate through chronological contexts and carrying returned state. Do not rely on the engine being written yet. A small helper in your test file may copy context, inject reserved defaults and loop through contexts. Standalone direct contexts must include state, peer_states, round_index, agent_index, uniform defaults if your mechanism uses them.

Implementation note format: short equation/process explanation, exact task and units, baseline, necessary conditions, positive and boundary scenario descriptions, assumptions and limitations. Do not describe passing software tests as empirical validation.
