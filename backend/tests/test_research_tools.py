import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request

from app.cache import Cache
from app.feedback import FeedbackInput, FeedbackStore
from app.live_client import LiveClient, own_snapshot, demo_snapshot, BASE
from app.main import require_local
from app.main import create_app
from app.config import Settings
from app.providers import ProviderClient, ENDPOINT
from scripts.validate_low_elo import evaluate
from scripts.build_item_evidence import build
from scripts import enroll_low_elo


def immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    finally:
        coroutine.close()
    raise AssertionError('Unexpected I/O suspension in mocked test')


def request(host='127.0.0.1', origin='http://127.0.0.1:8000', client='127.0.0.1', marker='1', site='same-origin'):
    return Request({'type': 'http', 'method': 'POST', 'scheme': 'http', 'path': '/api/private-feedback',
                    'server': (host, 8000), 'client': (client, 12345), 'query_string': b'',
                    'headers': [(b'host', f'{host}:8000'.encode()), (b'origin', origin.encode()),
                                (b'x-lolai-local', marker.encode()), (b'sec-fetch-site', site.encode())]})


def test_private_boundary_blocks_cross_origin_dns_rebinding_and_nonlocal_clients():
    require_local(request())
    for values in [{'origin': 'https://attacker.example'}, {'host': 'attacker.example'},
                   {'client': '192.168.1.2'}, {'marker': ''}, {'site': 'cross-site'}]:
        with pytest.raises(HTTPException) as error:
            require_local(request(**values))
        assert error.value.status_code == 403


def feedback(**changes):
    return FeedbackInput.model_validate({'match_id': 'KR_123', 'perspective': 'peer_report',
                                        'teamwork': 4, 'communication': 3, 'note': 'Shared vision before dragon.',
                                        'consent': True, **changes})


def test_feedback_is_private_persistent_separate_from_expiring_cache_and_deletable(tmp_path):
    path = str(tmp_path / 'notes.sqlite3')
    store = FeedbackStore(path)
    row = store.add(feedback())
    assert row['perspective'] == 'peer_report' and 'consent' not in row
    store.close()
    store = FeedbackStore(path)
    assert store.list('KR_123') == [row]
    assert store.list("KR_123' OR 1=1 --") == []
    assert store.delete(row['id'])
    assert store.list('KR_123') == []
    assert not store.delete(row['id'])
    store.close()


@pytest.mark.parametrize('changes', [{'consent': False}, {'consent': 1}, {'teamwork': 0}, {'teamwork': True},
                                      {'communication': 6}, {'match_id': '../x'}, {'note': 'x'*501},
                                      {'note': '\x00'}, {'perspective': 'verified_peer'}, {'riot_key': 'no'}])
def test_feedback_rejects_missing_consent_bad_ratings_and_sensitive_extra_fields(changes):
    with pytest.raises(ValidationError):
        feedback(**changes)


def provider_handler(calls, invalid=False):
    def handler(request):
        assert str(request.url) == ENDPOINT
        assert 'x-riot-token' not in request.headers and 'authorization' not in request.headers
        body = json.loads(request.content)
        calls.append(body)
        method = body['method']
        if method == 'initialize':
            result = {'protocolVersion': '2025-06-18'}
        elif method == 'notifications/initialized':
            return httpx.Response(202)
        elif method == 'tools/list':
            result = {'tools': [{'name': 'lol_get_champion_analysis', 'inputSchema': {
                'type': 'object', 'required': ['champion'], 'properties': {'champion': {'type': 'string'}}}},
                {'name': 'delete_everything', 'inputSchema': {'type': 'object'}}]}
        elif method == 'tools/call':
            result = {'content': None if invalid else [{'type': 'text', 'text': '<script>untrusted</script>'}]}
        else:
            raise AssertionError('Unexpected method')
        return httpx.Response(200, json={'jsonrpc': '2.0', 'id': body['id'], 'result': result})
    return handler


def test_opgg_calls_only_allowlisted_tools_uses_real_schema_and_caches_plain_output():
    calls, cache = [], Cache(':memory:')
    client = ProviderClient(cache, httpx.MockTransport(provider_handler(calls)))
    assert [tool['name'] for tool in client.schemas()['tools']] == ['lol_get_champion_analysis']
    for name, arguments in [('delete_everything', {}), ('lol_get_champion_analysis', {}),
                            ('lol_get_champion_analysis', {'champion': 'Ahri', 'unknown': 1}),
                            ('lol_get_champion_analysis', {'champion': 'x'*8001})]:
        with pytest.raises(ValueError):
            client.call(name, arguments)
    result = client.call('lol_get_champion_analysis', {'champion': 'Ahri'})
    assert result['text'] == '<script>untrusted</script>' and not result['independently_validated']
    assert client.call('lol_get_champion_analysis', {'champion': 'Ahri'})['cached']
    assert len([call for call in calls if call['method'] == 'tools/call']) == 1
    client.close()
    cache.close()


def test_opgg_invalid_content_fails_without_executing_it():
    cache = Cache(':memory:')
    client = ProviderClient(cache, httpx.MockTransport(provider_handler([], invalid=True)))
    with pytest.raises(ValueError):
        client.call('lol_get_champion_analysis', {'champion': 'Ahri'})
    client.close()
    cache.close()


def test_live_connection_only_reads_own_stats_from_fixed_https_loopback(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        assert str(request.url).startswith(BASE)
        assert 'x-riot-token' not in request.headers and 'authorization' not in request.headers
        path = request.url.path
        if path.endswith('/activeplayer'):
            result = {'riotId': 'Private#KR1', 'level': 8, 'currentGold': 1300,
                      'championStats': {'currentHealth': 500, 'maxHealth': 1000}, 'private_extra': 'discard'}
        elif path.endswith('/gamestats'):
            result = {'gameTime': 600}
        else:
            assert path.endswith('/playerscores') and request.url.params['riotId'] == 'Private#KR1'
            result = {'creepScore': 70, 'kills': 2, 'deaths': 1, 'assists': 3, 'wardScore': 8, 'private_extra': 'discard'}
        return httpx.Response(200, json=result)
    client = LiveClient(tmp_path / 'unused.pem', httpx.MockTransport(handler))
    result = immediate(client.snapshot())
    assert len(calls) == 3 and result['cs'] == 70 and result['status'] == 'connected'
    assert 'Private' not in json.dumps(result) and 'private_extra' not in result
    assert immediate(LiveClient(tmp_path / 'missing.pem').snapshot()) == {'status': 'certificate_required'}
    assert demo_snapshot()['source'] == 'synthetic'
    with pytest.raises(ValueError):
        own_snapshot({}, {'gameTime': float('nan')}, {})


def test_live_redirects_and_bad_data_never_fall_back_to_another_host(tmp_path):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(302, headers={'Location': 'https://evil.example'})
    result = immediate(LiveClient(tmp_path / 'unused.pem', httpx.MockTransport(handler)).snapshot())
    assert result['status'] == 'not_connected' and len(calls) == 1


def test_item_validation_reproduces_locked_split_and_reports_no_causal_win_benefit(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    if not (backend / 'data/riot_matches.jsonl').exists():
        pytest.skip('Private dataset is not included in source distributions')
    result = build(backend / 'data/riot_matches.jsonl', backend / 'data/model.json', tmp_path / 'items.json')
    assert result['train_matches'] == 83 and result['holdout_matches'] == 21
    assert 0 <= result['coverage'] <= 1 and not result['validated_win_improvement']
    assert result['covered_player_rows'] <= result['holdout_player_rows']
    output = json.loads((tmp_path / 'items.json').read_text())
    assert all(group['unique_matches'] >= 5 for group in output['groups'].values())
    assert all(item['count'] <= group['samples'] for group in output['groups'].values() for item in group['items'])


def test_low_elo_rejects_old_games_current_rank_relabeling_training_ids_and_wrong_model(monkeypatch):
    from scripts import validate_low_elo as module
    frozen = '2026-10-01T00:00:00+00:00'
    stamp = int(datetime.fromisoformat(frozen).timestamp()*1000)
    model = {'created_at': frozen, 'report': {'train': {'match_ids': ['train']}, 'test': {'match_ids': ['old-test']}}}
    monkeypatch.setattr(module, 'extract_features', lambda *args: {'ok': 1})
    monkeypatch.setattr(module, '_predict_probability', lambda *args: .7)
    def record(mid='new', start=stamp+2000):
        return {'source': 'riot', 'timeline': {}, 'match': {'metadata': {'matchId': mid}, 'info': {
            'gameStartTimestamp': start, 'queueId': 420,
            'participants': [{'puuid': 'p1', 'teamId': 100, 'win': True}]}}}
    entry = {'source': 'riot_rank_at_enrollment', 'tier': 'BRONZE', 'queue': 'RANKED_SOLO_5x5',
             'model_sha256': 'frozen', 'observed_at_ms': stamp+1000, 'puuid': 'p1'}
    assert evaluate([record(), record()], [entry], model, 'frozen')['eligible_unique_matches'] == 1
    for records, entries in [([record('train')], [entry]), ([record('old-test')], [entry]),
                              ([record(start=stamp-1)], [entry]), ([record()], [{**entry, 'observed_at_ms': stamp+3000}]),
                              ([record()], [{**entry, 'tier': 'GOLD'}]), ([record()], [{**entry, 'model_sha256': 'other'}])]:
        result = evaluate(records, entries, model, 'frozen')
        assert result['eligible_unique_matches'] == 0 and result['metrics'] is None
    assert evaluate([record()], [entry], model, 'frozen')['metrics'] is None


def test_private_endpoints_run_with_lifespan_and_bounded_bodies():
    stub = httpx.MockTransport(lambda request: httpx.Response(503))
    app = create_app(Settings(cache_path=':memory:'), transport=stub, video_transport=stub)
    routes = {route.path: route.endpoint for route in app.routes}
    context = app.router.lifespan_context(app)
    immediate(context.__aenter__())
    try:
        def body_request(body):
            original = request()
            async def receive():
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return Request({**original.scope, 'app': app}, receive=receive)
        payload = feedback().model_dump()
        good = body_request(json.dumps(payload).encode())
        add = next(route.endpoint for route in app.routes if route.path == '/api/private-feedback' and 'POST' in route.methods)
        read = next(route.endpoint for route in app.routes if route.path == '/api/private-feedback' and 'GET' in route.methods)
        row = immediate(add(good))
        assert read(good, 'KR_123')['entries'] == [row]
        assert routes['/api/private-feedback/{entry_id}'](row['id'], good) == {'deleted': True}
        for body in [b'x'*5001, b'{}', b'null']:
            with pytest.raises(HTTPException) as error:
                immediate(add(body_request(body)))
            assert error.value.status_code in (413, 422)
        assert immediate(routes['/api/live-self'](good, 'demo'))['source'] == 'synthetic'
    finally:
        immediate(context.__aexit__(None, None, None))
