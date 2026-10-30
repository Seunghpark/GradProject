"""Expose only bounded benchmark metrics matching the installed model/split."""
import hashlib
import json
import math
from pathlib import Path

from .ml import _model_path

COMPARISON_PATH = Path(__file__).resolve().parents[1] / 'data' / 'model_comparison.json'
MAX_BYTES = 2_000_000


def _read(path):
    with path.open('rb') as source:
        content = source.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError('Comparison artifact exceeds size limit')
    return content


def get_comparison_cache_version():
    try:
        return hashlib.sha256(_read(COMPARISON_PATH)).hexdigest()
    except FileNotFoundError:
        return 'missing'
    except ValueError:
        return 'oversized'
    except OSError:
        return 'unreadable'


def _metrics(values):
    if not isinstance(values, dict) or set(values) != {'accuracy', 'roc_auc', 'brier_score'}:
        raise ValueError('Invalid comparison metrics')
    for key, value in values.items():
        if key == 'roc_auc' and value is None:
            continue
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Invalid comparison metric value')
    return {key: values[key] for key in ('accuracy', 'roc_auc', 'brier_score')}


def get_model_comparison():
    try:
        comparison = json.loads(_read(COMPARISON_PATH))
        model_content = _read(_model_path())
        active = json.loads(model_content)
        if (comparison.get('schema_version') != 1
                or comparison.get('reference_model_sha256') != hashlib.sha256(model_content).hexdigest()
                or comparison.get('input_sha256') != active['report']['input_sha256']
                or comparison.get('data_source') != active['trained_on']
                or active['trained_on'] not in ('riot', 'synthetic')
                or comparison.get('train') != active['report']['train']
                or comparison.get('test') != active['report']['test']):
            return None
        notice = comparison['notice']
        if not isinstance(notice, str) or not notice or len(notice) > 4000:
            return None
        counts = [comparison[name]['count'] for name in ('train', 'test')]
        if any(type(count) is not int or count <= 0 for count in counts):
            return None
        raw_models = comparison['models']
        if not isinstance(raw_models, dict) or set(raw_models) != {'logistic_regression', 'random_forest', 'xgboost'}:
            return None
        models = []
        for name in ('logistic_regression', 'random_forest', 'xgboost'):
            entry = raw_models[name]
            row = {'algorithm': name, 'status': entry['status']}
            if entry['status'] == 'evaluated':
                row['metrics'] = _metrics(entry['metrics'])
            elif entry['status'] == 'unavailable':
                if not isinstance(entry.get('notice'), str) or len(entry['notice']) > 2000:
                    return None
                row['notice'] = entry['notice']
            else:
                return None
            models.append(row)
        return {'notice': notice, 'train_count': counts[0], 'test_count': counts[1],
                'models': models, 'active_model_unchanged': True}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return None
