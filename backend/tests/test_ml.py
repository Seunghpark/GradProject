from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.cache import Cache
from app.ml import FEATURE_NAMES, extract_features, get_model_cache_version, get_model_info, predict_snapshot
from scripts.generate_synthetic_training import generate_records
from scripts.train_model import train


def clone(record):
    return json.loads(json.dumps(record))


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.record = clone(generate_records(1)[0])

    def features(self, record=None):
        record = record or self.record
        return extract_features(record["match"], record["timeline"])

    def test_future_and_final_data_cannot_change_features(self):
        before = self.features()
        self.assertEqual(set(before), set(FEATURE_NAMES))
        changed = clone(self.record)
        for player in changed["match"]["info"]["participants"]:
            player.update(kills=99999, goldEarned=999999, win=False)
        changed["match"]["info"]["teams"][0]["win"] = False
        for frame in changed["timeline"]["info"]["frames"]:
            if frame["timestamp"] > 600_000:
                for pframe in frame["participantFrames"].values():
                    pframe["totalGold"] += 100000
            frame["events"].append({"type": "CHAMPION_KILL", "timestamp": 600_001, "killerId": 10})
        self.assertEqual(before, self.features(changed))

    def test_incomplete_frame_and_wrong_match_are_rejected(self):
        changed = clone(self.record)
        del changed["timeline"]["info"]["frames"][0]["participantFrames"]["10"]
        self.assertIsNone(self.features(changed))
        changed = clone(self.record)
        changed["timeline"]["metadata"]["matchId"] = "wrong"
        self.assertIsNone(self.features(changed))

    def test_old_future_short_or_unranked_snapshots_are_rejected(self):
        for timestamp in (539_999, 600_001):
            changed = clone(self.record)
            changed["timeline"]["info"]["frames"][0]["timestamp"] = timestamp
            self.assertIsNone(self.features(changed))
        changed = clone(self.record)
        changed["match"]["info"]["gameDuration"] = 600
        self.assertIsNone(self.features(changed))
        changed["match"]["info"]["gameDuration"] = 1800
        changed["match"]["info"]["queueId"] = 450
        self.assertIsNone(self.features(changed))

    def test_team_mapping_uses_metadata_not_participant_number(self):
        before = self.features()
        changed = clone(self.record)
        for participant in changed["match"]["info"]["participants"]:
            participant["teamId"] = 300 - participant["teamId"]
        for frame in changed["timeline"]["info"]["frames"]:
            for event in frame["events"]:
                for key in ("teamId", "killerTeamId"):
                    if key in event:
                        event[key] = 300 - event[key]
        after = self.features(changed)
        for name in FEATURE_NAMES:
            self.assertEqual(before[name], -after[name])

    def test_tower_owner_and_killer_zero(self):
        frame = self.record["timeline"]["info"]["frames"][0]
        frame["events"] = [{"type": "BUILDING_KILL", "buildingType": "TOWER_BUILDING",
                            "teamId": 200, "timestamp": 500000, "killerId": 0},
                           {"type": "CHAMPION_KILL", "killerId": 0, "timestamp": 500000}]
        self.assertEqual(self.features()["towers_diff"], 1)
        self.assertEqual(self.features()["kills_diff"], 0)


class InferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.model_path = Path(self.temp.name) / "model.json"
        self.environment = patch.dict(os.environ, {"MODEL_PATH": str(self.model_path)})
        self.environment.start()
        self.features = dict.fromkeys(FEATURE_NAMES, 0)
        self.model = {"schema_version": 1, "algorithm": "logistic_regression", "trained_on": "synthetic",
                      "feature_names": list(FEATURE_NAMES), "coefficients": [0] * 6, "intercept": 1,
                      "scaler": {"mean": [0] * 6, "scale": [1] * 6}}

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def install(self):
        self.model_path.write_text(json.dumps(self.model), encoding="utf-8")

    def test_missing_model_never_fabricates_probability(self):
        self.assertEqual(get_model_info()["status"], "not_trained")
        self.assertIsNone(predict_snapshot(self.features)["probability"])

    def test_synthetic_refused_for_real_and_team_probabilities_complement(self):
        self.install()
        self.assertIsNone(predict_snapshot(self.features, source="riot")["probability"])
        blue = predict_snapshot(self.features, 100, "synthetic")["probability"]
        red = predict_snapshot(self.features, 200, "synthetic")["probability"]
        self.assertGreater(blue, 0.5)
        self.assertAlmostEqual(blue + red, 1)
        self.model["trained_on"] = "riot"
        self.install()
        mismatch = predict_snapshot(self.features, source="synthetic")
        self.assertIsNone(mismatch["probability"])
        self.assertIn("data sources differ", mismatch["notice"])

    def test_corrupt_model_and_nonfinite_input_disabled(self):
        self.model["scaler"]["scale"][0] = 0
        self.install()
        self.assertEqual(get_model_info()["status"], "invalid")
        self.model["scaler"]["scale"][0] = 1
        self.install()
        self.features["gold_diff"] = float("nan")
        self.assertIsNone(predict_snapshot(self.features, source="synthetic")["probability"])

    def test_model_content_versions_fresh_and_stale_analysis_without_losing_raw_cache(self):
        missing_version = get_model_cache_version()
        self.install()
        first_version = get_model_cache_version()
        self.assertTrue(first_version.startswith("inference-v3:"))
        self.assertNotEqual(missing_version, first_version)
        cache = Cache(":memory:")
        try:
            cache.put("analysis:" + first_version, {"probability": 0.7}, 300)
            cache.put("riot:raw-match", {"match": "retained"}, 604800)
            self.model["intercept"] = -1
            self.install()
            second_version = get_model_cache_version()
            self.assertNotEqual(first_version, second_version)
            self.assertIsNone(cache.get("analysis:" + second_version))
            self.assertIsNone(cache.get("analysis:" + second_version, stale=True))
            self.assertEqual(cache.get("riot:raw-match"), {"match": "retained"})
            self.model["report"] = {"metrics": {"accuracy": 0.6}}
            self.install()
            self.assertNotEqual(second_version, get_model_cache_version())
        finally:
            cache.close()


class TrainingTests(unittest.TestCase):
    def write_records(self, path, records):
        path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    def test_deduplicated_temporal_split_and_train_only_scaler(self):
        records = generate_records(120)
        # A holdout-only shift exposes accidentally fitting the scaler on all data.
        for record in records[96:]:
            record["timeline"]["info"]["frames"][0]["participantFrames"]["1"]["totalGold"] += 50000
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "data.jsonl", Path(directory) / "model.json"
            self.write_records(source, list(reversed(records)) + [records[0]])
            model = train(source, output)
        report = model["report"]
        self.assertEqual(report["eligible_unique_matches"], 120)
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(report["train"]["count"], 96)
        self.assertEqual(report["test"]["count"], 24)
        self.assertFalse(set(report["train"]["match_ids"]) & set(report["test"]["match_ids"]))
        self.assertLess(report["train"]["last_match_at"], report["test"]["first_match_at"])
        expected = sum(extract_features(row["match"], row["timeline"])["gold_diff"] for row in records[:96]) / 96
        self.assertAlmostEqual(model["scaler"]["mean"][0], expected)
        self.assertTrue(report["synthetic_demo_only"])
        self.assertIn("brier_score", report["baseline"])

    def test_small_and_mixed_datasets_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "data.jsonl", Path(directory) / "model.json"
            self.write_records(source, generate_records(99))
            with self.assertRaisesRegex(ValueError, "at least 100"):
                train(source, output)
            records = generate_records(120)
            records[-1]["source"] = "riot"
            self.write_records(source, records)
            with self.assertRaisesRegex(ValueError, "mix real and synthetic"):
                train(source, output)

    def test_single_class_holdout_has_null_auc(self):
        records = generate_records(120)
        for record in records[96:]:
            record["match"]["info"]["teams"][0]["win"] = True
            record["match"]["info"]["teams"][1]["win"] = False
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "data.jsonl", Path(directory) / "model.json"
            self.write_records(source, records)
            model = train(source, output)
        self.assertIsNone(model["report"]["metrics"]["roc_auc"])


class DeepMLPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import numpy as np
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler
        cls.temp = tempfile.TemporaryDirectory()
        cls.source = Path(cls.temp.name) / "records.jsonl"
        cls.path = Path(cls.temp.name) / "deep.json"
        cls.records = generate_records(120)
        cls.source.write_text("\n".join(json.dumps(row) for row in cls.records), encoding="utf-8")
        cls.model = train(cls.source, cls.path, algorithm="mlp")
        train_ids = set(cls.model["report"]["train"]["match_ids"])
        rows = [row for row in cls.records if row["match"]["metadata"]["matchId"] in train_ids]
        features = np.array([[extract_features(row["match"], row["timeline"])[name]
                              for name in FEATURE_NAMES] for row in rows])
        labels = np.array([int(next(team["win"] for team in row["match"]["info"]["teams"]
                                    if team["teamId"] == 100)) for row in rows])
        cls.scaler = StandardScaler().fit(features)
        cls.reference = MLPClassifier(hidden_layer_sizes=(16, 8, 4), activation="relu", solver="lbfgs",
                                      alpha=1.0, random_state=42, max_iter=2000, max_fun=20000,
                                      tol=1e-6, early_stopping=False).fit(cls.scaler.transform(features), labels)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.path.write_text(json.dumps(self.model), encoding="utf-8")
        self.environment = patch.dict(os.environ, {"MODEL_PATH": str(self.path)})
        self.environment.start()

    def tearDown(self):
        self.environment.stop()

    def test_exported_deep_network_matches_sklearn_and_red_complement(self):
        self.assertEqual(self.model["hidden_layers"], [16, 8, 4])
        self.assertEqual(self.model["parameter_count"], 289)
        self.assertEqual(get_model_info()["algorithm"], "mlp")
        self.assertIn("Deep MLP", get_model_info()["method"])
        for record in self.records:
            features = extract_features(record["match"], record["timeline"])
            values = [[features[name] for name in FEATURE_NAMES]]
            expected = float(self.reference.predict_proba(self.scaler.transform(values))[0, 1])
            blue = predict_snapshot(features, 100, "synthetic")
            red = predict_snapshot(features, 200, "synthetic")
            self.assertEqual(blue["method"], "mlp")
            self.assertAlmostEqual(blue["probability"], expected, places=11)
            self.assertAlmostEqual(blue["probability"] + red["probability"], 1)

    def test_deep_network_and_logistic_use_identical_partitions_and_scaler(self):
        logistic = train(self.source, self.path.with_name("logistic.json"))
        report = self.model["report"]
        self.assertEqual(report["train"], logistic["report"]["train"])
        self.assertEqual(report["test"], logistic["report"]["test"])
        self.assertEqual(self.model["scaler"], logistic["scaler"])
        self.assertEqual(report["logistic_baseline"]["metrics"], logistic["report"]["metrics"])
        self.assertEqual(report["baseline"], logistic["report"]["baseline"])
        self.assertEqual(report["train"]["count"], 96)
        self.assertEqual(report["test"]["count"], 24)
        self.assertEqual(report["training"]["hidden_layers"], [16, 8, 4])
        self.assertTrue(report["synthetic_demo_only"])

    def test_invalid_deep_artifacts_disable_predictions(self):
        invalid = []
        model = clone(self.model); model["layers"][0]["weights"].pop(); invalid.append(model)
        model = clone(self.model); model["layers"][-1]["biases"].append(0); invalid.append(model)
        model = clone(self.model); model["layers"][1]["weights"][0][0] = float("nan"); invalid.append(model)
        model = clone(self.model); model["layers"][0]["biases"][0] = 10 ** 500; invalid.append(model)
        model = clone(self.model); model["activation"] = "tanh"; invalid.append(model)
        model = clone(self.model); model["hidden_layers"] = [16, 8]; invalid.append(model)
        for model in invalid:
            with self.subTest(algorithm=model["algorithm"]):
                self.path.write_text(json.dumps(model), encoding="utf-8")
                self.assertEqual(get_model_info()["status"], "invalid")
                self.assertIsNone(predict_snapshot(dict.fromkeys(FEATURE_NAMES, 0), source="synthetic")["probability"])

    def test_deep_network_source_guard_and_intermediate_overflow(self):
        features = dict.fromkeys(FEATURE_NAMES, 0)
        self.assertIsNone(predict_snapshot(features, source="riot")["probability"])
        model = clone(self.model)
        model["trained_on"] = "riot"
        self.path.write_text(json.dumps(model), encoding="utf-8")
        self.assertIsNone(predict_snapshot(features, source="synthetic")["probability"])
        self.assertIsNotNone(predict_snapshot(features, source="riot")["probability"])
        model["layers"][0]["weights"][0][0] = 1e308
        features["gold_diff"] = 1e308
        self.path.write_text(json.dumps(model), encoding="utf-8")
        self.assertIsNone(predict_snapshot(features, source="riot")["probability"])

    def test_unknown_training_algorithm_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            train(self.source, self.path, algorithm="unknown")


if __name__ == "__main__":
    unittest.main()
