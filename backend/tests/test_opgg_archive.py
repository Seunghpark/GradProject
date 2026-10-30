from copy import deepcopy
import json
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.cache import Cache
from app.config import Settings
from app.main import create_app
from app.opgg_archive import PROFILE_FIELDS, PROFILE_TOOL, _data, rank_archive
from app.providers import ProviderClient
from app.rank_history import RankHistory

STAMP = '2026-10-30T07:00:00+00:00'
TEXT = '''class Response: data
class Data: summoner
class Summoner: game_name,tagline,region,previous_season_tiers
class Season: season_id,rank_entries
class Entry: game_type,rank_info,high_rank_info
class Rank: tier,division,lp,created_at
Response(Data(Summoner("Example","TEST",null,[Season(31,[Entry("SOLORANKED",Rank("SILVER",3,38,"2026-01-08T01:49:49+09:00"),Rank("SILVER",3,18,"2025-01-18T22:33:24+09:00")),Entry("FLEXRANKED",null,null)]),Season(27,[Entry("FLEXRANKED",Rank("BRONZE",1,73,"2024-09-25T01:55:38+09:00"),null)])])))'''


def payload(text=TEXT):
    return {'text': text, 'data': None, 'fetched_at': STAMP, 'cached': False}


def test_real_provider_format_normalizes_seasons_queues_tiers_and_preserves_peak_as_separate_unverified_data():
    result = rank_archive(payload(), 'Example', 'TEST', 'KR')
    assert result['provider'] == 'OP.GG' and result['source'] == 'opgg_archive'
    assert result['fetched_at'] == STAMP and result['independently_validated'] is False
    assert len(result['entries']) == 2
    latest = result['latest_solo']
    assert latest['season_id'] == 31 and latest['rank']['division'] == 'III'
    assert latest['rank']['league_points'] == 38
    assert latest['provider_reported_peak']['league_points'] == 18
    assert latest['rank']['provider_recorded_at'] == '2026-01-07T16:49:49+00:00'
    assert result['latest_flex']['rank']['division'] == 'I'
    assert 'no calendar years are inferred' in result['notice']
    assert not any('elo' in row['rank'] for row in result['entries'])


@pytest.mark.parametrize('text', [
    '__import__("os").system("echo unsafe")',
    'class X: value\nX((lambda: 1)())',
    'class X: value\nX([value for value in []])',
    'class X: value\nX(1e999)',
    'class X: value\nX(value=1)',
    'class X: value\nX(1,2)',
    'class X: value\nclass X: other\nX(1)',
    '{"value": NaN}',
    'class X: value\n'+('X('*45)+'1'+(')'*45),
])
def test_provider_constructor_text_is_data_only_never_executable(text):
    with pytest.raises(ValueError):
        _data(text)


def test_json_payload_is_supported_but_wrong_identity_unclassified_queues_and_malformed_ranks_are_not_invented():
    parsed = _data(TEXT)
    result = rank_archive(payload(json.dumps(parsed)), 'example', 'test', 'KR')
    assert result['status'] == 'available'
    for name, tag, region in [('other', 'TEST', 'KR'), ('Example', 'other', 'KR')]:
        with pytest.raises(ValueError, match='identity'):
            rank_archive(payload(), name, tag, region)
    changed = deepcopy(parsed)
    summoner = changed['data']['summoner']
    summoner['region'] = 'NA'
    with pytest.raises(ValueError):
        rank_archive({**payload(), 'data': changed}, 'Example', 'TEST', 'KR')
    summoner['region'] = 'KR'
    entries = summoner['previous_season_tiers'][0]['rank_entries']
    entries[0]['rank_info']['division'] = True
    summoner['previous_season_tiers'][1]['rank_entries'][0]['game_type'] = 'UNKNOWN'
    result = rank_archive({**payload(), 'data': changed}, 'Example', 'TEST', 'KR')
    assert result['status'] == 'no_history' and result['latest_solo'] is None


def test_conflicting_duplicate_season_queue_and_missing_fetch_date_are_rejected():
    data = _data(TEXT)
    seasons = data['data']['summoner']['previous_season_tiers']
    duplicate = deepcopy(seasons[0])
    duplicate['rank_entries'][0]['rank_info']['tier'] = 'GOLD'
    seasons.append(duplicate)
    result = rank_archive({**payload(), 'data': data}, 'Example', 'TEST', 'KR')
    assert result['latest_solo'] is None and result['latest_flex'] is not None
    with pytest.raises(ValueError, match='fetch time'):
        rank_archive({**payload(), 'fetched_at': None}, 'Example', 'TEST', 'KR')


def test_provider_profile_access_is_narrow_and_generic_tool_allowlist_is_not_expanded():
    calls = []
    def handler(request):
        calls.append(request)
        assert request.url.host == 'mcp-api.op.gg' and 'X-Riot-Token' not in request.headers
        body = json.loads(request.content)
        assert body['params']['name'] == PROFILE_TOOL
        assert body['params']['arguments']['desired_output_fields'] == PROFILE_FIELDS
        return httpx.Response(200, json={'jsonrpc': '2.0', 'id': 1001, 'result': {'content': [{'type': 'text', 'text': TEXT}]}})
    inputs = {'required': ['game_name','tag_line','region','desired_output_fields'],
              'properties': {name: {} for name in ('game_name','tag_line','region','lang','desired_output_fields')}}
    schema = {'fetched_at': STAMP, 'tools': [{'name': PROFILE_TOOL, 'inputSchema': inputs}]}
    cache = Cache(':memory:')
    client = ProviderClient(cache, httpx.MockTransport(handler))
    with patch('app.providers.discover', return_value=(schema, {})):
        first = client.rank_history('Example', 'TEST')
        second = client.rank_history('Example', 'TEST')
        assert not first['cached'] and second['cached'] and first['fetched_at'] == second['fetched_at']
        with pytest.raises(ValueError):
            client.call(PROFILE_TOOL, {})
        assert client.schemas()['tools'] == []
    assert len(calls) == 1
    client.close()
    cache.close()


def request(app, host='127.0.0.1'):
    return Request({'type':'http','method':'GET','scheme':'http','path':'/api/providers/opgg/rank-history',
        'server':(host,8000),'client':('127.0.0.1',12345),'query_string':b'', 'app':app,
        'headers':[(b'host',f'{host}:8000'.encode()),(b'origin',b'http://127.0.0.1:8000'),(b'x-lolai-local',b'1')]})


def immediate(coroutine):
    with pytest.raises(StopIteration) as result:
        coroutine.send(None)
    return result.value.value


def test_optional_archive_endpoint_validates_input_and_persists_fallback_without_relabeling_fetch_time(tmp_path):
    archive = rank_archive(payload(), 'Example', 'TEST', 'KR')
    class Provider:
        fail = False
        def rank_history(self, name, tag, region):
            assert (name,tag,region) == ('Example','TEST','KR')
            if self.fail:
                raise ValueError('Provider unavailable')
            return archive
    async def inline(function, *args):
        return function(*args)
    app = create_app(Settings(cache_path=':memory:'))
    app.state.rank_history = RankHistory(tmp_path / 'ranks.sqlite3')
    app.state.providers = Provider()
    routes = {route.path:route.endpoint for route in app.routes}
    endpoint = routes['/api/providers/opgg/rank-history']
    assert list(routes).index('/api/providers/opgg/rank-history') < list(routes).index('/{path:path}')
    with patch('starlette.concurrency.run_in_threadpool', inline):
        result = immediate(endpoint(request(app), ' Example ', ' TEST ', 'KR'))
        assert result['storage_status'] == 'saved' and result['served_from'] == 'provider'
        app.state.providers.fail = True
        saved = immediate(endpoint(request(app), 'Example', 'TEST', 'kr'))
        assert saved['served_from'] == 'saved_archive' and saved['fetched_at'] == STAMP and saved['cached']
        for name, tag, platform in [('', 'TEST', 'kr'), ('Example#x','TEST','kr'), ('Example','TEST','na1')]:
            with pytest.raises(HTTPException) as error:
                immediate(endpoint(request(app), name, tag, platform))
            assert error.value.status_code == 422
        with pytest.raises(HTTPException) as error:
            immediate(endpoint(request(app, 'evil.example'), 'Example','TEST','kr'))
        assert error.value.status_code == 403
    assert app.state.rank_history.observe('kr','some-puuid',[],cached=True)['recorded_checks'] == 0
    app.state.rank_history.close()
