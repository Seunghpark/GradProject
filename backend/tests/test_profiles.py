"""Descriptive profile counts and personal review never borrow model outcomes."""
import copy
import math

import pytest

from app.analytics import analysis_payload, analyze_match
from app.demo import DEMO_ACCOUNT, DEMO_PUUID, demo_records
from app.profiles import ROLES, comparison_insight, personal_comparison, player_profile


def match(index, role='MIDDLE', champion='Ahri', win=True, **values):
    return {
        'id': str(index), 'role': role, 'champion': champion, 'win': win,
        'kills': 3, 'deaths': 2, 'assists': 5, 'cs_per_min': 6,
        'kill_participation': .5, 'vision_score': 20, 'duration_minutes': 25,
        **values,
    }


def test_empty_profile_preserves_all_roles_without_inventing_rates():
    profile = player_profile([])
    assert profile['games'] == 0
    assert [group['role'] for group in profile['roles']] == list(ROLES)
    assert all(group['games'] == 0 and group['win_rate'] is None and group['kda'] is None
               for group in profile['roles'])
    assert profile['champions'] == []
    assert profile['main_role'] is None
    assert profile['main_role_stats'] is None
    assert not profile['main_role_tied']


def test_profile_uses_unique_games_and_separates_unknown_role():
    games = [match(1), match(2, win=False), match(3, 'TOP', 'Gnar'), match(4, 'UNKNOWN', 'Lux')]
    profile = player_profile(games + [games[0]])
    assert profile['games'] == 4
    assert profile['main_role'] == 'MIDDLE'
    assert profile['main_role_stats']['games'] == 2
    assert profile['main_role_stats']['win_rate'] == .5
    assert profile['off_role_stats']['games'] == 1
    assert profile['main_off_role_win_rate_gap'] == -.5
    assert profile['unknown_role_games'] == 1
    assert profile['champions'][0]['champion'] == 'Ahri'
    assert profile['champions'][0]['games'] == 2
    assert profile['main_role_stats']['kda'] == 4
    assert profile['main_role_stats']['vision_per_min'] == .8


def test_most_played_tie_does_not_assign_a_preferred_role():
    profile = player_profile([match(1), match(2, 'TOP')])
    assert profile['main_role_tied']
    assert profile['main_role'] is None
    assert profile['main_role_stats'] is None
    assert profile['off_role_stats'] is None
    assert profile['main_off_role_win_rate_gap'] is None


def test_zero_death_kda_is_finite_with_documented_ratio_convention():
    group = player_profile([match(1, deaths=0)])['champions'][0]
    assert group['kda'] == 8
    assert math.isfinite(group['kda'])


def test_personal_comparison_prefers_same_champion_and_excludes_current_id():
    selected = match(0, cs_per_min=9, kill_participation=.8, vision_score=40, deaths=3)
    games = [selected, selected, match(1), match(2), match(3), match(4, champion='Lux', cs_per_min=1)]
    comparison = personal_comparison(selected, games)
    assert comparison['basis'] == 'same_champion_role'
    assert comparison['games'] == 3
    assert comparison['averages']['cs_per_min'] == 6
    assert comparison['deltas']['cs_per_min'] == 3
    assert comparison['deltas']['kill_participation'] == .3
    assert comparison['deltas']['vision_per_min'] == .8
    assert comparison['deltas']['deaths_per_game'] == 1
    insight = comparison_insight(selected, comparison)
    assert '3 other' in insight['detail']
    assert 'same champion and role' in insight['detail']
    assert 'causal' in insight['detail']


def test_personal_comparison_falls_back_to_same_role_only():
    selected = match(0)
    games = [selected, match(1), match(2, champion='Lux'), match(3, champion='Viktor'),
             match(4, role='UTILITY', cs_per_min=1)]
    comparison = personal_comparison(selected, games)
    assert comparison['basis'] == 'same_role'
    assert comparison['games'] == 3
    assert comparison['averages']['cs_per_min'] == 6


def test_too_few_unique_other_games_does_not_fabricate_benchmark():
    selected = match(0)
    other = match(1)
    comparison = personal_comparison(selected, [selected, other, other, other])
    assert comparison['basis'] == 'none'
    assert comparison['games'] == 1
    assert comparison['averages'] is None
    assert comparison['deltas'] is None
    assert comparison_insight(selected, comparison) is None


def test_unknown_role_has_no_personal_comparison_even_with_many_unknown_games():
    selected = match(0, role='UNKNOWN')
    comparison = personal_comparison(selected, [selected] + [match(i, role='UNKNOWN') for i in range(1, 5)])
    assert comparison['basis'] == 'none'
    assert comparison['games'] == 0


@pytest.mark.parametrize('wards,surrender,expected_wards,expected_surrender', [
    (4, True, 4, True), (0, False, 0, False),
    (None, None, None, None), (-1, 1, None, None),
    (True, 'false', None, None), (1.5, {}, None, None),
])
def test_optional_upstream_metrics_are_not_invented_or_coerced(monkeypatch, tmp_path, wards, surrender, expected_wards, expected_surrender):
    monkeypatch.setenv('MODEL_PATH', str(tmp_path / 'not-trained.json'))
    record = copy.deepcopy(demo_records(1)[0])
    player = next(p for p in record['match']['info']['participants'] if p['puuid'] == DEMO_PUUID)
    player['detectorWardsPlaced'] = wards
    player['gameEndedInSurrender'] = surrender
    parsed = analyze_match(record['match'], None, DEMO_PUUID, 'synthetic')
    assert parsed['control_wards_placed'] == expected_wards
    assert parsed['surrendered'] is expected_surrender


def test_payload_deduplicates_matches_before_summary_profiles_and_comparisons(monkeypatch, tmp_path):
    monkeypatch.setenv('MODEL_PATH', str(tmp_path / 'not-trained.json'))
    records = demo_records(4)
    data = analysis_payload(DEMO_ACCOUNT, records + [records[0]], 'kr', 'demo')
    assert len(data['matches']) == data['summary']['games'] == data['profile']['games'] == 4
    assert data['profile']['main_role'] == 'MIDDLE'
    assert data['matches'][0]['personal_comparison']['games'] == 3
    assert data['matches'][0]['personal_comparison']['basis'] == 'same_role'
    assert len(data['matches'][0]['insights']) == 4
    assert all(m['control_wards_placed'] is None and m['surrendered'] is None for m in data['matches'])
