"""Frozen-model evaluation on future games of prospectively enrolled low-elo players.

Enrollment records are created by enroll_low_elo.py using Riot's rank response.
Current ranks never retrospectively label old matches. No weights are fitted here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.ml import _validate_model, _predict_probability, extract_features
from scripts.benchmark_models import measure

LOW_TIERS = {'IRON', 'BRONZE', 'SILVER'}


def evaluate(records, enrollments, model, model_hash):
    trained_ids = set(model['report']['train']['match_ids']) | set(model['report']['test']['match_ids'])
    frozen_at = int(datetime.fromisoformat(model['created_at'].replace('Z', '+00:00')).timestamp() * 1000)
    probabilities, labels, seen, players = [], [], set(), set()
    for record in records:
        if record.get('source') != 'riot':
            continue
        match, timeline = record.get('match', {}), record.get('timeline')
        info, match_id = match.get('info', {}), match.get('metadata', {}).get('matchId')
        start = info.get('gameStartTimestamp', 0)
        if (not isinstance(start, (int, float)) or start <= frozen_at or match_id in trained_ids
                or not match_id or match_id in seen or info.get('queueId') != 420):
            continue
        features = extract_features(match, timeline)
        if features is None:
            continue
        eligible = [entry for entry in enrollments if entry.get('source') == 'riot_rank_at_enrollment'
                    and entry.get('tier') in LOW_TIERS and entry.get('queue') == 'RANKED_SOLO_5x5'
                    and entry.get('model_sha256') == model_hash
                    and type(entry.get('observed_at_ms')) is int
                    and frozen_at <= entry['observed_at_ms'] <= start
                    and start - entry['observed_at_ms'] <= 30 * 86400000]
        anchor = next(((entry, player) for entry in sorted(eligible, key=lambda item: item['puuid'])
                       for player in info.get('participants', []) if player.get('puuid') == entry.get('puuid')), None)
        if anchor is None:
            continue
        entry, player = anchor
        if type(player.get('win')) is not bool or player.get('teamId') not in (100, 200):
            continue
        seen.add(match_id)
        players.add(entry['puuid'])
        labels.append(int(player['win']))
        probabilities.append(_predict_probability(model, features, player['teamId']))
    ready = len(seen) >= 20 and len(players) >= 3 and len(set(labels)) == 2
    return {'status': 'pilot_evaluated' if ready else 'insufficient_prospective_data',
            'eligible_unique_matches': len(seen), 'enrolled_players_observed': len(players),
            'wins': sum(labels), 'losses': len(labels) - sum(labels), 'minimum_matches': 20, 'minimum_players': 3,
            'metrics': measure(labels, probabilities) if ready else None,
            'constant_50_percent_baseline': measure(labels, [.5] * len(labels)) if ready else None,
            'model_sha256': model_hash, 'low_elo_definition': 'Prospectively enrolled Iron/Bronze/Silver solo-queue player; not an assertion about every player in the lobby.',
            'notice': 'Frozen model; future games only; rank at enrollment valid for 30 days. One record per game. No old match is labeled using a current rank. No coaching benefit or broad low-elo performance established.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BACKEND / 'data/riot_matches.jsonl')
    parser.add_argument('--enrollments', type=Path, default=BACKEND / 'data/low_elo_enrollments.jsonl')
    parser.add_argument('--model', type=Path, default=BACKEND / 'data/model.json')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data/low_elo_evaluation.json')
    args = parser.parse_args()
    if (args.output.resolve() in {args.input.resolve(), args.enrollments.resolve(), args.model.resolve()}
            or args.output.name in {'model.json', 'riot_model.json', 'riot_mlp_model.json', 'timeline_models.json', 'model_comparison.json'}):
        parser.error('Output must preserve all inputs')
    model_bytes = args.model.read_bytes()
    model = _validate_model(json.loads(model_bytes))
    if model['trained_on'] != 'riot':
        parser.error('A real-match model is required')
    enrollments = [json.loads(line) for line in args.enrollments.read_text(encoding='utf-8-sig').splitlines() if line.strip()] if args.enrollments.exists() else []
    records = (json.loads(line) for line in args.input.read_text(encoding='utf-8-sig').splitlines() if line.strip())
    result = evaluate(records, enrollments, model, hashlib.sha256(model_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
