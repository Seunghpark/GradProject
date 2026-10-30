"""Riot gateway with server-only authentication, caching and shared cooldown."""
import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import time
from urllib.parse import quote
import httpx
from .cache import Cache
from .config import PLATFORMS, Settings

class RiotError(Exception):
    def __init__(self, code: str, message: str, status: int = 503, retry_after: int | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.retry_after = code, message, status, retry_after

class RiotClient:
    def __init__(self, settings: Settings, cache: Cache, transport=None):
        self.settings = settings
        self.cache = cache
        self.client = httpx.AsyncClient(timeout=settings.timeout, transport=transport, follow_redirects=False)
        self.lock = asyncio.Lock()
        self.next_request = 0.0
        self.cooldown_until = 0.0

    async def close(self):
        await self.client.aclose()

    async def get(self, route: str, path: str, *, ttl: int = 300):
        if route not in {'asia', 'americas', 'europe', 'sea', *PLATFORMS} or not path.startswith('/'):
            raise ValueError('Unsupported Riot route')
        cache_key = f'riot:{route}:{path}'
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached, True
        if not self.settings.riot_api_key:
            raise RiotError('missing_key', 'Live lookup needs RIOT_API_KEY in the backend .env file.')
        async with self.lock:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached, True
            now = time.monotonic()
            if self.cooldown_until > now:
                wait = max(1, int(self.cooldown_until - now) + 1)
                raise RiotError('rate_limited', f'Riot rate limit reached. Retry in {wait} seconds.', 429, wait)
            delay = self.next_request - now
            if delay > 0:
                await asyncio.sleep(delay)
            self.next_request = time.monotonic() + self.settings.request_interval
            try:
                response = await self.client.get(f'https://{route}.api.riotgames.com{path}', headers={'X-Riot-Token': self.settings.riot_api_key})
            except httpx.TimeoutException:
                raise RiotError('timeout', 'Riot did not respond in time. Please try again.') from None
            except httpx.RequestError:
                raise RiotError('unavailable', 'Riot is temporarily unreachable. Please try again.') from None
            if response.status_code == 429:
                raw = response.headers.get('Retry-After', '60')
                try:
                    seconds = int(float(raw))
                except (ValueError, OverflowError):
                    try:
                        seconds = int((parsedate_to_datetime(raw) - datetime.now(timezone.utc)).total_seconds())
                    except (ValueError, TypeError, OverflowError):
                        seconds = 60
                seconds = max(1, seconds)
                self.cooldown_until = time.monotonic() + seconds
                raise RiotError('rate_limited', f'Riot rate limit reached. Retry in {seconds} seconds.', 429, seconds)
            if response.status_code in (401, 403):
                raise RiotError('invalid_key', 'The backend Riot key is invalid or expired. Development keys expire after 24 hours.')
            if response.status_code == 404:
                raise RiotError('not_found', 'Riot could not find this player or match. Check Riot ID, tagline and platform.', 404)
            if response.status_code != 200:
                raise RiotError('upstream_error', 'Riot could not complete the request. Please try again later.')
            try:
                data = response.json()
            except ValueError:
                raise RiotError('invalid_response', 'Riot returned an unreadable response. Please try again.') from None
            self.cache.put(cache_key, data, ttl)
            return data, False

    async def account(self, platform: str, game_name: str, tag_line: str):
        route, _ = PLATFORMS[platform]
        return await self.get(route, f'/riot/account/v1/accounts/by-riot-id/{quote(game_name, safe="")}/{quote(tag_line, safe="")}')

    async def match_ids(self, platform: str, puuid: str, count: int, start: int = 0):
        if type(count) is not int or not 1 <= count <= 100:
            raise ValueError('count must be an integer between 1 and 100')
        if type(start) is not int or not 0 <= start <= 10000:
            raise ValueError('start must be an integer between 0 and 10000')
        _, route = PLATFORMS[platform]
        return await self.get(route, f'/lol/match/v5/matches/by-puuid/{quote(puuid, safe="")}/ids?start={start}&count={count}&type=ranked', ttl=120)

    async def match(self, platform: str, match_id: str):
        _, route = PLATFORMS[platform]
        return await self.get(route, f'/lol/match/v5/matches/{quote(match_id, safe="")}', ttl=604800)

    async def timeline(self, platform: str, match_id: str):
        _, route = PLATFORMS[platform]
        return await self.get(route, f'/lol/match/v5/matches/{quote(match_id, safe="")}/timeline', ttl=604800)

    async def ranks(self, platform: str, puuid: str):
        return await self.get(platform, f'/lol/league/v4/entries/by-puuid/{quote(puuid, safe="")}')

    async def champion_mastery(self, platform: str, puuid: str, champion_id: int):
        return await self.get(platform, f'/lol/champion-mastery/v4/champion-masteries/by-puuid/{quote(puuid, safe="")}/by-champion/{champion_id}')
