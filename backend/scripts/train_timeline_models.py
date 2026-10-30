"""Train fixed minute-specific MLPs on the saved experiment's unchanged game split."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.ml import FEATURE_NAMES, extract_features
from app.temporal_model import NOTICE
from scripts.train_model import _partition_report


def train_timeline(input_path: Path, reference_path: Path, output_path: Path,
                   minutes=tuple(range(5, 21))) -> dict:
    import numpy as np
    import sklearn
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler

    if output_path.resolve() in (input_path.resolve(), reference_path.resolve()):
        raise ValueError('Temporal output must preserve the input and reference model')
    if (not minutes or len(set(minutes)) != len(minutes)
            or any(type(minute) is not int or not 5 <= minute <= 20 for minute in minutes)):
        raise ValueError('Temporal targets must be unique whole minutes from 5 to 20')
    content = input_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    report = reference['report']
    if report['input_sha256'] != digest:
        raise ValueError('Dataset hash differs from the saved experiment; establish a new documented split first')
    train_ids = set(report['train']['match_ids'])
    test_ids = set(report['test']['match_ids'])
    if train_ids & test_ids or len(train_ids) < 60 or len(test_ids) < 20:
        raise ValueError('Reference must contain disjoint training and later holdout match IDs')
    records, seen = [], set()
    for line in content.decode('utf-8-sig').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        match_id = record['match']['metadata']['matchId']
        if match_id not in train_ids | test_ids or match_id in seen:
            continue
        if record['source'] != reference['trained_on'] or record['source'] not in ('riot', 'synthetic'):
            raise ValueError('Do not mix real and synthetic data')
        info = record['match']['info']
        outcomes = {team['teamId']: team['win'] for team in info['teams']}
        if (set(outcomes) != {100, 200} or any(type(value) is not bool for value in outcomes.values())
                or outcomes[100] == outcomes[200]):
            raise ValueError('Reference game has invalid outcomes')
        timestamp = info.get('gameStartTimestamp') or info['gameCreation']
        if type(timestamp) not in (int, float) or not np.isfinite(timestamp) or timestamp <= 0:
            raise ValueError('Reference game has invalid timestamp')
        seen.add(match_id)
        records.append({'match_id': match_id, 'timestamp': timestamp, 'source': record['source'],
                        'label': int(outcomes[100]), 'patch': str(info.get('gameVersion', 'unknown')),
                        'queue': info['queueId'], 'record': record,
                        'ended_at': timestamp + info['gameDuration'] * 1000})
    if seen != train_ids | test_ids:
        raise ValueError('Reference split contains games absent from the dataset')
    records.sort(key=lambda row: (row['timestamp'], row['match_id']))
    if max(row['ended_at'] for row in records if row['match_id'] in train_ids) >= min(
            row['timestamp'] for row in records if row['match_id'] in test_ids):
        raise ValueError('A training game ends after the holdout starts')
    bundle = {'schema_version': 1, 'kind': 'minute_specific_mlp', 'trained_on': reference['trained_on'],
              'created_at': datetime.now(timezone.utc).isoformat(), 'models': [],
              'report': {'notice': NOTICE, 'input_sha256': digest,
                         'reference_model_sha256': hashlib.sha256(reference_path.read_bytes()).hexdigest(),
                         'global_train_count': len(train_ids), 'global_test_count': len(test_ids),
                         'requested_minutes': list(minutes), 'skipped_minutes': [],
                         'selection': 'Unchanged saved global match split; no game can move between partitions at another minute.',
                         'libraries': {'numpy': np.__version__, 'scikit_learn': sklearn.__version__}}}
    for minute in sorted(minutes):
        target = minute * 60_000
        eligible = []
        actual_times = []
        for row in records:
            record = row['record']
            features = extract_features(record['match'], record['timeline'], snapshot_ms=target)
            if features is None:
                continue
            actual = max(frame['timestamp'] for frame in record['timeline']['info']['frames']
                         if target - 60_000 <= frame['timestamp'] <= target)
            actual_times.append(actual / 1000)
            eligible.append({key: value for key, value in row.items() if key not in ('record', 'ended_at')}
                            | {'features': [features[name] for name in FEATURE_NAMES]})
        earlier = [row for row in eligible if row['match_id'] in train_ids]
        later = [row for row in eligible if row['match_id'] in test_ids]
        if len(earlier) < 60 or len(later) < 20 or len({row['label'] for row in earlier}) != 2:
            bundle['report']['skipped_minutes'].append({'minute': minute, 'train_count': len(earlier),
                                                       'test_count': len(later), 'reason': 'Need 60 training, 20 holdout, and both training outcomes'})
            continue
        x_train = np.array([row['features'] for row in earlier], dtype=float)
        y_train = np.array([row['label'] for row in earlier])
        x_test = np.array([row['features'] for row in later], dtype=float)
        y_test = np.array([row['label'] for row in later])
        scaler = StandardScaler().fit(x_train)
        train_x, test_x = scaler.transform(x_train), scaler.transform(x_test)
        neural = MLPClassifier(hidden_layer_sizes=(16, 8, 4), activation='relu', solver='lbfgs',
                               alpha=1.0, random_state=42, max_iter=2000, max_fun=20000,
                               tol=1e-6, early_stopping=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ConvergenceWarning)
            neural.fit(train_x, y_train)
        logistic = LogisticRegression(C=1.0, max_iter=2000, random_state=42).fit(train_x, y_train)

        def measure(probabilities, labels=y_test):
            return {'accuracy': float(accuracy_score(labels, probabilities >= 0.5)),
                    'brier_score': float(brier_score_loss(labels, probabilities)),
                    'roc_auc': float(roc_auc_score(labels, probabilities)) if len(set(labels)) == 2 else None}

        prior = float(y_train.mean())
        model = {'schema_version': 2, 'algorithm': 'mlp', 'trained_on': reference['trained_on'],
                 'feature_names': list(FEATURE_NAMES), 'hidden_layers': [16, 8, 4], 'activation': 'relu',
                 'output_activation': 'logistic', 'parameter_count': 289,
                 'scaler': {'mean': scaler.mean_.tolist(), 'scale': scaler.scale_.tolist()},
                 'layers': [{'weights': weights.tolist(), 'biases': biases.tolist()}
                            for weights, biases in zip(neural.coefs_, neural.intercepts_)],
                 'report': {'notice': NOTICE, 'target_minute': minute,
                            'actual_snapshot_seconds': {'minimum': min(actual_times), 'maximum': max(actual_times)},
                            'train': _partition_report(earlier), 'test': _partition_report(later),
                            'scaler_fit': 'training partition only',
                            'metrics': measure(neural.predict_proba(test_x)[:, 1]),
                            'training_metrics': measure(neural.predict_proba(train_x)[:, 1], y_train),
                            'baseline': {'probability': prior, **measure(np.full(len(y_test), prior))},
                            'logistic_baseline': {'method': 'Logistic regression', 'metrics': measure(logistic.predict_proba(test_x)[:, 1])},
                            'training': {'solver': 'lbfgs', 'alpha': 1.0, 'random_state': 42,
                                         'max_iter': 2000, 'max_fun': 20000, 'tol': 1e-6,
                                         'early_stopping': False, 'iterations': int(neural.n_iter_),
                                         'warnings': [str(item.message) for item in caught]}}}
        bundle['models'].append({'minute': minute, 'model': model})
        print(f'Minute {minute}: trained {len(earlier)}, evaluated {len(later)}; fixed parameters, no model selection.', flush=True)
    if not bundle['models']:
        raise ValueError('No temporal target has sufficient eligible games')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return bundle


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data' / 'riot_matches.jsonl')
    parser.add_argument('--reference', type=Path, default=ROOT / 'data' / 'model.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'data' / 'timeline_models.json')
    args = parser.parse_args()
    try:
        result = train_timeline(args.input, args.reference, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f'Temporal training not completed: {error}\n')
    print(json.dumps({'minutes_trained': [entry['minute'] for entry in result['models']],
                      'skipped_minutes': result['report']['skipped_minutes'], 'notice': NOTICE}, indent=2))
