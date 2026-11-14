"""Illustrative less-is-better choice process; not a detector or fitted model."""
import math


METADATA = {
    'id': 'less_is_better_effect',
    'name': 'Less-is-Better Effect',
    'kind': 'cognitive_bias',
    'description': (
        'Under separate evaluation, blend total net value with average net value '
        'per item; under joint evaluation, compare total net value only.'
    ),
    'required_inputs': ['evaluation_mode', 'options'],
    'state_fields': ['last_choice', 'decision_count', 'choice_history'],
    'metric_name': 'selected_option_total_net_value',
    'metric_units': 'synthetic net-value units (sum of item values minus total option cost)',
    'assumptions': [
        'Each option supplies item_values and a genuine total_cost in comparable synthetic units.',
        'Separate evaluation emphasizes average net value per item; joint evaluation compares total net value.',
        'Strength linearly controls the added average-value weighting only under separate evaluation.',
        'Higher total net value is the explicit strength-zero reference policy; exact ties select the first option.',
        'All coefficients and scenarios are illustrative assumptions, not measured effect sizes.',
    ],
    'limitations': [
        'This narrow arithmetic choice task does not model real-world perception, context learning, or preference formation.',
        'A mean and a total have different scales; their interpolation is a transparent toy intervention, not a calibrated psychological law.',
        'The supplied values and costs are hypothetical and do not establish prevalence or empirical validity.',
        'Separate evaluation is an explicit task input; the mechanism does not infer it from language or hidden motives.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _finite_nonnegative(value, description):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f'{description} must be a finite nonnegative number')
    return float(value)


def _option_values(context):
    if not isinstance(context, dict):
        raise ValueError('context must be an object')
    mode = context.get('evaluation_mode')
    if mode not in ('separate', 'joint'):
        raise ValueError("evaluation_mode must be 'separate' or 'joint'")
    options = context.get('options')
    if not isinstance(options, list) or len(options) != 2:
        raise ValueError('options must contain exactly two option objects')
    parsed = []
    labels = []
    for i, option in enumerate(options):
        if not isinstance(option, dict) or not isinstance(option.get('label'), str) or not option['label'].strip():
            raise ValueError(f'option {i} needs a nonempty label')
        if not isinstance(option.get('item_values'), list) or not option['item_values']:
            raise ValueError(f"option {option.get('label', i)} needs a nonempty item_values list")
        values = [_finite_nonnegative(v, 'item value') for v in option['item_values']]
        cost = _finite_nonnegative(option.get('total_cost'), 'total_cost')
        net_total = sum(values) - cost
        parsed.append({
            'label': option['label'],
            'net_total': net_total,
            'net_per_item': net_total / len(values),
            'item_count': len(values),
            'total_cost': cost,
        })
        labels.append(option['label'])
    if len(set(labels)) != 2:
        raise ValueError('option labels must be distinct')
    return mode, parsed


def evaluate(context: dict, strength: float) -> dict:
    """Evaluate one explicit pair without mutating context or prior state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    mode, options = _option_values(context)
    old_state = context.get('state', {})
    if not isinstance(old_state, dict):
        raise ValueError('state must be an object')
    count = old_state.get('decision_count', 0)
    history = old_state.get('choice_history', [])
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('state.decision_count must be a nonnegative integer')
    if not isinstance(history, list) or len(history) != count or not all(isinstance(x, str) for x in history):
        raise ValueError('state.choice_history must be a string list matching decision_count')

    s = float(strength)
    if mode == 'separate':
        scores = [(1.0 - s) * o['net_total'] + s * o['net_per_item'] for o in options]
    else:
        scores = [o['net_total'] for o in options]
    selected_index = 0 if scores[0] >= scores[1] else 1
    reference_index = 0 if options[0]['net_total'] >= options[1]['net_total'] else 1
    selected = options[selected_index]
    changed_choice = selected_index != reference_index
    next_history = list(history) + [selected['label']]
    next_state = {
        'last_choice': selected['label'],
        'decision_count': count + 1,
        'choice_history': next_history,
    }
    return {
        'metric': selected['net_total'],
        'active': mode == 'separate' and s > 0 and changed_choice,
        'state': next_state,
        'trace': [
            f"mode={mode}; strength={s:g}; option net totals={[o['net_total'] for o in options]}; ",
            f"net-per-item={[o['net_per_item'] for o in options]}; comparison scores={scores}; ",
            f"selected={selected['label']}; strength-zero total-net reference={options[reference_index]['label']}; ",
            f"actual total_costs={[o['total_cost'] for o in options]};",
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'evaluation_mode': 'separate',
                'options': [
                    {'label': 'compact', 'item_values': [6.0], 'total_cost': 0.5},
                    {'label': 'large_bundle', 'item_values': [4.0, 4.0], 'total_cost': 2.0},
                ],
            }],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [{
                'evaluation_mode': 'joint',
                'options': [
                    {'label': 'compact', 'item_values': [6.0], 'total_cost': 0.5},
                    {'label': 'large_bundle', 'item_values': [4.0, 4.0], 'total_cost': 2.0},
                ],
            }],
            'expectation': 'equal',
        },
    ]
