"""Illustrative tool-choice process for the law of the instrument.

This is a synthetic task model, not a classifier or empirically fitted account.
"""

from copy import deepcopy
import math


METADATA = {
    'id': 'law_of_the_instrument',
    'name': 'Law of the Instrument',
    'kind': 'cognitive_bias',
    'description': (
        'In transferable tasks, choice blends a tool\'s requirement coverage '
        'with its supplied familiarity; a best-fit policy is the reference.'
    ),
    'required_inputs': ['requirements', 'tools', 'application_mode'],
    'state_fields': [
        'decision_count', 'choice_history', 'last_choice',
        'last_reference_choice', 'last_fit', 'last_unmet_requirements',
    ],
    'metric_name': 'unmet_task_requirements',
    'metric_units': 'count of required capabilities absent from the chosen tool',
    'assumptions': [
        'A requirement is met when its exact string appears in a tool capability list.',
        'Familiarity and capability coverage are on a 0–1 scale and equally interpretable in the illustrative choice score.',
        'The strength parameter linearly controls the familiarity weight only for transfer applications.',
        'Equal scores are resolved by the order of tools supplied in the context.',
    ],
    'limitations': [
        'The scoring rule and coefficients are illustrative assumptions, not measured psychological effects.',
        'The model represents one structured tool choice and cannot detect overgeneralization in natural language or real behavior.',
        'Familiarity may be beneficial, rational, or correlated with unmodeled task fit; the model does not establish error outside its stipulated task.',
        'Customary use is represented only by an explicit application_mode input; this is not inferred.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _validate_inputs(context):
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    for field in METADATA['required_inputs']:
        if field not in context:
            raise ValueError(f'missing required input: {field}')

    requirements = context['requirements']
    if (not isinstance(requirements, list) or not requirements
            or any(not isinstance(item, str) or not item.strip() for item in requirements)
            or len(set(requirements)) != len(requirements)):
        raise ValueError('requirements must be a nonempty list of unique nonempty strings')

    tools = context['tools']
    if not isinstance(tools, list) or not tools:
        raise ValueError('tools must be a nonempty list')
    names = []
    validated = []
    for item in tools:
        if not isinstance(item, dict):
            raise ValueError('each tool must be a dict')
        if not isinstance(item.get('name'), str) or not item['name'].strip():
            raise ValueError('each tool requires a nonempty name')
        capabilities = item.get('capabilities')
        if (not isinstance(capabilities, list)
                or any(not isinstance(cap, str) or not cap.strip() for cap in capabilities)
                or len(set(capabilities)) != len(capabilities)):
            raise ValueError('tool capabilities must be a list of unique nonempty strings')
        familiarity = item.get('familiarity')
        if (isinstance(familiarity, bool) or not isinstance(familiarity, (int, float))
                or not math.isfinite(familiarity) or not 0 <= familiarity <= 1):
            raise ValueError('tool familiarity must be finite and in [0, 1]')
        names.append(item['name'])
        validated.append((item['name'], set(capabilities), float(familiarity)))
    if len(set(names)) != len(names):
        raise ValueError('tool names must be unique')

    mode = context['application_mode']
    if mode not in ('transfer', 'customary'):
        raise ValueError("application_mode must be 'transfer' or 'customary'")

    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be a dict')
    count = state.get('decision_count', 0)
    history = state.get('choice_history', [])
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.decision_count must be a nonnegative integer')
    if not isinstance(history, list) or any(not isinstance(name, str) for name in history):
        raise ValueError('state.choice_history must be a list of strings')
    return requirements, validated, mode, count, history


def evaluate(context: dict, strength: float) -> dict:
    """Choose a tool, returning unmet capability count and a complete next state."""
    if (isinstance(strength, bool) or not isinstance(strength, (int, float))
            or not math.isfinite(strength) or not 0 <= strength <= 1):
        raise ValueError('strength must be finite and in [0, 1]')
    requirements, tools, mode, prior_count, prior_history = _validate_inputs(context)

    # Coverage is the fraction of explicitly required capabilities supplied.
    # The reference policy maximizes coverage; transfer mode interpolates this
    # task fit with declared familiarity. Customary use remains best-fit only.
    scored = []
    for name, capabilities, familiarity in tools:
        coverage = len(set(requirements) & capabilities) / len(requirements)
        decision_score = (
            (1.0 - strength) * coverage + strength * familiarity
            if mode == 'transfer' else coverage
        )
        scored.append((name, capabilities, coverage, decision_score))

    reference = max(scored, key=lambda row: row[2])
    chosen = max(scored, key=lambda row: row[3])
    unmet = len(set(requirements) - chosen[1])
    reference_unmet = len(set(requirements) - reference[1])
    metric = float(unmet)
    if not math.isfinite(metric):  # Defensive guarantee for the public contract.
        raise ValueError('computed metric is not finite')

    state = deepcopy(context.get('state', {}))
    history = list(prior_history) + [chosen[0]]
    state.update({
        'decision_count': prior_count + 1,
        'choice_history': history,
        'last_choice': chosen[0],
        'last_reference_choice': reference[0],
        'last_fit': chosen[2],
        'last_unmet_requirements': unmet,
    })
    trace = [
        f"Mode={mode}; requirements={requirements}; coverage is exact capability overlap / {len(requirements)}.",
        'Reference chooses maximum coverage; ties follow supplied tool order.',
        (
            f"Transfer choice score=(1-{float(strength):g})*coverage + "
            f"{float(strength):g}*familiarity; customary mode uses coverage alone."
        ),
        f"Selected {chosen[0]!r} (coverage={chosen[2]:g}, score={chosen[3]:g}); ",
        f"unmet requirements={unmet}; reference={reference[0]!r} ({reference_unmet} unmet).",
    ]
    return {
        'metric': metric,
        'active': chosen[0] != reference[0],
        'state': state,
        'trace': trace,
    }


def scenarios() -> list[dict]:
    tools = [
        {'name': 'familiar_spreadsheet', 'capabilities': ['calculate'], 'familiarity': 1.0},
        {'name': 'specialist_suite', 'capabilities': ['calculate', 'visualize'], 'familiarity': 0.1},
    ]
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'requirements': ['calculate', 'visualize'],
                'tools': tools,
                'application_mode': 'transfer',
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'requirements': ['calculate', 'visualize'],
                'tools': tools,
                'application_mode': 'customary',
            }],
            'expectation': 'equal',
        },
    ]
