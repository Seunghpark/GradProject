"""LolAi's own champion/build aggregates, derived from local Riot match records."""
from collections import Counter
from datetime import datetime, timezone
import json

from .config import BACKEND_DIR
from .native_review import ROLES, item_slots
from .loadout_timeline import loadout_histories

CATALOG_VERSION = 2


def build_catalog(records):
    from .analytics import eligible_match
    groups, seen, patches, queues = {}, set(), set(), set()
    provenance = set()
    for record in records:
        source = record.get('source')
        if source not in ('riot', 'synthetic'):
            raise ValueError('Unknown record provenance')
        provenance.add(source)
        if len(provenance) > 1:
            raise ValueError('Do not combine fictional and real match records')
        match = record.get('match', {})
        if not eligible_match(match):
            continue
        match_id, info = match['metadata']['matchId'], match['info']
        if match_id in seen:
            continue
        seen.add(match_id)
        patch = '.'.join(str(info.get('gameVersion', '')).split('.')[:2])
        patches.add(patch)
        queues.add(info['queueId'])
        loadouts = loadout_histories(match, record.get('timeline'))
        for player in info['participants']:
            role, champion = player.get('teamPosition'), player['championName']
            if role not in ROLES:
                continue
            key = (champion, role, patch, info['queueId'])
            group = groups.setdefault(key, {'champion': champion, 'champion_id': player.get('championId'),
                'role': role, 'patch': patch, 'queue_id': info['queueId'], 'games': 0, 'wins': 0,
                'kills': 0, 'deaths': 0, 'assists': 0, 'cs_per_min': 0, 'vision_per_min': 0,
                'items': Counter(), 'inventories': Counter(), 'runes': Counter(), 'matchups': {},
                'purchase_sequences': Counter(), 'skill_orders': Counter(),
                'purchase_order_games': 0, 'skill_order_games': 0})
            group['games'] += 1
            group['wins'] += int(player['win'])
            history = loadouts[player['participantId']]
            if history.get('purchase_aggregate_eligible'):
                group['purchase_order_games'] += 1
                group['purchase_sequences'].update([tuple(item['item_id'] for item in history['purchases'][:6])])
            if history.get('skill_aggregate_eligible'):
                group['skill_order_games'] += 1
                group['skill_orders'].update([tuple(item['ability'] for item in history['skill_order'][:6])])
            for metric in ('kills', 'deaths', 'assists'):
                group[metric] += player[metric]
            minutes = info['gameDuration'] / 60
            group['cs_per_min'] += (player['totalMinionsKilled'] + player['neutralMinionsKilled']) / minutes
            group['vision_per_min'] += player['visionScore'] / minutes
            slots = item_slots(player)
            items = tuple(sorted({item for item in slots[:6] if item}))
            group['items'].update(items)
            # Missing slots cannot be treated as a known complete inventory.
            if None not in slots[:6] and items:
                group['inventories'][items] += 1
            perks = player.get('perks', {})
            styles = perks.get('styles') if isinstance(perks, dict) else None
            for style in styles if isinstance(styles, list) else []:
                if not isinstance(style, dict) or not isinstance(style.get('selections'), list):
                    continue
                choices = [entry.get('perk') for entry in style['selections'] if isinstance(entry, dict)]
                if choices and type(choices[0]) is int and choices[0] > 0:
                    group['runes'][choices[0]] += 1
                break
            opponents = [other for other in info['participants'] if other['teamId'] != player['teamId']
                         and other.get('teamPosition') == role]
            if len(opponents) == 1:
                opponent = opponents[0]['championName']
                matchup = group['matchups'].setdefault(opponent, {'champion': opponent, 'games': 0, 'wins': 0})
                matchup['games'] += 1
                matchup['wins'] += int(player['win'])
    output = []
    for group in groups.values():
        games = group['games']
        group['win_rate'] = group['wins'] / games
        group['kda'] = (group.pop('kills') + group.pop('assists')) / max(1, group['deaths'])
        group['deaths_per_game'] = group.pop('deaths') / games
        group['cs_per_min'] /= games
        group['vision_per_min'] /= games
        group['items'] = [{'id': item, 'games': count, 'frequency': count / games}
                          for item, count in group['items'].most_common(6)]
        group['inventories'] = [{'ids': list(items), 'games': count}
                                for items, count in group['inventories'].most_common(3)]
        group['runes'] = [{'id': rune, 'games': count} for rune, count in group['runes'].most_common(3)]
        for field, denominator in (('purchase_sequences', 'purchase_order_games'), ('skill_orders', 'skill_order_games')):
            group[field] = [{'sequence': list(sequence), 'games': count,
                             'frequency': count / group[denominator]} for sequence, count in group[field].most_common(3)]
        group['matchups'] = sorted(group['matchups'].values(), key=lambda row: (-row['games'], row['champion']))
        output.append(group)
    return {'schema_version': 1, 'computation_version': CATALOG_VERSION, 'source': next(iter(provenance), 'riot'),
            'created_at': datetime.now(timezone.utc).isoformat(), 'unique_matches': len(seen),
            'patches': sorted(patches, key=lambda value: tuple(int(part) for part in value.split('.')) if all(part.isdigit() for part in value.split('.')) else (-1,)), 'queues': sorted(queues),
            'groups': sorted(output, key=lambda row: (-row['games'], row['champion'], row['role'], row['patch'], row['queue_id']))}


def get_catalog():
    path = BACKEND_DIR / 'data/native_champions.json'
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if (data.get('schema_version') != 1 or data.get('source') not in ('riot', 'synthetic')
                or not isinstance(data.get('groups'), list) or not isinstance(data.get('unique_matches'), int)):
            raise ValueError('Invalid champion catalog')
        return {**data, 'status': 'available'}
    except (OSError, ValueError, AttributeError):
        return {'status': 'unavailable', 'source': None, 'unique_matches': 0, 'groups': [], 'patches': [], 'queues': []}
