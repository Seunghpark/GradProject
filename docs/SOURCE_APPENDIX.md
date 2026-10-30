# 핵심 원천코드 부록 초안

현재 학습·추론·API·자료형의 실제 소스를 수록한다. 원문 코드를 변경하거나 실행한 결과로 가장하지 않는다. 최종 HWP에서 쪽수·글꼴·줄바꿈과 부록 범위를 검토해야 하며, 전체 프런트엔드·기타 백엔드·테스트·실행파일은 별도 전체 소스 ZIP에 포함된다. 비밀키, 원시 경기 자료, 생성 모델과 의존성 폴더는 이 부록에 포함하지 않는다.

## backend/app/ml.py

SHA-256: 8360e82c41626f6c3907b08844c84c5cfeeac8189c43f96e37123503b4749ca6

```python
"""Safe retrospective minute-10 features and stdlib JSON model inference."""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

FEATURE_NAMES = ("gold_diff", "xp_diff", "cs_diff", "kills_diff", "towers_diff", "dragons_diff")
SNAPSHOT_MS = 600_000
MIN_SNAPSHOT_MS = 540_000


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Expected a finite number")
    try:
        result = float(value)
    except OverflowError as error:
        raise ValueError("Expected a finite number") from error
    if not math.isfinite(result):
        raise ValueError("Expected a finite number")
    return result


def extract_features(match: dict, timeline: dict) -> dict[str, float] | None:
    """Blue-minus-red features; None for incomplete/ineligible snapshots.

    Never reads final outcomes or final player stats. Uses static team metadata
    and observations at or before minute 10. Rejects frames older than minute 9.
    Events are cut off at the selected frame's timestamp.
    """
    try:
        info = match["info"]
        if info.get("mapId") != 11 or info.get("queueId") not in (420, 440):
            return None
        if _number(info["gameDuration"]) <= 600:
            return None
        participants = info["participants"]
        if len(participants) != 10:
            return None
        teams: dict[int, int] = {}
        for participant in participants:
            pid, team = participant["participantId"], participant["teamId"]
            if type(pid) is not int or pid <= 0 or type(team) is not int:
                return None
            if pid in teams or team not in (100, 200):
                return None
            teams[pid] = team
        if list(teams.values()).count(100) != 5 or list(teams.values()).count(200) != 5:
            return None
        match_id = match.get("metadata", {}).get("matchId")
        if not match_id or timeline.get("metadata", {}).get("matchId") != match_id:
            return None
        frames = timeline["info"]["frames"]
        eligible = [frame for frame in frames
                    if MIN_SNAPSHOT_MS <= _number(frame["timestamp"]) <= SNAPSHOT_MS]
        if not eligible:
            return None
        frame = max(eligible, key=lambda item: item["timestamp"])
        cutoff = frame["timestamp"]
        pframes = frame["participantFrames"]
        if set(pframes) != {str(pid) for pid in teams}:
            return None
        result = dict.fromkeys(FEATURE_NAMES, 0.0)
        for pid, team in teams.items():
            participant_frame = pframes[str(pid)]
            if participant_frame.get("participantId", pid) != pid:
                return None
            values = [_number(participant_frame[key]) for key in
                      ("totalGold", "xp", "minionsKilled", "jungleMinionsKilled")]
            if any(value < 0 for value in values):
                return None
            sign = 1 if team == 100 else -1
            result["gold_diff"] += sign * values[0]
            result["xp_diff"] += sign * values[1]
            result["cs_diff"] += sign * (values[2] + values[3])
        for event_frame in frames:
            if _number(event_frame["timestamp"]) > cutoff:
                continue
            for event in event_frame.get("events", []):
                if "timestamp" not in event or not 0 <= _number(event["timestamp"]) <= cutoff:
                    continue
                kind = event.get("type")
                credited_team, feature = None, None
                if kind == "CHAMPION_KILL":
                    credited_team = teams.get(event.get("killerId"))
                    feature = "kills_diff"
                elif kind == "BUILDING_KILL" and event.get("buildingType") == "TOWER_BUILDING":
                    # Riot's teamId is the destroyed tower's owner.
                    owner = event.get("teamId")
                    credited_team = 300 - owner if owner in (100, 200) else None
                    feature = "towers_diff"
                elif kind == "ELITE_MONSTER_KILL" and event.get("monsterType") == "DRAGON":
                    credited_team = event.get("killerTeamId") or teams.get(event.get("killerId"))
                    feature = "dragons_diff"
                if feature and credited_team in (100, 200):
                    result[feature] += 1 if credited_team == 100 else -1
        return result
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return None


def _model_path() -> Path:
    return Path(os.environ.get("MODEL_PATH", str(Path(__file__).resolve().parents[1] / "data" / "model.json")))


def get_model_cache_version() -> str:
    """Version cached analyses by artifact content, including evaluation metadata."""
    try:
        with _model_path().open("rb") as handle:
            content = handle.read(2_000_001)
        if len(content) > 2_000_000:
            return "oversized"
        # New inference code must not reuse analyses made by an older backend.
        return "inference-v2:" + hashlib.sha256(content).hexdigest()
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "unreadable"


def _read_model() -> dict | None:
    path = _model_path()
    if not path.is_file():
        return None
    if path.stat().st_size > 2_000_000:
        raise ValueError("Model artifact exceeds size limit")
    model = json.loads(path.read_text(encoding="utf-8"))
    algorithm = model.get("algorithm")
    if (model.get("schema_version"), algorithm) not in ((1, "logistic_regression"), (2, "mlp")):
        raise ValueError("Unsupported model format")
    if model.get("feature_names") != list(FEATURE_NAMES) or model.get("trained_on") not in ("riot", "synthetic"):
        raise ValueError("Invalid model provenance or features")
    for field in (model["scaler"]["mean"], model["scaler"]["scale"]):
        if len(field) != len(FEATURE_NAMES):
            raise ValueError("Invalid model dimensions")
        for value in field:
            _number(value)
    if any(value <= 0 for value in model["scaler"]["scale"]):
        raise ValueError("Invalid scaler")
    if algorithm == "logistic_regression":
        if len(model["coefficients"]) != len(FEATURE_NAMES):
            raise ValueError("Invalid logistic dimensions")
        for value in model["coefficients"]:
            _number(value)
        _number(model["intercept"])
    else:
        if (model.get("hidden_layers") != [16, 8, 4] or model.get("activation") != "relu"
                or model.get("output_activation") != "logistic" or model.get("parameter_count") != 289):
            raise ValueError("Unsupported neural network architecture")
        layers = model["layers"]
        if not isinstance(layers, list) or len(layers) != 4:
            raise ValueError("Invalid neural network layers")
        previous = len(FEATURE_NAMES)
        for layer, width in zip(layers, (16, 8, 4, 1)):
            weights, biases = layer["weights"], layer["biases"]
            if len(weights) != previous or len(biases) != width:
                raise ValueError("Invalid neural network dimensions")
            for row in weights:
                if len(row) != width:
                    raise ValueError("Invalid neural network dimensions")
                for value in row:
                    _number(value)
            for value in biases:
                _number(value)
            previous = width
    return model


def get_model_info() -> dict:
    try:
        model = _read_model()
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return {"status": "invalid", "available": False, "trained_on": None,
                "notice": "Model artifact is invalid; predictions are disabled.", "evaluation": None}
    if model is None:
        return {"status": "not_trained", "available": False, "trained_on": None,
                "notice": "No trained model is installed. No real-match prediction performance is established.",
                "evaluation": None}
    synthetic = model["trained_on"] == "synthetic"
    return {"status": "synthetic_demo" if synthetic else "trained", "available": True,
            "trained_on": model["trained_on"], "algorithm": model["algorithm"],
            "method": "Deep MLP (16-8-4)" if model["algorithm"] == "mlp" else "Logistic regression",
            "hidden_layers": model.get("hidden_layers", []), "parameter_count": model.get("parameter_count", 7),
            "snapshot_minute": 10, "feature_names": list(FEATURE_NAMES),
            "notice": ("Synthetic demo only. Evaluation measures a fictional data generator, not real League of Legends performance."
                       if synthetic else ("Deep MLP retrospective pilot. Small, previously viewed holdout; no calibrated or general accuracy established."
                                          if model["algorithm"] == "mlp" else "Retrospective minute-10 model. Holdout results apply only to the documented dataset.")),
            "evaluation": model.get("report")}


def predict_snapshot(features: dict | None, team_id: int = 100, source: str = "riot") -> dict:
    info = get_model_info()
    response = {"probability": None, "method": "unavailable", "trained_on": info["trained_on"],
                "notice": info["notice"], "snapshot_minute": 10, "features": features or {}}
    if not features:
        response["notice"] = "No complete eligible minute-10 snapshot is available for this match."
        return response
    if team_id not in (100, 200) or source not in ("riot", "synthetic"):
        response["notice"] = "Unsupported team or data provenance."
        return response
    if not info["available"]:
        return response
    if info["trained_on"] != source:
        response["notice"] = "Model and match data sources differ; this model cannot estimate this match."
        return response
    try:
        model = _read_model()
        if model is None or model["trained_on"] != source:
            return response
        values = [_number((_number(features[name]) - mean) / scale)
                  for name, mean, scale in zip(FEATURE_NAMES, model["scaler"]["mean"], model["scaler"]["scale"])]
        if model["algorithm"] == "logistic_regression":
            z = _number(model["intercept"] + sum(coefficient * value
                                                for value, coefficient in zip(values, model["coefficients"])))
        else:
            for index, layer in enumerate(model["layers"]):
                values = [_number(bias + sum(value * row[column] for value, row in zip(values, layer["weights"])))
                          for column, bias in enumerate(layer["biases"])]
                if index < len(model["layers"]) - 1:
                    values = [max(0.0, value) for value in values]
            z = values[0]
        probability_blue = 1 / (1 + math.exp(-max(-60.0, min(60.0, z))))
        response.update(probability=probability_blue if team_id == 100 else 1 - probability_blue,
                        method=model["algorithm"])
    except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        response["notice"] = "Snapshot or model is invalid; prediction is unavailable."
    return response
```

## backend/scripts/train_model.py

SHA-256: e5dac87b9fae0a77cab494cfb77c9df153fddc1393da98af6035b28e38dab6fa

```python
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
```

## backend/app/main.py

SHA-256: 44752518daf9f84c786d0ee94ef134fa122bd81e602895cf30ac7c3be7d9a2a7

```python
"""LolAi.gg HTTP API and optional single-process frontend serving."""
from contextlib import asynccontextmanager
import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .analytics import analysis_payload, eligible_match
from .cache import Cache
from .config import BACKEND_DIR, PLATFORMS, Settings
from .demo import DEMO_ACCOUNT, demo_records
from .ml import get_model_cache_version
from .riot import RiotClient, RiotError

DEMO_NOTICE = 'Synthetic demo: fictional player and matches for presentation. These are not Riot results or evidence of real-world model accuracy.'


def create_app(settings: Settings | None = None, transport=None):
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        app.state.cache = Cache(config.cache_path)
        app.state.riot = RiotClient(config, app.state.cache, transport=transport)
        yield
        await app.state.riot.close()
        app.state.cache.close()

    app = FastAPI(title='LolAi.gg API', version='0.1.0', lifespan=lifespan,
                  description='Historical League of Legends analysis with an explicit synthetic demo.')
    app.add_middleware(CORSMiddleware, allow_origins=[
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'http://localhost:8000', 'http://127.0.0.1:8000',
    ], allow_methods=['GET'], allow_headers=['Accept', 'Content-Type'])

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RiotError)
    async def riot_error_handler(request: Request, error: RiotError):
        headers = {'Retry-After': str(error.retry_after)} if error.retry_after else None
        return JSONResponse(status_code=error.status, headers=headers,
                            content={'detail': {'code': error.code, 'message': error.message}})

    @app.get('/api/health')
    async def health():
        return {'status': 'ok', 'version': '0.1.0', 'riot_configured': bool(config.riot_api_key),
                'demo_available': True, 'platforms': list(PLATFORMS)}

    @app.get('/api/analysis')
    async def analysis(
        request: Request,
        game_name: str = Query('DemoPlayer', min_length=1, max_length=32),
        tag_line: str = Query('SKKU', min_length=1, max_length=16),
        platform: str = Query('kr'),
        mode: Literal['demo', 'auto', 'live'] = 'auto',
        count: int = Query(10, ge=1, le=20),
    ):
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        if platform not in PLATFORMS:
            raise HTTPException(422, detail={'code': 'invalid_platform', 'message': 'Choose a supported platform.'})
        if not game_name or not tag_line or any(ord(c) < 32 for c in game_name + tag_line) or '#' in game_name + tag_line:
            raise HTTPException(422, detail={'code': 'invalid_riot_id', 'message': 'Enter a game name and tagline without the # separator.'})
        if mode == 'demo':
            return analysis_payload(DEMO_ACCOUNT, demo_records(count), 'kr', 'demo', DEMO_NOTICE)
        cache: Cache = request.app.state.cache
        riot: RiotClient = request.app.state.riot
        model_version = get_model_cache_version()
        analysis_key = 'analysis:' + json.dumps([platform, game_name.casefold(), tag_line.casefold(), count, model_version])
        cached = cache.get(analysis_key)
        if cached is not None:
            cached['source'] = 'cache'
            cached['warning'] = 'Showing a saved Riot analysis (cached for up to five minutes). ' + (cached.get('warning') or '')
            return cached
        records, warnings, any_network = [], [], False
        try:
            account, from_cache = await riot.account(platform, game_name, tag_line)
            any_network |= not from_cache
            if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
                raise RiotError('invalid_response', 'Riot returned an incomplete player record.')
            account['gameName'] = account['gameName'] if isinstance(account.get('gameName'), str) and account['gameName'] else game_name
            account['tagLine'] = account['tagLine'] if isinstance(account.get('tagLine'), str) and account['tagLine'] else tag_line
            match_ids, from_cache = await riot.match_ids(platform, account['puuid'], count)
            any_network |= not from_cache
            if not isinstance(match_ids, list) or not all(isinstance(x, str) for x in match_ids):
                raise RiotError('invalid_response', 'Riot returned an incomplete match list.')
            for match_id in list(dict.fromkeys(match_ids))[:count]:
                try:
                    match, from_cache = await riot.match(platform, match_id)
                    any_network |= not from_cache
                    if not isinstance(match, dict) or not eligible_match(match):
                        warnings.append('Ineligible or incomplete match records were skipped.')
                        continue
                    if match['metadata']['matchId'] != match_id:
                        warnings.append('A mismatched match record was skipped.')
                        continue
                    timeline = None
                    try:
                        timeline, from_cache = await riot.timeline(platform, match_id)
                        any_network |= not from_cache
                        if not isinstance(timeline, dict) or not isinstance(timeline.get('info'), dict) or not isinstance(timeline['info'].get('frames'), list):
                            timeline = None
                            warnings.append('Some timelines are incomplete; those matches have no historical prediction.')
                    except RiotError as error:
                        if error.code == 'invalid_key':
                            raise
                        warnings.append('Some timelines are unavailable; those matches have no historical prediction. ' + error.message)
                    records.append({'match': match, 'timeline': timeline, 'source': 'riot'})
                except RiotError as error:
                    if error.code == 'not_found':
                        warnings.append('One match was no longer available from Riot and was skipped.')
                        continue
                    if records and error.code != 'invalid_key':
                        warnings.append('Only part of the match history loaded. ' + error.message)
                        break
                    raise
            if not records:
                warnings.append('No eligible ranked Summoner\'s Rift games were found in the requested recent history. Remakes and other queues are excluded.')
            payload = analysis_payload(account, records, platform, 'live' if any_network else 'cache', ' '.join(dict.fromkeys(warnings)) or None)
            # A model may be replaced while the awaited Riot requests are running.
            if get_model_cache_version() == model_version:
                cache.put(analysis_key, payload, 300)
            return payload
        except RiotError as error:
            if mode == 'live' or error.code == 'not_found':
                raise
            stale = cache.get(analysis_key, stale=True) if get_model_cache_version() == model_version else None
            if stale is not None:
                stale['source'] = 'cache'
                stale['warning'] = 'Riot lookup failed; showing previously saved data, up to seven days old. ' + error.message + ' ' + (stale.get('warning') or '')
                return stale
            payload = analysis_payload(DEMO_ACCOUNT, demo_records(count), 'kr', 'demo', error.message + ' ' + DEMO_NOTICE)
            payload['requested_player'] = {'game_name': game_name, 'tag_line': tag_line, 'platform': platform}
            return payload

    # A built frontend can be served from the same origin with a single Python process.
    dist = BACKEND_DIR.parent / 'frontend' / 'dist'

    @app.get('/{path:path}', include_in_schema=False)
    async def frontend(path: str):
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404, 'Unknown API endpoint')
        if not (dist / 'index.html').is_file():
            raise HTTPException(404, 'Frontend is not built. Run the frontend build or use the Vite development server.')
        candidate = (dist / path).resolve()
        if not candidate.is_relative_to(dist.resolve()):
            raise HTTPException(404, 'Not found')
        if candidate.is_file():
            return FileResponse(candidate)
        if Path(path).suffix:
            raise HTTPException(404, 'Not found')
        return FileResponse(dist / 'index.html')

    return app


app = create_app()
```

## frontend/src/types.ts

SHA-256: 36ffcf7a9587384326b96d907dbad71dddf6dbba2dac41de0f4607dc0be02229

```typescript
export interface Insight {title:string;detail:string;tone?:string}
export interface Prediction {probability:number|null;method:string;trained_on?:string|null;notice?:string;snapshot_minute?:number;features?:Record<string,number>}
export interface Match {id:string;champion:string;role:string;win:boolean;kills:number;deaths:number;assists:number;duration_minutes:number;cs_per_min:number;vision_score:number;kill_participation:number;damage:number;played_at:string|number;team_id:number;prediction:Prediction|null;insights:Insight[];timeline:{minute:number;gold_diff:number}[]}
export interface Analysis {source:'demo'|'live'|'cache';warning?:string|null;fetched_at?:string;player:{game_name:string;tag_line:string;platform:string;puuid?:string};summary:{games:number;wins:number;win_rate:number;kda:number;cs_per_min:number;vision_per_min:number;kill_participation:number};matches:Match[];insights:Insight[];model:Record<string,unknown>}
export type DataMode='demo'|'auto'|'live'
```
