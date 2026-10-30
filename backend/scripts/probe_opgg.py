"""Read-only schema discovery for OP.GG's fixed official MCP endpoint.

Run: .venv\\Scripts\\python.exe backend\\scripts\\probe_opgg.py
No Riot key, tool calls, account information or MCP settings are used.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time

import httpx

ENDPOINT = 'https://mcp-api.op.gg/mcp'
PROTOCOL = '2025-06-18'
SUPPORTED_PROTOCOLS = {'2024-11-05', '2025-03-26', '2025-06-18'}
MAX_BYTES = 2_000_000


def _message(content, content_type, request_id):
    """Read JSON or SSE replies; server-originated requests are never executed."""
    if 'application/json' in content_type:
        messages = [json.loads(content)]
    elif 'text/event-stream' in content_type:
        messages, data = [], []
        for line in (content.decode('utf-8') + '\n\n').splitlines():
            if line.startswith('data:'):
                data.append(line[5:].lstrip(' '))
            elif not line and data:
                messages.append(json.loads('\n'.join(data)))
                data = []
    else:
        raise ValueError('Unsupported MCP response type')
    for message in messages:
        if isinstance(message, dict) and message.get('id') == request_id:
            if message.get('jsonrpc') != '2.0' or 'error' in message or not isinstance(message.get('result'), dict):
                raise ValueError('MCP request failed or returned an invalid result')
            return message['result']
    raise ValueError('MCP response did not match the request')


def discover(client, *, with_session=False):
    headers = {'Accept': 'application/json, text/event-stream'}

    def post(body):
        deadline = time.monotonic() + 30
        with client.stream('POST', ENDPOINT, json=body, headers=headers) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content) > MAX_BYTES or time.monotonic() > deadline:
                    raise ValueError('MCP response exceeds the size/time limit')
            return bytes(content), response.headers

    content, response_headers = post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                                      'params': {'protocolVersion': PROTOCOL, 'capabilities': {},
                                                 'clientInfo': {'name': 'LolAi-read-only-probe', 'version': '1.0'}}})
    initialized = _message(content, response_headers.get('content-type', ''), 1)
    protocol = initialized.get('protocolVersion')
    if protocol not in SUPPORTED_PROTOCOLS:
        raise ValueError('Unsupported negotiated MCP version')
    headers['MCP-Protocol-Version'] = protocol
    session = response_headers.get('mcp-session-id')
    if session:
        if len(session) > 1024 or any(not 0x21 <= ord(char) <= 0x7e for char in session):
            raise ValueError('Invalid MCP session header')
        headers['Mcp-Session-Id'] = session
    post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    tools, cursor, seen_cursors, names = [], None, set(), set()
    for page in range(10):
        request_id = page + 2
        body = {'jsonrpc': '2.0', 'id': request_id, 'method': 'tools/list', 'params': {}}
        if cursor:
            body['params']['cursor'] = cursor
        content, response_headers = post(body)
        result = _message(content, response_headers.get('content-type', ''), request_id)
        if not isinstance(result.get('tools'), list):
            raise ValueError('Missing MCP tool schemas')
        for tool in result['tools']:
            if (not isinstance(tool, dict) or not isinstance(tool.get('name'), str)
                    or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', tool['name'])
                    or tool['name'] in names or not isinstance(tool.get('inputSchema'), dict)):
                raise ValueError('Invalid or duplicate MCP tool schema')
            names.add(tool['name'])
            tools.append(tool)
        if len(tools) > 1000 or len(json.dumps(tools).encode('utf-8')) > MAX_BYTES:
            raise ValueError('MCP schemas exceed the size limit')
        cursor = result.get('nextCursor')
        if not cursor:
            result = {'endpoint': ENDPOINT, 'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'protocol_version': protocol, 'tools': tools,
                    'notice': 'Schema discovery only. No tool was called or provider feature integrated.'}
            return (result, headers) if with_session else result
        if not isinstance(cursor, str) or len(cursor) > 4096 or cursor in seen_cursors:
            raise ValueError('Invalid MCP pagination cursor')
        seen_cursors.add(cursor)
    raise ValueError('MCP schema pagination exceeds ten pages')


def main():
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            result = discover(client)
        output = Path(__file__).resolve().parents[2] / '.tmp' / 'opgg_tools.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"Discovered {len(result['tools'])} tool schemas. Saved {output}. No tools were called.")
        return 0
    except (httpx.HTTPError, ValueError) as error:
        print(f'OP.GG discovery failed ({type(error).__name__}). No integration is verified.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
