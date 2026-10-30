"""Exercise endpoint/lifespan/cache/analysis together with in-process HTTP mocks.

This does not replace the TestClient routing/middleware or live-browser checks.
"""
from types import SimpleNamespace
import httpx

from app.config import Settings
from app.demo import DEMO_PUUID, demo_records
from app.main import create_app


def immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    finally:
        coroutine.close()
    raise AssertionError('In-process mock unexpectedly suspended')


def test_extended_payload_runs_through_lifespan_gateway_analysis_and_cache():
    records = demo_records(4)
    by_id = {record['match']['metadata']['matchId']: record for record in records}
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers['X-Riot-Token'] == 'test-secret'
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': DEMO_PUUID, 'gameName': 'TestPlayer', 'tagLine': 'KR1'})
        if request.url.path.endswith('/ids'):
            return httpx.Response(200, json=list(by_id))
        match_id = request.url.path.split('/')[-2 if request.url.path.endswith('/timeline') else -1]
        record = by_id[match_id]
        return httpx.Response(200, json=record['timeline' if request.url.path.endswith('/timeline') else 'match'])
    async def run():
        app = create_app(Settings(riot_api_key='test-secret', cache_path=':memory:', request_interval=0),
                         transport=httpx.MockTransport(handler), video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            endpoint = next(route.endpoint for route in app.routes if route.path == '/api/analysis')
            request = SimpleNamespace(app=app)
            first = await endpoint(request, 'TestPlayer', 'KR1', 'kr', 'live', 4)
            assert first['source'] == 'live' and first['profile']['games'] == 4
            assert len(first['profile']['roles']) == 5
            assert sum(row['games'] for row in first['profile']['champions']) == 4
            for match in first['matches']:
                assert match['personal_comparison']['games'] == 3
                assert match['personal_comparison']['basis'] == 'same_role'
                assert len(match['events']) > 0
                assert isinstance(match['probability_timeline']['points'], list)
                assert match['snapshot_timestamp_ms'] is not None
            second = await endpoint(request, 'TestPlayer', 'KR1', 'kr', 'live', 4)
            assert second['source'] == 'cache'
            assert second['profile'] == first['profile']
            assert second['matches'] == first['matches']
            assert len(calls) == 10
    immediate(run())


def test_demo_extensions_keep_fictional_identity_and_no_rank_lookups():
    async def run():
        def unexpected(request):
            raise AssertionError('Demo must not contact providers')
        app = create_app(Settings(cache_path=':memory:'), transport=httpx.MockTransport(unexpected),
                         video_transport=httpx.MockTransport(unexpected))
        async with app.router.lifespan_context(app):
            endpoint = next(route.endpoint for route in app.routes if route.path == '/api/analysis')
            data = await endpoint(SimpleNamespace(app=app), 'OtherPlayer', 'KR1', 'kr', 'demo', 4)
            assert data['source'] == 'demo' and data['player']['game_name'] == 'DemoPlayer'
            assert data['profile']['games'] == 4
            assert len(data['matches'][0]['insights']) >= 2
            assert not any(key.startswith('riot:') for key, in app.state.cache.connection.execute('SELECT key FROM cache'))
    immediate(run())
