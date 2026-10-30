"""Opt-in own-player dashboard via the documented local Game Client API."""
import math
import json
from pathlib import Path
import ssl

import httpx

BASE = 'https://127.0.0.1:2999/liveclientdata'


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def own_snapshot(active, game, scores):
    if not all(isinstance(value, dict) for value in (active, game, scores)):
        raise ValueError('Invalid live client response')
    seconds = number(game.get('gameTime'))
    if seconds is None or seconds > 86400:
        raise ValueError('Invalid game clock')
    stats = active.get('championStats', {})
    if not isinstance(stats, dict):
        raise ValueError('Invalid own player stats')
    return {'status': 'connected', 'source': 'local_game_client', 'game_seconds': seconds,
            'level': number(active.get('level')), 'current_gold': number(active.get('currentGold')),
            'health': number(stats.get('currentHealth')), 'max_health': number(stats.get('maxHealth')),
            'kills': number(scores.get('kills')), 'deaths': number(scores.get('deaths')),
            'assists': number(scores.get('assists')), 'cs': number(scores.get('creepScore')),
            'vision': number(scores.get('wardScore'))}


class LiveClient:
    def __init__(self, certificate, transport=None):
        self.certificate, self.transport = Path(certificate), transport

    async def snapshot(self):
        if not self.certificate.is_file() and self.transport is None:
            return {'status': 'certificate_required'}
        try:
            context = ssl.create_default_context(cafile=str(self.certificate)) if self.transport is None else True
            async with httpx.AsyncClient(verify=context, transport=self.transport, timeout=2,
                                         follow_redirects=False, trust_env=False) as client:
                async def read(path, params=None):
                    async with client.stream('GET', BASE + path, params=params) as response:
                        response.raise_for_status()
                        content = bytearray()
                        async for chunk in response.aiter_bytes():
                            content.extend(chunk)
                            if len(content) > 100000:
                                raise ValueError('Live response too large')
                        return json.loads(content)
                active = await read('/activeplayer')
                if not isinstance(active, dict):
                    raise ValueError('Invalid player')
                riot_id = active.get('riotId')
                if not isinstance(riot_id, str) or not 1 <= len(riot_id) <= 100 or any(ord(c) < 32 for c in riot_id):
                    raise ValueError('Missing active Riot ID')
                game = await read('/gamestats')
                scores = await read('/playerscores', {'riotId': riot_id})
                return own_snapshot(active, game, scores)
        except (httpx.HTTPError, ValueError, OSError):
            return {'status': 'not_connected'}


def demo_snapshot():
    return {**own_snapshot({'level': 8, 'currentGold': 1250, 'championStats': {'currentHealth': 800, 'maxHealth': 1400}},
                           {'gameTime': 615}, {'kills': 2, 'deaths': 1, 'assists': 3, 'creepScore': 65, 'wardScore': 5}),
            'source': 'synthetic', 'status': 'demo'}
