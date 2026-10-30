"""Deterministic fictional examples, never represented as Riot records."""
from datetime import datetime, timezone
import random

DEMO_PUUID = 'synthetic-demo-player'
DEMO_ACCOUNT = {'puuid': DEMO_PUUID, 'gameName': 'DemoPlayer', 'tagLine': 'SKKU'}
CHAMPIONS = ['Ahri', 'Orianna', 'Syndra', 'Viktor', 'Lux', 'Akali', 'Taliyah', 'Sylas']
ROLES = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
CHAMPION_IDS = {'Ahri': 103, 'Orianna': 61, 'Syndra': 134, 'Viktor': 112, 'Lux': 99, 'Akali': 84,
                'Taliyah': 163, 'Sylas': 517, 'Gnar': 150, 'Vi': 254, 'Jinx': 222, 'Leona': 89}


def demo_records(count: int = 10):
    records = []
    origin = int(datetime(2026, 10, 25, 14, tzinfo=timezone.utc).timestamp() * 1000)
    for index in range(count):
        rng = random.Random(20261026 + index)
        win = index % 5 in (0, 1, 3)
        player_team = 100 if index % 2 == 0 else 200
        blue_win = win if player_team == 100 else not win
        duration = rng.randint(24, 37) * 60 + rng.randint(0, 59)
        player_id = 3 if player_team == 100 else 8
        advantage = rng.randint(600, 2800) * (1 if blue_win else -1)
        if index % 4 == 3:
            advantage *= -1
        participants = []
        for pid in range(1, 11):
            team = 100 if pid <= 5 else 200
            is_player = pid == player_id
            kills = rng.randint(2, 13)
            deaths = rng.randint(1, 6) if (team == 100) == blue_win else rng.randint(4, 11)
            assists = rng.randint(3, 17)
            participants.append({
                'participantId': pid, 'teamId': team,
                'puuid': DEMO_PUUID if is_player else f'synthetic-{index}-{pid}',
                'riotIdGameName': 'DemoPlayer' if is_player else f'Example{pid}',
                'riotIdTagline': 'SKKU',
                'championName': CHAMPIONS[index % len(CHAMPIONS)] if is_player else ['Gnar', 'Vi', 'Ahri', 'Jinx', 'Leona'][(pid - 1) % 5],
                'teamPosition': ROLES[(pid - 1) % 5], 'win': (team == 100) == blue_win,
                'kills': kills, 'deaths': deaths, 'assists': assists,
                'totalMinionsKilled': int(duration / 60 * rng.uniform(5.2, 8.0)) if (pid - 1) % 5 not in (1, 4) else rng.randint(10, 35),
                'neutralMinionsKilled': rng.randint(110, 170) if (pid - 1) % 5 == 1 else rng.randint(0, 12),
                'visionScore': rng.randint(15, 40) if (pid - 1) % 5 != 4 else rng.randint(45, 80),
                'totalDamageDealtToChampions': rng.randint(14000, 36000),
                'goldEarned': rng.randint(10000, 16000),
                'gameEndedInEarlySurrender': False,
            })
            participants[-1].update(championId=CHAMPION_IDS[participants[-1]['championName']],
                                     champLevel=min(18, duration // 120), item0=3152, item1=3020, item2=3157,
                                     item3=0, item4=0, item5=0, item6=3340, summoner1Id=4,
                                     summoner2Id=11 if (pid - 1) % 5 == 1 else 14,
                                     perks={'styles': [{'selections': [{'perk': 8112}, {'perk': 8139}, {'perk': 8138}]}]})
        match = {
            'metadata': {'matchId': f'DEMO_{index + 1:04d}', 'participants': [p['puuid'] for p in participants]},
            'info': {'gameCreation': origin - index * 7200000, 'gameStartTimestamp': origin - index * 7200000,
                     'gameDuration': duration, 'gameVersion': '16.20.synthetic', 'queueId': 420,
                     'mapId': 11, 'gameMode': 'CLASSIC', 'participants': participants,
                     'teams': [{'teamId': 100, 'win': blue_win}, {'teamId': 200, 'win': not blue_win}]},
        }
        frames = []
        for minute in range(duration // 60 + 1):
            snapshots = {}
            for participant in participants:
                pid = participant['participantId']
                direction = 1 if participant['teamId'] == 100 else -1
                # Independent synthetic paths with a known 10-minute snapshot.
                lead = advantage * min(minute / 10, 1.0) / 10
                late = (minute - 10) * (150 if blue_win else -150) / 10 if minute > 10 else 0
                snapshots[str(pid)] = {
                    'participantId': pid, 'totalGold': max(500, int(500 + minute * 310 + direction * (lead + late))),
                    'xp': max(0, int(minute * 490 + direction * lead * .65)),
                    'minionsKilled': int(minute * (6.5 if (pid - 1) % 5 not in (1, 4) else 1.2)),
                    'jungleMinionsKilled': int(minute * 4.5) if (pid - 1) % 5 == 1 else 0,
                }
            events = []
            if minute in (3, 5, 7, 9):
                killer = 3 if advantage > 0 else 8
                events.append({'type': 'CHAMPION_KILL', 'timestamp': minute * 60000,
                               'killerId': killer, 'victimId': 8 if killer == 3 else 3})
            if minute == 8:
                events.append({'type': 'ELITE_MONSTER_KILL', 'timestamp': 480000,
                               'killerId': 2 if advantage > 0 else 7, 'killerTeamId': 100 if advantage > 0 else 200,
                               'monsterType': 'DRAGON'})
            frames.append({'timestamp': minute * 60000, 'participantFrames': snapshots, 'events': events})
        timeline = {'metadata': match['metadata'], 'info': {'frameInterval': 60000, 'frames': frames}}
        records.append({'match': match, 'timeline': timeline, 'source': 'synthetic'})
    return records
