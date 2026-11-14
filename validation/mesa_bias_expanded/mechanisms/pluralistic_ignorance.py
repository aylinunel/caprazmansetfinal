"""Illustrative process model for pluralistic ignorance in a small group task."""
import math


METADATA = {
    'id': 'pluralistic_ignorance',
    'name': 'Pluralistic Ignorance',
    'kind': 'cognitive_bias',
    'description': (
        'When an agent privately agrees with the actual strict group majority but '
        'believes the group majority is opposite, the agent may publicly conform '
        'to that mistaken perceived majority.'
    ),
    'required_inputs': ['private_positions', 'perceived_support'],
    'state_fields': ['private_position', 'public_position', 'private_public_mismatch', 'conforming_steps'],
    'metric_name': 'private_public_mismatch',
    'metric_units': 'binary per-agent indicator (1 if public position differs from private position)',
    'assumptions': [
        'Positions are binary: 1 means support and 0 means oppose; the supplied vector is the full hypothetical group.',
        'Each perceived_support entry is an agent-specific perceived fraction of group members supporting.',
        'When the necessary shared-misperception condition holds, strength is the illustrative probability of expressing the perceived majority rather than the private position.',
        'The supplied uniform is an exogenous choice draw; coefficients and strengths are not calibrated.',
    ],
    'limitations': [
        'This is a compact hypothetical choice process, not a detector or diagnosis of real people or groups.',
        'The model assumes an explicit full-group private-position vector and perceptions; it does not infer either from language or behavior.',
        'Binary positions, one-step choices, and a single conformity probability omit uncertainty, relationships, costs, and alternative motives.',
        'A simulated mismatch does not establish that pluralistic ignorance occurs empirically or that conformity is harmful.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _validate(context, strength):
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')
    positions = context['private_positions']
    perceptions = context['perceived_support']
    if not isinstance(positions, list) or not positions:
        raise ValueError('private_positions must be a nonempty list')
    if any(isinstance(x, bool) or not isinstance(x, int) or x not in (0, 1) for x in positions):
        raise ValueError('private_positions must contain only binary integers 0 or 1')
    if not isinstance(perceptions, list) or len(perceptions) != len(positions):
        raise ValueError('perceived_support must match the private_positions group length')
    for value in perceptions:
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 1):
            raise ValueError('perceived_support entries must be finite fractions in [0, 1]')
    index = context.get('agent_index')
    if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(positions):
        raise ValueError('agent_index must identify a member of the supplied group')
    uniform = context.get('uniform')
    if (isinstance(uniform, bool) or not isinstance(uniform, (int, float))
            or not math.isfinite(uniform) or not 0 <= uniform < 1):
        raise ValueError('uniform must be finite and in [0, 1)')
    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be an object')
    count = state.get('conforming_steps', 0)
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.conforming_steps must be a nonnegative integer')
    return positions, perceptions, index, float(uniform), count


def evaluate(context: dict, strength: float) -> dict:
    """Choose public expression; metric is the realized public/private mismatch."""
    positions, perceptions, index, uniform, previous_count = _validate(context, strength)
    private = positions[index]
    support_count = sum(positions)
    if support_count * 2 == len(positions):
        actual_majority = None
    else:
        actual_majority = 1 if support_count * 2 > len(positions) else 0
    perceived = perceptions[index]
    perceived_majority = 1 if perceived > 0.5 else (0 if perceived < 0.5 else None)

    # Shared misperception requires the agent's private view to align with a
    # strict actual majority while their perceived strict majority is opposite.
    gate = (actual_majority is not None and perceived_majority is not None
            and private == actual_majority and perceived_majority != actual_majority)
    conforms = bool(gate and strength > 0 and uniform < strength)
    public = perceived_majority if conforms else private
    mismatch = int(public != private)
    new_count = previous_count + int(conforms)
    next_state = {
        'private_position': private,
        'public_position': public,
        'private_public_mismatch': mismatch,
        'conforming_steps': new_count,
    }
    return {
        'metric': mismatch,
        'active': conforms,
        'state': next_state,
        'trace': [
            f'private={private}; actual_strict_majority={actual_majority}; perceived_strict_majority={perceived_majority}; necessary_misperception_gate={bool(gate)}.',
            f'Public position={public}; conformity selected={conforms} using uniform={uniform:g} < strength={float(strength):g}; metric is public/private mismatch.',
        ],
    }


def scenarios() -> list[dict]:
    """The three-agent scenario remains the direct-test contract default."""
    return scenarios_for_population(3)


def scenarios_for_population(n_agents: int) -> list[dict]:
    """Generate explicit homogeneous teaching data, not inferred group views.

    Only built-in scenarios use this factory. Supplied custom group vectors are
    not resized, repeated, or wrapped modulo their original population.
    """
    if isinstance(n_agents, bool) or not isinstance(n_agents, int) or n_agents < 2:
        raise ValueError('n_agents must be an integer >= 2')
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'private_positions': [1] * n_agents,
                'perceived_support': [0.2] * n_agents,
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # Same private group and same agents; perception now matches its
            # actual majority, removing the necessary shared-misperception gate.
            'contexts': [{
                'private_positions': [1] * n_agents,
                'perceived_support': [0.8] * n_agents,
            }],
            'expectation': 'equal',
        },
    ]
