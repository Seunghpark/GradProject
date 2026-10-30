"""Explicit read-only calls to OP.GG's official MCP service. No Riot credentials."""
import json
from datetime import datetime, timezone
import threading
import time

import httpx
from scripts.probe_opgg import ENDPOINT, MAX_BYTES, _message, discover
from .opgg_archive import PROFILE_TOOL, PROFILE_FIELDS, rank_archive

ALLOWED_TOOLS = {'lol_get_champion_analysis', 'lol_get_lane_matchup_guide', 'lol_list_items'}
PROVIDERS = [
    {'name': 'OP.GG', 'url': 'https://op.gg/', 'access': 'official_mcp'},
    {'name': 'FOW', 'url': 'https://fow.lol/', 'access': 'external_link_only'},
    {'name': 'GGQ', 'url': 'https://ggq.gg/', 'access': 'external_link_only'},
    {'name': 'DEEPLOL', 'url': 'https://www.deeplol.gg/', 'access': 'external_link_only'},
]


class ProviderClient:
    def __init__(self, cache, transport=None):
        self.cache = cache
        self.client = httpx.Client(timeout=12, transport=transport, follow_redirects=False, trust_env=False)
        self.lock = threading.Lock()
        self.session = None

    def close(self):
        self.client.close()

    def _discover(self):
        if self.session is None or time.monotonic() - self.session[0] > 300:
            data, headers = discover(self.client, with_session=True)
            self.session = (time.monotonic(), data, headers)
        return self.session[1:]

    def schemas(self):
        with self.lock:
            data, _ = self._discover()
            return {'provider': 'OP.GG', 'fetched_at': data['fetched_at'],
                    'tools': [tool for tool in data['tools'] if tool['name'] in ALLOWED_TOOLS]}

    def call(self, name, arguments):
        return self._call(name, arguments, ALLOWED_TOOLS)

    def rank_history(self, game_name, tag_line, region='KR'):
        payload = self._call(PROFILE_TOOL, {'game_name': game_name, 'tag_line': tag_line,
            'region': region, 'lang': 'en_US', 'desired_output_fields': PROFILE_FIELDS}, {PROFILE_TOOL})
        return rank_archive(payload, game_name, tag_line, region)

    def _call(self, name, arguments, allowed):
        if name not in allowed:
            raise ValueError('Only the three read-only champion/item tools are allowed.')
        if (not isinstance(arguments, dict) or len(json.dumps(arguments, allow_nan=False).encode()) > 8000
                or any(not isinstance(key, str) for key in arguments)):
            raise ValueError('Provider arguments must be a JSON object smaller than 8 KB.')
        key = 'opgg:v1:' + json.dumps([name, arguments], sort_keys=True, allow_nan=False)
        with self.lock:
            cached = self.cache.get(key)
            if cached is not None:
                return {**cached, 'cached': True}
            data, headers = self._discover()
            schema = next((tool['inputSchema'] for tool in data['tools'] if tool['name'] == name), None)
            if schema is None:
                raise ValueError('This tool is not currently offered by OP.GG.')
            # OP.GG validates the full schema; reject missing/unknown top-level inputs locally too.
            if (set(schema.get('required', [])) - arguments.keys()
                    or arguments.keys() - schema.get('properties', {}).keys()):
                raise ValueError('Use only fields in the current OP.GG schema and fill every required field.')
            try:
                with self.client.stream('POST', ENDPOINT, headers=headers, json={
                    'jsonrpc': '2.0', 'id': 1001, 'method': 'tools/call',
                    'params': {'name': name, 'arguments': arguments},
                }) as response:
                    response.raise_for_status()
                    content, deadline = bytearray(), time.monotonic() + 30
                    for chunk in response.iter_bytes():
                        content.extend(chunk)
                        if len(content) > MAX_BYTES or time.monotonic() > deadline:
                            raise ValueError('OP.GG response exceeds the size/time limit.')
                    result = _message(bytes(content), response.headers.get('content-type', ''), 1001)
            except (httpx.HTTPError, ValueError):
                self.session = None
                raise
            if result.get('isError'):
                raise ValueError('OP.GG rejected the request. Check its current schema and try again.')
            # Remote output remains plain text/data. No returned URL, instruction or code is executed.
            blocks = result.get('content', [])
            if not isinstance(blocks, list):
                raise ValueError('OP.GG returned invalid content.')
            text = '\n'.join(block['text'] for block in blocks
                             if isinstance(block, dict) and block.get('type') == 'text'
                             and isinstance(block.get('text'), str))
            structured = result.get('structuredContent')
            if not text and not isinstance(structured, dict):
                raise ValueError('OP.GG returned no readable data.')
            payload = {'provider': 'OP.GG', 'tool': name, 'text': text, 'data': structured,
                       'fetched_at': datetime.now(timezone.utc).isoformat(),
                       'cached': False, 'independently_validated': False}
            self.cache.put(key, payload, 900)
            return payload
