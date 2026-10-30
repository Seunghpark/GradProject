"""LolAi's own completed-match review, computed directly from Riot records."""
import math

ROLES = ('TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY')


def number(value):
    return value if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def item_slots(player):
    return [value if type(value := player.get(f'item{slot}')) is int and 0 <= value < 10_000_000 else None
            for slot in range(7)]


def public_player(player, selected_id, team_damage, team_gold, team_taken, team_kills, minutes):
    damage, gold = number(player.get('totalDamageDealtToChampions')), number(player.get('goldEarned'))
    cs = player['totalMinionsKilled'] + player['neutralMinionsKilled']
    runes = []
    perks = player.get('perks', {})
    styles = perks.get('styles') if isinstance(perks, dict) else None
    for style in styles if isinstance(styles, list) else []:
        if not isinstance(style, dict):
            continue
        for entry in style.get('selections', []) if isinstance(style.get('selections', []), list) else []:
            if isinstance(entry, dict) and type(entry.get('perk')) is int and entry['perk'] > 0:
                runes.append(entry['perk'])
    name = player.get('riotIdGameName')
    name = name if isinstance(name, str) and 0 < len(name) <= 32 else player['championName']
    tag = player.get('riotIdTagline')
    return {'participant_id': player['participantId'], 'team_id': player['teamId'],
            'selected': player['participantId'] == selected_id, 'name': name,
            'tag': tag if isinstance(tag, str) and len(tag) <= 16 else '',
            'champion': player['championName'], 'champion_id': (player['championId'] if type(player.get('championId')) is int and player['championId'] > 0 else None),
            'role': player.get('teamPosition') if player.get('teamPosition') in ROLES else 'UNKNOWN',
            'kills': player['kills'], 'deaths': player['deaths'], 'assists': player['assists'],
            'cs': cs, 'cs_per_min': round(cs / minutes, 2), 'damage': damage, 'gold': gold,
            'damage_share': damage / team_damage if damage is not None and team_damage else None,
            'gold_share': gold / team_gold if gold is not None and team_gold else None,
            'damage_taken_share': number(player.get('totalDamageTaken')) / team_taken if number(player.get('totalDamageTaken')) is not None and team_taken else None,
            'kill_participation': min(1, (player['kills'] + player['assists']) / team_kills) if team_kills else 0,
            'vision': player['visionScore'], 'level': number(player.get('champLevel')),
            'wards_placed': number(player.get('wardsPlaced')), 'wards_cleared': number(player.get('wardsKilled')),
            'items': item_slots(player), 'runes': list(dict.fromkeys(runes))[:6],
            'spells': [value if type(value := player.get(key)) is int and value > 0 else None
                       for key in ('summoner1Id', 'summoner2Id')]}


def native_match_review(match, timeline, puuid):
    info, people = match['info'], match['info']['participants']
    player = next(person for person in people if person['puuid'] == puuid)
    selected_id, team_id = player['participantId'], player['teamId']
    minutes = info['gameDuration'] / 60
    teams = []
    for tid in (100, 200):
        members = [person for person in people if person['teamId'] == tid]
        damage_values = [number(person.get('totalDamageDealtToChampions')) for person in members]
        gold_values = [number(person.get('goldEarned')) for person in members]
        taken_values = [number(person.get('totalDamageTaken')) for person in members]
        damage = sum(damage_values) if None not in damage_values else None
        gold = sum(gold_values) if None not in gold_values else None
        taken = sum(taken_values) if None not in taken_values else None
        kills = sum(person['kills'] for person in members)
        entries = info.get('teams')
        team = next((entry for entry in entries if isinstance(entry, dict) and entry.get('teamId') == tid), {}) if isinstance(entries, list) else {}
        objectives = team.get('objectives', {})
        objectives = objectives if isinstance(objectives, dict) else {}
        totals = {kind: number(value.get('kills')) if isinstance(value := objectives.get(kind), dict) else None
                  for kind in ('tower', 'dragon', 'baron', 'riftHerald', 'inhibitor')}
        teams.append({'team_id': tid, 'own': tid == team_id, 'win': members[0]['win'],
                      'kills': kills, 'gold': gold, 'objectives': totals,
                      'players': sorted([public_player(person, selected_id, damage, gold, taken, kills, minutes)
                                         for person in members],
                                        key=lambda row: (ROLES.index(row['role']) if row['role'] in ROLES else 5,
                                                         row['participant_id']))})
    opponents = [person for person in people if person['teamId'] != team_id
                 and player.get('teamPosition') in ROLES and person.get('teamPosition') == player['teamPosition']]
    opponent = opponents[0] if len(opponents) == 1 else None
    result = {'teams': teams, 'role_opponent': opponent['championName'] if opponent else None,
              'role_timeline': [], 'early_comparison': None, 'mid_comparison': None,
              'objective_credits': None, 'deaths_before_14': None, 'death_windows': []}
    if (not isinstance(timeline, dict) or not isinstance(timeline.get('metadata'), dict)
            or timeline['metadata'].get('matchId') != match['metadata']['matchId']
            or not isinstance(timeline.get('info'), dict) or not isinstance(timeline['info'].get('frames'), list)
            or not timeline['info']['frames']):
        return result
    frames, events, seen_events, points = timeline['info']['frames'], [], set(), {}
    participant_teams = {person['participantId']: person['teamId'] for person in people}
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        timestamp = number(frame.get('timestamp'))
        participants = frame.get('participantFrames', {})
        if timestamp is not None and timestamp <= info['gameDuration'] * 1000 and opponent and isinstance(participants, dict):
            own, other = participants.get(str(selected_id), {}), participants.get(str(opponent['participantId']), {})
            if isinstance(own, dict) and isinstance(other, dict):
                values = [number(row.get(key)) for row in (own, other)
                          for key in ('totalGold', 'xp', 'minionsKilled', 'jungleMinionsKilled')]
                if None not in values:
                    point = {'timestamp_ms': timestamp, 'gold_diff': values[0] - values[4],
                                         'xp_diff': values[1] - values[5],
                                         'cs_diff': values[2] + values[3] - values[6] - values[7],
                                         'own_cs': values[2] + values[3], 'opponent_cs': values[6] + values[7]}
                    if all(math.isfinite(value) for value in point.values()):
                        points[timestamp] = point
        for event in frame.get('events', []) if isinstance(frame.get('events'), list) else []:
            if not isinstance(event, dict):
                continue
            stamp = number(event.get('timestamp'))
            if stamp is None or stamp > info['gameDuration'] * 1000:
                continue
            key = (stamp, str(event.get('type')), event.get('killerId') if type(event.get('killerId')) is int else None,
                   event.get('victimId') if type(event.get('victimId')) is int else None, str(event.get('monsterType')))
            if key not in seen_events:
                seen_events.add(key)
                events.append(event)
    result['role_timeline'] = [points[stamp] for stamp in sorted(points)]
    snapshots = [point for point in result['role_timeline'] if 540000 <= point['timestamp_ms'] <= 600000]
    result['early_comparison'] = snapshots[-1] if snapshots else None
    snapshots = [point for point in result['role_timeline'] if 840000 <= point['timestamp_ms'] <= 900000]
    result['mid_comparison'] = snapshots[-1] if snapshots else None
    monsters = [event for event in events if event.get('type') == 'ELITE_MONSTER_KILL']
    own_objectives = [event for event in monsters
                      if (event.get('killerTeamId') if type(event.get('killerTeamId')) is int
                          else participant_teams.get(event.get('killerId')) if type(event.get('killerId')) is int else None) == team_id]
    credits = sum((type(event.get('killerId')) is int and event['killerId'] == selected_id) or
                  (isinstance(event.get('assistingParticipantIds'), list)
                   and any(type(pid) is int and pid == selected_id for pid in event['assistingParticipantIds']))
                  for event in own_objectives)
    result['objective_credits'] = {'recorded': credits, 'team_objectives': len(own_objectives)}
    deaths = sorted([event for event in events if event.get('type') == 'CHAMPION_KILL'
                     and type(event.get('victimId')) is int and event['victimId'] == selected_id], key=lambda event: event['timestamp'])
    result['deaths_before_14'] = sum(event['timestamp'] < 840000 for event in deaths)
    for death in deaths:
        upcoming = sorted([event for event in monsters if 0 <= event['timestamp'] - death['timestamp'] <= 45000],
                          key=lambda event: event['timestamp'])
        if upcoming:
            event = upcoming[0]
            result['death_windows'].append({'death_timestamp_ms': death['timestamp'],
                                            'objective_timestamp_ms': event['timestamp'],
                                            'objective': str(event.get('monsterType', 'Objective'))[:40],
                                            'seconds_apart': round((event['timestamp'] - death['timestamp']) / 1000)})
    return result
