"""Endpoint-function checks without external services or a loopback test server."""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from fastapi import HTTPException

from app.config import Settings
from app.main import create_app


def immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    finally:
        coroutine.close()
    raise AssertionError('Stub endpoint unexpectedly suspended')


def endpoints():
    app = create_app(Settings(cache_path=':memory:'))
    return {route.path: route.endpoint for route in app.routes}, app


def test_video_route_passes_only_validated_context_to_backend_client():
    routes, app = endpoints()
    calls = []
    class Videos:
        async def search(self, *args):
            calls.append(args)
            return {'status': 'not_configured', 'videos': []}
    app.state.videos = Videos()
    request = SimpleNamespace(app=app)
    assert immediate(routes['/api/videos'](request, ' Ahri ', ' Mid ', '16.21', 'viewCount', 30))['status'] == 'not_configured'
    assert calls == [('Ahri', 'Mid', '16.21', 'viewCount', 30)]
    for champion, role, patch_value, days in [('', 'Mid', '', 30), ('Ahri', '\n', '', 30),
                                             ('Ahri', 'Mid', '16.21&x=1', 30), ('Ahri', 'Mid', '', 31)]:
        with pytest.raises(HTTPException) as error:
            immediate(routes['/api/videos'](request, champion, role, patch_value, 'date', days))
        assert error.value.status_code == 422
    assert len(calls) == 1


def test_context_route_resolves_account_server_side_and_rejects_unsafe_platform():
    routes, app = endpoints()
    app.state.riot = object()
    calls = []
    async def context(*args):
        calls.append(args)
        return {'source': 'riot'}
    with patch('app.main.get_player_context', context):
        assert immediate(routes['/api/player-context'](SimpleNamespace(app=app), ' Name ', ' KR1 ', 'KR', 103)) == {'source': 'riot'}
        for name, tag, platform in [('', 'KR1', 'kr'), ('Name', 'bad#tag', 'kr'), ('Name', 'KR1', 'evil.example')]:
            with pytest.raises(HTTPException):
                immediate(routes['/api/player-context'](SimpleNamespace(app=app), name, tag, platform, 103))
    assert calls == [(app.state.riot, 'kr', 'Name', 'KR1', 103, None)]


def test_new_routes_are_registered_before_the_frontend_catchall():
    routes, app = endpoints()
    paths = [route.path for route in app.routes]
    assert paths.index('/api/videos') < paths.index('/{path:path}')
    assert paths.index('/api/player-context') < paths.index('/{path:path}')
    schema = app.openapi()
    video = {parameter['name']: parameter['schema'] for parameter in schema['paths']['/api/videos']['get']['parameters']}
    assert video['order']['enum'] == ['viewCount', 'date']
    assert video['days']['minimum'] == 14 and video['days']['maximum'] == 90
    assert not any('key' in key.lower() for key in video)
