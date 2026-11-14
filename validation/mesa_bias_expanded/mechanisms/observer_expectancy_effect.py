"""Illustrative observer-expectancy transmission process; not a human detector."""
from __future__ import annotations
import math

METADATA = {
    'id': 'observer_expectancy_effect',
    'name': 'Observer Expectancy Effect',
    'kind': 'cognitive_bias',
    'description': (
        'An explicitly conveyed observer expectation shifts a participant\'s task-specific '
        'self-expectancy, which can shift task performance; observation alone does not.'
    ),
    'required_inputs': [
        'observer_present', 'observer_expectation', 'cue_visibility',
        'participant_responsiveness', 'task_susceptibility', 'baseline_performance',
    ],
    'state_fields': ['participant_expectancy'],
    'metric_name': 'task_performance',
    'metric_units': 'illustrative task-performance units',
    'assumptions': [
        'The signed observer expectation and the degree to which it is conveyed are explicit hypothetical inputs.',
        'Participant responsiveness and task susceptibility are bounded user-settable process parameters.',
        'Strength controls transmission from observer cue to participant expectancy; it is not calibrated.',
        'The zero-strength reference holds participant expectancy at its prior value and uses the same baseline task.',
    ],
    'limitations': [
        'This compact process model is hypothetical and has no measured effect sizes or empirical validation.',
        'Actual interpersonal cues, participant interpretations, task performance, and alternative causes are not inferred.',
        'It models neither observer-biased scoring nor the mere effect of being watched.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(context, key, low, high):
    value = context[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{key} must be a finite number')
    value = float(value)
    if value < low or value > high:
        raise ValueError(f'{key} must be in [{low}, {high}]')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Transmit an explicit observer expectation through an expressed cue."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError(f"missing required task input: {', '.join(missing)}")
    if not isinstance(context['observer_present'], bool):
        raise ValueError('observer_present must be a boolean')
    # Presence is contextual, not causal: no cue is transmitted if no observer is present.
    expectation = _number(context, 'observer_expectation', -1.0, 1.0)
    cue = _number(context, 'cue_visibility', 0.0, 1.0)
    responsiveness = _number(context, 'participant_responsiveness', 0.0, 1.0)
    susceptibility = _number(context, 'task_susceptibility', 0.0, 1.0)
    baseline = _number(context, 'baseline_performance', 0.0, 1_000_000.0)
    state = context.get('state')
    if not isinstance(state, dict):
        raise ValueError('state must be a dictionary supplied by the runner')
    prior = state.get('participant_expectancy', 0.0)
    if isinstance(prior, bool) or not isinstance(prior, (int, float)) or not math.isfinite(prior) or not -1.0 <= prior <= 1.0:
        raise ValueError('state.participant_expectancy must be finite and in [-1, 1]')
    prior = float(prior)

    conveyed_cue = cue if context['observer_present'] else 0.0
    transmission = float(strength) * conveyed_cue * responsiveness
    next_expectancy = prior + transmission * (expectation - prior)
    performance = baseline + susceptibility * next_expectancy
    active = not math.isclose(performance, baseline, rel_tol=0.0, abs_tol=1e-15)
    return {
        'metric': performance,
        'active': active,
        'state': {'participant_expectancy': next_expectancy},
        'trace': [
            f"expectancy' = {prior:.6g} + ({float(strength):.6g} × {conveyed_cue:.6g} × {responsiveness:.6g}) × ({expectation:.6g} - {prior:.6g}) = {next_expectancy:.6g}",
            f'task performance = baseline {baseline:.6g} + task susceptibility {susceptibility:.6g} × participant expectancy {next_expectancy:.6g} = {performance:.6g}',
        ],
    }


def scenarios() -> list[dict]:
    common = {
        'observer_present': True,
        'observer_expectation': 0.8,
        'participant_responsiveness': 0.5,
        'task_susceptibility': 0.6,
        'baseline_performance': 10.0,
    }
    return [
        {
            'name': 'positive',
            'initial_state': {'participant_expectancy': 0.0},
            'contexts': [
                {**common, 'cue_visibility': 0.5},
                {**common, 'cue_visibility': 0.75},
                {**common, 'cue_visibility': 0.75},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'participant_expectancy': 0.0},
            # Observer presence and expectation remain; no expectation is conveyed.
            'contexts': [
                {**common, 'cue_visibility': 0.0},
                {**common, 'cue_visibility': 0.0},
            ],
            'expectation': 'equal',
        },
    ]
