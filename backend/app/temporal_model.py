"""Separately trained, time-specific models for retrospective probability curves."""
import hashlib
import json
import os
from pathlib import Path

from .ml import _number, _predict_probability, _validate_model, extract_features

NOTICE = ('Exploratory retrospective probabilities from separately trained minute-specific MLPs. '
          'Each point uses the latest complete frame at or up to one minute before its target. '
          'The same small holdout was already viewed; these are uncalibrated research outputs, '
          'not independent validation, causal effects, or live coaching. Late-match samples select games still in progress.')


def _temporal_path() -> Path:
    return Path(os.environ.get('TEMPORAL_MODEL_PATH', str(Path(__file__).resolve().parents[1] / 'data' / 'timeline_models.json')))


def get_temporal_cache_version() -> str:
    try:
        with _temporal_path().open('rb') as handle:
            content = handle.read(2_000_001)
        return hashlib.sha256(content).hexdigest() if len(content) <= 2_000_000 else 'oversized'
    except FileNotFoundError:
        return 'missing'
    except OSError:
        return 'unreadable'


def _read_temporal() -> dict | None:
    path = _temporal_path()
    if not path.is_file():
        return None
    if path.stat().st_size > 2_000_000:
        raise ValueError('Temporal artifact exceeds size limit')
    bundle = json.loads(path.read_text(encoding='utf-8'))
    if (bundle.get('schema_version') != 1 or bundle.get('kind') != 'minute_specific_mlp'
            or bundle.get('trained_on') not in ('riot', 'synthetic')
            or not isinstance(bundle.get('models'), list) or not 1 <= len(bundle['models']) <= 16):
        raise ValueError('Invalid temporal artifact')
    seen = set()
    for entry in bundle['models']:
        minute = entry['minute']
        if type(minute) is not int or not 5 <= minute <= 20 or minute in seen:
            raise ValueError('Invalid temporal target')
        seen.add(minute)
        model = _validate_model(entry['model'])
        if model['algorithm'] != 'mlp' or model['trained_on'] != bundle['trained_on']:
            raise ValueError('Invalid temporal model provenance')
        report = model['report']
        if report['target_minute'] != minute:
            raise ValueError('Temporal target does not match training report')
        for partition in ('train', 'test'):
            count = report[partition]['count']
            if type(count) is not int or count < (60 if partition == 'train' else 20):
                raise ValueError('Insufficient temporal evaluation sample')
        for metrics in (report['metrics'], report['baseline'], report['logistic_baseline']['metrics']):
            for key in ('accuracy', 'brier_score', 'roc_auc'):
                value = metrics[key]
                if value is None and key == 'roc_auc':
                    continue
                if not 0 <= _number(value) <= 1:
                    raise ValueError('Invalid temporal metric')
    return bundle


def probability_timeline(match: dict, timeline: dict | None, team_id: int, source: str) -> dict:
    response = {'available': False, 'trained_on': None, 'notice': NOTICE, 'points': [], 'evaluation': []}
    try:
        bundle = _read_temporal()
        if bundle is None:
            response['notice'] = 'No separately trained temporal models are installed; no probability curve is estimated.'
            return response
        response['trained_on'] = bundle['trained_on']
        for entry in sorted(bundle['models'], key=lambda entry: entry['minute']):
            minute, model = entry['minute'], entry['model']
            report = model['report']
            response['evaluation'].append({'minute': minute, 'train_count': report['train']['count'],
                                           'test_count': report['test']['count'], 'metrics': report['metrics'],
                                           'baseline': report['baseline'], 'logistic_baseline': report['logistic_baseline']})
            if (type(team_id) is not int or team_id not in (100, 200)
                    or source != bundle['trained_on'] or timeline is None):
                continue
            target = minute * 60_000
            features = extract_features(match, timeline, snapshot_ms=target)
            if features is None:
                continue
            timestamp = max(frame['timestamp'] for frame in timeline['info']['frames']
                            if target - 60_000 <= frame['timestamp'] <= target)
            response['points'].append({'minute': minute, 'snapshot_timestamp_ms': timestamp,
                                       'probability': _predict_probability(model, features, team_id)})
        response['available'] = bool(response['points'])
        if source != bundle['trained_on']:
            response['notice'] = 'Temporal model and match data sources differ; probabilities are disabled. ' + NOTICE
        elif bundle['trained_on'] == 'synthetic':
            response['notice'] = 'Synthetic demonstration only; no real-match performance claim. ' + NOTICE
    except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        response.update(available=False, points=[], evaluation=[], notice='Temporal model or snapshot is invalid; probabilities are disabled.')
    return response
