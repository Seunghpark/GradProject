"""Fixed split, metrics and model-preservation checks use fictional fixtures."""
import hashlib
import json

import pytest

from scripts.benchmark_models import benchmark, fixed_rows, measure
from scripts.generate_synthetic_training import generate_records
from scripts.train_model import train


@pytest.fixture(scope='module')
def experiment(tmp_path_factory):
    directory = tmp_path_factory.mktemp('benchmark')
    source, reference = directory / 'raw.jsonl', directory / 'reference.json'
    source.write_text('\n'.join(json.dumps(row) for row in generate_records(100)), encoding='utf-8')
    model = train(source, reference)
    return source, reference, model


def test_metrics_match_independent_small_example():
    result = measure([0, 0, 1, 1], [.1, .8, .4, .9])
    assert result['accuracy'] == .5
    assert result['brier_score'] == pytest.approx((.01 + .64 + .36 + .01) / 4)
    assert result['roc_auc'] == .75
    assert measure([1, 1], [.5, .9])['roc_auc'] is None


@pytest.mark.parametrize('labels,probabilities', [([], []), ([0], [1, 0]), ([2], [.5]), ([0], [float('nan')]), ([0], [1.1])])
def test_invalid_metrics_rejected(labels, probabilities):
    with pytest.raises(ValueError):
        measure(labels, probabilities)


def test_benchmark_preserves_reference_and_compares_same_split(experiment, tmp_path, monkeypatch):
    source, reference, model = experiment
    original = reference.read_bytes()
    monkeypatch.setattr('scripts.benchmark_models.importlib.util.find_spec', lambda name: None)
    result = benchmark(source, reference, tmp_path / 'comparison.json')
    assert reference.read_bytes() == original
    assert result['input_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert result['train'] == model['report']['train']
    assert result['test'] == model['report']['test']
    assert result['models']['logistic_regression']['metrics'] == model['report']['metrics']
    forest = result['models']['random_forest']
    assert forest['status'] == 'evaluated'
    assert forest['parameters']['min_samples_leaf'] == 3
    assert forest['parameters']['max_depth'] == 5
    assert 0 <= forest['metrics']['accuracy'] <= 1
    assert result['models']['xgboost']['status'] == 'unavailable'
    assert result['synthetic_demo_only'] is True
    assert 'already-viewed' in result['notice']


def test_hash_mismatch_rejected(experiment, tmp_path):
    source, reference, _ = experiment
    changed = tmp_path / 'changed.jsonl'
    changed.write_bytes(source.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='hash'):
        fixed_rows(changed, reference)


def test_overlapping_or_duplicate_reference_ids_rejected(experiment, tmp_path):
    source, _, model = experiment
    changed = json.loads(json.dumps(model))
    changed['report']['test']['match_ids'][0] = changed['report']['train']['match_ids'][0]
    reference = tmp_path / 'changed-reference.json'
    reference.write_text(json.dumps(changed), encoding='utf-8')
    with pytest.raises(ValueError, match='disjoint'):
        fixed_rows(source, reference)


def test_output_cannot_replace_reference_or_active_model(experiment, tmp_path):
    source, reference, _ = experiment
    for output in (reference, source, tmp_path / 'model.json', tmp_path / 'timeline_models.json'):
        with pytest.raises(ValueError, match='preserve'):
            benchmark(source, reference, output)


def test_reference_label_counts_cannot_be_changed(experiment, tmp_path):
    source, _, model = experiment
    changed = json.loads(json.dumps(model))
    changed['report']['test']['blue_wins'] += 1
    reference = tmp_path / 'changed-reference.json'
    reference.write_text(json.dumps(changed), encoding='utf-8')
    with pytest.raises(ValueError, match='outcome counts'):
        fixed_rows(source, reference)
