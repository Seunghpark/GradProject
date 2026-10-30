"""Read-only historical-rank capability probe; not a product integration."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re
import sys
import time

import httpx

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from scripts.probe_opgg import ENDPOINT, MAX_BYTES, _message, discover
from app.opgg_archive import PROFILE_TOOL as TOOL, PROFILE_FIELDS as FIELDS

def probe(client, riot_id, region):
    name, separator, tag = riot_id.strip().rpartition('#')
    if (not separator or not 0 < len(name) <= 32 or not 0 < len(tag) <= 16 or '#' in name
            or any(ord(char) < 32 for char in name+tag) or not re.fullmatch('[A-Z0-9]{2,8}', region)):
        raise ValueError('Use a valid GameName#TagLine and region such as KR')
    schema, headers = discover(client, with_session=True)
    tool = next((tool for tool in schema['tools'] if tool['name'] == TOOL), None)
    if not tool or tool.get('annotations', {}).get('readOnlyHint') is not True:
        raise ValueError('The expected read-only profile tool was not offered')
    arguments = {'game_name': name, 'tag_line': tag, 'region': region, 'lang': 'en_US', 'desired_output_fields': FIELDS}
    inputs = tool['inputSchema']
    if set(inputs.get('required', []))-arguments.keys() or arguments.keys()-inputs.get('properties', {}).keys():
        raise ValueError('The profile schema changed; inspect it before sending a query')
    with client.stream('POST', ENDPOINT, headers=headers, json={
            'jsonrpc': '2.0', 'id': 1001, 'method': 'tools/call', 'params': {'name': TOOL, 'arguments': arguments}}) as response:
        response.raise_for_status()
        content, deadline = bytearray(), time.monotonic()+30
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content)>MAX_BYTES or time.monotonic()>deadline:
                raise ValueError('Profile response exceeds the size/time limit')
        result = _message(bytes(content), response.headers.get('content-type', ''), 1001)
    if result.get('isError'):
        raise ValueError('The provider rejected the profile query')
    return {'provider': 'OP.GG', 'tool': TOOL, 'riot_id': f'{name}#{tag}', 'region': region,
            'fetched_at': datetime.now(timezone.utc).isoformat(), 'requested_fields': FIELDS,
            'result': result, 'notice': 'Capability probe only. Provider-supplied history is not independently verified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--riot-id', required=True)
    parser.add_argument('--region', default='KR')
    args = parser.parse_args()
    try:
        with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
            result = probe(client, args.riot_id, args.region.upper())
        output = BACKEND.parent / '.tmp/opgg_profile_probe.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'OP.GG profile response saved to {output}. Historical fields still need inspection; no app integration is claimed.')
        return 0
    except (ValueError, httpx.HTTPError) as error:
        print(f'Profile probe failed ({type(error).__name__}): {error}. No past-season rank is verified.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
