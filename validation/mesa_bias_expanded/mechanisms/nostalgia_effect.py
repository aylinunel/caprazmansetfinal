"""Illustrative model of a linked autobiographical memory changing a spending choice."""

import math
from numbers import Real


METADATA = {
    'id': 'nostalgia_effect',
    'name': 'Nostalgia Effect',
    'kind': 'motivational_mechanism',
    'description': (
        'A positively felt autobiographical episode from the past raises reservation '
        'willingness-to-pay only when the current offering is explicitly associated with it.'
    ),
    # Only `phase` is required in every chronological phase; phase-specific fields
    # are checked by evaluate rather than being misleadingly listed here.
    'required_inputs': ['phase'],
    'state_fields': [
        'phase', 'memory_episode', 'reference_wtp', 'adjusted_wtp',
        'reservation_adjustment', 'purchased', 'product_id', 'actual_spend',
    ],
    'metric_name': 'purchase_spend',
    'metric_units': 'currency units spent on the single offered item in this task step',
    'assumptions': [
        'A participant-reported past autobiographical episode and its warmth are explicit structured inputs, not inferred from language.',
        'The item-to-memory association strength and spending sensitivity are task-set illustrative quantities, not estimated human parameters.',
        'Willingness-to-pay is increased by strength × positive memory warmth × matched association strength × supplied spending sensitivity.',
        'The reference policy buys exactly when baseline willingness-to-pay is at least the supplied price; the item is indivisible and one item is offered.',
        'Strength is an uncalibrated intervention setting, not confidence, prevalence, or a population effect estimate.',
    ],
    'limitations': [
        'The toy model excludes budgets, competing goods, payment pain, social context, memory reconstruction, and individual heterogeneity.',
        'An explicit match and warm autobiographical report do not establish that nostalgia caused real-world spending.',
        'The model is a hypothetical process illustration, not a detector, diagnosis, empirical finding, or claim that nostalgia is harmful.',
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}


def _number(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f'{name} must be a finite number in [{low}, {high}]')
    value = float(value)
    if not math.isfinite(value) or value < low or value > high:
        raise ValueError(f'{name} must be a finite number in [{low}, {high}]')
    return value


def _year(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 9999:
        raise ValueError(f'{name} must be an integer year from 1 to 9999')
    return value


def _context_state(context):
    if not isinstance(context, dict):
        raise ValueError('context must be a dict')
    if 'phase' not in context:
        raise ValueError('missing required input: phase')
    if context['phase'] not in ('memory', 'purchase'):
        raise ValueError("phase must be 'memory' or 'purchase'")
    state = context.get('state', {})
    if not isinstance(state, dict):
        raise ValueError('state must be a dict')
    return context['phase'], state


def _require(context, fields, phase):
    for field in fields:
        if field not in context:
            raise ValueError(f'{phase} phase missing required input: {field}')


def evaluate(context: dict, strength: float) -> dict:
    """Process one memory or later purchase phase without mutating its inputs."""
    intensity = _number(strength, 'strength', 0, 1)
    phase, prior = _context_state(context)
    next_state = dict(prior)
    if phase == 'memory':
        fields = ('episode_id', 'event_year', 'observed_year', 'autobiographical', 'warmth')
        _require(context, fields, phase)
        episode_id = context['episode_id']
        if not isinstance(episode_id, str) or not episode_id:
            raise ValueError('episode_id must be a non-empty string')
        event_year = _year(context['event_year'], 'event_year')
        observed_year = _year(context['observed_year'], 'observed_year')
        if event_year >= observed_year:
            raise ValueError('event_year must precede observed_year for a past memory')
        if type(context['autobiographical']) is not bool:
            raise ValueError('autobiographical must be bool')
        warmth = _number(context['warmth'], 'warmth', 0, 1)
        episode = {
            'episode_id': episode_id,
            'event_year': event_year,
            'observed_year': observed_year,
            'autobiographical': context['autobiographical'],
            'warmth': warmth,
        }
        next_state.update({
            'phase': 'memory', 'memory_episode': episode,
            'reference_wtp': None, 'adjusted_wtp': None,
            'reservation_adjustment': 0.0, 'purchased': False,
            'product_id': None, 'actual_spend': 0.0,
        })
        return {
            'metric': 0.0,
            'active': False,
            'state': next_state,
            'trace': [
                f"Recorded explicit episode {episode_id!r} from {event_year}, recalled in {observed_year}; "
                f"autobiographical={context['autobiographical']}, warmth={warmth:g}.",
                'A memory record alone does not alter a purchase decision; a later matched offering is required.',
            ],
        }

    fields = (
        'current_year', 'product_id', 'item_memory_link', 'association_strength',
        'baseline_wtp', 'price', 'spend_sensitivity',
    )
    _require(context, fields, phase)
    memory = prior.get('memory_episode')
    if not isinstance(memory, dict) or not all(
        key in memory for key in ('episode_id', 'event_year', 'observed_year', 'autobiographical', 'warmth')
    ):
        raise ValueError('purchase phase requires a prior memory-phase state')
    current_year = _year(context['current_year'], 'current_year')
    if current_year < memory['observed_year']:
        raise ValueError('purchase current_year cannot precede the memory observation')
    product_id = context['product_id']
    if not isinstance(product_id, str) or not product_id:
        raise ValueError('product_id must be a non-empty string')
    link = context['item_memory_link']
    if link is not None and (not isinstance(link, str) or not link):
        raise ValueError('item_memory_link must be a non-empty string or None')
    association = _number(context['association_strength'], 'association_strength', 0, 1)
    baseline = _number(context['baseline_wtp'], 'baseline_wtp', 0, 1_000_000_000)
    price = _number(context['price'], 'price', 0, 1_000_000_000)
    sensitivity = _number(context['spend_sensitivity'], 'spend_sensitivity', 0, 1_000_000_000)

    matched_warm_episode = (
        memory['autobiographical'] is True
        and memory['warmth'] > 0
        and link == memory['episode_id']
        and association > 0
    )
    # The effect acts on reservation willingness-to-pay, not as a free-standing
    # metric offset. Mismatched/non-warm/non-autobiographical memories add nothing.
    adjustment = (
        intensity * memory['warmth'] * association * sensitivity
        if matched_warm_episode else 0.0
    )
    adjusted = baseline + adjustment
    purchased = adjusted >= price
    spend = price if purchased else 0.0
    next_state.update({
        'phase': 'purchase', 'memory_episode': dict(memory),
        'reference_wtp': baseline, 'adjusted_wtp': adjusted,
        'reservation_adjustment': adjustment, 'purchased': purchased,
        'product_id': product_id, 'actual_spend': spend,
    })
    active = adjustment > 0
    return {
        'metric': spend,
        'active': active,
        'state': next_state,
        'trace': [
            f'Reference rule: buy one item iff baseline willingness-to-pay {baseline:g} >= price {price:g}.',
            'Matched warm autobiographical memory condition: '
            f'{matched_warm_episode} (episode match={link == memory["episode_id"]}, '
            f'autobiographical={memory["autobiographical"]}, warmth={memory["warmth"]:g}, '
            f'association={association:g}).',
            f'WTP adjustment = strength({intensity:g}) × warmth({memory["warmth"]:g}) × '
            f'association({association:g}) × sensitivity({sensitivity:g}) = {adjustment:g}; '
            f'adjusted WTP={adjusted:g}.',
            f"Purchase={purchased}; task spend={spend:g} currency units for {product_id!r}.",
        ],
    }


def scenarios() -> list[dict]:
    memory = {
        'phase': 'memory', 'episode_id': 'summer-fair', 'event_year': 1998,
        'observed_year': 2026, 'autobiographical': True, 'warmth': 0.9,
    }
    return [
        {
            'name': 'positive',
            'initial_state': {},
            'contexts': [
                memory,
                {
                    'phase': 'purchase', 'current_year': 2026,
                    'product_id': 'fairground-reissue', 'item_memory_link': 'summer-fair',
                    'association_strength': 0.8, 'baseline_wtp': 8.5,
                    'price': 10.0, 'spend_sensitivity': 4.0,
                },
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {},
            'contexts': [
                memory,
                {
                    'phase': 'purchase', 'current_year': 2026,
                    'product_id': 'unrelated-reissue', 'item_memory_link': 'different-episode',
                    'association_strength': 0.8, 'baseline_wtp': 8.5,
                    'price': 10.0, 'spend_sensitivity': 4.0,
                },
            ],
            'expectation': 'equal',
        },
    ]
