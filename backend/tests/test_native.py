"""Native Riot computations must not depend on outside analytics providers."""
from copy import deepcopy
import json
from unittest.mock import patch

import pytest

from app.analytics import analyze_match, eligible_match
from app.demo import DEMO_PUUID, demo_records
from app.native_review import native_match_review
from app.native_catalog import build_catalog, get_catalog
from app.main import create_app
from app.config import Settings


def review(record=None, puuid=DEMO_PUUID):
    record = record or demo_records(1)[0]
    return native_match_review(record['match'], record['timeline'], puuid)


def test_full_scoreboard_has_ten_players_and_correct_team_denominators():
    result = review()
    rows = [row for team in result['teams'] for row in team['players']]
    assert len(rows) == 10 and sum(row['selected'] for row in rows) == 1
    assert all('puuid' not in row for row in rows)
    for team in result['teams']:
        assert [row['role'] for row in team['players']] == ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
        assert sum(row['damage_share'] for row in team['players']) == pytest.approx(1)
        assert sum(row['gold_share'] for row in team['players']) == pytest.approx(1)
        assert sum(row['kills'] for row in team['players']) == team['kills']
        assert all(value is None for value in team['objectives'].values())
    assert rows[2]['champion_id'] == 103
    assert rows[2]['items'] == [3152, 3020, 3157, 0, 0, 0, 3340]


def test_incomplete_gold_loadout_and_objective_fields_remain_unknown():
    record = demo_records(1)[0]
    player = record['match']['info']['participants'][0]
    del player['goldEarned']
    player.update(item0=True, item1=-1, item2=None, perks={'styles': [None, {'selections': 1}]})
    record['match']['info']['teams'][0]['objectives'] = {'tower': {'kills': 6}, 'dragon': {'kills': True}}
    result = review(record)
    assert result['teams'][0]['gold'] is None
    assert all(row['gold_share'] is None for row in result['teams'][0]['players'])
    assert result['teams'][0]['players'][0]['items'][:3] == [None, None, None]
    assert result['teams'][0]['objectives']['tower'] == 6
    assert result['teams'][0]['objectives']['dragon'] is None
    assert result['teams'][0]['players'][0]['runes'] == []


def test_role_comparison_uses_latest_9_to_10_minute_frame_and_selected_side():
    record = demo_records(1)[0]
    blue = review(record)
    red_puuid = record['match']['info']['participants'][7]['puuid']
    red = review(record, red_puuid)
    assert blue['early_comparison']['timestamp_ms'] == 600000
    for metric in ('gold_diff', 'xp_diff', 'cs_diff'):
        assert blue['early_comparison'][metric] == -red['early_comparison'][metric]
    for frame in record['timeline']['info']['frames']:
        if frame['timestamp'] > 600000:
            frame['participantFrames']['3']['totalGold'] = 99999999
    assert review(record)['early_comparison'] == blue['early_comparison']
    record['timeline']['info']['frames'] = [frame for frame in record['timeline']['info']['frames'] if frame['timestamp'] != 600000]
    assert review(record)['early_comparison']['timestamp_ms'] == 540000


def test_ambiguous_roles_and_invalid_snapshot_values_do_not_invent_a_lane_opponent():
    record = demo_records(1)[0]
    record['match']['info']['participants'][6]['teamPosition'] = 'MIDDLE'
    assert review(record)['role_opponent'] is None
    assert review(record)['early_comparison'] is None
    record['match']['info']['participants'][6]['teamPosition'] = 'JUNGLE'
    for frame in record['timeline']['info']['frames']:
        frame['participantFrames']['3']['xp'] = float('nan')
    assert review(record)['role_timeline'] == []


@pytest.mark.parametrize('timeline', [None, {}, {'metadata': {'matchId': 'wrong'}},
    {'metadata': {'matchId': 'DEMO_0001'}, 'info': {'frames': []}}])
def test_missing_or_mismatched_timeline_keeps_roster_but_unknown_timing(timeline):
    record = demo_records(1)[0]
    record['timeline'] = timeline
    result = review(record)
    assert len(result['teams']) == 2
    assert result['early_comparison'] is None
    assert result['objective_credits'] is None


def test_objective_assists_and_death_windows_use_recorded_ids_and_exact_boundaries():
    record = demo_records(1)[0]
    frame = record['timeline']['info']['frames'][0]
    for row in record['timeline']['info']['frames']:
        row['events'] = []
    frame['events'] = [
        {'type': 'CHAMPION_KILL', 'timestamp': 800000, 'victimId': 3, 'killerId': 8},
        {'type': 'ELITE_MONSTER_KILL', 'timestamp': 845000, 'killerId': 2, 'killerTeamId': 100,
         'monsterType': 'DRAGON', 'assistingParticipantIds': [3]},
        {'type': 'ELITE_MONSTER_KILL', 'timestamp': 846000, 'killerId': 7, 'killerTeamId': 200,
         'monsterType': 'RIFTHERALD', 'assistingParticipantIds': [True]},
        {'type': 'CHAMPION_KILL', 'timestamp': 900000, 'victimId': 3, 'killerId': 8},
        {'type': 'ELITE_MONSTER_KILL', 'timestamp': 945001, 'killerId': 2, 'killerTeamId': 100,
         'monsterType': 'BARON_NASHOR', 'assistingParticipantIds': [True]},
    ]
    frame['events'].append(deepcopy(frame['events'][1]))
    result = review(record)
    assert result['objective_credits'] == {'recorded': 1, 'team_objectives': 2}
    assert len(result['death_windows']) == 1
    assert result['death_windows'][0]['seconds_apart'] == 45
    assert 'avoidable' not in json.dumps(result)


def test_existing_analysis_adds_native_fields_without_changing_player_stats():
    record = demo_records(1)[0]
    assert eligible_match(record['match'])
    result = analyze_match(record['match'], record['timeline'], DEMO_PUUID, 'demo')
    selected = next(row for team in result['native']['teams'] for row in team['players'] if row['selected'])
    assert selected['kills'] == result['kills']
    assert selected['champion'] == result['champion']


def test_additional_review_metrics_use_available_raw_fields_and_bounded_timestamps():
    record = demo_records(1)[0]
    for person in record['match']['info']['participants']:
        person.update(totalDamageTaken=10000, wardsPlaced=8, wardsKilled=2)
    result = review(record)
    selected = next(row for team in result['teams'] for row in team['players'] if row['selected'])
    assert selected['damage_taken_share'] == .2
    assert selected['wards_placed'] == 8 and selected['wards_cleared'] == 2
    assert result['early_comparison']['own_cs'] == 65
    assert result['mid_comparison']['timestamp_ms'] == 900000
    assert result['deaths_before_14'] >= 0
    for frame in record['timeline']['info']['frames']:
        frame['events'] = []
    record['timeline']['info']['frames'][0]['events'] = [
        {'type': 'CHAMPION_KILL', 'timestamp': 839999, 'victimId': 3},
        {'type': 'CHAMPION_KILL', 'timestamp': 840000, 'victimId': 3}]
    assert review(record)['deaths_before_14'] == 1


def test_champion_catalog_deduplicates_games_and_counts_each_item_once_per_inventory():
    record = demo_records(1)[0]
    player = record['match']['info']['participants'][2]
    player.update(item0=3157, item1=3157)
    catalog = build_catalog([record, deepcopy(record)])
    assert catalog['source'] == 'synthetic' and catalog['unique_matches'] == 1
    group = next(row for row in catalog['groups'] if row['champion'] == 'Ahri' and row['role'] == 'MIDDLE')
    assert group['games'] == 2
    assert next(row for row in group['items'] if row['id'] == 3157)['games'] == 2
    assert group['items'][0]['frequency'] <= 1
    assert 'puuid' not in json.dumps(catalog) and DEMO_PUUID not in json.dumps(catalog)


def test_catalog_keeps_patch_queue_role_separate_and_does_not_complete_missing_inventory():
    record = demo_records(1)[0]
    second = deepcopy(record)
    second['match']['metadata']['matchId'] = 'DEMO_OTHER'
    second['match']['info'].update(queueId=440, gameVersion='16.21.1')
    second['match']['info']['participants'][2].pop('item1')
    catalog = build_catalog([record, second])
    assert catalog['queues'] == [420, 440] and catalog['patches'] == ['16.20', '16.21']
    group = next(row for row in catalog['groups'] if row['champion'] == 'Ahri' and row['role'] == 'MIDDLE' and row['queue_id'] == 440)
    assert sum(row['games'] for row in group['inventories']) == 1
    assert sum(row['games'] for row in group['matchups']) == 2


def test_catalog_refuses_mixed_or_unknown_provenance_and_skips_ineligible_matches():
    record = demo_records(1)[0]
    riot = {**record, 'source': 'riot'}
    with pytest.raises(ValueError, match='fictional'):
        build_catalog([record, riot])
    with pytest.raises(ValueError, match='provenance'):
        build_catalog([{**record, 'source': 'unknown'}])
    record['match']['info']['queueId'] = 450
    assert build_catalog([record])['groups'] == []


def test_catalog_endpoint_is_registered_before_frontend_and_handles_absent_artifact(tmp_path):
    with patch('app.native_catalog.BACKEND_DIR', tmp_path):
        assert get_catalog()['status'] == 'unavailable'
        (tmp_path / 'data').mkdir()
        (tmp_path / 'data/native_champions.json').write_text('{broken')
        assert get_catalog()['groups'] == []
        artifact = build_catalog(demo_records(1))
        (tmp_path / 'data/native_champions.json').write_text(json.dumps(artifact))
        app = create_app(Settings(cache_path=':memory:'))
        routes = {route.path: route.endpoint for route in app.routes}
        assert list(routes).index('/api/champions') < list(routes).index('/{path:path}')
        assert routes['/api/champions']()['unique_matches'] == 1
