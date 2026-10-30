"""Train a historical logistic baseline or deep MLP from raw match/timeline JSONL.

Synthetic-only inputs are explicitly marked and never enabled for real games.
"""
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


def _iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).isoformat()


def _partition_report(rows: list[dict]) -> dict:
    return {"count": len(rows), "blue_wins": sum(row["label"] for row in rows),
            "red_wins": sum(1 - row["label"] for row in rows),
            "first_match_at": _iso(rows[0]["timestamp"]),
            "last_match_at": _iso(rows[-1]["timestamp"]),
            "match_ids": [row["match_id"] for row in rows],
            "patches": sorted({row["patch"] for row in rows}),
            "queues": sorted({row["queue"] for row in rows})}


def train(input_path: Path, output_path: Path, min_matches: int = 100, algorithm: str = "logistic_regression") -> dict:
    import numpy as np
    import sklearn
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.metrics import accuracy_score, brier_score_loss, roc_auc_score
    from sklearn.preprocessing import StandardScaler

    if algorithm not in ("logistic_regression", "mlp"):
        raise ValueError("Unsupported training algorithm")
    if min_matches < 100:
        raise ValueError("At least 100 eligible unique matches are required")
    rows, seen, duplicates, skipped = [], set(), 0, 0
    input_bytes = input_path.read_bytes()
    for line_number, line in enumerate(input_bytes.decode("utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            source = record["source"]
            if source not in ("riot", "synthetic"):
                raise ValueError("source must be riot or synthetic")
            match, timeline = record["match"], record["timeline"]
            features = extract_features(match, timeline)
            if features is None:
                skipped += 1
                continue
            info = match["info"]
            match_id = match["metadata"]["matchId"]
            timestamp = int(info.get("gameStartTimestamp", info.get("gameCreation", 0)))
            if timestamp <= 0:
                skipped += 1
                continue
            team_results = {team["teamId"]: team["win"] for team in info["teams"]}
            if set(team_results) != {100, 200} or any(type(value) is not bool for value in team_results.values()):
                skipped += 1
                continue
            if team_results[100] == team_results[200]:
                skipped += 1
                continue
            if match_id in seen:
                duplicates += 1
                continue
            seen.add(match_id)
            rows.append({"match_id": match_id, "timestamp": timestamp, "source": source,
                         "features": [features[name] for name in FEATURE_NAMES],
                         "label": int(team_results[100]), "queue": info["queueId"],
                         "patch": str(info.get("gameVersion", "unknown"))})
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(f"Invalid input record on line {line_number}: {type(exc).__name__}") from exc
    if len(rows) < min_matches:
        raise ValueError(f"Need at least {min_matches} eligible unique matches; received {len(rows)}")
    sources = {row["source"] for row in rows}
    if len(sources) != 1:
        raise ValueError("Do not mix real and synthetic data in a model or evaluation")
    rows.sort(key=lambda row: (row["timestamp"], row["match_id"]))
    split_index = int(len(rows) * 0.8)
    boundary = rows[split_index]["timestamp"]
    train_rows = [row for row in rows if row["timestamp"] < boundary]
    test_rows = [row for row in rows if row["timestamp"] >= boundary]
    if len(train_rows) < 60 or len(test_rows) < 20:
        raise ValueError("Need at least 60 earlier training and 20 later holdout matches")
    y_train = np.array([row["label"] for row in train_rows])
    y_test = np.array([row["label"] for row in test_rows])
    if len(set(y_train)) != 2:
        raise ValueError("Training partition must contain both outcomes")
    x_train = np.array([row["features"] for row in train_rows], dtype=float)
    x_test = np.array([row["features"] for row in test_rows], dtype=float)
    scaler = StandardScaler().fit(x_train)
    scaled_train, scaled_test = scaler.transform(x_train), scaler.transform(x_test)
    logistic = LogisticRegression(C=1.0, max_iter=2000, random_state=42).fit(scaled_train, y_train)
    classifier, training_warnings = logistic, []
    if algorithm == "mlp":
        # Fixed before this comparison; do not tune against the already viewed holdout.
        classifier = MLPClassifier(hidden_layer_sizes=(16, 8, 4), activation="relu", solver="lbfgs",
                                   alpha=1.0, max_iter=2000, max_fun=20000, tol=1e-6,
                                   random_state=42, early_stopping=False)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            classifier.fit(scaled_train, y_train)
        training_warnings = [str(item.message) for item in caught]
    probabilities = classifier.predict_proba(scaled_test)[:, 1]

    def measure(values, labels=y_test):
        return {"accuracy": float(accuracy_score(labels, values >= 0.5)),
                "brier_score": float(brier_score_loss(labels, values)),
                "roc_auc": float(roc_auc_score(labels, values)) if len(set(labels)) == 2 else None}

    prior = float(y_train.mean())
    baseline = np.full(len(y_test), prior)
    source = next(iter(sources))
    report = {
        "data_source": source,
        "synthetic_demo_only": source == "synthetic",
        "interpretation": ("Fictional generator evaluation only; NOT evidence of real League of Legends performance."
                           if source == "synthetic" else "Chronological holdout estimate on this collected sample; no claim of universal performance."),
        "input_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "eligible_unique_matches": len(rows), "duplicates_removed": duplicates,
        "ineligible_records_skipped": skipped,
        "split": "chronological 80/20 target; equal boundary timestamps remain together in holdout",
        "scaler_fit": "training partition only", "selection": "one blue-side row per unique match",
        "train": _partition_report(train_rows), "test": _partition_report(test_rows),
        "metrics": measure(probabilities),
        "baseline": {"method": "constant training-set blue-win prevalence", "probability": prior,
                     "accuracy": float(accuracy_score(y_test, baseline >= 0.5)),
                     "brier_score": float(brier_score_loss(y_test, baseline)),
                     "roc_auc": 0.5 if len(set(y_test)) == 2 else None},
        "limitations": ["One temporal holdout; no independent external validation or calibration study.",
                        "No hyperparameter tuning; patch drift and player-selection bias may affect results.",
                        "Retrospective minute-10 analysis only; no live coaching or causal claims.",
                        "Synthetic provenance is declarative; verify collection provenance before real-data claims."],
        "libraries": {"numpy": np.__version__, "scikit_learn": sklearn.__version__},
    }
    if algorithm == "mlp":
        report["training_metrics"] = measure(classifier.predict_proba(scaled_train)[:, 1], y_train)
        report["logistic_baseline"] = {"method": "Logistic regression", "metrics": measure(logistic.predict_proba(scaled_test)[:, 1])}
        report["experiment_notice"] = ("The same holdout was previously viewed for the logistic baseline. This is an exploratory comparison, not fresh independent validation."
                                       if source == "riot" else "Synthetic generator comparison only; no empirical game-performance claim.")
        report["training"] = {"hidden_layers": [16, 8, 4], "activation": "relu", "output_activation": "logistic",
                              "solver": "lbfgs", "alpha": 1.0, "random_state": 42, "max_iter": 2000,
                              "max_fun": 20000, "tol": 1e-6, "early_stopping": False,
                              "iterations": int(classifier.n_iter_), "training_loss": float(classifier.loss_),
                              "warnings": training_warnings, "converged": not training_warnings}
        report["limitations"].append("Deep-network capacity is large relative to this small training set; overfitting remains possible.")
    model = {"schema_version": 2 if algorithm == "mlp" else 1, "algorithm": algorithm, "trained_on": source,
             "created_at": datetime.now(timezone.utc).isoformat(), "feature_names": list(FEATURE_NAMES),
             "scaler": {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()},
             "report": report}
    if algorithm == "mlp":
        model.update(hidden_layers=[16, 8, 4], activation="relu", output_activation="logistic",
                     layers=[{"weights": weights.tolist(), "biases": biases.tolist()}
                             for weights, biases in zip(classifier.coefs_, classifier.intercepts_)],
                     parameter_count=int(sum(weights.size + biases.size
                                             for weights, biases in zip(classifier.coefs_, classifier.intercepts_))))
    else:
        model.update(coefficients=classifier.coef_[0].tolist(), intercept=float(classifier.intercept_[0]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(model, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    output_path.with_name(output_path.stem + "_evaluation.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "model.json")
    parser.add_argument("--algorithm", choices=("logistic_regression", "mlp"), default="logistic_regression")
    args = parser.parse_args()
    try:
        model = train(args.input, args.output, algorithm=args.algorithm)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Training not completed: {exc}\n")
    report = model["report"]
    print(json.dumps({"model": str(args.output), "trained_on": model["trained_on"],
                      "notice": report["interpretation"], "train_count": report["train"]["count"],
                      "test_count": report["test"]["count"], "metrics": report["metrics"],
                      "baseline": report["baseline"], "logistic_baseline": report.get("logistic_baseline"),
                      "training": report.get("training"), "algorithm": model["algorithm"]}, indent=2))


if __name__ == "__main__":
    main()
