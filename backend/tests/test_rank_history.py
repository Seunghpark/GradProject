import json
import sqlite3
from types import SimpleNamespace

import httpx
import pytest

from app.player_context import get_player_context
from app.rank_history import RankHistory
from app.riot import RiotError
from app.main import create_app
from app.config import Settings

ENTRY = {'queue': 'RANKED_SOLO_5x5', 'tier': 'GOLD', 'division': 'II', 'league_points': 40,
         'wins': 20, 'losses': 10, 'win_rate': 2/3}
RAW = {'queueType': 'RANKED_SOLO_5x5', 'tier': 'GOLD', 'rank': 'II', 'leaguePoints': 40, 'wins': 20, 'losses': 10}


def test_fresh_checks_persist_across_restarts_and_previous_is_an_observation_not_a_guessed_season(tmp_path):
    path = tmp_path / 'rank_history.sqlite3'
    history = RankHistory(path)
    first = history.observe('kr', 'private-account', [ENTRY], cached=False)
    assert first['recorded_checks'] == 1 and first['previous_observation'] is None
    second = history.observe('kr', 'private-account', [{**ENTRY, 'league_points': 55}], cached=False)
    assert second['previous_observation']['entries'][0]['league_points'] == 40
    assert second['current_observation']['entries'][0]['league_points'] == 55
    assert second['previous_season_status'] == 'not_verified'
    assert second['first_observed_at'] == first['current_observation']['observed_at']
    history.close()
    history = RankHistory(path)
    again = history.observe('kr', 'private-account', [{**ENTRY, 'league_points': 55}], cached=True)
    assert again['observations'] == second['observations'] and again['recorded_checks'] == 2
    history.close()
    assert b'private-account' not in path.read_bytes()
    assert 'private-account' not in json.dumps(second)


def test_cached_only_response_never_becomes_a_newly_dated_rank():
    history = RankHistory(':memory:')
    assert history.observe('kr', 'account', [ENTRY], cached=True)['status'] == 'no_observations'
    recorded = history.observe('kr', 'account', [ENTRY], cached=False)
    cached = history.observe('kr', 'account', [ENTRY], cached=True)
    assert recorded['observations'] == cached['observations']
    assert cached['recorded_checks'] == 1
    mismatch = history.observe('kr', 'account', [{**ENTRY, 'league_points': 20}], cached=True)
    assert mismatch['current_observation'] is None and mismatch['previous_observation'] is None
    assert mismatch['recorded_checks'] == 1
    history.close()


def test_same_rank_on_two_fresh_checks_is_still_a_real_previous_lookup_and_other_accounts_are_isolated():
    history = RankHistory(':memory:')
    history.observe('kr', 'account', [ENTRY], cached=False)
    second = history.observe('kr', 'account', [ENTRY], cached=False)
    assert second['recorded_checks'] == 2
    assert second['previous_observation']['entries'] == second['current_observation']['entries']
    assert not history.observe('na1', 'account', [ENTRY], cached=True)['observations']
    assert not history.observe('kr', 'other-account', [ENTRY], cached=True)['observations']
    history.close()


def test_empty_official_rank_response_is_recorded_without_a_fake_tier_and_display_limit_does_not_delete_old_history():
    history = RankHistory(':memory:')
    for index in range(25):
        result = history.observe('kr', 'account', [] if index == 24 else [{**ENTRY, 'league_points': index}], cached=False)
    assert result['current_observation']['entries'] == []
    assert len(result['observations']) == 20 and result['recorded_checks'] == 25
    assert result['previous_observation']['entries'][0]['league_points'] == 23
    assert result['first_observed_at'] < result['observations'][-1]['observed_at']
    with pytest.raises(ValueError):
        history.observe('kr', 'account', None, cached=False)
    history.close()


class Riot:
    async def account(self, *args):
        return {'puuid': 'resolved-account', 'gameName': 'Player', 'tagLine': 'KR1'}, False

    async def ranks(self, *args):
        return [RAW], False


def immediate(coroutine):
    with pytest.raises(StopIteration) as result:
        coroutine.send(None)
    return result.value.value


def test_context_saves_validated_fresh_ranks_and_failed_ranks_leave_saved_history_available():
    history = RankHistory(':memory:')
    data = immediate(get_player_context(Riot(), 'kr', 'Player', 'KR1', history=history))
    assert data['rank_history']['recorded_checks'] == 1
    assert data['rank']['entries'][0]['tier'] == 'GOLD'
    class FailedRiot(Riot):
        async def ranks(self, *args):
            raise RiotError('upstream_error', 'Try later')
    failed = immediate(get_player_context(FailedRiot(), 'kr', 'Player', 'KR1', history=history))
    assert failed['rank']['status'] == 'unavailable'
    assert failed['rank_history']['recorded_checks'] == 1
    assert failed['rank_history']['current_observation'] is None
    history.close()


def test_malformed_rank_does_not_enter_history_and_storage_failure_does_not_hide_official_current_rank():
    history = RankHistory(':memory:')
    class InvalidRiot(Riot):
        async def ranks(self, *args):
            return [{**RAW, 'leaguePoints': -1}], False
    data = immediate(get_player_context(InvalidRiot(), 'kr', 'Player', 'KR1', history=history))
    assert data['rank']['status'] == 'unavailable' and data['rank_history']['recorded_checks'] == 0
    class BrokenHistory:
        def observe(self, *args, **kwargs):
            raise sqlite3.OperationalError('Disk unavailable')
    data = immediate(get_player_context(Riot(), 'kr', 'Player', 'KR1', history=BrokenHistory()))
    assert data['rank']['status'] == 'available'
    assert data['rank_history']['status'] == 'storage_unavailable'
    history.close()


def test_rank_history_is_wired_through_real_lifespan_endpoint_and_riot_cache():
    rank_calls = []
    def handler(request):
        if '/accounts/' in request.url.path:
            return httpx.Response(200, json={'puuid': 'resolved', 'gameName': 'Player', 'tagLine': 'KR1'})
        assert '/league/v4/entries/by-puuid/' in request.url.path
        rank_calls.append(request)
        return httpx.Response(200, json=[{**RAW, 'leaguePoints': 40 if len(rank_calls) == 1 else 55}])
    async def run():
        app = create_app(Settings(riot_api_key='test-only', cache_path=':memory:', request_interval=0), transport=httpx.MockTransport(handler), video_transport=httpx.MockTransport(handler))
        async with app.router.lifespan_context(app):
            endpoint = next(route.endpoint for route in app.routes if route.path == '/api/player-context')
            request = SimpleNamespace(app=app)
            first = await endpoint(request, 'Player', 'KR1', 'kr', None)
            second = await endpoint(request, 'Player', 'KR1', 'kr', None)
            assert first['rank_history']['recorded_checks'] == second['rank_history']['recorded_checks'] == 1
            assert first['rank']['cached'] is False and second['rank']['cached'] is True
            app.state.cache.connection.execute("DELETE FROM cache WHERE key LIKE 'riot:kr:/lol/league/%'")
            app.state.cache.connection.commit()
            third = await endpoint(request, 'Player', 'KR1', 'kr', None)
            assert third['rank_history']['recorded_checks'] == 2
            assert third['rank_history']['previous_observation']['entries'][0]['league_points'] == 40
            assert third['rank']['entries'][0]['league_points'] == 55
            assert 'resolved' not in json.dumps(third)
    immediate(run())
    assert len(rank_calls) == 2
