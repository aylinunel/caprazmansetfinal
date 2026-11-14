"""Illustrative rosy-retrospection process: asymmetric accessibility of remembered details."""
from copy import deepcopy
import math


METADATA = {
    'id': 'rosy_retrospection',
    'name': 'Rosy Retrospection',
    'kind': 'cognitive_bias',
    'description': (
        'On delayed recall of an explicitly experienced episode, positive details '
        'retain accessibility better than negative details, shifting a structured '
        'reconstructed rating relative to its recorded rating.'
    ),
    # Only `phase` is present in every task phase. Episode and cue fields are
    # validated conditionally below, rather than declared globally required.
    'required_inputs': ['phase'],
    'state_fields': ['episodes', 'recall_history'],
    'metric_name': 'recalled_episode_rating',
    'metric_units': 'illustrative rating points on a 0–100 task scale',
    'assumptions': [
        'Episodes and their initial 0–100 ratings are explicit hypothetical inputs.',
        'Cue saliences are nonnegative weights; a positive and negative cue both need to be encoded for asymmetric loss to change valence.',
        'Positive and negative cue accessibility decay at illustrative rates 0.10 and 0.45 per simulated round; these are not fitted effects.',
        'Strength linearly scales this reconstruction relative to the explicit recorded-rating reference policy.'
    ],
    'limitations': [
        'A tiny structured task model, not a natural-language memory detector or account of every form of rosy retrospection.',
        'It assumes differential cue accessibility and omits retrieval goals, context, rehearsal, and individual differences.',
        'Strength is an uncalibrated intervention setting; passing software checks does not establish psychological validity.'
    ],
    'empirically_validated': False,
    'synthetic_only': True,
}

_POSITIVE_DECAY = 0.10
_NEGATIVE_DECAY = 0.45
_MAX_SHIFT = 20.0


def _number(value, name, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if low is not None and value < low or high is not None and value > high:
        bounds = f'{low if low is not None else "-infinity"}..{high if high is not None else "infinity"}'
        raise ValueError(f'{name} must be in {bounds}')
    return float(value)


def _cue_total(value, name):
    if not isinstance(value, list):
        raise ValueError(f'{name} must be a list of salience weights')
    weights = [_number(item, f'{name} item', 0.0, 1.0) for item in value]
    return sum(weights)


def evaluate(context: dict, strength: float) -> dict:
    """Apply experience encoding or delayed recall without mutating caller data."""
    if isinstance(strength, bool) or not isinstance(strength, (int, float)) or not math.isfinite(strength) or not 0 <= strength <= 1:
        raise ValueError('strength must be finite and in [0, 1]')
    if not isinstance(context, dict):
        raise ValueError('context must be a dictionary')
    if 'phase' not in context:
        raise ValueError('missing required task input phase')
    phase = context['phase']
    if phase not in ('experience', 'recall'):
        raise ValueError("phase must be 'experience' or 'recall'")
    episode_id = context.get('episode_id')
    if not isinstance(episode_id, str) or not episode_id.strip():
        raise ValueError('episode_id must be a nonempty string in both phases')
    round_index = context.get('round_index')
    if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 0:
        raise ValueError('round_index must be a nonnegative integer')

    prior = context.get('state', {})
    if not isinstance(prior, dict):
        raise ValueError('state must be a dictionary')
    state = deepcopy(prior)
    episodes = state.get('episodes', {})
    recall_history = state.get('recall_history', [])
    if not isinstance(episodes, dict) or not isinstance(recall_history, list):
        raise ValueError('state episodes must be an object and recall_history a list')
    episodes = deepcopy(episodes)
    recall_history = deepcopy(recall_history)
    state['episodes'] = episodes
    state['recall_history'] = recall_history

    if phase == 'experience':
        required = ('experience_score', 'positive_cues', 'negative_cues')
        missing = [key for key in required if key not in context]
        if missing:
            raise ValueError('experience phase missing task input(s): ' + ', '.join(missing))
        score = _number(context['experience_score'], 'experience_score', 0.0, 100.0)
        positive_total = _cue_total(context['positive_cues'], 'positive_cues')
        negative_total = _cue_total(context['negative_cues'], 'negative_cues')
        if positive_total + negative_total <= 0:
            raise ValueError('experience must encode at least one nonzero-valence detail')
        if episode_id in episodes:
            raise ValueError(f'episode_id {episode_id!r} has already been experienced')
        episodes[episode_id] = {
            'experience_score': score,
            'positive_salience': positive_total,
            'negative_salience': negative_total,
            'encoded_round': round_index,
        }
        metric = score
        active = False
        trace = [
            f"Encoded episode {episode_id!r}: explicit experience rating={score:g}; "
            f"positive cue salience={positive_total:g}, negative cue salience={negative_total:g}. "
            'No retrospective reconstruction occurs during experience encoding.'
        ]
    else:
        if episode_id not in episodes:
            raise ValueError(f'recall phase requires a previously experienced episode {episode_id!r}')
        record = episodes[episode_id]
        if not isinstance(record, dict):
            raise ValueError('stored episode record is invalid')
        try:
            actual = _number(record['experience_score'], 'stored experience_score', 0.0, 100.0)
            positive_total = _number(record['positive_salience'], 'stored positive_salience', 0.0)
            negative_total = _number(record['negative_salience'], 'stored negative_salience', 0.0)
            encoded_round = record['encoded_round']
        except KeyError as exc:
            raise ValueError(f'stored episode is missing {exc.args[0]}') from None
        if isinstance(encoded_round, bool) or not isinstance(encoded_round, int) or encoded_round < 0:
            raise ValueError('stored encoded_round must be a nonnegative integer')
        elapsed = round_index - encoded_round
        if elapsed < 1:
            raise ValueError('recall must occur at least one simulated round after experience')
        if positive_total + negative_total <= 0:
            raise ValueError('stored episode has no encoded cue evidence')

        # Compare encoded valence with valence reconstructed from differentially
        # accessible details. With both valences present, faster negative-cue
        # decay raises reconstructed valence; with either side absent, no shift.
        encoded_denominator = positive_total + negative_total
        encoded_valence = (positive_total - negative_total) / encoded_denominator
        positive_access = positive_total * math.exp(-_POSITIVE_DECAY * elapsed)
        negative_access = negative_total * math.exp(-_NEGATIVE_DECAY * elapsed)
        accessible_total = positive_access + negative_access
        recalled_valence = (positive_access - negative_access) / accessible_total
        raw_shift = _MAX_SHIFT * (recalled_valence - encoded_valence)
        metric = min(100.0, max(0.0, actual + strength * raw_shift))
        active = strength > 0 and metric != actual
        recall_history.append({
            'episode_id': episode_id,
            'round': round_index,
            'elapsed_rounds': elapsed,
            'recalled_rating': metric,
        })
        trace = [
            f'Recall after {elapsed} round(s): encoded valence=(P-N)/(P+N)={encoded_valence:.6g}; '
            f'accessible P={positive_access:.6g}, N={negative_access:.6g} using exp(-0.10t) and exp(-0.45t); '
            f'recalled valence={recalled_valence:.6g}; rating=clip({actual:g}+strength*20*(recalled-encoded),0,100)={metric:.6g}.'
        ]

    return {'metric': float(metric), 'active': active, 'state': state, 'trace': trace}


def scenarios() -> list[dict]:
    return [
        {
            'name': 'positive',
            'initial_state': {'episodes': {}, 'recall_history': []},
            'contexts': [
                {'phase': 'experience', 'episode_id': 'mixed_episode', 'experience_score': 50,
                 'positive_cues': [1.0], 'negative_cues': [1.0]},
                {'phase': 'recall', 'episode_id': 'mixed_episode'},
            ],
            'expectation': 'increase',
        },
        {
            'name': 'boundary',
            'initial_state': {'episodes': {}, 'recall_history': []},
            'contexts': [
                {'phase': 'experience', 'episode_id': 'positive_only', 'experience_score': 50,
                 'positive_cues': [1.0], 'negative_cues': []},
                {'phase': 'recall', 'episode_id': 'positive_only'},
            ],
            'expectation': 'equal',
        },
    ]
