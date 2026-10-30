"""Current account context is validated, partial and never exposes auth headers."""
import json

import httpx
import pytest

from app.cache import Cache
from app.config import Settings
from app.player_context import get_player_context
from app.riot import RiotClient, RiotError


RANK = {'queueType': 'RANKED_SOLO_5x5', 'tier': 'GOLD', 'rank': 'II',
        'leaguePoints': 40, 'wins': 20, 'losses': 10}
MASTERY = {'championId': 103, 'championLevel': 9, 'championPoints': 12345, 'lastPlayTime': 1760000000000}


class FakeRiot:
    def __init__(self, rank=None, mastery=None):
        self.rank = [] if rank is None else rank
        self.mastery = MASTERY if mastery is None else mastery
        self.calls = []

    async def account(self, *args):
        self.calls.append(('account', args))
        return {'puuid': 'server-resolved', 'gameName': 'CurrentPlayer', 'tagLine': 'KR1'}, False

    async def ranks(self, platform, puuid):
        self.calls.append(('ranks', platform, puuid))
        if isinstance(self.rank, Exception):
            raise self.rank
        return self.rank, True

    async def champion_mastery(self, platform, puuid, champion_id):
        self.calls.append(('mastery', platform, puuid, champion_id))
        if isinstance(self.mastery, Exception):
            raise self.mastery
        return self.mastery, False


def immediate(coroutine):
    # Fakes have no IO; do not create an event loop/socket for pure parsing tests.
    with pytest.raises(StopIteration) as completed:
        coroutine.send(None)
    return completed.value.value


def test_current_rank_mastery_have_narrow_fields_and_clear_temporal_limits():
    riot = FakeRiot([RANK])
    data = immediate(get_player_context(riot, 'kr', 'Input', 'KR1', 103))
    assert data['rank']['status'] == data['mastery']['status'] == 'available'
    assert data['rank']['entries'][0]['win_rate'] == 2 / 3
    assert data['rank']['cached'] is True
    assert data['mastery']['points'] == 12345
    assert data['mastery']['level'] == 9
    assert data['mastery']['last_played_at'].endswith('+00:00')
    assert 'not used' in data['notice']
    assert 'server-resolved' not in json.dumps(data)
    assert riot.calls[1] == ('ranks', 'kr', 'server-resolved')
    assert riot.calls[2] == ('mastery', 'kr', 'server-resolved', 103)


def test_empty_rank_and_missing_mastery_are_not_fake_zero_skill():
    data = immediate(get_player_context(FakeRiot(mastery=RiotError('not_found', 'missing', 404)),
                                        'kr', 'Input', 'KR1', 103))
    assert data['rank']['status'] == 'no_ranked_entries'
    assert data['rank']['entries'] == []
    assert data['mastery']['status'] == 'no_record'
    assert 'points' not in data['mastery']


def test_partial_rank_failure_keeps_valid_mastery():
    data = immediate(get_player_context(FakeRiot(rank=RiotError('upstream_error', 'Try later')),
                                        'kr', 'Input', 'KR1', 103))
    assert data['rank']['status'] == 'unavailable'
    assert data['rank']['notice'] == 'Try later'
    assert data['mastery']['status'] == 'available'


def test_no_champion_id_skips_mastery_request():
    riot = FakeRiot([RANK])
    data = immediate(get_player_context(riot, 'kr', 'Input', 'KR1'))
    assert data['rank']['status'] == 'available'
    assert data['mastery']['status'] == 'not_requested'
    assert len(riot.calls) == 2


@pytest.mark.parametrize('rank', [None, {}, [{'queueType': 'RANKED_SOLO_5x5'}],
                                 [{**RANK, 'wins': True}], [{**RANK, 'tier': 'FAKE'}], [RANK, RANK]])
def test_malformed_rank_is_unavailable_not_inferred(rank):
    riot = FakeRiot()
    riot.rank = rank
    data = immediate(get_player_context(riot, 'kr', 'Input', 'KR1', 103))
    assert data['rank']['status'] == 'unavailable'
    assert data['rank']['entries'] == []
    assert data['mastery']['status'] == 'available'


@pytest.mark.parametrize('mastery', [{**MASTERY, 'championId': 99}, {**MASTERY, 'championLevel': True},
                                    {**MASTERY, 'championPoints': -1}, {**MASTERY, 'lastPlayTime': 10**1000}, []])
def test_malformed_mastery_does_not_invent_points_or_drop_rank(mastery):
    data = immediate(get_player_context(FakeRiot([RANK], mastery), 'kr', 'Input', 'KR1', 103))
    assert data['rank']['status'] == 'available'
    assert data['mastery']['status'] == 'unavailable'
    assert 'points' not in data['mastery']


@pytest.mark.parametrize('platform,champion_id', [('evil.example', 103), ('kr', True), ('kr', -1), ('kr', 100001)])
def test_invalid_input_rejected_before_network(platform, champion_id):
    riot = FakeRiot()
    with pytest.raises(ValueError):
        immediate(get_player_context(riot, platform, 'Input', 'KR1', champion_id))
    assert riot.calls == []


def test_platform_gateway_routes_only_to_riot_and_reuses_cache(tmp_path):
    calls = []
    secret = 'only-in-header-test'

    def handler(request):
        calls.append(request)
        assert request.url.host == 'kr.api.riotgames.com'
        assert request.url.scheme == 'https'
        assert request.headers['X-Riot-Token'] == secret
        return httpx.Response(200, json=[RANK] if '/league/' in request.url.path else MASTERY)

    async def run():
        cache = Cache(str(tmp_path / 'db'))
        riot = RiotClient(Settings(riot_api_key=secret, request_interval=0), cache, httpx.MockTransport(handler))
        try:
            ranks, cached = await riot.ranks('kr', 'a/b')
            assert not cached and ranks == [RANK]
            assert (await riot.ranks('kr', 'a/b'))[1]
            await riot.champion_mastery('kr', 'a/b', 103)
            with pytest.raises(ValueError):
                await riot.get('evil.example', '/x')
        finally:
            await riot.close()
            cache.close()

    immediate(run())
    assert len(calls) == 2
    assert 'a%2Fb' in str(calls[0].url)
    assert secret.encode() not in (tmp_path / 'db').read_bytes()
