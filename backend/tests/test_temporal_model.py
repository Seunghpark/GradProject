from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.demo import demo_records
from app.ml import FEATURE_NAMES, extract_features
from app.temporal_model import get_temporal_cache_version, probability_timeline
from scripts.train_model import train
from scripts.train_timeline_models import train_timeline


class TemporalModelsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)
        cls.source = cls.directory / 'records.jsonl'
        cls.reference = cls.directory / 'reference.json'
        cls.output = cls.directory / 'timeline.json'
        cls.records = list(reversed(demo_records(120)))
        # A held-out-only shift must not affect preprocessing fitted to earlier games.
        for record in cls.records[96:]:
            for frame in record['timeline']['info']['frames']:
                frame['participantFrames']['1']['totalGold'] += 50_000
        cls.source.write_text('\n'.join(json.dumps(record) for record in cls.records), encoding='utf-8')
        cls.reference_model = train(cls.source, cls.reference)
        cls.bundle = train_timeline(cls.source, cls.reference, cls.output, minutes=(5, 20))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.output.write_text(json.dumps(self.bundle), encoding='utf-8')
        self.environment = patch.dict(os.environ, {'TEMPORAL_MODEL_PATH': str(self.output)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_default_extract_features_unchanged_and_targets_exclude_future(self):
        record = self.records[0]
        self.assertEqual(extract_features(record['match'], record['timeline']),
                         extract_features(record['match'], record['timeline'], snapshot_ms=600_000))
        before = extract_features(record['match'], record['timeline'], snapshot_ms=300_000)
        changed = copy.deepcopy(record)
        for frame in changed['timeline']['info']['frames']:
            if frame['timestamp'] > 300_000:
                frame['participantFrames']['1']['totalGold'] += 99_999
        for player in changed['match']['info']['participants']:
            player.update(kills=999_999, win=not player['win'])
        self.assertEqual(before, extract_features(changed['match'], changed['timeline'], snapshot_ms=300_000))
        self.assertIsNone(extract_features(record['match'], record['timeline'], snapshot_ms=True))

    def test_global_game_split_and_train_only_scalers_reused_at_every_minute(self):
        train_ids = set(self.reference_model['report']['train']['match_ids'])
        test_ids = set(self.reference_model['report']['test']['match_ids'])
        for entry in self.bundle['models']:
            model, minute = entry['model'], entry['minute']
            report = model['report']
            self.assertEqual(set(report['train']['match_ids']), train_ids)
            self.assertEqual(set(report['test']['match_ids']), test_ids)
            self.assertFalse(set(report['train']['match_ids']) & set(report['test']['match_ids']))
            values = [extract_features(record['match'], record['timeline'], minute * 60_000)['gold_diff']
                      for record in self.records if record['match']['metadata']['matchId'] in train_ids]
            self.assertAlmostEqual(model['scaler']['mean'][0], sum(values) / len(values))
            self.assertEqual(report['train']['count'], 96)
            self.assertEqual(report['test']['count'], 24)
            self.assertEqual(model['parameter_count'], 289)

    def test_predictions_complement_by_team_and_are_source_guarded(self):
        record = self.records[-1]
        blue = probability_timeline(record['match'], record['timeline'], 100, 'synthetic')
        red = probability_timeline(record['match'], record['timeline'], 200, 'synthetic')
        self.assertTrue(blue['available'])
        self.assertEqual([point['minute'] for point in blue['points']], [5, 20])
        for blue_point, red_point in zip(blue['points'], red['points']):
            self.assertAlmostEqual(blue_point['probability'] + red_point['probability'], 1)
            self.assertEqual(blue_point['snapshot_timestamp_ms'], blue_point['minute'] * 60_000)
        real = probability_timeline(record['match'], record['timeline'], 100, 'riot')
        self.assertFalse(real['available'])
        self.assertEqual(real['points'], [])
        self.assertEqual(blue['evaluation'], red['evaluation'])
        self.assertEqual(real['evaluation'], blue['evaluation'])
        self.assertIn('already viewed', blue['notice'])

    def test_evaluation_matches_saved_models_and_reports_every_target(self):
        import numpy as np
        from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
        from app.ml import _predict_probability
        for entry in self.bundle['models']:
            model, minute = entry['model'], entry['minute']
            test_ids = set(model['report']['test']['match_ids'])
            probabilities, labels = [], []
            for record in self.records:
                if record['match']['metadata']['matchId'] not in test_ids:
                    continue
                features = extract_features(record['match'], record['timeline'], minute * 60_000)
                probabilities.append(_predict_probability(model, features, 100))
                labels.append(int(record['match']['info']['teams'][0]['win']))
            probabilities = np.array(probabilities)
            metrics = model['report']['metrics']
            self.assertAlmostEqual(metrics['accuracy'], accuracy_score(labels, probabilities >= 0.5))
            self.assertAlmostEqual(metrics['brier_score'], brier_score_loss(labels, probabilities))
            self.assertAlmostEqual(metrics['roc_auc'], roc_auc_score(labels, probabilities))

    def test_invalid_temporal_artifact_fails_closed_and_versions_content(self):
        record = self.records[-1]
        before = get_temporal_cache_version()
        altered = copy.deepcopy(self.bundle)
        altered['models'][0]['model']['report']['target_minute'] = 20
        self.output.write_text(json.dumps(altered), encoding='utf-8')
        self.assertNotEqual(before, get_temporal_cache_version())
        prediction = probability_timeline(record['match'], record['timeline'], 100, 'synthetic')
        self.assertFalse(prediction['available'])
        self.assertEqual(prediction['points'], [])
        self.assertEqual(prediction['evaluation'], [])
        self.output.unlink()
        self.assertEqual(get_temporal_cache_version(), 'missing')
        self.assertFalse(probability_timeline(record['match'], record['timeline'], 100, 'synthetic')['available'])

    def test_invalid_training_requests_and_changed_dataset_preserve_reference(self):
        original = self.reference.read_bytes()
        with self.assertRaisesRegex(ValueError, 'preserve'):
            train_timeline(self.source, self.reference, self.reference, minutes=(5,))
        with self.assertRaisesRegex(ValueError, 'unique'):
            train_timeline(self.source, self.reference, self.output, minutes=(5, 5))
        changed = self.source.with_name('changed.jsonl')
        changed.write_bytes(self.source.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'hash differs'):
            train_timeline(changed, self.reference, self.output, minutes=(5,))
        self.assertEqual(original, self.reference.read_bytes())

    def test_short_or_missing_snapshot_omits_point_instead_of_extrapolating(self):
        changed = copy.deepcopy(self.records[-1])
        changed['match']['info']['gameDuration'] = 19 * 60
        response = probability_timeline(changed['match'], changed['timeline'], 100, 'synthetic')
        self.assertEqual([point['minute'] for point in response['points']], [5])
        self.assertEqual(probability_timeline(changed['match'], None, 100, 'synthetic')['points'], [])


if __name__ == '__main__':
    unittest.main()
