"""Match history pagination uses bounded offsets and separate cached pages."""
from unittest.mock import AsyncMock

import httpx
import pytest

from app.cache import Cache
from app.config import Settings
from app.riot import RiotClient


def immediate(coroutine):
    with pytest.raises(StopIteration) as completed:
        coroutine.send(None)
    return completed.value.value


@pytest.mark.parametrize('count,start', [
    (0, 0), (101, 0), (True, 0), (False, 0), (1.0, 0), ('1', 0), (None, 0),
    (1, -1), (1, 10001), (1, True), (1, False), (1, 0.0), (1, '0'), (1, None),
])
def test_invalid_page_rejected_before_gateway(count, start):
    riot = RiotClient.__new__(RiotClient)
    riot.get = AsyncMock()
    with pytest.raises(ValueError):
        immediate(riot.match_ids('kr', 'player', count, start))
    riot.get.assert_not_called()


def test_page_offsets_use_existing_gateway_and_distinct_cache_keys(tmp_path):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=[f"KR_{request.url.params['start']}"])

    async def run():
        cache = Cache(str(tmp_path / 'cache.sqlite3'))
        riot = RiotClient(Settings(riot_api_key='mock-key', request_interval=0), cache,
                          httpx.MockTransport(handler))
        try:
            assert await riot.match_ids('kr', 'a/b', 1) == (['KR_0'], False)
            assert await riot.match_ids('kr', 'a/b', 1, start=0) == (['KR_0'], True)
            assert await riot.match_ids('kr', 'a/b', 100, start=10000) == (['KR_10000'], False)
            assert await riot.match_ids('kr', 'a/b', 100, start=10000) == (['KR_10000'], True)
        finally:
            await riot.close()
            cache.close()

    immediate(run())
    assert len(calls) == 2
    assert calls[0].url.host == 'asia.api.riotgames.com'
    assert 'a%2Fb' in str(calls[0].url)
    assert calls[0].url.query == b'start=0&count=1&type=ranked'
    assert calls[1].url.query == b'start=10000&count=100&type=ranked'
