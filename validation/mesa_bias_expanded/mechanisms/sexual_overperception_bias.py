"""Illustrative structured-cue model of sexual overperception; not a detector."""
import math


METADATA = {
    'id': 'sexual_overperception_bias',
    'name': 'Sexual Overperception Bias',
    'kind': 'cognitive_bias',
    'description': (
        'Models an uncalibrated excess attribution of sexual interest when ambiguous '
        'warmth and personally directed attention are jointly over-read; neither '
        'cue alone, nor gender, is treated as evidence of sexual interest.'
    ),
    'required_inputs': [
        'direct_reciprocal_evidence', 'ambiguous_warmth', 'personalized_attention'
    ],
    'state_fields': ['last_estimate', 'step_count'],
    'metric_name': 'inferred_interest_estimate',
    'metric_units': 'bounded illustrative estimate on a 0–1 scale; not a probability or diagnosis',
    'assumptions': [
        'Inputs are explicit hypothetical structured ratings in [0, 1], not text, demographic, or behavioral detection.',
        'Direct reciprocal evidence is the strength-zero reference; ambiguous warmth and personalized attention interact to add unsupported attribution.',
        'The coefficient 0.5 is an illustrative user-settable process assumption; strength is an uncalibrated intervention setting.'
    ],
    'limitations': [
        'Not an empirical model, classifier, consent assessment, or claim about any person or population.',
        'The ratings compress context, may encode observer assumptions, and cannot establish another person’s internal state.',
        'Gender and generic friendliness are not inputs and cannot independently activate the modeled effect.'
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _unit_interval(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} must be a finite number in [0, 1]')
    if not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name} must be a finite number in [0, 1]')
    return float(value)


def evaluate(context: dict, strength: float) -> dict:
    """Return a hypothetical estimate, using only supplied structured evidence."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    for key in METADATA['required_inputs']:
        if key not in context:
            raise ValueError(f'missing required task input {key}')

    direct = _unit_interval(context['direct_reciprocal_evidence'], 'direct_reciprocal_evidence')
    warmth = _unit_interval(context['ambiguous_warmth'], 'ambiguous_warmth')
    attention = _unit_interval(context['personalized_attention'], 'personalized_attention')

    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be a dict')
    prior_steps = state.get('step_count', 0)
    if isinstance(prior_steps, bool) or not isinstance(prior_steps, int) or prior_steps < 0:
        raise ValueError('state.step_count must be a nonnegative integer')
    if 'last_estimate' in state:
        _unit_interval(state['last_estimate'], 'state.last_estimate')

    # Reference: direct reciprocal evidence only. The modeled over-read is an
    # interaction, not a generic offset: it requires both ambiguous cues and
    # diminishes as direct evidence already accounts for the estimate.
    excess = float(strength) * 0.5 * warmth * attention * (1.0 - direct)
    estimate = direct + excess
    next_state = dict(state)
    next_state.update({'last_estimate': estimate, 'step_count': prior_steps + 1})
    changed = excess > 0.0
    return {
        'metric': estimate,
        'active': changed,
        'state': next_state,
        'trace': [
            f'Reference=direct reciprocal evidence ({direct:.6g}); excess = strength '
            f'({float(strength):.6g}) × 0.5 × ambiguous warmth ({warmth:.6g}) × '
            f'personalized attention ({attention:.6g}) × (1 − direct evidence) '
            f'({1.0-direct:.6g}) = {excess:.6g}; estimate={estimate:.6g}.'
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{
                'direct_reciprocal_evidence': 0.1,
                'ambiguous_warmth': 0.8,
                'personalized_attention': 0.75,
            }],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # Warmth remains, but the second necessary ambiguous cue is absent.
            'contexts': [{
                'direct_reciprocal_evidence': 0.1,
                'ambiguous_warmth': 0.8,
                'personalized_attention': 0.0,
            }],
            'expectation': 'equal',
        },
    ]
