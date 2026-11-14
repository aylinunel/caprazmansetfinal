"""Illustrative paired-case omission-bias process; not a detector or fitted model."""
import math


METADATA = {
    'id': 'omission_bias',
    'name': 'Omission Bias',
    'kind': 'cognitive_bias',
    'description': (
        'In an explicitly matched action-versus-inaction harm comparison, add a '
        'strength-scaled premium to blame for the harmful action only when '
        'knowledge, duty, intention, and consequence comparability are all supplied.'
    ),
    # These are the flat, common case fields required in every scenario phase.
    'required_inputs': [
        'action_harm', 'omission_harm', 'actor_knew_risk', 'duty_to_act',
        'intentional_choice', 'consequences_comparable',
    ],
    'state_fields': [
        'case_count', 'eligible_case_count', 'last_action_blame',
        'last_omission_blame', 'last_action_premium',
    ],
    'metric_name': 'action_minus_omission_blame',
    'metric_units': 'difference in normalized illustrative blame points (0 to 1 scale per pathway)',
    'assumptions': [
        'Harm inputs are hypothetical severities on a normalized 0–1 scale.',
        'The reference policy assigns both pathways harm-proportional blame under shared knowledge, duty, and intention conditions.',
        'The illustrative action premium is 0.25 times strength times the lesser of the two harms; 0.25 is an arbitrary task parameter, not an empirical estimate.',
        'The premium is enabled only for a comparable pair with explicit knowledge, duty, and intentional choice.',
    ],
    'limitations': [
        'This models one stipulated paired judgment, not actual human judgments or a diagnostic signal.',
        'The compact inputs do not represent the many legal, moral, causal, or contextual distinctions in real cases.',
        'The coefficient and generic strength setting are uncalibrated; no prevalence, causal, or empirical-validity claim is made.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _harm(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f'{name} must be a finite number in [0, 1]')
    return float(value)


def _flag(context, name):
    value = context[name]
    if not isinstance(value, bool):
        raise ValueError(f'{name} must be a boolean explicit case fact')
    return value


def evaluate(context: dict, strength: float) -> dict:
    """Return blame difference for one case without mutating context or its state."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    missing = [key for key in METADATA['required_inputs'] if key not in context]
    if missing:
        raise ValueError('missing required task input(s): ' + ', '.join(missing))

    action_harm = _harm(context['action_harm'], 'action_harm')
    omission_harm = _harm(context['omission_harm'], 'omission_harm')
    knew = _flag(context, 'actor_knew_risk')
    duty = _flag(context, 'duty_to_act')
    intentional = _flag(context, 'intentional_choice')
    comparable = _flag(context, 'consequences_comparable')

    # Strength zero is the explicit reference: both paths receive equal
    # harm-proportional treatment, conditioned on the same accountability facts.
    accountability = float(knew and duty and intentional)
    action_blame = action_harm * accountability
    omission_blame = omission_harm * accountability
    eligible = knew and duty and intentional and comparable
    premium = 0.0
    if eligible:
        # A matched-severity contrast is necessary: the smaller harm is the
        # common severity supported by both pathways, not an arbitrary offset.
        premium = float(strength) * 0.25 * min(action_harm, omission_harm)
        action_blame = min(1.0, action_blame + premium)
    metric = action_blame - omission_blame

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be an object')
    case_count = prior.get('case_count', 0)
    eligible_count = prior.get('eligible_case_count', 0)
    for name, value in (('case_count', case_count), ('eligible_case_count', eligible_count)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f'state.{name} must be a nonnegative integer')

    trace = (
        f"Reference blame: action={action_harm:g}*accountability({int(accountability)})="
        f"{action_harm * accountability:g}; omission={omission_harm:g}*accountability="
        f"{omission_blame:g}. Eligibility requires knowledge, duty, intention, and "
        f"comparable consequences (observed: {knew}, {duty}, {intentional}, {comparable}). "
        f"{'Applied' if premium else 'Did not apply'} action premium: strength*0.25*"
        f"min(action_harm, omission_harm)={premium:g}; metric=action_blame-omission_blame={metric:g}."
    )
    return {
        'metric': metric,
        'active': bool(premium > 0),
        'state': {
            'case_count': case_count + 1,
            'eligible_case_count': eligible_count + int(eligible),
            'last_action_blame': action_blame,
            'last_omission_blame': omission_blame,
            'last_action_premium': premium,
        },
        'trace': [trace],
    }


def scenarios() -> list[dict]:
    common = {
        'action_harm': 0.8,
        'omission_harm': 0.8,
        'actor_knew_risk': True,
        'duty_to_act': True,
        'intentional_choice': True,
    }
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [{**common, 'consequences_comparable': True}],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            # Same explicit knowledge, duty, intention, and harms; the necessary
            # matched-consequences condition is removed, so no asymmetry is licensed.
            'contexts': [{**common, 'consequences_comparable': False}],
            'expectation': 'equal',
        },
    ]
