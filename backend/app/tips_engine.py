"""Explainable post-match review priorities; no generated prose or win-impact claim."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean, median

from .config import BACKEND_DIR
from .native_review import ROLES, native_match_review

CONFIG_PATH = Path(__file__).with_name('tips_config.json')
TIERS = {'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND', 'MASTER', 'GRANDMASTER', 'CHALLENGER'}


def config():
    return json.loads(CONFIG_PATH.read_text(encoding='utf-8'))


def identity(puuid):
    return sha256(puuid.encode('utf-8')).hexdigest()


def metrics(match):
    native = match.get('native') or {}
    own = next((player for team in native.get('teams', []) for player in team['players'] if player['selected']), {})
    early, middle, objective = native.get('early_comparison'), native.get('mid_comparison'), native.get('objective_credits')
    minutes = match['duration_minutes']
    return {'cs_per_min': match['cs_per_min'], 'kill_participation': match['kill_participation'] * 100,
            'vision_per_min': match['vision_score'] / minutes,
            'early_cs': early.get('own_cs') if early else None,
            'gold_diff_10': early['gold_diff'] if early else None,
            'gold_diff_15': middle['gold_diff'] if middle else None,
            'damage_share': own['damage_share'] * 100 if own.get('damage_share') is not None else None,
            'wards_placed_per_min': own['wards_placed'] / minutes if own.get('wards_placed') is not None else None,
            'wards_cleared_per_min': own['wards_cleared'] / minutes if own.get('wards_cleared') is not None else None,
            'deaths_before_14': native.get('deaths_before_14') if minutes >= 14 else None,
            'objective_participation': objective['recorded'] / objective['team_objectives'] * 100 if objective and objective['team_objectives'] else None}


def verified_tier(player, match, observations, settings):
    start = match['info'].get('gameStartTimestamp') or match['info']['gameCreation']
    eligible = [row for row in observations if isinstance(row, dict) and row.get('source') == 'riot_rank_at_enrollment'
                and row.get('puuid') == player['puuid'] and isinstance(row.get('tier'), str) and row['tier'] in TIERS
                and row.get('queue') == 'RANKED_SOLO_5x5' and match['info']['queueId'] == 420
                and isinstance(row.get('platform'), str) and row['platform'].upper() == match['metadata']['matchId'].split('_')[0]
                and type(row.get('observed_at_ms')) is int and row['observed_at_ms'] > 0
                and 0 <= start - row['observed_at_ms'] <= settings['rank_observation_max_days'] * 86400000]
    return max(eligible, key=lambda row: row['observed_at_ms'])['tier'] if eligible else None


def build_benchmarks(records, rank_observations=()):
    from .analytics import eligible_match
    settings, rows, seen, provenance = config(), [], set(), set()
    for record in records:
        source = record.get('source')
        if source not in ('riot', 'synthetic'):
            raise ValueError('Unknown benchmark provenance')
        provenance.add(source)
        if len(provenance) > 1:
            raise ValueError('Cannot mix real and fictional benchmarks')
        match = record['match']
        if not eligible_match(match) or match['metadata']['matchId'] in seen:
            continue
        seen.add(match['metadata']['matchId'])
        info = match['info']
        for player in info['participants']:
            if player.get('teamPosition') not in ROLES:
                continue
            native = native_match_review(match, record.get('timeline'), player['puuid'])
            minutes = info['gameDuration'] / 60
            kills = sum(person['kills'] for person in info['participants'] if person['teamId'] == player['teamId'])
            row = {'cs_per_min': (player['totalMinionsKilled'] + player['neutralMinionsKilled']) / minutes,
                   'kill_participation': min(1, (player['kills'] + player['assists']) / kills) if kills else 0,
                   'duration_minutes': minutes, 'vision_score': player['visionScore'], 'native': native}
            rows.append({'match_id': match['metadata']['matchId'], 'player_hash': identity(player['puuid']),
                         'role': player['teamPosition'], 'champion': player['championName'],
                         'patch': '.'.join(info.get('gameVersion', '').split('.')[:2]), 'queue_id': info['queueId'],
                         'tier': verified_tier(player, match, rank_observations, settings) if source == 'riot' else None,
                         'values': metrics(row)})
    return {'schema_version': 1, 'source': next(iter(provenance), 'riot'), 'unique_matches': len(seen),
            'created_at': datetime.now(timezone.utc).isoformat(), 'rows': rows}


def load_benchmarks():
    try:
        value = json.loads((BACKEND_DIR / 'data/tip_benchmarks.json').read_text(encoding='utf-8'))
        if value.get('schema_version') != 1 or value.get('source') not in ('riot', 'synthetic') or not isinstance(value.get('rows'), list):
            raise ValueError('Invalid benchmarks')
        return value
    except (OSError, ValueError, AttributeError):
        return None


def get_tips_cache_version():
    try:
        file = (BACKEND_DIR / 'data/tip_benchmarks.json').stat()
        return f'{file.st_mtime_ns}:{file.st_size}:{CONFIG_PATH.stat().st_mtime_ns}'
    except OSError:
        return 'no-tip-benchmarks'


def percentile(value, reference, higher_is_better):
    rank = (sum(item < value for item in reference) + .5 * sum(item == value for item in reference)) / len(reference)
    return 100 * (rank if higher_is_better else 1 - rank)


def generate_tips(matches, benchmarks, role, puuid, source, scope='local_role', tier=None):
    settings = config()
    result = {'status': 'insufficient_data', 'scope': scope, 'tier': tier, 'role': role,
              'weighting': settings['weighting'], 'tips': [], 'strength': None,
              'tier_status': 'requires_verified_rank_data', 'minimum_reference_matches': settings['minimum_reference_matches'],
              'minimum_reference_players': settings['minimum_reference_players']}
    if scope not in ('local_role', 'role_tier') or (scope == 'role_tier' and tier not in TIERS):
        return {**result, 'status': 'tier_unavailable'}
    if not benchmarks or benchmarks['source'] != source:
        return {**result, 'status': 'benchmark_unavailable'}
    games = sorted([match for match in matches if match['role'] == role], key=lambda row: row['played_at'], reverse=True)
    if len(games) < settings['minimum_recent_games']:
        return result
    # Compare only the latest loaded patch and queue; never pool different metas.
    patch, queue = '.'.join((games[0].get('patch') or '').split('.')[:2]), games[0]['queue_id']
    games = [match for match in games if '.'.join((match.get('patch') or '').split('.')[:2]) == patch and match['queue_id'] == queue][:settings['recent_games']]
    if len(games) < settings['minimum_recent_games']:
        return result
    excluded, player_hash = {match['id'] for match in matches}, identity(puuid)
    reference = [row for row in benchmarks['rows'] if row['role'] == role and row['patch'] == patch
                 and row['queue_id'] == queue and row['match_id'] not in excluded and row['player_hash'] != player_hash
                 and (scope != 'role_tier' or row.get('tier') == tier)]
    if scope == 'role_tier' and not reference:
        return {**result, 'status': 'tier_unavailable'}
    champion = games[0]['champion']
    champion_rows = [row for row in reference if row['champion'] == champion]
    use_champion = (all(match['champion'] == champion for match in games)
                    and len({row['match_id'] for row in champion_rows}) >= settings['minimum_champion_matches'])
    if use_champion:
        reference = champion_rows
    result.update(patch=patch, queue_id=queue, champion=champion if use_champion else None,
                  cohort_matches=len({row['match_id'] for row in reference}), recent_games=len(games))
    values, candidates = [(match, metrics(match)) for match in games], []
    for metric, definition in settings['metrics'].items():
        if role in definition.get('exclude_roles', []):
            continue
        cohort = [row for row in reference if type(row['values'].get(metric)) in (int, float) and math.isfinite(row['values'][metric])]
        recent = [(index, row[metric]) for index, (_, row) in enumerate(values) if type(row.get(metric)) in (int, float) and math.isfinite(row[metric])]
        players = len({row['player_hash'] for row in cohort})
        if (len({row['match_id'] for row in cohort}) < settings['minimum_reference_matches']
                or players < settings['minimum_reference_players'] or len(recent) < settings['minimum_recent_games']):
            continue
        pool = [row['values'][metric] for row in cohort]
        benchmark = median(pool)
        actual = mean(value for _, value in recent)
        higher = definition['higher_is_better']
        below = lambda value: value < benchmark if higher else value > benchmark
        weights = [(settings['recency_decay'] ** index, below(value)) for index, value in recent]
        consistency = sum(weight for weight, bad in weights if bad) / sum(weight for weight, _ in weights)
        rank = percentile(actual, pool, higher)
        candidates.append({'metric': metric, 'actual': round(actual, 3), 'benchmark': round(benchmark, 3),
                           'percentile': round(rank, 2), 'gap': max(0, (settings['target_percentile'] - rank) / 100),
                           'consistency': consistency, 'below_games': sum(below(value) for _, value in recent),
                           'recent_games': len(recent), 'reference_rows': len(cohort),
                           'reference_matches': len({row['match_id'] for row in cohort}),
                           'reference_players': players, 'metric_coverage': len(recent)/len(games)})
    if not candidates:
        return result
    for item in candidates:
        item['impact_weight'] = 1 / len(candidates)
        item['priority'] = item['gap'] * item['impact_weight'] * item['consistency']
    result.update(status='available', tier_status='available' if scope == 'role_tier' else 'requires_verified_rank_data',
                  tips=sorted([item for item in candidates if item['priority'] > 0], key=lambda item: (-item['priority'], item['metric']))[:3],
                  strength=max((item for item in candidates if item['percentile'] >= settings['target_percentile']), key=lambda item: item['percentile'], default=None))
    return result
