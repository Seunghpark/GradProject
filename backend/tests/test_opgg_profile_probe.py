import json
from unittest.mock import patch

import httpx
import pytest

from scripts.probe_opgg_profile import FIELDS, TOOL, probe


def schema():
    return {'tools': [{'name': TOOL, 'annotations': {'readOnlyHint': True}, 'inputSchema': {
        'properties': {key: {} for key in ('game_name', 'tag_line', 'region', 'lang', 'desired_output_fields')},
        'required': ['game_name', 'tag_line', 'region', 'desired_output_fields']}}]}


def test_profile_probe_uses_only_fixed_official_endpoint_and_narrow_historical_fields_without_riot_auth():
    calls = []
    def handler(request):
        calls.append(request)
        assert str(request.url) == 'https://mcp-api.op.gg/mcp'
        assert 'X-Riot-Token' not in request.headers
        body = json.loads(request.content)
        assert body['params']['name'] == TOOL
        args = body['params']['arguments']
        assert args['game_name'] == 'Public Player' and args['tag_line'] == 'KR1'
        assert args['desired_output_fields'] == FIELDS
        assert not any('puuid' in field or 'elo' in field for field in FIELDS)
        return httpx.Response(200, json={'jsonrpc': '2.0', 'id': 1001, 'result': {'content': [
            {'type': 'text', 'text': '{"data":{"summoner":{"previous_seasons":[]}}}'}]}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client, patch('scripts.probe_opgg_profile.discover', return_value=(schema(), {'Accept': 'application/json'})):
        result = probe(client, 'Public Player#KR1', 'KR')
    assert len(calls) == 1 and result['provider'] == 'OP.GG'
    assert result['result']['content'][0]['type'] == 'text'
    assert 'not independently verified' in result['notice']


@pytest.mark.parametrize('riot_id,region', [('NoTag','KR'), ('Name#Tag#Bad','KR'), ('Name#KR1','https://evil.example'), ('Name\n#KR1','KR')])
def test_profile_probe_rejects_invalid_input_before_discovery(riot_id, region):
    with patch('scripts.probe_opgg_profile.discover') as discover:
        with pytest.raises(ValueError):
            probe(None, riot_id, region)
        discover.assert_not_called()


def test_profile_probe_stops_when_schema_changes_instead_of_guessing_new_arguments():
    data = schema()
    data['tools'][0]['inputSchema']['required'].append('new_auth_requirement')
    with patch('scripts.probe_opgg_profile.discover', return_value=(data, {})):
        with pytest.raises(ValueError, match='schema changed'):
            probe(None, 'Player#KR1', 'KR')
