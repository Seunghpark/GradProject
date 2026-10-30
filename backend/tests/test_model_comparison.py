import hashlib
import json

import pytest

from app import model_comparison as module


@pytest.fixture
def comparison(tmp_path, monkeypatch):
    active = {'trained_on': 'riot', 'report': {'input_sha256': 'a' * 64,
              'train': {'count': 83, 'match_ids': ['private-train-id']},
              'test': {'count': 21, 'match_ids': ['private-test-id']}}}
    model_path, comparison_path = tmp_path / 'active.json', tmp_path / 'comparison.json'
    model_path.write_text(json.dumps(active), encoding='utf-8')
    metrics = {'accuracy': .5, 'roc_auc': .6, 'brier_score': .25}
    data = {'schema_version': 1, 'reference_model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
            'input_sha256': 'a' * 64, 'data_source': 'riot',
            'train': active['report']['train'], 'test': active['report']['test'],
            'notice': 'Exploratory reused holdout, active model unchanged.',
            'models': {'logistic_regression': {'status': 'evaluated', 'metrics': metrics},
                       'random_forest': {'status': 'evaluated', 'metrics': metrics},
                       'xgboost': {'status': 'unavailable', 'notice': 'Not installed'}}}
    comparison_path.write_text(json.dumps(data), encoding='utf-8')
    monkeypatch.setenv('MODEL_PATH', str(model_path))
    monkeypatch.setattr(module, 'COMPARISON_PATH', comparison_path)
    return data, comparison_path, model_path


def test_compact_output_excludes_ids_paths_weights_and_parameters(comparison):
    data, _, _ = comparison
    result = module.get_model_comparison()
    assert result['active_model_unchanged'] is True
    assert (result['train_count'], result['test_count']) == (83, 21)
    assert result['models'][1]['algorithm'] == 'random_forest'
    assert result['models'][1]['metrics'] == data['models']['random_forest']['metrics']
    assert 'private-' not in json.dumps(result)
    assert 'sha256' not in json.dumps(result)


@pytest.mark.parametrize('field,value', [('reference_model_sha256', 'wrong'), ('input_sha256', 'wrong'),
                                        ('data_source', 'synthetic'), ('schema_version', 99),
                                        ('test', {'count': 20}), ('notice', None)])
def test_mismatched_comparison_is_not_attached(comparison, field, value):
    data, path, _ = comparison
    data[field] = value
    path.write_text(json.dumps(data), encoding='utf-8')
    assert module.get_model_comparison() is None


@pytest.mark.parametrize('value', [True, -1, 1.1, float('nan'), float('inf'), '0.5'])
def test_nonfinite_or_invalid_metrics_disabled(comparison, value):
    data, path, _ = comparison
    data['models']['random_forest']['metrics']['accuracy'] = value
    path.write_text(json.dumps(data), encoding='utf-8')
    assert module.get_model_comparison() is None


def test_null_auc_allowed_and_active_weight_change_invalidates_reference(comparison):
    data, path, active_path = comparison
    data['models']['random_forest']['metrics']['roc_auc'] = None
    path.write_text(json.dumps(data), encoding='utf-8')
    assert module.get_model_comparison()['models'][1]['metrics']['roc_auc'] is None
    active_path.write_bytes(active_path.read_bytes() + b'\n')
    assert module.get_model_comparison() is None


def test_missing_and_oversized_cache_versions_are_bounded(comparison):
    _, path, _ = comparison
    first = module.get_comparison_cache_version()
    path.write_bytes(path.read_bytes() + b'\n')
    assert module.get_comparison_cache_version() != first
    path.unlink()
    assert module.get_model_comparison() is None
    assert module.get_comparison_cache_version() == 'missing'
    path.write_bytes(b'x' * (module.MAX_BYTES + 1))
    assert module.get_model_comparison() is None
    assert module.get_comparison_cache_version() == 'oversized'
