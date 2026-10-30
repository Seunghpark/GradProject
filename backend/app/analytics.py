"""Transparent historical metrics and descriptive post-match review prompts."""
from datetime import datetime, timezone
from statistics import mean
import math
from .ml import extract_features, get_model_info, predict_snapshot
from .temporal_model import probability_timeline
from .profiles import ROLES, comparison_insight, personal_comparison, player_profile
from .prediction_review import prediction_review
from .model_comparison import get_model_comparison
from .native_review import native_match_review
from .tips_engine import generate_tips, load_benchmarks
from .loadout_timeline import loadout_histories


def eligible_match(match: dict) -> bool:
    """Skip incomplete upstream records instead of inventing missing statistics."""
    try:
        info = match['info']
        people = info['participants']
        duration = info['gameDuration']
        if (info.get('queueId') not in (420, 440) or info.get('mapId') != 11
                or type(duration) not in (int, float) or not math.isfinite(duration)
                or duration <= 600 or len(people) != 10
                or not isinstance(match['metadata']['matchId'], str)):
            return False
        timestamp = info.get('gameStartTimestamp') or info['gameCreation']
        if type(timestamp) not in (int, float) or not math.isfinite(timestamp) or timestamp <= 0:
            return False
        datetime.fromtimestamp(timestamp / 1000, timezone.utc)
        numeric_fields = ('kills', 'deaths', 'assists', 'totalMinionsKilled',
                          'neutralMinionsKilled', 'visionScore', 'totalDamageDealtToChampions')
        if {p['participantId'] for p in people} != set(range(1, 11)):
            return False
        if sum(p['teamId'] == 100 for p in people) != 5 or sum(p['teamId'] == 200 for p in people) != 5:
            return False
        for player in people:
            if (player.get('gameEndedInEarlySurrender', False)
                    or not isinstance(player['puuid'], str) or not player['puuid']
                    or not isinstance(player['championName'], str)
                    or type(player['win']) is not bool):
                return False
            if any(type(player[k]) not in (int, float) or not math.isfinite(player[k])
                   or player[k] < 0 for k in numeric_fields):
                return False
        return True
    except (KeyError, TypeError, ValueError, OverflowError, OSError, AttributeError):
        return False


def review_insights(stats: dict):
    items = []
    if stats['role'] not in ('UTILITY', 'JUNGLE'):
        if stats['cs_per_min'] < 6:
            items.append({'title': 'Review missed farm', 'detail': f"{stats['cs_per_min']:.1f} CS/min in this match. Review a few waves you missed and set a small personal farming target; this is a review prompt, not a rank benchmark.", 'tone': 'focus'})
        else:
            items.append({'title': 'Farming foundation', 'detail': f"You recorded {stats['cs_per_min']:.1f} CS/min. Compare this with your own games on the same champion and role.", 'tone': 'positive'})
    if stats['deaths'] >= 7:
        items.append({'title': 'Review your deaths', 'detail': f"You died {stats['deaths']} times. Use the replay to review the minute before each death; aggregate data cannot establish positioning or intent.", 'tone': 'focus'})
    else:
        items.append({'title': 'Check your involvement', 'detail': f"You participated in {stats['kill_participation']:.0%} of your team's kills. Review when you could safely join allies and when farming was more valuable.", 'tone': 'neutral'})
    items.append({'title': 'Vision review', 'detail': f"Vision score: {stats['vision_score']} over {stats['duration_minutes']:.1f} minutes. Review your ward timing around objectives; vision score alone does not prove ward quality.", 'tone': 'neutral'})
    return items


def gold_timeline(match: dict, timeline: dict, team_id: int):
    teams = {str(p['participantId']): p['teamId'] for p in match['info']['participants']}
    if not isinstance(timeline, dict) or not isinstance(timeline.get('metadata'), dict) or timeline['metadata'].get('matchId') != match['metadata']['matchId']:
        return []
    info = timeline.get('info')
    if not isinstance(info, dict) or not isinstance(info.get('frames'), list):
        return []
    result = []
    for frame in info['frames']:
        try:
            frames, timestamp = frame['participantFrames'], frame['timestamp']
            if set(teams) != set(frames) or type(timestamp) not in (int, float) or not math.isfinite(timestamp) or timestamp < 0:
                continue
            gold = {pid: p['totalGold'] for pid, p in frames.items()}
            if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in gold.values()):
                continue
            own = sum(v for pid, v in gold.items() if teams[pid] == team_id)
            enemy = sum(v for pid, v in gold.items() if teams[pid] != team_id)
            result.append({'minute': round(timestamp / 60000, 2), 'gold_diff': round(own - enemy)})
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return sorted(result, key=lambda point: point['minute'])


def analyze_match(match: dict, timeline: dict | None, puuid: str, source: str):
    info = match['info']
    player = next((p for p in info['participants'] if p.get('puuid') == puuid), None)
    if player is None:
        return None
    duration = max(info['gameDuration'] / 60, 1)
    team_id = player['teamId']
    team_kills = sum(p.get('kills', 0) for p in info['participants'] if p['teamId'] == team_id)
    timestamp = info.get('gameStartTimestamp') or info['gameCreation']
    result = {
        'id': match['metadata']['matchId'], 'champion': player.get('championName', 'Unknown'),
        'champion_id': player.get('championId') if type(player.get('championId')) is int and player['championId'] > 0 else None,
        'role': player.get('teamPosition') if player.get('teamPosition') in ROLES else 'UNKNOWN', 'win': bool(player.get('win')),
        'kills': player.get('kills', 0), 'deaths': player.get('deaths', 0), 'assists': player.get('assists', 0),
        'duration_minutes': round(duration, 2),
        'cs_per_min': round((player.get('totalMinionsKilled', 0) + player.get('neutralMinionsKilled', 0)) / duration, 2),
        'vision_score': player.get('visionScore', 0),
        'kill_participation': round(min(1, (player.get('kills', 0) + player.get('assists', 0)) / max(team_kills, 1)), 4),
        'damage': player.get('totalDamageDealtToChampions', 0),
        'played_at': datetime.fromtimestamp(timestamp / 1000, timezone.utc).isoformat(),
        'team_id': team_id, 'queue_id': info.get('queueId'), 'patch': info.get('gameVersion'),
        'prediction': None, 'timeline': [],
        'control_wards_placed': (player['detectorWardsPlaced'] if type(player.get('detectorWardsPlaced')) is int
                                 and player['detectorWardsPlaced'] >= 0 else None),
        'surrendered': player.get('gameEndedInSurrender') if type(player.get('gameEndedInSurrender')) is bool else None,
    }
    if timeline:
        features = extract_features(match, timeline)
        if features is not None:
            result['prediction'] = predict_snapshot(features, team_id=team_id, source=source)
        result['timeline'] = gold_timeline(match, timeline, team_id)
    result.update(prediction_review(match, timeline, team_id, source))
    result['probability_timeline'] = probability_timeline(match, timeline, team_id, source)
    result['insights'] = review_insights(result)
    result['native'] = native_match_review(match, timeline, puuid)
    result['loadout'] = loadout_histories(match, timeline)[player['participantId']]
    return result


def analysis_payload(account: dict, records: list, platform: str, source: str, warning: str | None = None, benchmarks=None):
    matches = []
    seen = set()
    for record in records:
        if not eligible_match(record['match']):
            continue
        parsed = analyze_match(record['match'], record.get('timeline'), account['puuid'], record.get('source', 'riot'))
        if parsed and parsed['id'] not in seen:
            seen.add(parsed['id'])
            matches.append(parsed)
    for parsed in matches:
        parsed['personal_comparison'] = personal_comparison(parsed, matches)
        insight = comparison_insight(parsed, parsed['personal_comparison'])
        if insight:
            parsed['insights'].append(insight)
    wins = sum(m['win'] for m in matches)
    games = len(matches)
    summary = {
        'games': games, 'wins': wins, 'win_rate': wins / games if games else 0,
        'kda': round(sum(m['kills'] + m['assists'] for m in matches) / max(1, sum(m['deaths'] for m in matches)), 2),
        'cs_per_min': round(mean(m['cs_per_min'] for m in matches), 2) if games else 0,
        'vision_per_min': round(mean(m['vision_score'] / m['duration_minutes'] for m in matches), 2) if games else 0,
        'kill_participation': round(mean(m['kill_participation'] for m in matches), 4) if games else 0,
    }
    insights = []
    if games:
        insights = [
            {'title': 'Your recent sample', 'detail': f'{wins} wins from {games} recent eligible ranked games. This small, player-selected sample is descriptive and does not establish a long-term skill or improvement trend.', 'tone': 'neutral'},
            {'title': 'Make review measurable', 'detail': f"Average {summary['cs_per_min']:.1f} CS/min and {summary['kill_participation']:.0%} kill participation. Choose one review goal and compare future games in the same role.", 'tone': 'focus'},
            {'title': 'Keep the evidence separate', 'detail': 'Post-match feedback uses final statistics. Historical predictions use information available at each displayed snapshot. The main estimate and time-specific models are exploratory; neither establishes that a metric caused the result.', 'tone': 'neutral'},
        ]
    model = get_model_info()
    model['comparison'] = get_model_comparison()
    benchmarks = load_benchmarks() if benchmarks is None else benchmarks
    return {
        'source': source, 'warning': warning,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'player': {'game_name': account.get('gameName', ''), 'tag_line': account.get('tagLine', ''), 'platform': platform, 'puuid': account['puuid']},
        'summary': summary, 'matches': matches, 'insights': insights, 'model': model,
        'profile': player_profile(matches),
        'tips': {role: generate_tips(matches, benchmarks, role, account['puuid'], 'synthetic' if source == 'demo' else 'riot')
                 for role in ROLES if any(match['role'] == role for match in matches)},
    }
