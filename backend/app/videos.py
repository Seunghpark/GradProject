"""On-demand YouTube Data API results; no scraping or claim of coaching quality."""
from datetime import datetime, timedelta, timezone
import html
import json
import re
import httpx

from .cache import Cache

NOTICE = ('Results are ordered by the selected YouTube search criterion within the publication window. '
          'A patch mention is a text match, not verified gameplay coverage. Views do not establish advice quality or player expertise.')


def video_results(payload: dict, patch: str) -> list[dict]:
    result, seen = [], set()
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('Unexpected video response')
    for item in payload['items']:
        if not isinstance(item, dict):
            continue
        identity, snippet = item.get('id'), item.get('snippet')
        if not isinstance(identity, str) or not re.fullmatch(r'[A-Za-z0-9_-]{11}', identity) or identity in seen or not isinstance(snippet, dict):
            continue
        title, channel, published = (snippet.get(name) for name in ('title', 'channelTitle', 'publishedAt'))
        if not all(isinstance(value, str) and value for value in (title, channel, published)):
            continue
        try:
            timestamp = datetime.fromisoformat(published.replace('Z', '+00:00'))
            if timestamp.tzinfo is None:
                continue
        except ValueError:
            continue
        statistics = item.get('statistics')
        raw_views = statistics.get('viewCount') if isinstance(statistics, dict) else None
        views = int(raw_views) if isinstance(raw_views, str) and re.fullmatch(r'\d{1,20}', raw_views) else None
        description = snippet.get('description', '')
        mentioned = bool(patch and re.search(r'(?<!\d)' + re.escape(patch) + r'(?!\d)',
                                            title + ' ' + (description if isinstance(description, str) else '')))
        result.append({'id': identity, 'url': f'https://www.youtube.com/watch?v={identity}',
                       'title': html.unescape(title)[:500], 'channel': html.unescape(channel)[:200],
                       'published_at': timestamp.isoformat(), 'views': views, 'patch_mentioned': mentioned})
        seen.add(identity)
    return result


class VideoClient:
    def __init__(self, key: str, cache: Cache, transport=None):
        self.key, self.cache = key, cache
        self.client = httpx.AsyncClient(timeout=10, follow_redirects=False, transport=transport)

    async def close(self):
        await self.client.aclose()

    async def search(self, champion: str, role: str, patch: str, order: str, days: int) -> dict:
        response = {'source': 'youtube', 'status': 'not_configured', 'videos': [], 'notice': NOTICE,
                    'query': f'League of Legends {champion} {role} {patch} guide'.replace('  ', ' '),
                    'patch': patch or None, 'order': order, 'days': days}
        if not self.key:
            response['notice'] = 'Video results need YOUTUBE_API_KEY in the backend .env. The YouTube search links remain available. ' + NOTICE
            return response
        cache_key = 'youtube:v1:' + json.dumps([champion.casefold(), role, patch, order, days])
        cached = self.cache.get(cache_key)
        if cached is not None:
            return {**cached, 'cached': True}
        try:
            after = datetime.now(timezone.utc) - timedelta(days=days)
            # The header keeps the backend key out of query strings and request URLs.
            headers = {'X-Goog-Api-Key': self.key}
            search = await self.client.get('https://www.googleapis.com/youtube/v3/search', headers=headers,
                params={'part': 'snippet', 'type': 'video', 'q': response['query'], 'maxResults': 6,
                        'order': order, 'safeSearch': 'moderate', 'publishedAfter': after.isoformat()})
            if search.status_code != 200:
                response.update(status='unavailable', notice='YouTube could not return results. Check the backend key, quota and network. ' + NOTICE)
                return response
            payload = search.json()
            if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
                raise ValueError('Unexpected search response')
            ids = []
            for item in payload['items']:
                identity = item.get('id') if isinstance(item, dict) else None
                video_id = identity.get('videoId') if isinstance(identity, dict) else None
                if isinstance(video_id, str) and re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id) and video_id not in ids:
                    ids.append(video_id)
            if ids:
                detail = await self.client.get('https://www.googleapis.com/youtube/v3/videos', headers=headers,
                    params={'part': 'snippet,statistics', 'id': ','.join(ids[:6])})
                if detail.status_code != 200:
                    raise ValueError('Video details unavailable')
                by_id = {item['id']: item for item in video_results(detail.json(), patch)}
                response['videos'] = [by_id[identity] for identity in ids if identity in by_id]
            response.update(status='ok', cached=False, fetched_at=datetime.now(timezone.utc).isoformat())
            self.cache.put(cache_key, response, 21600)
        except (httpx.RequestError, ValueError, TypeError, KeyError, OverflowError):
            response.update(status='unavailable', videos=[], notice='Video results are temporarily unavailable. Use the search links or try again later. ' + NOTICE)
        return response
