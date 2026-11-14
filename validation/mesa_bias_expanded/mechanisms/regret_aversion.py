"""Illustrative, feedback-dependent anticipated-regret choice process."""
from __future__ import annotations

import math


METADATA = {
    'id': 'regret_aversion',
    'name': 'Regret Aversion',
    'kind': 'cognitive_bias',
    'description': (
        'In a framed action-versus-status-quo task, subtract expected downside regret '
        'from the action score when matched counterfactual feedback is available.'
    ),
    # Both inputs occur in every scenario; nested option evidence is validated below.
    'required_inputs': ['options', 'comparison_feedback'],
    'state_fields': ['last_choice', 'decision_count', 'cumulative_expected_regret'],
    'metric_name': 'action_selected',
    'metric_units': 'binary choice indicator (1 action, 0 status quo)',
    'assumptions': [
        'The two supplied options are an action and its status-quo reference with matched outcome states.',
        'Only anticipated action regret is penalized; the reference option is the explicit zero-penalty comparator.',
        'The regret coefficient is illustrative and fixed at 1; strength scales this intervention, not a person-level trait.',
        'Outcome probabilities and feedback availability are supplied task facts, not inferred motives.',
    ],
    'limitations': [
        'This asymmetric framing is one hypothetical process, not a universal model of regret or rationality.',
        'No fitted coefficient, prevalence, diagnostic inference, or empirical validation is claimed.',
        'Expected-value scoring ignores nonlinear utility, learning, and other legitimate preferences.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(value, label, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be a finite number')
    value = float(value)
    if minimum is not None and value < minimum:
        raise ValueError(f'{label} must be >= {minimum}')
    if maximum is not None and value > maximum:
        raise ValueError(f'{label} must be <= {maximum}')
    return value


def _read_options(context):
    if not isinstance(context, dict):
        raise ValueError('context must be a dictionary')
    if 'options' not in context:
        raise ValueError('missing required task input options')
    if 'comparison_feedback' not in context:
        raise ValueError('missing required task input comparison_feedback')
    feedback = _number(context['comparison_feedback'], 'comparison_feedback', minimum=0, maximum=1)
    options = context['options']
    if not isinstance(options, list) or len(options) != 2:
        raise ValueError('options must contain exactly action and status_quo')
    by_name = {}
    for option in options:
        if not isinstance(option, dict) or option.get('name') not in ('action', 'status_quo'):
            raise ValueError('each option must be named action or status_quo')
        name = option['name']
        if name in by_name:
            raise ValueError('option names must be unique')
        outcomes = option.get('outcomes')
        if not isinstance(outcomes, list) or not outcomes:
            raise ValueError(f'{name}.outcomes must be a nonempty list')
        parsed = {}
        for outcome in outcomes:
            if not isinstance(outcome, dict) or not isinstance(outcome.get('state'), str) or not outcome['state']:
                raise ValueError('each outcome needs a nonempty state name')
            state = outcome['state']
            if state in parsed:
                raise ValueError(f'{name} outcome states must be unique')
            probability = _number(outcome.get('probability'), f'{name}.{state}.probability', minimum=0, maximum=1)
            payoff = _number(outcome.get('payoff'), f'{name}.{state}.payoff')
            parsed[state] = (probability, payoff)
        if not math.isclose(sum(p for p, _ in parsed.values()), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f'{name} outcome probabilities must sum to 1')
        by_name[name] = parsed
    if set(by_name) != {'action', 'status_quo'}:
        raise ValueError('options must contain action and status_quo exactly once')
    action, reference = by_name['action'], by_name['status_quo']
    if set(action) != set(reference):
        raise ValueError('options must provide matched outcome states')
    for state in action:
        if not math.isclose(action[state][0], reference[state][0], rel_tol=0, abs_tol=1e-9):
            raise ValueError(f'options must use matched probabilities for state {state}')
    return action, reference, feedback


def evaluate(context: dict, strength: float) -> dict:
    """Choose by expected payoff, subtracting strength-scaled expected downside regret."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    strength = float(strength)
    action, reference, feedback = _read_options(context)

    action_ev = sum(probability * payoff for probability, payoff in action.values())
    reference_ev = sum(probability * payoff for probability, payoff in reference.values())
    # Regret here is the expected shortfall of taking action versus the matched
    # status-quo outcome, conditional on the comparison actually being observable.
    expected_regret = feedback * sum(
        probability * max(0.0, reference[state][1] - payoff)
        for state, (probability, payoff) in action.items()
    )
    action_score = action_ev - strength * expected_regret
    reference_choice = 'action' if action_ev > reference_ev else 'status_quo'
    choice = 'action' if action_score > reference_ev else 'status_quo'

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be a dictionary')
    previous_count = prior.get('decision_count', 0)
    if isinstance(previous_count, bool) or not isinstance(previous_count, int) or previous_count < 0:
        raise ValueError('state.decision_count must be a nonnegative integer')
    prior_total = _number(prior.get('cumulative_expected_regret', 0), 'state.cumulative_expected_regret', minimum=0)
    state = {
        'last_choice': choice,
        'decision_count': previous_count + 1,
        'cumulative_expected_regret': prior_total + expected_regret,
    }
    return {
        'metric': 1.0 if choice == 'action' else 0.0,
        'active': choice != reference_choice,
        'state': state,
        'trace': [
            f'action EV={action_ev:.6g}; status-quo EV={reference_ev:.6g}; '
            f'expected downside regret={expected_regret:.6g} after feedback={feedback:.6g}; '
            f'action score={action_score:.6g} (EV - strength {strength:.6g} * regret); '
            f'reference choice={reference_choice}; chose {choice}.'
        ],
    }


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {'last_choice': None, 'decision_count': 0, 'cumulative_expected_regret': 0.0},
            'contexts': [{
                'comparison_feedback': 1.0,
                'options': [
                    {'name': 'action', 'outcomes': [
                        {'state': 'good', 'probability': 0.5, 'payoff': 8.0},
                        {'state': 'bad', 'probability': 0.5, 'payoff': 0.0},
                    ]},
                    {'name': 'status_quo', 'outcomes': [
                        {'state': 'good', 'probability': 0.5, 'payoff': 3.0},
                        {'state': 'bad', 'probability': 0.5, 'payoff': 3.0},
                    ]},
                ],
            }],
            'expectation': 'decrease',
        },
        {
            'name': 'boundary',
            'initial_state': {'last_choice': None, 'decision_count': 0, 'cumulative_expected_regret': 0.0},
            'contexts': [{
                # Without observable counterfactual feedback, anticipated regret has no basis.
                'comparison_feedback': 0.0,
                'options': [
                    {'name': 'action', 'outcomes': [
                        {'state': 'good', 'probability': 0.5, 'payoff': 8.0},
                        {'state': 'bad', 'probability': 0.5, 'payoff': 0.0},
                    ]},
                    {'name': 'status_quo', 'outcomes': [
                        {'state': 'good', 'probability': 0.5, 'payoff': 3.0},
                        {'state': 'bad', 'probability': 0.5, 'payoff': 3.0},
                    ]},
                ],
            }],
            'expectation': 'equal',
        },
    ]
