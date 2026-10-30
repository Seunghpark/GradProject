"""Validate optional OP.GG archival ranks; never infer past tiers from current rank."""
import ast
from datetime import datetime, timezone
import json
import math
import re

from .player_context import TIERS

PROFILE_TOOL = 'lol_get_summoner_profile'
PROFILE_FIELDS = [
    'data.summoner.{game_name,tagline,region}',
    'data.summoner.previous_seasons[].season_id',
    'data.summoner.previous_seasons[].tier_info.{tier,division,lp}',
    'data.summoner.previous_season_tiers[].season_id',
    'data.summoner.previous_season_tiers[].rank_entries[].game_type',
    'data.summoner.previous_season_tiers[].rank_entries[].rank_info.{created_at,division,lp,tier}',
    'data.summoner.previous_season_tiers[].rank_entries[].high_rank_info.{created_at,division,lp,tier}',
]
QUEUES = {'SOLORANKED': 'RANKED_SOLO_5x5', 'FLEXRANKED': 'RANKED_FLEX_SR'}


def _nonfinite(value):
    raise ValueError('Nonfinite JSON')


def _data(text):
    if not isinstance(text, str) or len(text) > 1_000_000:
        raise ValueError('Invalid provider text')
    try:
        if text.lstrip().startswith(('{', '[')):
            return json.loads(text, parse_constant=_nonfinite)
        classes, expression = {}, []
        for line in text.strip().splitlines():
            if not line.strip():
                continue
            declaration = re.fullmatch(r'class ([A-Za-z]\w{0,79}):\s*([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)?', line.strip())
            if declaration and not expression:
                name, fields = declaration.groups()
                if name in classes or len(classes) >= 100:
                    raise ValueError('Duplicate or excessive provider definitions')
                classes[name] = re.split(r'\s*,\s*', fields) if fields else []
                if len(classes[name]) != len(set(classes[name])) or len(classes[name]) > 100:
                    raise ValueError('Invalid provider fields')
            else:
                expression.append(line)
        tree = ast.parse('\n'.join(expression), mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 20000:
            raise ValueError('Provider expression is too large')

        def read(node, depth=0):
            if depth > 40:
                raise ValueError('Provider expression is too deep')
            if isinstance(node, ast.Constant) and type(node.value) in (str, int, float, bool, type(None)):
                if type(node.value) in (int, float) and not math.isfinite(node.value):
                    raise ValueError('Nonfinite provider value')
                return node.value
            if isinstance(node, ast.Name) and node.id in {'null', 'true', 'false'}:
                return {'null': None, 'true': True, 'false': False}[node.id]
            if isinstance(node, ast.List):
                return [read(value, depth+1) for value in node.elts]
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
                value = read(node.operand, depth+1)
                if type(value) in (int, float):
                    return -value if isinstance(node.op, ast.USub) else value
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
                fields = classes.get(node.func.id)
                if fields is not None and len(fields) == len(node.args):
                    return {field: read(value, depth+1) for field, value in zip(fields, node.args)}
            raise ValueError('Provider output must contain data only')
        return read(tree.body)
    except (SyntaxError, RecursionError, OverflowError) as error:
        raise ValueError('Invalid provider data') from error


def _date(value):
    if not isinstance(value, str) or len(value) > 64:
        return None
    try:
        date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return date.astimezone(timezone.utc).isoformat() if date.tzinfo is not None else None
    except (ValueError, OverflowError, OSError):
        return None


def _rank(value):
    if not isinstance(value, dict) or not isinstance(value.get('tier'), str) or value['tier'] not in TIERS:
        return None
    division = value.get('division')
    if type(division) is int and 1 <= division <= 4:
        division = ('I', 'II', 'III', 'IV')[division-1]
    if division not in ('I', 'II', 'III', 'IV') or type(value.get('lp')) is not int or not 0 <= value['lp'] <= 1_000_000:
        return None
    return {'tier': value['tier'], 'division': division, 'league_points': value['lp'],
            'provider_recorded_at': _date(value.get('created_at'))}


def rank_archive(payload, game_name, tag_line, region):
    value = payload.get('data')
    if not isinstance(value, dict):
        value = _data(payload.get('text'))
    summoner = value.get('data', {}).get('summoner') if isinstance(value, dict) and isinstance(value.get('data'), dict) else None
    if (not isinstance(summoner, dict) or not isinstance(summoner.get('game_name'), str)
            or not isinstance(summoner.get('tagline'), str)
            or summoner['game_name'].casefold() != game_name.casefold() or summoner['tagline'].casefold() != tag_line.casefold()
            or (summoner.get('region') is not None and summoner['region'] != region)):
        raise ValueError('Provider profile identity does not match the request')
    seasons = summoner.get('previous_season_tiers')
    if not isinstance(seasons, list) or len(seasons) > 100:
        raise ValueError('Provider returned no structured historical rank list')
    entries, conflicts = {}, set()
    for season in seasons:
        if not isinstance(season, dict) or type(season.get('season_id')) is not int or not 0 < season['season_id'] < 100000:
            continue
        rows = season.get('rank_entries')
        for row in rows if isinstance(rows, list) and len(rows) <= 10 else []:
            if not isinstance(row, dict) or not isinstance(row.get('game_type'), str) or row['game_type'] not in QUEUES:
                continue
            archived = _rank(row.get('rank_info'))
            if archived is None:
                continue
            item = {'season_id': season['season_id'], 'queue': QUEUES[row['game_type']],
                    'rank': archived, 'provider_reported_peak': _rank(row.get('high_rank_info'))}
            key = (item['season_id'], item['queue'])
            if key in entries and entries[key] != item:
                conflicts.add(key)
            entries[key] = item
    rows = sorted([item for key, item in entries.items() if key not in conflicts],
                  key=lambda item: (item['rank']['provider_recorded_at'] or '', item['season_id'], item['queue']), reverse=True)
    fetched_at = _date(payload.get('fetched_at'))
    if fetched_at is None:
        raise ValueError('Provider fetch time is missing')
    return {'status': 'available' if rows else 'no_history', 'source': 'opgg_archive', 'provider': 'OP.GG',
            'provider_url': 'https://op.gg/', 'fetched_at': fetched_at, 'cached': payload.get('cached') is True,
            'independently_validated': False, 'entries': rows,
            'latest_solo': next((row for row in rows if row['queue'] == 'RANKED_SOLO_5x5'), None),
            'latest_flex': next((row for row in rows if row['queue'] == 'RANKED_FLEX_SR'), None),
            'notice': 'Optional OP.GG archived ranks, not Riot-verified final-season standings or match-time tiers. Season IDs are provider IDs; no calendar years are inferred. Reported peaks remain separate. These records do not label historical model or benchmark data.'}
