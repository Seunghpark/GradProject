import json
import httpx
import pytest

from app.cache import Cache
from app.videos import VideoClient, video_results


def immediate(coroutine):
    """MockTransport has no pending I/O; an unexpected suspension fails this test."""
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    finally:
        coroutine.close()
    raise AssertionError('Mock request unexpectedly suspended')


def fixture():
    return {'items': [{'id': 'Abcdef123_-', 'snippet': {'title': 'Ahri 16.21 guide &amp; tips',
        'channelTitle': 'Example', 'publishedAt': '2026-10-25T00:00:00Z', 'description': 'guide'},
        'statistics': {'viewCount': '12345'}}]}


def test_video_result_links_dates_patch_mentions_and_missing_counts():
    row = video_results(fixture(), '16.21')[0]
    assert row['url'] == 'https://www.youtube.com/watch?v=Abcdef123_-'
    assert row['title'] == 'Ahri 16.21 guide & tips'
    assert row['views'] == 12345 and row['patch_mentioned']
    assert not video_results(fixture(), '16.2')[0]['patch_mentioned']
    changed = fixture()
    del changed['items'][0]['statistics']
    assert video_results(changed, '')[0]['views'] is None
    assert not video_results(changed, '')[0]['patch_mentioned']


def test_invalid_or_duplicate_videos_never_become_external_links():
    changed = fixture()
    item = changed['items'][0]
    changed['items'] = [None, {'id': 'javascript:alert(1)'}, item, item,
                        {**item, 'id': 'BadDate1234', 'snippet': {**item['snippet'], 'publishedAt': 'bad'}}]
    assert len(video_results(changed, '16.21')) == 1
    with pytest.raises(ValueError):
        video_results({'items': {}}, '')


def test_video_client_key_is_server_header_and_cached_results_preserve_search_order():
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers['X-Goog-Api-Key'] == 'private-test-key'
        assert 'private-test-key' not in str(request.url)
        assert 'X-Riot-Token' not in request.headers
        if request.url.path.endswith('/search'):
            assert request.url.params['q'] == 'League of Legends Ahri Mid 16.21 guide'
            assert request.url.params['order'] == 'viewCount'
            assert request.url.params['type'] == 'video'
            return httpx.Response(200, json={'items': [{'id': {'videoId': 'Abcdef123_-'}}]})
        return httpx.Response(200, json=fixture())
    async def run():
        cache = Cache(':memory:')
        client = VideoClient('private-test-key', cache, httpx.MockTransport(handler))
        try:
            result = await client.search('Ahri', 'Mid', '16.21', 'viewCount', 30)
            assert result['status'] == 'ok' and result['videos'][0]['views'] == 12345
            assert 'private-test-key' not in json.dumps(result)
            assert (await client.search('Ahri', 'Mid', '16.21', 'viewCount', 30))['cached']
            assert len(calls) == 2
        finally:
            await client.close()
            cache.close()
    immediate(run())


def test_video_key_missing_and_upstream_errors_are_explicit():
    async def run():
        for key, response, expected in [('', httpx.Response(200, json={}), 'not_configured'),
                                        ('secret', httpx.Response(403, text='secret'), 'unavailable'),
                                        ('secret', httpx.Response(200, json=[]), 'unavailable')]:
            cache = Cache(':memory:')
            client = VideoClient(key, cache, httpx.MockTransport(lambda request: response))
            try:
                result = await client.search('Ahri', 'Mid', '16.21', 'date', 14)
                assert result['status'] == expected and not result['videos']
                assert 'secret' not in json.dumps(result)
            finally:
                await client.close()
                cache.close()
    immediate(run())
