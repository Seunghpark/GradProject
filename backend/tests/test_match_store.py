from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
import sqlite3
from unittest.mock import patch

import pytest

from app.demo import demo_records
from app.match_store import MatchStore


def genuine_fixture(index=0):
    # Fictional contents, relabeled only inside isolated tests to exercise collection.
    record = deepcopy(demo_records(index+1)[index])
    record['source'] = 'riot'
    match_id = f'KR_{1000+index}'
    record['match']['metadata']['matchId'] = match_id
    record['timeline']['metadata']['matchId'] = match_id
    return record


def test_ingestion_is_persistent_deduplicated_and_keeps_raw_source_provenance(tmp_path):
    path = tmp_path/'matches.sqlite3'
    store = MatchStore(path)
    record = genuine_fixture()
    assert store.ingest([record, record]) == {'added':1,'upgraded':0,'duplicates':1,'skipped':0}
    assert store.stats()['unique_matches'] == 1 and store.stats()['revision'] == 1
    store.refresh()
    first = store.view()
    assert first['catalog']['unique_matches'] == first['benchmarks']['unique_matches'] == 1
    assert first['catalog']['source'] == first['benchmarks']['source'] == 'riot'
    assert first['aggregates_current'] and not store.refresh()
    store.close()
    store = MatchStore(path)
    assert store.get('KR_1000') == record
    assert store.stats()['revision'] == 1 and store.stats()['aggregates_current']
    store.close()


def test_synthetic_bad_match_and_nonfinite_records_never_enter_shared_data():
    valid = genuine_fixture()
    wrong_id = deepcopy(valid)
    wrong_id['match']['metadata']['matchId'] = 'DEMO_0001'
    broken = deepcopy(valid)
    broken['match']['info']['queueId'] = 450
    nonfinite = deepcopy(valid)
    nonfinite['match']['info']['participants'][0]['goldEarned'] = float('nan')
    store = MatchStore(':memory:')
    assert store.ingest([None, demo_records(1)[0], wrong_id, broken, nonfinite])['skipped'] == 5
    assert store.stats()['unique_matches'] == 0
    store.close()


def test_missing_timeline_can_be_upgraded_without_duplicate_or_later_downgrade():
    full = genuine_fixture()
    missing = {**full, 'timeline': None}
    store = MatchStore(':memory:')
    assert store.ingest([missing])['added'] == 1
    assert store.ingest([full])['upgraded'] == 1
    assert store.ingest([missing])['duplicates'] == 1
    assert store.stats()['unique_matches'] == 1 and store.stats()['revision'] == 2
    assert store.get('KR_1000')['timeline'] == full['timeline']
    store.close()


def test_mismatched_timeline_is_not_saved_as_valid_early_evidence():
    record = genuine_fixture()
    record['timeline']['metadata'] = {'matchId':'KR_other'}
    store = MatchStore(':memory:')
    store.ingest([record])
    assert store.get('KR_1000')['timeline'] is None
    store.close()


def test_seed_import_does_not_rewrite_original_and_skips_unchanged_source(tmp_path):
    source = tmp_path/'original.jsonl'
    record = genuine_fixture()
    source.write_text(json.dumps(record)+'\n',encoding='utf-8')
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    store = MatchStore(tmp_path/'matches.sqlite3')
    assert store.seed(source)['added'] == 1
    assert store.seed(source)['status'] == 'unchanged'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    with source.open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(genuine_fixture(1))+'\n')
    assert store.seed(source)['added'] == 1
    assert store.stats()['unique_matches'] == 2
    store.close()


def test_corrupt_seed_line_rolls_back_new_import_and_preserves_existing_data(tmp_path):
    store = MatchStore(':memory:')
    store.ingest([genuine_fixture()])
    source = tmp_path/'bad.jsonl'
    source.write_text(json.dumps(genuine_fixture(1))+'\n{broken\n',encoding='utf-8')
    with pytest.raises(ValueError):
        store.seed(source)
    assert store.stats()['unique_matches'] == 1
    assert store.get('KR_1000') is not None and store.get('KR_1001') is None
    store.close()


def test_aggregate_build_failure_preserves_previous_complete_snapshot_and_new_raw_records():
    store = MatchStore(':memory:')
    store.ingest([genuine_fixture()])
    store.refresh()
    before = store.view()
    store.ingest([genuine_fixture(1)])
    with patch('app.match_store.build_benchmarks',side_effect=ValueError('Build failed')):
        with pytest.raises(ValueError):
            store.refresh()
    after = store.view()
    assert after['catalog'] == before['catalog'] and after['benchmarks'] == before['benchmarks']
    assert after['unique_matches'] == 2 and not after['aggregates_current']
    assert store.refresh() and store.view()['aggregates_current']
    store.close()


def test_two_snapshot_writes_are_transactional_when_second_write_fails():
    store = MatchStore(':memory:')
    store.ingest([genuine_fixture()])
    store.refresh()
    before = store.view()
    store.ingest([genuine_fixture(1)])
    store.db.execute("""CREATE TRIGGER stop_benchmark BEFORE INSERT ON native_snapshots
        WHEN NEW.name='benchmarks' BEGIN SELECT RAISE(ABORT,'Test failure'); END""")
    with pytest.raises(sqlite3.Error):
        store.refresh()
    assert store.view()['catalog'] == before['catalog']
    assert store.view()['benchmarks'] == before['benchmarks']
    store.close()


def test_concurrent_repeated_ingestion_has_one_record_and_one_revision():
    store = MatchStore(':memory:')
    record = genuine_fixture()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _:store.ingest([record]),range(12)))
    assert sum(result['added'] for result in results) == 1
    assert store.stats()['unique_matches'] == 1 and store.stats()['revision'] == 1
    store.close()
