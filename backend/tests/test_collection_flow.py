from copy import deepcopy
import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
import httpx
import pytest

from app.config import Settings
from app.demo import DEMO_PUUID, demo_records
from app.main import create_app


def fixtures(count=3):
    records = deepcopy(demo_records(count))
    for index, record in enumerate(records):
        record['source'] = 'riot'
        record['match']['metadata']['matchId'] = record['timeline']['metadata']['matchId'] = f'KR_{5000+index}'
    return records


async def inline(function, *args):
    return function(*args)


def immediate(coroutine):
    with pytest.raises(StopIteration) as result:
        coroutine.send(None)
    return result.value.value


def test_live_pages_feed_one_shared_dataset_cached_repeats_do_not_claim_new_writes_and_details_reuse_records():
    records, calls = fixtures(), []
    by_id = {row['match']['metadata']['matchId']: row for row in records}
    def handler(request):
        calls.append(request)
        if '/accounts/' in request.url.path:
            return httpx.Response(200,json={'puuid':DEMO_PUUID,'gameName':'Test','tagLine':'KR1'})
        if request.url.path.endswith('/ids'):
            start,count = int(request.url.params['start']),int(request.url.params['count'])
            return httpx.Response(200,json=list(by_id)[start:start+count])
        match_id = request.url.path.split('/')[-2 if request.url.path.endswith('/timeline') else -1]
        return httpx.Response(200,json=by_id[match_id]['timeline' if request.url.path.endswith('/timeline') else 'match'])
    async def run():
        app = create_app(Settings(riot_api_key='test',cache_path=':memory:',request_interval=0,match_store_path=':memory:'),
            transport=httpx.MockTransport(handler),video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            routes = {route.path:route.endpoint for route in app.routes}
            request = SimpleNamespace(app=app)
            first = await routes['/api/analysis'](request,'Test','KR1','kr','live',1,0)
            assert first['ingestion']['added'] == 1 and first['pagination']['next_start'] == 1
            assert first['dataset']['unique_matches'] == 1 and first['dataset']['aggregates_current']
            assert routes['/api/champions']()['unique_matches'] == 1
            cached = await routes['/api/analysis'](request,'Test','KR1','kr','live',1,0)
            assert cached['source'] == 'cache' and cached['ingestion']['added'] == 0
            second = await routes['/api/analysis'](request,'Test','KR1','kr','live',1,1)
            assert second['matches'][0]['id'] == 'KR_5001' and second['dataset']['unique_matches'] == 2
            assert routes['/api/champions']()['unique_matches'] == 2
            assert app.state.match_store.view()['benchmarks']['unique_matches'] == 2
            before = len(calls)
            detail = await routes['/api/matches/{match_id}'](request,'KR_5001','Test','KR1','kr')
            assert detail['source'] == 'cache' and detail['match']['id'] == 'KR_5001'
            assert detail['ingestion']['duplicates'] == 1 and len(calls) == before
            empty = await routes['/api/analysis'](request,'Test','KR1','kr','live',1,3)
            assert empty['matches'] == [] and not empty['pagination']['has_more']
    with patch('app.main.run_in_threadpool',inline):
        immediate(run())


def test_interrupted_page_resumes_at_first_unprocessed_id_and_retains_saved_records():
    records, limited = fixtures(), [True]
    by_id = {row['match']['metadata']['matchId']:row for row in records}
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200,json={'puuid':DEMO_PUUID})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200,json=list(by_id)[int(request.url.params['start']):])
        match_id = request.url.path.split('/')[-2 if request.url.path.endswith('/timeline') else -1]
        if match_id == 'KR_5001' and limited[0]:
            return httpx.Response(429,headers={'Retry-After':'60'})
        return httpx.Response(200,json=by_id[match_id]['timeline' if request.url.path.endswith('/timeline') else 'match'])
    async def run():
        app = create_app(Settings(riot_api_key='test',cache_path=':memory:',request_interval=0,match_store_path=':memory:'),
            transport=httpx.MockTransport(handler),video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            route = next(route.endpoint for route in app.routes if route.path == '/api/analysis')
            first = await route(SimpleNamespace(app=app),'Test','KR1','kr','live',3,0)
            assert len(first['matches']) == 1 and first['pagination']['next_start'] == 1
            assert first['dataset']['unique_matches'] == 1
            limited[0],app.state.riot.cooldown_until = False,0
            rest = await route(SimpleNamespace(app=app),'Test','KR1','kr','live',3,1)
            assert [match['id'] for match in rest['matches']] == ['KR_5001','KR_5002']
            assert rest['dataset']['unique_matches'] == 3 and not rest['pagination']['has_more']
    with patch('app.main.run_in_threadpool',inline):
        immediate(run())


def test_storage_failure_leaves_analysis_available_and_does_not_cache_a_false_save():
    record = fixtures(1)[0]
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200,json={'puuid':DEMO_PUUID})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200,json=['KR_5000'])
        return httpx.Response(200,json=record['timeline' if request.url.path.endswith('/timeline') else 'match'])
    async def run():
        app = create_app(Settings(riot_api_key='test',cache_path=':memory:',request_interval=0,match_store_path=':memory:'),
            transport=httpx.MockTransport(handler),video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            route = next(route.endpoint for route in app.routes if route.path == '/api/analysis')
            with patch.object(app.state.match_store,'ingest',side_effect=sqlite3.OperationalError('Storage failed')):
                result = await route(SimpleNamespace(app=app),'Test','KR1','kr','live',1,0)
            assert len(result['matches']) == 1 and result['ingestion']['status'] == 'save_failed'
            assert 'saving or refresh did not finish' in result['warning']
            assert not list(app.state.cache.connection.execute("SELECT key FROM cache WHERE key LIKE 'analysis:v5:%'"))
    with patch('app.main.run_in_threadpool',inline):
        immediate(run())


def test_demo_history_is_bounded_and_never_enters_collection_and_api_schema_exposes_paging():
    async def run():
        def unexpected(request):
            raise AssertionError('Demo must not request Riot')
        app = create_app(Settings(cache_path=':memory:',match_store_path=':memory:'),transport=httpx.MockTransport(unexpected),video_transport=httpx.MockTransport(unexpected))
        async with app.router.lifespan_context(app):
            route = next(route.endpoint for route in app.routes if route.path == '/api/analysis')
            data = await route(SimpleNamespace(app=app),'Test','KR1','kr','demo',10,10)
            assert data['matches'][0]['id'] == 'DEMO_0011' and len(data['matches']) == 10
            assert not data['pagination']['has_more'] and app.state.match_store.stats()['unique_matches'] == 0
            assert (await route(SimpleNamespace(app=app),'Test','KR1','kr','demo',10,10000))['matches'] == []
            with pytest.raises(HTTPException):
                await route(SimpleNamespace(app=app),'Test','KR1','kr','demo',10,-1)
    with patch('app.main.run_in_threadpool',inline):
        immediate(run())
    app = create_app(Settings())
    params = {item['name']:item['schema'] for item in app.openapi()['paths']['/api/analysis']['get']['parameters']}
    assert params['start']['minimum'] == 0 and params['start']['maximum'] == 10000


def test_detail_rejects_bad_region_id_or_wrong_player_without_ingestion():
    record = fixtures(1)[0]
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200,json={'puuid':'other-player'})
        return httpx.Response(200,json=record['timeline' if request.url.path.endswith('/timeline') else 'match'])
    async def run():
        app = create_app(Settings(riot_api_key='test',cache_path=':memory:',request_interval=0,match_store_path=':memory:'),transport=httpx.MockTransport(handler),video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            route = next(route.endpoint for route in app.routes if route.path == '/api/matches/{match_id}')
            for value in ['bad','DEMO_0001','EUW1_123']:
                with pytest.raises(HTTPException) as error:
                    await route(SimpleNamespace(app=app),value,'Test','KR1','kr')
                assert error.value.status_code == 422
            with pytest.raises(HTTPException) as error:
                await route(SimpleNamespace(app=app),'KR_5000','Test','KR1','kr')
            assert error.value.status_code == 404 and app.state.match_store.stats()['unique_matches'] == 0
    with patch('app.main.run_in_threadpool',inline):
        immediate(run())
