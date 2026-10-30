"""Lazy current-rank/mastery context; never added to historical model inputs."""
from datetime import datetime, timezone
import sqlite3

from .config import PLATFORMS
from .riot import RiotClient, RiotError


TIERS = {'IRON', 'BRONZE', 'SILVER', 'GOLD', 'PLATINUM', 'EMERALD', 'DIAMOND',
         'MASTER', 'GRANDMASTER', 'CHALLENGER'}
QUEUES = {'RANKED_SOLO_5x5', 'RANKED_FLEX_SR'}


def _integer(value):
    return type(value) is int and value >= 0


def _ranks(data):
    if not isinstance(data, list):
        raise ValueError('Invalid rank response')
    entries = []
    for row in data:
        if not isinstance(row, dict) or row.get('queueType') not in QUEUES:
            raise ValueError('Invalid rank response')
        if (row.get('tier') not in TIERS or row.get('rank') not in {'I', 'II', 'III', 'IV'}
                or any(not _integer(row.get(key)) for key in ('leaguePoints', 'wins', 'losses'))):
            raise ValueError('Invalid rank response')
        games = row['wins'] + row['losses']
        entries.append({'queue': row['queueType'], 'tier': row['tier'], 'division': row['rank'],
                        'league_points': row['leaguePoints'], 'wins': row['wins'], 'losses': row['losses'],
                        'win_rate': row['wins'] / games if games else None})
    if len({entry['queue'] for entry in entries}) != len(entries):
        raise ValueError('Duplicate rank queue')
    return sorted(entries, key=lambda entry: entry['queue'])


def _mastery(data, champion_id):
    if (not isinstance(data, dict) or type(data.get('championId')) is not int
            or data['championId'] != champion_id
            or any(not _integer(data.get(key)) for key in ('championLevel', 'championPoints', 'lastPlayTime'))):
        raise ValueError('Invalid mastery response')
    last_played = (datetime.fromtimestamp(data['lastPlayTime'] / 1000, timezone.utc).isoformat()
                   if data['lastPlayTime'] else None)
    return {'champion_id': champion_id, 'level': data['championLevel'],
            'points': data['championPoints'], 'last_played_at': last_played}


async def get_player_context(riot: RiotClient, platform: str, game_name: str, tag_line: str,
                             champion_id: int | None = None, history=None) -> dict:
    if platform not in PLATFORMS or (champion_id is not None and
                                    (type(champion_id) is not int or not 0 < champion_id <= 100000)):
        raise ValueError('Invalid platform or champion ID')
    account, _ = await riot.account(platform, game_name, tag_line)
    if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
        raise RiotError('invalid_response', 'Riot returned an invalid account response.')
    rank = {'status': 'unavailable', 'entries': [], 'cached': False, 'notice': None}
    rank_history = {'status': 'unavailable', 'observations': [], 'previous_season_status': 'not_verified'}
    mastery = {'status': 'not_requested', 'champion_id': champion_id, 'cached': False,
               'notice': 'This match has no validated champion ID.'}
    try:
        data, cached = await riot.ranks(platform, account['puuid'])
        entries = _ranks(data)
        rank.update(status='available' if entries else 'no_ranked_entries', entries=entries,
                    cached=cached, notice=None if entries else 'No current solo/flex rank entries were returned.')
        if history is not None:
            try:
                rank_history = history.observe(platform, account['puuid'], entries, cached=cached)
            except (sqlite3.Error, OSError, ValueError):
                rank_history['status'] = 'storage_unavailable'
    except RiotError as error:
        rank['notice'] = error.message
    except (ValueError, TypeError, OverflowError, OSError):
        rank['notice'] = 'Riot returned an invalid rank response; no rank is inferred.'
    if history is not None and rank['status'] == 'unavailable':
        try:
            rank_history = history.observe(platform, account['puuid'], None, cached=True)
        except (sqlite3.Error, OSError, ValueError):
            rank_history['status'] = 'storage_unavailable'
    if champion_id is not None:
        mastery['status'] = 'unavailable'
        try:
            data, cached = await riot.champion_mastery(platform, account['puuid'], champion_id)
            mastery.update(_mastery(data, champion_id), status='available', cached=cached, notice=None)
        except RiotError as error:
            mastery.update(status='no_record' if error.status == 404 else 'unavailable',
                           notice='Riot returned no mastery record for this champion.' if error.status == 404 else error.message)
        except (ValueError, TypeError, OverflowError, OSError):
            mastery['notice'] = 'Riot returned an invalid mastery response; no level or points are inferred.'
    return {
        'source': 'riot', 'fetched_at': datetime.now(timezone.utc).isoformat(),
        'player': {'game_name': account.get('gameName') if isinstance(account.get('gameName'), str) else game_name,
                   'tag_line': account.get('tagLine') if isinstance(account.get('tagLine'), str) else tag_line,
                   'platform': platform},
        'rank': rank, 'rank_history': rank_history, 'mastery': mastery,
        'notice': ('Current account context from Riot, cached for up to five minutes. It is not '
                   'the rank or mastery at the time of the selected match and is not used by '
                   'the historical predictor. Mastery points reflect recorded play, not verified expertise.'),
    }
