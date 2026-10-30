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


def extract_features(match: dict, timeline: dict, snapshot_ms: int = SNAPSHOT_MS) -> dict[str, float] | None:
    """Blue-minus-red features; None for incomplete/ineligible snapshots.

    Never reads final outcomes or final player stats. Uses static team metadata
    and observations at or before the requested time. Rejects frames older than
    one minute before that time. The default remains the minute-10 experiment.
    Events are cut off at the selected frame's timestamp.
    """
    try:
        if type(snapshot_ms) is not int or not 60_000 <= snapshot_ms <= 3_600_000:
            return None
        info = match["info"]
        if info.get("mapId") != 11 or info.get("queueId") not in (420, 440):
            return None
        if _number(info["gameDuration"]) * 1000 <= snapshot_ms:
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
                    if snapshot_ms - 60_000 <= _number(frame["timestamp"]) <= snapshot_ms]
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
        return "inference-v3:" + hashlib.sha256(content).hexdigest()
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
    return _validate_model(model)


def _validate_model(model: dict) -> dict:
    """Validate the same numeric model schema for standalone and temporal models."""
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


def _predict_probability(model: dict, features: dict, team_id: int) -> float:
    """Use one validated artifact for inference and reference-input comparisons."""
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
    blue = 1 / (1 + math.exp(-max(-60.0, min(60.0, z))))
    return blue if team_id == 100 else 1 - blue


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
        response.update(probability=_predict_probability(model, features, team_id),
                        method=model["algorithm"])
    except (OSError, ValueError, KeyError, TypeError, OverflowError, AttributeError):
        response["notice"] = "Snapshot or model is invalid; prediction is unavailable."
    return response
