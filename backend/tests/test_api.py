"""Integration tests exercise actual API routing with mocked upstream HTTP."""
import asyncio
import copy
import json
import time

import httpx
from fastapi.testclient import TestClient
import pytest

from app.cache import Cache
from app.config import Settings
from app.demo import DEMO_PUUID, demo_records
from app.main import create_app
from app.riot import RiotClient, RiotError


@pytest.fixture
def settings(tmp_path):
    return Settings(cache_path=str(tmp_path / 'cache.sqlite3'), request_interval=0)


def test_health_and_demo_work_without_key(settings):
    with TestClient(create_app(settings)) as client:
        health = client.get('/api/health').json()
        assert health['status'] == 'ok'
        assert health['riot_configured'] is False
        response = client.get('/api/analysis', params={'mode': 'demo', 'count': 4})
        assert response.status_code == 200
        data = response.json()
        assert data['source'] == 'demo'
        assert data['player']['game_name'] == 'DemoPlayer'
        assert data['summary']['games'] == 4
        assert 0 <= data['summary']['win_rate'] <= 1
        assert 0 <= data['summary']['kill_participation'] <= 1
        assert len(data['matches'][0]['timeline']) > 10
        assert 'Synthetic' in data['warning']
        assert response.headers['cache-control'] == 'no-store'


def test_auto_fallback_does_not_impersonate_requested_player(settings):
    with TestClient(create_app(settings)) as client:
        data = client.get('/api/analysis', params={'game_name': 'ActualName', 'tag_line': 'REAL', 'mode': 'auto'}).json()
        assert data['source'] == 'demo'
        assert data['player']['game_name'] == 'DemoPlayer'
        assert data['requested_player']['game_name'] == 'ActualName'
        assert 'RIOT_API_KEY' in data['warning']


def test_live_without_key_is_an_actionable_error(settings):
    with TestClient(create_app(settings)) as client:
        response = client.get('/api/analysis', params={'mode': 'live'})
        assert response.status_code == 503
        assert response.json()['detail']['code'] == 'missing_key'


@pytest.mark.parametrize('params', [{'platform': 'attacker.example'}, {'count': 21}, {'count': 0}, {'game_name': '   '}, {'tag_line': 'bad#tag'}, {'mode': 'unknown'}])
def test_invalid_requests_are_rejected(settings, params):
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/analysis', params=params).status_code == 422


def test_upstream_not_found_never_silently_returns_demo(tmp_path):
    transport = httpx.MockTransport(lambda request: httpx.Response(404, text='<not json>'))
    settings = Settings(riot_api_key='secret-test-key', cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=transport)) as client:
        response = client.get('/api/analysis', params={'mode': 'auto'})
        assert response.status_code == 404
        assert response.json()['detail']['code'] == 'not_found'
        assert 'secret-test-key' not in response.text


def test_live_flow_and_persistent_cache_never_expose_key(tmp_path):
    calls = []
    record = demo_records(1)[0]
    secret = 'secret-only-in-request-header'
    def handler(request):
        calls.append(request)
        assert request.headers['X-Riot-Token'] == secret
        assert secret not in str(request.url)
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': DEMO_PUUID, 'gameName': 'VerifiedPlayer', 'tagLine': 'KR1'})
        if request.url.path.endswith('/ids'):
            assert request.url.params['type'] == 'ranked'
            return httpx.Response(200, json=['KR_1234'])
        if request.url.path.endswith('/timeline'):
            return httpx.Response(200, json=record['timeline'])
        match = copy.deepcopy(record['match'])
        match['metadata']['matchId'] = 'KR_1234'
        return httpx.Response(200, json=match)
    settings = Settings(riot_api_key=secret, cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        first = client.get('/api/analysis', params={'game_name': 'VerifiedPlayer', 'tag_line': 'KR1', 'mode': 'live', 'count': 1})
        assert first.status_code == 200, first.text
        assert first.json()['source'] == 'live'
        assert first.json()['player']['game_name'] == 'VerifiedPlayer'
        assert len(calls) == 4
        second = client.get('/api/analysis', params={'game_name': 'VerifiedPlayer', 'tag_line': 'KR1', 'mode': 'live', 'count': 1})
        assert second.json()['source'] == 'cache'
        assert len(calls) == 4
        assert secret not in first.text + second.text
    raw = (tmp_path / 'db').read_bytes()
    assert secret.encode() not in raw


def test_sea_account_and_match_routes_are_separate(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json={'puuid': 'p'} if '/accounts/' in request.url.path else [])
    async def run():
        cache = Cache(str(tmp_path / 'db'))
        riot = RiotClient(Settings(riot_api_key='test', request_interval=0), cache, httpx.MockTransport(handler))
        await riot.account('oc1', 'Space Name', 'OCE')
        await riot.match_ids('oc1', 'p', 1)
        await riot.close()
        cache.close()
    asyncio.run(run())
    assert calls[0].url.host == 'asia.api.riotgames.com'
    assert calls[1].url.host == 'sea.api.riotgames.com'
    assert 'Space%20Name' in str(calls[0].url)


def test_rate_limit_cooldown_applies_across_requests(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(429, headers={'Retry-After': '120'}, text='not JSON')
    async def run():
        cache = Cache(str(tmp_path / 'db'))
        riot = RiotClient(Settings(riot_api_key='test', request_interval=0), cache, httpx.MockTransport(handler))
        with pytest.raises(RiotError) as first:
            await riot.account('kr', 'One', 'KR1')
        assert first.value.retry_after == 120
        with pytest.raises(RiotError) as second:
            await riot.account('kr', 'Two', 'KR1')
        assert second.value.code == 'rate_limited'
        assert len(calls) == 1
        await riot.close()
        cache.close()
    asyncio.run(run())


def test_cache_stale_access_is_bounded(tmp_path):
    cache = Cache(str(tmp_path / 'db'))
    cache.put('x', {'ok': True}, -1)
    assert cache.get('x') is None
    assert cache.get('x', stale=True) == {'ok': True}
    cache.connection.execute('UPDATE cache SET created = ? WHERE key = ?', (time.time() - 604801, 'x'))
    cache.connection.commit()
    assert cache.get('x', stale=True) is None
    cache.close()


def test_empty_history_is_real_empty_result_not_demo(tmp_path):
    def handler(request):
        return httpx.Response(200, json={'puuid': 'no-games', 'gameName': 'NewPlayer', 'tagLine': 'KR1'} if '/accounts/' in request.url.path else [])
    settings = Settings(riot_api_key='test', cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        data = client.get('/api/analysis', params={'mode': 'live'}).json()
        assert data['source'] == 'live'
        assert data['matches'] == []
        assert data['summary']['games'] == 0
        assert data['player']['game_name'] == 'NewPlayer'


def test_unknown_api_route_is_not_frontend(settings):
    with TestClient(create_app(settings)) as client:
        assert client.get('/api/does-not-exist').status_code == 404

@pytest.mark.parametrize('broken', [None, {'info': None}, {'info': {'participants': None}}, {'metadata': {'matchId': 'KR_1'}, 'info': {'queueId': 420, 'mapId': 11, 'gameDuration': None, 'participants': [None] * 10}}])
def test_incomplete_match_records_do_not_crash_api(tmp_path, broken):
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': DEMO_PUUID, 'gameName': 'Player', 'tagLine': 'KR1'})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200, json=['KR_1'])
        return httpx.Response(200, content=json.dumps(broken), headers={'Content-Type': 'application/json'})
    settings = Settings(riot_api_key='test', cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        response = client.get('/api/analysis', params={'mode': 'live'})
        assert response.status_code == 200, response.text
        assert response.json()['matches'] == []
        assert 'skipped' in response.json()['warning']


@pytest.mark.parametrize('timeline', [None, [], {'info': None}, {'info': {'frames': [None]}, 'metadata': None}])
def test_bad_timeline_keeps_match_but_disables_prediction(tmp_path, timeline):
    record = demo_records(1)[0]
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': DEMO_PUUID, 'gameName': 'Player', 'tagLine': 'KR1'})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200, json=[record['match']['metadata']['matchId']])
        if request.url.path.endswith('/timeline'):
            return httpx.Response(200, content=json.dumps(timeline), headers={'Content-Type': 'application/json'})
        return httpx.Response(200, json=record['match'])
    settings = Settings(riot_api_key='test', cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        response = client.get('/api/analysis', params={'mode': 'live'})
        assert response.status_code == 200, response.text
        match = response.json()['matches'][0]
        assert match['prediction'] is None
        assert match['timeline'] == []


def test_partial_warning_is_preserved_in_cached_response(tmp_path):
    record = demo_records(1)[0]
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': DEMO_PUUID, 'gameName': 'Player', 'tagLine': 'KR1'})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200, json=[record['match']['metadata']['matchId']])
        if request.url.path.endswith('/timeline'):
            return httpx.Response(503, text='unavailable')
        return httpx.Response(200, json=record['match'])
    settings = Settings(riot_api_key='test', cache_path=str(tmp_path / 'db'), request_interval=0)
    with TestClient(create_app(settings, transport=httpx.MockTransport(handler))) as client:
        first = client.get('/api/analysis', params={'mode': 'live'}).json()
        second = client.get('/api/analysis', params={'mode': 'live'}).json()
        assert 'Some timelines are unavailable' in first['warning']
        assert 'Some timelines are unavailable' in second['warning']
        assert second['source'] == 'cache'


def test_optional_rank_archive_http_boundary_cache_and_saved_fallback(tmp_path):
    from app.opgg_archive import PROFILE_TOOL
    fail = False
    def provider(request):
        assert request.url.host == 'mcp-api.op.gg'
        assert 'X-Riot-Token' not in request.headers
        body = json.loads(request.content)
        method = body['method']
        if method == 'initialize':
            result = {'protocolVersion': '2025-06-18'}
        elif method == 'notifications/initialized':
            return httpx.Response(202)
        elif method == 'tools/list':
            result = {'tools': [{'name': PROFILE_TOOL, 'inputSchema': {
                'required': ['game_name','tag_line','region','desired_output_fields'],
                'properties': {key: {} for key in ('game_name','tag_line','region','lang','desired_output_fields')}}}]}
        else:
            assert method == 'tools/call' and body['params']['name'] == PROFILE_TOOL
            if fail:
                raise httpx.ConnectError('Provider unavailable', request=request)
            summoner = {'game_name':'Example','tagline':'TEST','region':'KR', 'previous_season_tiers':[
                {'season_id':31,'rank_entries':[{'game_type':'SOLORANKED','rank_info':
                    {'tier':'SILVER','division':3,'lp':38,'created_at':'2026-01-08T01:49:49+09:00'}}]}]}
            result = {'structuredContent': {'data': {'summoner': summoner}}}
        return httpx.Response(200, json={'jsonrpc':'2.0','id':body['id'],'result':result})
    settings = Settings(cache_path=str(tmp_path/'cache.sqlite3'),request_interval=0)
    app = create_app(settings,provider_transport=httpx.MockTransport(provider))
    headers = {'X-Lolai-Local':'1','Origin':'http://127.0.0.1:8000'}
    params = {'game_name':'Example','tag_line':'TEST','platform':'kr'}
    with TestClient(app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',50000)) as client:
        assert client.get('/api/providers/opgg/rank-history',params=params).status_code == 403
        response = client.get('/api/providers/opgg/rank-history',params=params,headers=headers)
        assert response.status_code == 200,response.text
        first = response.json()
        assert first['latest_solo']['rank']['division'] == 'III'
        assert first['source'] == 'opgg_archive' and first['storage_status'] == 'saved'
        second = client.get('/api/providers/opgg/rank-history',params=params,headers=headers).json()
        assert second['served_from'] == 'provider_cache' and second['fetched_at'] == first['fetched_at']
        app.state.cache.connection.execute("DELETE FROM cache WHERE key LIKE 'opgg:v1:%'")
        app.state.cache.connection.commit()
        fail = True
        saved = client.get('/api/providers/opgg/rank-history',params=params,headers=headers).json()
        assert saved['served_from'] == 'saved_archive' and saved['fetched_at'] == first['fetched_at']
        assert 'warning' in saved


def test_paged_analysis_collects_rebuilds_and_serves_standalone_detail_without_changing_seed(tmp_path):
    import hashlib
    records = copy.deepcopy(demo_records(3))
    for index, record in enumerate(records):
        record['source'] = 'riot'  # Isolated mocked upstream fixture, not empirical data.
        record['match']['metadata']['matchId'] = record['timeline']['metadata']['matchId'] = f'KR_{9000+index}'
    source = tmp_path/'seed.jsonl'
    source.write_text(json.dumps(records[0])+'\n',encoding='utf-8')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    calls = []
    by_id = {record['match']['metadata']['matchId']:record for record in records}
    def handler(request):
        calls.append(request)
        if '/accounts/' in request.url.path:
            return httpx.Response(200,json={'puuid':DEMO_PUUID,'gameName':'Test','tagLine':'KR1'})
        if request.url.path.endswith('/ids'):
            start = int(request.url.params['start'])
            return httpx.Response(200,json=[f'KR_{9001+start}'] if start < 2 else [])
        match_id = request.url.path.split('/')[-2 if request.url.path.endswith('/timeline') else -1]
        return httpx.Response(200,json=by_id[match_id]['timeline' if request.url.path.endswith('/timeline') else 'match'])
    settings = Settings(riot_api_key='test',cache_path=str(tmp_path/'cache.sqlite3'),request_interval=0,
                        match_store_path=str(tmp_path/'matches.sqlite3'),match_seed_path=str(source))
    with TestClient(create_app(settings,transport=httpx.MockTransport(handler))) as client:
        params = {'game_name':'Test','tag_line':'KR1','platform':'kr','mode':'live','count':1}
        first = client.get('/api/analysis',params=params).json()
        assert first['ingestion']['added'] == 1 and first['dataset']['unique_matches'] == 2
        assert first['pagination']['next_start'] == 1
        assert client.get('/api/champions').json()['unique_matches'] == 2
        assert client.get('/api/analysis',params=params).json()['ingestion']['added'] == 0
        second = client.get('/api/analysis',params={**params,'start':1}).json()
        assert second['matches'][0]['id'] == 'KR_9002' and second['dataset']['unique_matches'] == 3
        count = len(calls)
        detail = client.get('/api/matches/KR_9002',params={'game_name':'Test','tag_line':'KR1','platform':'kr'})
        assert detail.status_code == 200,detail.text
        assert len(detail.json()['match']['native']['teams'][0]['players']) == 5 and len(calls) == count
        assert client.get('/api/dataset/status').json()['aggregates_current']
        assert not client.get('/api/analysis',params={**params,'start':2}).json()['pagination']['has_more']
        for start in (-1,10001):
            assert client.get('/api/analysis',params={**params,'start':start}).status_code == 422
        demo = client.get('/api/analysis',params={'mode':'demo','start':10,'count':10}).json()
        assert demo['matches'][0]['id'] == 'DEMO_0011'
        assert client.get('/api/dataset/status').json()['unique_matches'] == 3
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before


def test_private_practice_api_requires_local_origin_and_persists_frozen_targets(tmp_path):
    records = copy.deepcopy(demo_records(3))
    for index,record in enumerate(records):
        record['source'] = 'riot'
        record['match']['metadata']['matchId'] = f'KR_{9300+index}'
        record['match']['info']['gameStartTimestamp'] = 1720000000000+index*3600000
        next(player for player in record['match']['info']['participants'] if player['puuid']==DEMO_PUUID)['teamPosition'] = 'MIDDLE'
    def handler(request):
        assert '/accounts/' in request.url.path
        return httpx.Response(200,json={'puuid':DEMO_PUUID})
    app = create_app(Settings(riot_api_key='test',cache_path=':memory:',request_interval=0,
        match_store_path=str(tmp_path/'matches.sqlite3')),transport=httpx.MockTransport(handler))
    headers = {'X-Lolai-Local':'1','Origin':'http://127.0.0.1:8000'}
    params = {'game_name':'Test','tag_line':'KR1','platform':'kr'}
    body = {'role':'MIDDLE','metric':'cs_per_min','target':6}
    with TestClient(app,base_url='http://127.0.0.1:8000',client=('127.0.0.1',50000)) as client:
        app.state.match_store.ingest(records)
        assert client.get('/api/practice',params=params).status_code == 403
        created = client.post('/api/practice',params=params,headers=headers,json=body)
        assert created.status_code == 201,created.text
        target = created.json()
        assert target['baseline_games'] == 3 and target['status'] == 'awaiting_future_games'
        assert client.get('/api/practice',params=params,headers=headers).json()['targets'][0]['id'] == target['id']
        assert client.post('/api/practice',params=params,headers=headers,json={**body,'target':True}).status_code == 422
        assert client.post('/api/practice',params=params,headers=headers,content=b'x'*3001).status_code == 413
        assert client.delete('/api/practice/'+target['id'],params=params,headers=headers).json()['deleted']
        assert client.get('/api/practice',params=params,headers=headers).json()['targets'] == []
