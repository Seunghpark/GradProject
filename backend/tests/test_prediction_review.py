from __future__ import annotations
import copy
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.demo import demo_records
from app.ml import FEATURE_NAMES, predict_snapshot
from app.prediction_review import feature_sensitivity, observed_events, prediction_review


class SensitivityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'model.json'
        self.environment = patch.dict(os.environ, {'MODEL_PATH': str(self.path)})
        self.environment.start()
        self.model = {
            'schema_version': 1, 'algorithm': 'logistic_regression', 'trained_on': 'synthetic',
            'feature_names': list(FEATURE_NAMES), 'coefficients': [2, 0, 0, 0, 0, 0], 'intercept': 0,
            'scaler': {'mean': [100, 10, 2, 0, 0, 0], 'scale': [1000, 100, 10, 1, 1, 1]},
        }
        self.features = dict(zip(FEATURE_NAMES, [1100, 20, 3, 0, 0, 0]))
        self.install()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def install(self):
        self.path.write_text(json.dumps(self.model), encoding='utf-8')

    def test_training_mean_substitution_has_exact_difference_without_mutating_inputs(self):
        before = dict(self.features)
        response = feature_sensitivity(self.features, 100, 'synthetic')
        self.assertTrue(response['available'])
        self.assertEqual(len(response['items']), 6)
        gold = response['items'][0]
        self.assertEqual(gold['feature'], 'gold_diff')
        self.assertEqual(gold['observed_value'], 1100)
        self.assertEqual(gold['reference_value'], 100)
        self.assertEqual(gold['probability_at_reference'], 0.5)
        self.assertAlmostEqual(gold['difference'], 1 / (1 + math.exp(-2)) - 0.5)
        self.assertTrue(all(item['difference'] == 0 for item in response['items'][1:]))
        self.assertEqual(self.features, before)
        self.assertIn('not causal', response['notice'])

    def test_red_sensitivity_and_reference_probability_complement_blue(self):
        blue = {item['feature']: item for item in feature_sensitivity(self.features, 100, 'synthetic')['items']}
        red = {item['feature']: item for item in feature_sensitivity(self.features, 200, 'synthetic')['items']}
        for name in FEATURE_NAMES:
            self.assertAlmostEqual(blue[name]['probability_at_reference'] + red[name]['probability_at_reference'], 1)
            self.assertAlmostEqual(blue[name]['difference'], -red[name]['difference'])

    def test_unavailable_model_and_wrong_source_never_leak_sensitivity(self):
        self.assertFalse(feature_sensitivity(self.features, 100, 'riot')['available'])
        self.assertEqual(feature_sensitivity(self.features, 100, 'riot')['items'], [])
        self.assertFalse(feature_sensitivity(self.features, 999, 'synthetic')['available'])
        self.path.unlink()
        self.assertFalse(feature_sensitivity(self.features, 100, 'synthetic')['available'])

    def test_invalid_or_nonfinite_features_are_unavailable(self):
        self.assertFalse(feature_sensitivity(None, 100, 'synthetic')['available'])
        for value in (float('nan'), float('inf'), True, '100'):
            changed = dict(self.features, gold_diff=value)
            self.assertFalse(feature_sensitivity(changed, 100, 'synthetic')['available'])

    def test_mlp_uses_same_forward_pass_and_fixed_reference(self):
        layers = []
        for previous, width in ((6, 16), (16, 8), (8, 4), (4, 1)):
            weights = [[0.0] * width for _ in range(previous)]
            weights[0][0] = 1.0
            layers.append({'weights': weights, 'biases': [0.0] * width})
        self.model.update(schema_version=2, algorithm='mlp', hidden_layers=[16, 8, 4], activation='relu',
                          output_activation='logistic', parameter_count=289, layers=layers)
        self.install()
        response = feature_sensitivity(self.features, 100, 'synthetic')
        gold = next(item for item in response['items'] if item['feature'] == 'gold_diff')
        actual = predict_snapshot(self.features, 100, 'synthetic')['probability']
        self.assertAlmostEqual(actual, 1 / (1 + math.exp(-1)))
        self.assertAlmostEqual(gold['difference'], actual - 0.5)
        self.assertEqual(gold['probability_at_reference'], 0.5)


class EventReviewTests(unittest.TestCase):
    def setUp(self):
        self.record = demo_records(1)[0]
        self.match, self.timeline = self.record['match'], self.record['timeline']

    def test_observed_event_team_and_unknown_killer_are_not_guessed(self):
        self.timeline['info']['frames'][0]['events'] = [
            {'type': 'BUILDING_KILL', 'buildingType': 'TOWER_BUILDING', 'teamId': 200,
             'killerId': 0, 'timestamp': 300_000},
            {'type': 'CHAMPION_KILL', 'killerId': 0, 'victimId': 3, 'timestamp': 310_000},
            {'type': 'CHAMPION_KILL', 'killerId': True, 'victimId': 3, 'timestamp': 320_000},
            {'type': 'ELITE_MONSTER_KILL', 'monsterType': 'BARON_NASHOR',
             'killerTeamId': 200, 'timestamp': 1_200_000},
        ]
        events = observed_events(self.match, self.timeline, 100)
        tower = next(event for event in events if event['label'] == 'Tower destroyed')
        self.assertEqual(tower['side'], 'own')
        self.assertEqual(tower['minute'], 5)
        unknown = [event for event in events if event['timestamp_ms'] in (310_000, 320_000)]
        self.assertTrue(all(event['side'] == 'unknown' and event['team_id'] is None for event in unknown))
        baron = next(event for event in events if event['label'] == 'Baron taken')
        self.assertEqual(baron['side'], 'opponent')

    def test_events_deduplicated_sorted_and_invalid_times_omitted(self):
        event = {'type': 'CHAMPION_KILL', 'timestamp': 100_000, 'killerId': 1, 'victimId': 6}
        self.timeline['info']['frames'] = [{'events': [event, dict(event), dict(event, timestamp=-1),
                                                        dict(event, timestamp=float('nan')),
                                                        dict(event, timestamp=10**8),
                                                        {'type': 'CHAT', 'timestamp': 200_000}]}]
        events = observed_events(self.match, self.timeline, 100)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['timestamp_ms'], 100_000)
        self.assertEqual(observed_events(self.match, None, 100), [])
        changed = copy.deepcopy(self.timeline)
        changed['metadata']['matchId'] = 'wrong'
        self.assertEqual(observed_events(self.match, changed, 100), [])

    def test_actual_snapshot_time_is_reported_without_other_minute_predictions(self):
        review = prediction_review(self.match, self.timeline, 100, 'synthetic')
        self.assertEqual(review['snapshot_timestamp_ms'], 600_000)
        self.assertTrue(review['events'])
        self.assertNotIn('probabilities', review)
        self.timeline['info']['frames'] = [frame for frame in self.timeline['info']['frames']
                                           if frame['timestamp'] != 600_000]
        self.timeline['info']['frames'][9]['timestamp'] = 540_088
        review = prediction_review(self.match, self.timeline, 100, 'synthetic')
        self.assertEqual(review['snapshot_timestamp_ms'], 540_088)
        self.timeline['info']['frames'] = []
        self.assertIsNone(prediction_review(self.match, self.timeline, 100, 'synthetic')['snapshot_timestamp_ms'])
        self.assertIsNone(prediction_review(self.match, None, 100, 'synthetic')['snapshot_timestamp_ms'])


if __name__ == '__main__':
    unittest.main()
