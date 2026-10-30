"""The probe discovers schemas from one endpoint, never invokes a tool."""
import json

import httpx
import pytest

from scripts.probe_opgg import ENDPOINT, _message, discover


def test_json_discovery_propagates_session_and_reads_paginated_schemas():
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert str(request.url) == ENDPOINT
        assert 'x-riot-token' not in request.headers
        assert 'authorization' not in request.headers
        if body['method'] == 'initialize':
            return httpx.Response(200, headers={'Mcp-Session-Id': 'local-test-session'},
                                  json={'jsonrpc': '2.0', 'id': 1, 'result': {'protocolVersion': '2025-06-18'}})
        assert request.headers['Mcp-Session-Id'] == 'local-test-session'
        assert request.headers['MCP-Protocol-Version'] == '2025-06-18'
        if body['method'] == 'notifications/initialized':
            return httpx.Response(202)
        assert body['method'] == 'tools/list'
        index = body['id'] - 2
        result = {'tools': [{'name': f'example_{index}', 'inputSchema': {'type': 'object'}}]}
        if index == 0:
            result['nextCursor'] = 'next-page'
        else:
            assert body['params']['cursor'] == 'next-page'
        return httpx.Response(200, json={'jsonrpc': '2.0', 'id': body['id'], 'result': result})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        data = discover(client)
    assert len(data['tools']) == 2
    assert len(calls) == 4
    assert 'tool was called' in data['notice']
    assert 'local-test-session' not in json.dumps(data)


def test_sse_ignores_notifications_and_joins_data_lines():
    content = b': heartbeat\n\nevent: message\ndata: {"jsonrpc":"2.0","method":"log"}\n\ndata: {"jsonrpc":"2.0",\ndata: "id":2,"result":{"tools":[]}}\n\n'
    assert _message(content, 'text/event-stream', 2) == {'tools': []}


@pytest.mark.parametrize('content', [b'{}', b'{"jsonrpc":"2.0","id":2,"error":{"code":-1}}',
                                     b'{"jsonrpc":"2.0","id":3,"result":{}}'])
def test_unmatched_or_failed_rpc_is_rejected(content):
    with pytest.raises(ValueError):
        _message(content, 'application/json', 2)


def test_redirect_is_not_followed():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(302, headers={'Location': 'https://attacker.example/'})

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
        with pytest.raises(httpx.HTTPStatusError):
            discover(client)
    assert len(requests) == 1
