"""Collector tests use mocked upstream data; no Riot network calls occur."""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest

from app.config import Settings
from scripts.generate_synthetic_training import generate_records

SPEC = importlib.util.spec_from_file_location(
    "collect_matches_under_test", Path(__file__).resolve().parents[1] / "scripts" / "collect_matches.py")
collector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(collector)


def immediate(coroutine):
    with pytest.raises(StopIteration) as completed:
        coroutine.send(None)
    return completed.value.value


def test_collector_deduplicates_appends_raw_pair_and_closes_resources(tmp_path, monkeypatch):
    existing, new = generate_records(2)
    existing["source"] = "riot"  # Mocked collection fixture, not empirical data.
    output = tmp_path / "matches.jsonl"
    output.write_text(json.dumps(existing) + "\n", encoding="utf-8")
    old_id = existing["match"]["metadata"]["matchId"]
    new_id = new["match"]["metadata"]["matchId"]
    settings = Settings(riot_api_key="mock-key", cache_path=str(tmp_path / "cache.sqlite3"))
    monkeypatch.setattr(collector.Settings, "from_env", classmethod(lambda cls: settings))
    cache = Mock()
    client = SimpleNamespace(
        account=AsyncMock(return_value=({"puuid": "mock-puuid"}, False)),
        match_ids=AsyncMock(return_value=([old_id, new_id, new_id], False)),
        match=AsyncMock(return_value=(new["match"], False)),
        timeline=AsyncMock(return_value=(new["timeline"], False)),
        close=AsyncMock())
    monkeypatch.setattr(collector, "Cache", Mock(return_value=cache))
    monkeypatch.setattr(collector, "RiotClient", Mock(return_value=client))
    args = SimpleNamespace(output=output, riot_id=["TestPlayer#KR1"], platform="kr", count=10)
    asyncio.run(collector.collect(args))
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert rows[0] == existing
    assert rows[1] == {"source": "riot", "match": new["match"], "timeline": new["timeline"]}
    client.match.assert_awaited_once_with("kr", new_id)
    client.timeline.assert_awaited_once_with("kr", new_id)
    client.close.assert_awaited_once()
    cache.close.assert_called_once()


def test_missing_key_does_not_create_output_or_resources(tmp_path, monkeypatch):
    monkeypatch.setattr(collector.Settings, "from_env", classmethod(lambda cls: Settings(riot_api_key="")))
    cache_factory, client_factory = Mock(), Mock()
    monkeypatch.setattr(collector, "Cache", cache_factory)
    monkeypatch.setattr(collector, "RiotClient", client_factory)
    output = tmp_path / "not-created" / "matches.jsonl"
    args = SimpleNamespace(output=output, riot_id=["TestPlayer#KR1"], platform="kr", count=10)
    with pytest.raises(SystemExit, match="RIOT_API_KEY"):
        asyncio.run(collector.collect(args))
    assert not output.exists()
    assert not output.parent.exists()
    cache_factory.assert_not_called()
    client_factory.assert_not_called()


@pytest.mark.parametrize('last_page', ['short', 'empty'])
def test_collector_pages_from_offset_deduplicates_and_stops(tmp_path, monkeypatch, last_page):
    records = generate_records(3)
    output = tmp_path / 'matches.jsonl'
    output.write_text(json.dumps(records[0]) + '\n', encoding='utf-8')
    ids = [record['match']['metadata']['matchId'] for record in records]
    pages = [[ids[0], ids[1]], [ids[1], ids[2]]] if last_page == 'empty' else [[ids[0], ids[1]], [ids[2]]]
    if last_page == 'empty':
        pages.append([])
    settings = Settings(riot_api_key='mock-key')
    monkeypatch.setattr(collector.Settings, 'from_env', classmethod(lambda cls: settings))
    cache = Mock()
    by_id = dict(zip(ids, records))
    client = SimpleNamespace(
        account=AsyncMock(return_value=({'puuid': 'mock-puuid'}, False)),
        match_ids=AsyncMock(side_effect=[(page, False) for page in pages]),
        match=AsyncMock(side_effect=lambda platform, match_id: (by_id[match_id]['match'], False)),
        timeline=AsyncMock(side_effect=lambda platform, match_id: (by_id[match_id]['timeline'], False)),
        close=AsyncMock())
    monkeypatch.setattr(collector, 'Cache', Mock(return_value=cache))
    monkeypatch.setattr(collector, 'RiotClient', Mock(return_value=client))
    args = SimpleNamespace(output=output, riot_id=['TestPlayer#KR1'], platform='kr', count=2, start=40, pages=5)

    immediate(collector.collect(args))

    saved = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
    assert saved[0] == records[0]
    assert [record['match']['metadata']['matchId'] for record in saved] == ids
    assert client.match_ids.await_args_list == [
        call('kr', 'mock-puuid', 2, start=40 + page * 2) for page in range(len(pages))]
    assert client.match.await_count == client.timeline.await_count == 2
    client.close.assert_awaited_once()
    cache.close.assert_called_once()


@pytest.mark.parametrize('options', [
    ['--start', '-1'], ['--start', '10001'], ['--start', '1.5'],
    ['--pages', '0'], ['--pages', '21'], ['--pages', '1.5'],
    ['--start', '10000', '--pages', '2'],
])
def test_invalid_paging_cli_rejected_before_collection(monkeypatch, options):
    runner = Mock()
    monkeypatch.setattr(collector.asyncio, 'run', runner)
    monkeypatch.setattr(collector.sys, 'argv', ['collect_matches.py', '--riot-id', 'Test#KR1', *options])
    with pytest.raises(SystemExit) as error:
        collector.main()
    assert error.value.code == 2
    runner.assert_not_called()


def test_later_page_failure_preserves_existing_and_completed_records(tmp_path, monkeypatch):
    existing, new = generate_records(2)
    output = tmp_path / 'matches.jsonl'
    original = json.dumps(existing) + '\n'
    output.write_text(original, encoding='utf-8')
    settings = Settings(riot_api_key='mock-key')
    monkeypatch.setattr(collector.Settings, 'from_env', classmethod(lambda cls: settings))
    cache = Mock()
    client = SimpleNamespace(
        account=AsyncMock(return_value=({'puuid': 'mock-puuid'}, False)),
        match_ids=AsyncMock(side_effect=[([new['match']['metadata']['matchId']], False),
                                        collector.RiotError('rate_limited', 'Retry later', 429, 60)]),
        match=AsyncMock(return_value=(new['match'], False)),
        timeline=AsyncMock(return_value=(new['timeline'], False)),
        close=AsyncMock())
    monkeypatch.setattr(collector, 'Cache', Mock(return_value=cache))
    monkeypatch.setattr(collector, 'RiotClient', Mock(return_value=client))
    args = SimpleNamespace(output=output, riot_id=['Test#KR1'], platform='kr', count=1, pages=2)

    with pytest.raises(SystemExit, match='Existing records are preserved'):
        immediate(collector.collect(args))

    contents = output.read_text(encoding='utf-8')
    assert contents.startswith(original)
    assert len(contents.splitlines()) == 2
    assert json.loads(contents.splitlines()[1])['match'] == new['match']
    client.close.assert_awaited_once()
    cache.close.assert_called_once()


@pytest.mark.parametrize('ids', [{'bad':'shape'}, [None], ['one','two']])
def test_bad_history_page_never_triggers_unbounded_or_invalid_match_fetches(tmp_path, monkeypatch, ids):
    settings = Settings(riot_api_key='mock-key')
    monkeypatch.setattr(collector.Settings,'from_env',classmethod(lambda cls:settings))
    cache = Mock()
    client = SimpleNamespace(account=AsyncMock(return_value=({'puuid':'mock'},False)),
        match_ids=AsyncMock(return_value=(ids,False)),match=AsyncMock(),timeline=AsyncMock(),close=AsyncMock())
    monkeypatch.setattr(collector,'Cache',Mock(return_value=cache))
    monkeypatch.setattr(collector,'RiotClient',Mock(return_value=client))
    output = tmp_path/'matches.jsonl'
    with pytest.raises(SystemExit,match='invalid history page'):
        immediate(collector.collect(SimpleNamespace(output=output,riot_id=['Test#KR1'],platform='kr',count=1)))
    client.match.assert_not_called()
    assert output.read_bytes() == b''
    client.close.assert_awaited_once()


def test_mismatched_returned_match_does_not_enter_dataset(tmp_path, monkeypatch):
    row = generate_records(1)[0]
    monkeypatch.setattr(collector.Settings,'from_env',classmethod(lambda cls:Settings(riot_api_key='mock')))
    cache = Mock()
    client = SimpleNamespace(account=AsyncMock(return_value=({'puuid':'mock'},False)),
        match_ids=AsyncMock(return_value=(['KR_wrong'],False)),match=AsyncMock(return_value=(row['match'],False)),
        timeline=AsyncMock(return_value=(row['timeline'],False)),close=AsyncMock())
    monkeypatch.setattr(collector,'Cache',Mock(return_value=cache))
    monkeypatch.setattr(collector,'RiotClient',Mock(return_value=client))
    output = tmp_path/'matches.jsonl'
    with pytest.raises(SystemExit,match='did not match'):
        immediate(collector.collect(SimpleNamespace(output=output,riot_id=['Test#KR1'],platform='kr',count=1)))
    assert output.read_bytes() == b''
    client.close.assert_awaited_once()
