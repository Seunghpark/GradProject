from copy import deepcopy

import pytest

from app.demo import DEMO_PUUID, demo_records
from app.analytics import analyze_match
from app.loadout_timeline import loadout_histories
from app.native_catalog import build_catalog


def fixture(events):
    record = demo_records(1)[0]
    for frame in record['timeline']['info']['frames']:
        frame['events'] = []
    record['timeline']['info']['frames'][0]['events'] = events
    return record


def item(kind, item_id=1001, stamp=100, **extra):
    return {'type': kind, 'itemId': item_id, 'timestamp': stamp, 'participantId': 3, **extra}


def history(record):
    return loadout_histories(record['match'], record['timeline'])[3]


def test_ordered_purchases_preserve_components_sales_and_consumption_but_cancel_a_known_undo():
    record = fixture([item('ITEM_PURCHASED'), item('ITEM_DESTROYED', stamp=200),
        item('ITEM_PURCHASED', 3020, 200), item('ITEM_UNDO', stamp=300, beforeId=3020, afterId=0),
        item('ITEM_PURCHASED', 3157, 400), item('ITEM_SOLD', 3157, 500)])
    result = history(record)
    assert result['status'] == 'available' and result['purchase_aggregate_eligible']
    assert [entry['item_id'] for entry in result['purchases']] == [1001, 3157]
    assert result['item_events'][2]['undone'] and result['item_events'][3]['reverses'] == 2
    assert not result['item_events'][5]['undone']


def test_sale_undo_and_multiple_identical_purchases_are_not_invented_duplicates():
    event = item('ITEM_PURCHASED', 2003)
    record = fixture([event, deepcopy(event), item('ITEM_SOLD', 2003, 200),
        item('ITEM_UNDO', stamp=300, beforeId=0, afterId=2003)])
    result = history(record)
    assert len(result['purchases']) == 2
    assert result['item_events'][2]['undone'] and result['unresolved_undos'] == 0
    record['timeline']['info']['frames'].append(deepcopy(record['timeline']['info']['frames'][0]))
    assert history(record) == result


@pytest.mark.parametrize('before,after', [(0, 0), (9999, 0), (True, 0), (1001, 2003)])
def test_unresolved_undo_stays_visible_and_cannot_create_trusted_build_aggregates(before, after):
    result = history(fixture([item('ITEM_PURCHASED'), item('ITEM_UNDO', stamp=200, beforeId=before, afterId=after)]))
    assert result['unresolved_undos'] == 1 and result['status'] == 'partial'
    assert not result['purchase_aggregate_eligible']
    assert len(result['purchases']) == 1  # Observed purchase remains visible, with uncertainty.


def test_skills_use_event_order_include_only_normal_levels_and_do_not_guess_missing_events():
    events = [{'type':'SKILL_LEVEL_UP','participantId':3,'timestamp':stamp,'skillSlot':slot,'levelUpType':kind}
              for stamp, slot, kind in [(300,3,'NORMAL'), (100,1,'NORMAL'), (200,2,'EVOLVE'), (400,4,'NORMAL')]]
    result = history(fixture(events))
    assert [entry['ability'] for entry in result['skill_order']] == ['Q','E','R']
    assert result['skill_aggregate_eligible'] and not result['purchase_aggregate_eligible']
    assert history(fixture([]))['skill_order'] == []


def test_invalid_values_and_incomplete_or_mismatched_timelines_never_become_complete_evidence():
    record = fixture([item('ITEM_PURCHASED', True), item('ITEM_PURCHASED', stamp=-1),
                      item('ITEM_PURCHASED', stamp=99999999), item('ITEM_PURCHASED', participantId=True)])
    assert history(record)['invalid_events'] == 3
    record = fixture([item('ITEM_PURCHASED')])
    record['timeline']['info']['frames'] = record['timeline']['info']['frames'][:1]
    assert not history(record)['purchase_aggregate_eligible']
    record['timeline']['metadata'] = {'matchId':'wrong'}
    assert history(record)['status'] == 'unavailable'


def test_analysis_and_catalog_expose_own_observed_orders_and_coverage_without_provider_calls():
    events = [item('ITEM_PURCHASED',1001), item('ITEM_PURCHASED',2003,200),
        {'type':'SKILL_LEVEL_UP','participantId':3,'timestamp':50,'skillSlot':2,'levelUpType':'NORMAL'}]
    record = fixture(events)
    parsed = analyze_match(record['match'], record['timeline'], DEMO_PUUID, 'demo')
    assert parsed['loadout']['skill_order'][0]['ability'] == 'W'
    catalog = build_catalog([record])
    group = next(row for row in catalog['groups'] if row['champion']=='Ahri' and row['role']=='MIDDLE')
    assert group['purchase_order_games'] == 1
    assert group['purchase_sequences'][0] == {'sequence':[1001,2003],'games':1,'frequency':1}
    assert group['skill_orders'][0]['sequence'] == ['W']
    assert catalog['computation_version'] == 2
    ambiguous = fixture([item('ITEM_PURCHASED'),item('ITEM_UNDO',stamp=200,beforeId=0,afterId=0)])
    other = next(row for row in build_catalog([ambiguous])['groups'] if row['champion']=='Ahri' and row['role']=='MIDDLE')
    assert other['purchase_order_games'] == 0 and other['purchase_sequences'] == []
