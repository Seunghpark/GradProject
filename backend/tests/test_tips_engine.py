from copy import deepcopy
from unittest.mock import patch
import json

import pytest

from app.demo import demo_records
from app.tips_engine import build_benchmarks, config, generate_tips, identity, metrics, percentile, verified_tier


def games():
    return [{'id': f'loaded-{index}', 'played_at': f'2026-10-{28-index:02d}T12:00:00+00:00',
             'role': 'MIDDLE', 'champion': 'Ahri', 'patch': '16.21.1', 'queue_id': 420,
             'cs_per_min': 4, 'kill_participation': .2, 'vision_score': 10, 'duration_minutes': 30}
            for index in range(3)]


def benchmarks(count=40, values=None):
    return {'source': 'riot', 'rows': [{'match_id': f'reference-{index}', 'player_hash': f'other-{index}',
             'role': 'MIDDLE', 'champion': 'Zed', 'patch': '16.21', 'queue_id': 420,
             'tier': None, 'values': values or {'cs_per_min': 6}}
            for index in range(count)]}


def tips(matches=None, reference=None, **kwargs):
    return generate_tips(matches or games(), reference or benchmarks(), 'MIDDLE', 'my-private-puuid', 'riot', **kwargs)


def test_priority_is_exact_gap_times_normalized_equal_weight_times_consistency():
    result = tips()
    assert result['status'] == 'available' and result['weighting'] == 'equal_descriptive'
    item = result['tips'][0]
    assert item['actual'] == 4 and item['benchmark'] == 6 and item['percentile'] == 0
    assert item['gap'] == .5 and item['impact_weight'] == 1 and item['consistency'] == 1
    assert item['priority'] == .5
    assert item['reference_matches'] == 40 and item['below_games'] == 3


def test_equal_weights_normalize_over_usable_metrics_and_top_three_are_deterministic():
    result = tips(reference=benchmarks(values={'cs_per_min': 6, 'kill_participation': 50, 'vision_per_min': 1}))
    assert len(result['tips']) == 3
    assert sum(item['impact_weight'] for item in result['tips']) == pytest.approx(1)
    assert all(item['priority'] == pytest.approx(.5/3) for item in result['tips'])
    assert result['strength'] is None


def test_tie_midranks_reverse_lower_is_better_and_do_not_invent_a_weakness():
    assert percentile(6, [4, 6, 6, 8], True) == 50
    assert percentile(1, [2, 3, 4], False) == 100
    matches = games()
    for match in matches:
        match['cs_per_min'] = 6
    result = tips(matches)
    assert result['tips'] == [] and result['strength']['percentile'] == 50


def test_recent_consistency_weights_new_games_more_than_old_games():
    matches = games()
    matches[1]['cs_per_min'] = matches[2]['cs_per_min'] = 6
    result = tips(matches)
    assert result['tips'][0]['consistency'] == pytest.approx(1 / (1+.85+.85**2))
    assert result['tips'][0]['below_games'] == 1


def test_minimum_is_unique_reference_games_not_rows_and_missing_metrics_are_gaps():
    reference = benchmarks(29)
    reference['rows'] += deepcopy(reference['rows'])
    assert tips(reference=reference)['status'] == 'insufficient_data'
    reference = benchmarks(values={'damage_share': None})
    assert tips(reference=reference)['tips'] == []
    assert tips(games()[:2])['status'] == 'insufficient_data'


def test_reference_requires_multiple_players_and_reports_metric_coverage_without_claiming_certainty():
    reference = benchmarks(40)
    for row in reference['rows']:
        row['player_hash'] = 'one-repeated-player'
    assert tips(reference=reference)['status'] == 'insufficient_data'
    result = tips()
    assert result['minimum_reference_players'] == 10
    assert result['tips'][0]['reference_players'] == 40
    assert result['tips'][0]['metric_coverage'] == 1


def test_self_rows_loaded_games_patch_queue_and_role_are_excluded():
    reference = benchmarks(29)
    extra = deepcopy(reference['rows'][0])
    for changes in [{'match_id': 'loaded-0'}, {'player_hash': identity('my-private-puuid')},
                    {'patch': '16.20'}, {'queue_id': 440}, {'role': 'UTILITY'}]:
        reference['rows'].append({**extra, 'match_id': str(changes), **changes})
    assert tips(reference=reference)['status'] == 'insufficient_data'


def test_champion_specific_cohort_requires_fifty_unique_games_and_all_reviewed_games_match():
    reference = benchmarks(60)
    for row in reference['rows']:
        row['champion'] = 'Ahri'
    assert tips(reference=reference)['champion'] == 'Ahri'
    reference = benchmarks(40)
    for row in reference['rows']:
        row['champion'] = 'Ahri'
    assert tips(reference=reference)['champion'] is None
    matches = games()
    matches[0]['champion'] = 'Sylas'
    assert tips(matches, reference)['champion'] is None


def test_tier_mode_is_unavailable_without_evidence_and_works_only_for_selected_tier():
    assert tips(scope='role_tier')['status'] == 'tier_unavailable'
    assert tips(scope='role_tier', tier='GOLD')['status'] == 'tier_unavailable'
    reference = benchmarks()
    for row in reference['rows']:
        row['tier'] = 'GOLD'
    result = tips(reference=reference, scope='role_tier', tier='GOLD')
    assert result['status'] == 'available' and result['tier_status'] == 'available'
    assert tips(reference=reference, scope='role_tier', tier='SILVER')['status'] == 'tier_unavailable'
    assert generate_tips(games(), reference, 'MIDDLE', 'me', 'synthetic')['status'] == 'benchmark_unavailable'


def test_rank_observation_must_precede_match_be_fresh_and_match_queue_platform_and_source():
    record = demo_records(1)[0]
    match = record['match']
    match['metadata']['matchId'] = 'KR_123'
    player = match['info']['participants'][2]
    start = match['info']['gameStartTimestamp']
    observation = {'source': 'riot_rank_at_enrollment', 'puuid': player['puuid'], 'tier': 'GOLD',
                   'platform': 'kr', 'queue': 'RANKED_SOLO_5x5', 'observed_at_ms': start-1000}
    assert verified_tier(player, match, [observation], config()) == 'GOLD'
    for changes in [{'observed_at_ms': start+1}, {'observed_at_ms': start-31*86400000},
                    {'source': 'current_rank_guess'}, {'queue': 'RANKED_FLEX_SR'},
                    {'platform': 'na1'}, {'tier': 'UNKNOWN'}, {'puuid': 'different'}]:
        assert verified_tier(player, match, [{**observation, **changes}], config()) is None


def test_benchmark_builder_preserves_provenance_deduplicates_and_never_exports_names_or_puuids():
    record = demo_records(1)[0]
    result = build_benchmarks([record, deepcopy(record)])
    assert result['source'] == 'synthetic' and result['unique_matches'] == 1 and len(result['rows']) == 10
    assert all(row['tier'] is None for row in result['rows'])
    output = json.dumps(result, allow_nan=False)
    assert 'synthetic-demo-player' not in output and 'Example' not in output
    with pytest.raises(ValueError, match='mix'):
        build_benchmarks([record, {**record, 'source': 'riot'}])


def test_short_matches_do_not_imply_complete_early_death_or_objective_observations():
    match = {**games()[0], 'duration_minutes': 11, 'native': {'deaths_before_14': 0, 'objective_credits': {'recorded': 0, 'team_objectives': 0}}}
    result = metrics(match)
    assert result['deaths_before_14'] is None
    assert result['objective_participation'] is None
