"""Model input sensitivity and observed events for completed-match review."""
from .ml import (FEATURE_NAMES, MIN_SNAPSHOT_MS, SNAPSHOT_MS, _number,
                 _predict_probability, _read_model, extract_features, predict_snapshot)


def feature_sensitivity(features: dict | None, team_id: int, source: str) -> dict:
    """Replace one input with its training mean, keeping all other inputs fixed."""
    result = {
        'available': False, 'method': 'training_mean_replacement', 'items': [],
        'notice': ('Inputs are blue minus red. Each comparison replaces one input with its training-set mean. '
                   'Differences use your team\'s probability and do not add up to an explanation of the result. '
                   'These are model sensitivity checks, not causal effects, SHAP values, or gameplay recommendations.'),
    }
    prediction = predict_snapshot(features, team_id, source)
    if prediction['probability'] is None:
        result['notice'] = prediction['notice']
        return result
    try:
        model = _read_model()
        if model is None or model['trained_on'] != source:
            return result
        probability = _predict_probability(model, features, team_id)
        items = []
        for name, reference in zip(FEATURE_NAMES, model['scaler']['mean']):
            changed = dict(features)
            changed[name] = reference
            at_reference = _predict_probability(model, changed, team_id)
            items.append({'feature': name, 'observed_value': _number(features[name]),
                          'reference_value': reference, 'probability_at_reference': at_reference,
                          'difference': probability - at_reference})
        result.update(available=True, items=sorted(items, key=lambda item: -abs(item['difference'])))
    except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        result['notice'] = 'Snapshot or model is invalid; input sensitivity is unavailable.'
    return result


def observed_events(match: dict, timeline: dict | None, team_id: int) -> list[dict]:
    """Observed kills and objectives, without inferred teamfights or causal labels."""
    try:
        if (team_id not in (100, 200) or not timeline
                or timeline['metadata']['matchId'] != match['metadata']['matchId']):
            return []
        people = match['info']['participants']
        teams = {p['participantId']: p['teamId'] for p in people}
        if (set(teams) != set(range(1, 11)) or any(type(pid) is not int for pid in teams)
                or list(teams.values()).count(100) != 5 or list(teams.values()).count(200) != 5):
            return []
        duration_ms = _number(match['info']['gameDuration']) * 1000
        frames = timeline['info']['frames']
        if not isinstance(frames, list):
            return []
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return []
    output, seen = [], set()
    for frame in frames:
        if not isinstance(frame, dict) or not isinstance(frame.get('events', []), list):
            continue
        for event in frame.get('events', []):
            try:
                timestamp = _number(event['timestamp'])
                if not 0 <= timestamp <= duration_ms:
                    continue
                kind, label, credited = event.get('type'), None, None
                killer = event.get('killerId')
                killer_team = teams.get(killer) if type(killer) is int else None
                if kind == 'CHAMPION_KILL':
                    label, credited = 'Champion kill', killer_team
                elif kind == 'BUILDING_KILL':
                    label = {'TOWER_BUILDING': 'Tower destroyed',
                             'INHIBITOR_BUILDING': 'Inhibitor destroyed'}.get(event.get('buildingType'))
                    owner = event.get('teamId')
                    credited = 300 - owner if type(owner) is int and owner in (100, 200) else None
                elif kind == 'ELITE_MONSTER_KILL':
                    label = {'DRAGON': 'Dragon taken', 'BARON_NASHOR': 'Baron taken',
                             'RIFTHERALD': 'Rift Herald taken', 'HORDE': 'Void Grub taken'}.get(event.get('monsterType'))
                    credited = event.get('killerTeamId') or killer_team
                if label is None:
                    continue
                if type(credited) is not int or credited not in (100, 200):
                    credited = None
                key = (timestamp, kind, label, event.get('killerId'), event.get('victimId'),
                       event.get('monsterSubType'), event.get('laneType'), event.get('towerType'))
                if key in seen:
                    continue
                seen.add(key)
                output.append({'timestamp_ms': timestamp, 'minute': round(timestamp / 60_000, 2),
                               'kind': kind, 'label': label, 'team_id': credited,
                               'side': 'unknown' if credited is None else 'own' if credited == team_id else 'opponent'})
            except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
                continue
    return sorted(output, key=lambda event: event['timestamp_ms'])


def prediction_review(match: dict, timeline: dict | None, team_id: int, source: str) -> dict:
    features = extract_features(match, timeline) if timeline else None
    timestamp = None
    if features is not None:
        timestamp = max(frame['timestamp'] for frame in timeline['info']['frames']
                        if MIN_SNAPSHOT_MS <= frame['timestamp'] <= SNAPSHOT_MS)
    return {'snapshot_timestamp_ms': timestamp,
            'sensitivity': feature_sensitivity(features, team_id, source),
            'events': observed_events(match, timeline, team_id)}
