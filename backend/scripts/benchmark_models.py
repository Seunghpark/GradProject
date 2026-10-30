"""Exploratory LR/RF/optional-XGBoost comparison on an existing locked split.

This never replaces the active MLP. The holdout has already been viewed and is
not used to choose parameters, select a winner or recover historical results.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ml import FEATURE_NAMES, extract_features
from scripts.train_model import _partition_report

NOTICE = ('Exploratory comparison on the already-viewed, unchanged holdout. RF/XGBoost parameters '
          'were chosen after that holdout had been seen, without tuning them on its results. '
          'This is not fresh independent validation and does not select or replace the active MLP. '
          'The lost historical 1,000-match results are not reproduced by this experiment.')
RF_PARAMS = {'n_estimators': 200, 'max_depth': 5, 'min_samples_leaf': 3, 'random_state': 42, 'n_jobs': 1}
XGB_PARAMS = {'n_estimators': 200, 'max_depth': 3, 'learning_rate': .05, 'subsample': 1.0,
              'colsample_bytree': 1.0, 'reg_lambda': 1.0, 'random_state': 42,
              'n_jobs': 1, 'eval_metric': 'logloss'}


def fixed_rows(input_path: Path, reference_path: Path):
    import numpy as np

    content, reference_content = input_path.read_bytes(), reference_path.read_bytes()
    reference = json.loads(reference_content)
    report = reference['report']
    digest = hashlib.sha256(content).hexdigest()
    if (report.get('input_sha256') != digest or reference.get('trained_on') not in ('riot', 'synthetic')
            or report.get('data_source') != reference['trained_on']
            or reference.get('feature_names') != list(FEATURE_NAMES)):
        raise ValueError('Input hash, provenance or features differ from the reference experiment')
    partitions = []
    for name in ('train', 'test'):
        group = report[name]
        ids = group['match_ids']
        if (not isinstance(ids, list) or not ids or any(not isinstance(item, str) or not item for item in ids)
                or len(ids) != len(set(ids)) or group['count'] != len(ids)):
            raise ValueError('Reference partition IDs/counts are invalid')
        partitions.append(ids)
    train_ids, test_ids = map(set, partitions)
    if train_ids & test_ids or len(train_ids) < 60 or len(test_ids) < 20:
        raise ValueError('Need disjoint reference partitions with 60 training and 20 holdout games')
    if report['eligible_unique_matches'] != len(train_ids | test_ids):
        raise ValueError('Reference eligible count differs from its partition IDs')
    rows, seen, duplicates, skipped = [], set(), 0, 0
    for number, line in enumerate(content.decode('utf-8-sig').splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if record['source'] != reference['trained_on']:
                raise ValueError('Mixed data provenance')
            match, timeline = record['match'], record['timeline']
            features = extract_features(match, timeline)
            if features is None:
                skipped += 1
                continue
            info, match_id = match['info'], match['metadata']['matchId']
            if match_id in seen:
                duplicates += 1
                continue
            if match_id not in train_ids | test_ids:
                raise ValueError('Eligible match absent from reference split')
            timestamp = info.get('gameStartTimestamp') or info.get('gameCreation')
            if type(timestamp) not in (int, float) or not np.isfinite(timestamp) or timestamp <= 0:
                raise ValueError('Invalid match timestamp')
            teams = info['teams']
            results = {team['teamId']: team['win'] for team in teams}
            if (len(teams) != 2 or set(results) != {100, 200}
                    or any(type(value) is not bool for value in results.values()) or results[100] == results[200]):
                raise ValueError('Invalid match outcomes')
            seen.add(match_id)
            rows.append({'match_id': match_id, 'timestamp': timestamp,
                         'ended_at': timestamp + info['gameDuration'] * 1000,
                         'patch': str(info.get('gameVersion', 'unknown')), 'queue': info['queueId'],
                         'features': [features[key] for key in FEATURE_NAMES], 'label': int(results[100])})
        except (KeyError, ValueError, TypeError, OverflowError, AttributeError) as error:
            raise ValueError(f'Invalid benchmark record on line {number}') from error
    if seen != train_ids | test_ids:
        raise ValueError('Dataset is missing reference games')
    rows.sort(key=lambda row: (row['timestamp'], row['match_id']))
    earlier = [row for row in rows if row['match_id'] in train_ids]
    later = [row for row in rows if row['match_id'] in test_ids]
    if ([row['match_id'] for row in earlier] != partitions[0]
            or [row['match_id'] for row in later] != partitions[1]
            or max(row['ended_at'] for row in earlier) >= min(row['timestamp'] for row in later)):
        raise ValueError('Reference order is not a separated chronological split')
    if len({row['label'] for row in earlier}) != 2:
        raise ValueError('Training partition must contain both outcomes')
    for group, partition_name in ((earlier, 'train'), (later, 'test')):
        if sum(row['label'] for row in group) != report[partition_name]['blue_wins']:
            raise ValueError('Reference outcome counts differ from source data')
        if _partition_report(group) != report[partition_name]:
            raise ValueError('Reference partition metadata differs from source data')
    return earlier, later, reference, {'input_sha256': digest,
                                     'reference_model_sha256': hashlib.sha256(reference_content).hexdigest(),
                                     'duplicates_removed': duplicates, 'ineligible_records_skipped': skipped}


def measure(labels, probabilities):
    import numpy as np
    from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score

    labels, probabilities = np.asarray(labels), np.asarray(probabilities, dtype=float)
    if (labels.ndim != 1 or probabilities.ndim != 1 or not len(labels)
            or len(labels) != len(probabilities) or not set(labels).issubset({0, 1})
            or not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1))):
        raise ValueError('Invalid outcome/probability arrays')
    return {'accuracy': float(accuracy_score(labels, probabilities >= .5)),
            'brier_score': float(brier_score_loss(labels, probabilities)),
            'roc_auc': float(roc_auc_score(labels, probabilities)) if len(set(labels)) == 2 else None}


def benchmark(input_path: Path, reference_path: Path, output_path: Path):
    import numpy as np
    import sklearn
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    if (output_path.resolve() in (input_path.resolve(), reference_path.resolve())
            or output_path.name in {'model.json', 'riot_model.json', 'riot_mlp_model.json', 'timeline_models.json'}):
        raise ValueError('Comparison output must preserve all source and active model files')
    earlier, later, reference, audit = fixed_rows(input_path, reference_path)
    train_x = np.asarray([row['features'] for row in earlier], dtype=float)
    test_x = np.asarray([row['features'] for row in later], dtype=float)
    train_y, test_y = np.asarray([row['label'] for row in earlier]), np.asarray([row['label'] for row in later])
    scaler = StandardScaler().fit(train_x)
    if not (np.allclose(scaler.mean_, reference['scaler']['mean'], rtol=0, atol=1e-10)
            and np.allclose(scaler.scale_, reference['scaler']['scale'], rtol=0, atol=1e-10)):
        raise ValueError('Training-only scaler does not match the locked reference')
    train_x, test_x = scaler.transform(train_x), scaler.transform(test_x)
    models = {}
    classifiers = [('logistic_regression', LogisticRegression(C=1.0, max_iter=2000, random_state=42),
                    {'C': 1.0, 'max_iter': 2000, 'random_state': 42}),
                   ('random_forest', RandomForestClassifier(**RF_PARAMS), RF_PARAMS)]
    if importlib.util.find_spec('xgboost') is None:
        models['xgboost'] = {'status': 'unavailable', 'notice': 'XGBoost is not installed in this Python environment; no dependency was installed.'}
    else:
        from xgboost import XGBClassifier
        classifiers.append(('xgboost', XGBClassifier(**XGB_PARAMS), XGB_PARAMS))
    for name, classifier, parameters in classifiers:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            classifier.fit(train_x, train_y)
        models[name] = {'status': 'evaluated', 'parameters': parameters,
                        'metrics': measure(test_y, classifier.predict_proba(test_x)[:, 1]),
                        'training_metrics': measure(train_y, classifier.predict_proba(train_x)[:, 1]),
                        'warnings': [str(item.message) for item in caught]}
    result = {'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
              'data_source': reference['trained_on'], 'synthetic_demo_only': reference['trained_on'] == 'synthetic',
              'notice': NOTICE, **audit,
              'feature_names': list(FEATURE_NAMES), 'train': reference['report']['train'],
              'test': reference['report']['test'], 'scaler_fit': 'training partition only; matches reference',
              'selection': 'unchanged reference match IDs; one blue-side row per unique match',
              'models': models, 'constant_baseline': measure(test_y, np.full(len(test_y), float(train_y.mean()))),
              'active_model_reference': {'algorithm': reference['algorithm'], 'status': 'unchanged; recorded reference metrics only',
                                         'metrics': reference['report']['metrics']},
              'libraries': {'numpy': np.__version__, 'scikit_learn': sklearn.__version__}}
    if result['synthetic_demo_only']:
        result['notice'] += ' Synthetic fixture results are not evidence of real game performance.'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data' / 'riot_matches.jsonl')
    parser.add_argument('--reference', type=Path, default=ROOT / 'data' / 'model.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'data' / 'model_comparison.json')
    args = parser.parse_args()
    try:
        result = benchmark(args.input, args.reference, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Comparison not completed: {error}\n')
    print(json.dumps({'notice': result['notice'], 'train_count': result['train']['count'],
                      'test_count': result['test']['count'],
                      'models': {name: {'status': model['status'], 'metrics': model.get('metrics')}
                                 for name, model in result['models'].items()},
                      'constant_baseline': result['constant_baseline']}, indent=2))


if __name__ == '__main__':
    main()
