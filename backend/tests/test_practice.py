from copy import deepcopy
import json

import pytest

from app.demo import DEMO_PUUID, demo_records
from app.match_store import MatchStore
from app.practice import PracticeInput, PracticeTracker


def records(count=3, start=1800000000000):
    result = deepcopy(demo_records(count))
    for index, row in enumerate(result):
        row['source'] = 'riot'
        row['match']['metadata']['matchId'] = f'KR_{100+index}'
        row['match']['info']['gameStartTimestamp'] = start+index*3600000
        next(player for player in row['match']['info']['participants'] if player['puuid']==DEMO_PUUID)['teamPosition'] = 'MIDDLE'
    return result


def test_frozen_baseline_persists_and_only_first_three_later_same_context_games_count(tmp_path):
    now = 1800000000000+4*3600000
    store = MatchStore(tmp_path/'data.sqlite3')
    tracker = PracticeTracker(store)
    before = records()
    target = tracker.create(DEMO_PUUID,PracticeInput(role='MIDDLE',metric='deaths',target=4),before,now)
    assert target['baseline_games'] == 3 and target['future_games'] == []
    later = records(5,now+3600000)
    for index,row in enumerate(later):
        row['match']['metadata']['matchId'] = f'KR_{500+index}'
        next(player for player in row['match']['info']['participants'] if player['puuid']==DEMO_PUUID)['deaths'] = 2
    wrong_patch = deepcopy(later[0])
    wrong_patch['match']['metadata']['matchId'] = 'KR_999'
    wrong_patch['match']['info']['gameVersion'] = '99.1.1'
    store.close()
    store = MatchStore(tmp_path/'data.sqlite3')
    tracker = PracticeTracker(store)
    updated = tracker.list(DEMO_PUUID,before+later+[later[0],wrong_patch])[0]
    assert updated['status'] == 'complete' and len(updated['future_games']) == 3
    assert [row['id'] for row in updated['future_games']] == ['KR_500','KR_501','KR_502']
    assert updated['followup_average'] == 2 and all(row['met'] for row in updated['future_games'])
    assert updated['baseline_average'] == target['baseline_average']
    assert updated['observed_change'] == 2-target['baseline_average']
    assert tracker.list('another-player',before+later) == []
    assert not tracker.delete('another-player',target['id'])
    assert tracker.delete(DEMO_PUUID,target['id']) and tracker.list(DEMO_PUUID,before) == []
    assert DEMO_PUUID not in json.dumps(updated)
    store.close()


@pytest.mark.parametrize('target', [True, -1, '6', float('nan'), float('inf')])
def test_invalid_practice_targets_are_rejected(target):
    with pytest.raises(ValueError):
        PracticeInput(role='MIDDLE',metric='cs_per_min',target=target)


def test_baseline_requires_three_completed_prior_games_and_never_accepts_synthetic_or_future_data():
    store = MatchStore(':memory:')
    tracker = PracticeTracker(store)
    value = PracticeInput(role='MIDDLE',metric='cs_per_min',target=6)
    for data in (records(2),demo_records(10),records(3,1900000000000)):
        with pytest.raises(ValueError,match='three earlier'):
            tracker.create(DEMO_PUUID,value,data,1800000000000+4*3600000)
    with pytest.raises(ValueError,match='supported metric range'):
        tracker.create(DEMO_PUUID,PracticeInput(role='MIDDLE',metric='kill_participation',target=101),records())
    store.close()
