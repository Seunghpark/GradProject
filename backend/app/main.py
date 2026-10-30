"""LolAi.gg HTTP API and optional single-process frontend serving."""
from contextlib import asynccontextmanager
import json
from pathlib import Path
import re
import sqlite3
from typing import Annotated, Literal
import httpx

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from .analytics import analysis_payload, eligible_match
from .cache import Cache
from .config import BACKEND_DIR, PLATFORMS, Settings
from .demo import DEMO_ACCOUNT, demo_records
from .ml import get_model_cache_version
from .riot import RiotClient, RiotError
from .videos import VideoClient
from .player_context import get_player_context
from .temporal_model import get_temporal_cache_version
from .model_comparison import get_comparison_cache_version
from .providers import ProviderClient, PROVIDERS
from .feedback import FeedbackInput, FeedbackStore
from .live_client import LiveClient, demo_snapshot
from .native_catalog import get_catalog
from .tips_engine import get_tips_cache_version
from .rank_history import RankHistory
from .match_store import MatchStore
from .practice import PracticeInput, PracticeTracker

DEMO_NOTICE = 'Synthetic demo: fictional player and matches for presentation. These are not Riot results or evidence of real-world model accuracy.'
VERSION = '0.6.0'
LOCAL_ORIGINS = {'http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:8000', 'http://127.0.0.1:8000'}


def require_local(request: Request):
    if (not request.client or request.client.host not in {'127.0.0.1', '::1'}
            or request.url.hostname not in {'localhost', '127.0.0.1', '::1'}
            or request.headers.get('x-lolai-local') != '1'
            or request.headers.get('sec-fetch-site') == 'cross-site'
            or (request.headers.get('origin') and request.headers['origin'] not in LOCAL_ORIGINS)):
        raise HTTPException(403, 'Private tools are available only from the local LolAi app.')


def create_app(settings: Settings | None = None, transport=None, video_transport=None, provider_transport=None, live_transport=None):
    config = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        app.state.cache = Cache(config.cache_path)
        app.state.riot = RiotClient(config, app.state.cache, transport=transport)
        app.state.videos = VideoClient(config.youtube_api_key, app.state.cache, transport=video_transport)
        app.state.providers = ProviderClient(app.state.cache, transport=provider_transport)
        feedback_path = ':memory:' if config.cache_path == ':memory:' else str(Path(config.cache_path).with_name('private_feedback.sqlite3'))
        app.state.feedback = FeedbackStore(feedback_path)
        rank_path = ':memory:' if config.cache_path == ':memory:' else str(Path(config.cache_path).with_name('rank_history.sqlite3'))
        app.state.rank_history = RankHistory(rank_path)
        app.state.match_store = None
        app.state.practice = None
        app.state.collection_seed = {'status': 'disabled'}
        if config.match_store_path:
            try:
                app.state.match_store = MatchStore(config.match_store_path)
                if config.match_seed_path:
                    try:
                        app.state.collection_seed = await run_in_threadpool(app.state.match_store.seed, config.match_seed_path)
                    except (OSError, ValueError, sqlite3.Error):
                        app.state.collection_seed = {'status': 'seed_unavailable'}
                await run_in_threadpool(app.state.match_store.refresh)
                app.state.practice = PracticeTracker(app.state.match_store)
            except (OSError, ValueError, sqlite3.Error):
                app.state.collection_seed = {'status': 'storage_unavailable'}
        app.state.live_client = LiveClient(BACKEND_DIR / 'data' / 'riotgames.pem', transport=live_transport)
        yield
        await app.state.riot.close()
        await app.state.videos.close()
        app.state.providers.close()
        app.state.feedback.close()
        app.state.rank_history.close()
        if app.state.match_store is not None:
            app.state.match_store.close()
        app.state.cache.close()

    app = FastAPI(title='LolAi.gg API', version=VERSION, lifespan=lifespan,
                  description='Historical League of Legends analysis with an explicit synthetic demo.')
    app.add_middleware(CORSMiddleware, allow_origins=[
        'http://localhost:5173', 'http://127.0.0.1:5173',
        'http://localhost:8000', 'http://127.0.0.1:8000',
    ], allow_methods=['GET', 'POST', 'DELETE'], allow_headers=['Accept', 'Content-Type', 'X-Lolai-Local'])

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'same-origin'
        if request.url.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.exception_handler(RiotError)
    async def riot_error_handler(request: Request, error: RiotError):
        headers = {'Retry-After': str(error.retry_after)} if error.retry_after else None
        return JSONResponse(status_code=error.status, headers=headers,
                            content={'detail': {'code': error.code, 'message': error.message}})

    @app.get('/api/health')
    async def health():
        return {'status': 'ok', 'version': VERSION, 'riot_configured': bool(config.riot_api_key),
                'demo_available': True, 'platforms': list(PLATFORMS), 'dataset': dataset_state()}

    def dataset_state(view=None):
        if view is not None:
            return {'status': 'available', **{key: view[key] for key in (
                'unique_matches', 'revision', 'aggregate_revision', 'aggregates_current')}, 'seed': app.state.collection_seed}
        store = getattr(app.state, 'match_store', None)
        if store is None:
            return {'status': 'disabled' if not config.match_store_path else 'unavailable', 'revision': None, 'aggregate_revision': None}
        try:
            return {'status': 'available', **store.stats(), 'seed': app.state.collection_seed}
        except (sqlite3.Error, ValueError, OSError):
            return {'status': 'unavailable', 'revision': None, 'aggregate_revision': None}

    async def save_records(records):
        store = getattr(app.state, 'match_store', None)
        if store is None:
            return {'status': 'disabled' if not config.match_store_path else 'unavailable'}, None
        counts = {}
        try:
            counts = await run_in_threadpool(store.ingest, records)
            await run_in_threadpool(store.refresh)
            view = store.view()
            return {'status': 'saved', **counts}, view
        except (OSError, ValueError, sqlite3.Error):
            return {'status': 'refresh_failed' if counts else 'save_failed', **counts}, None

    @app.get('/api/dataset/status')
    def collection_status():
        return dataset_state()

    @app.get('/api/model-validation')
    def later_model_validation():
        path = BACKEND_DIR / 'data/later_validation.json'
        try:
            if path.stat().st_size>1000000:
                raise ValueError('Oversized audit')
            def reject_constant(value):
                raise ValueError('Nonfinite audit')
            report = json.loads(path.read_text(encoding='utf-8'),parse_constant=reject_constant)
            if (not isinstance(report,dict) or report.get('schema_version')!=1
                    or report.get('mode')!='retrospective_later_period'
                    or report.get('status') not in {'evaluated','insufficient_later_data'}):
                raise ValueError('Invalid audit')
            if report.get('model_hashes',{}).get('mlp') != get_model_cache_version().removeprefix('inference-v3:'):
                return {'status':'different_model','notice':'The saved later-period audit does not match the active model.'}
            return report
        except (OSError,ValueError,TypeError,AttributeError):
            return {'status':'not_run','notice':'No valid later-period model audit has been saved.'}

    async def practice_identity(request, game_name, tag_line, platform):
        require_local(request)
        if getattr(request.app.state, 'practice', None) is None:
            raise HTTPException(503, 'Private practice tracking needs the local match store.')
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        if (platform not in PLATFORMS or not game_name or not tag_line or len(game_name)>32 or len(tag_line)>16
                or '#' in game_name+tag_line or any(ord(char)<32 for char in game_name+tag_line)):
            raise HTTPException(422, 'Enter a valid Riot ID and supported platform.')
        account, _ = await request.app.state.riot.account(platform, game_name, tag_line)
        if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
            raise RiotError('invalid_response', 'Riot returned an incomplete player record.')
        return account['puuid']

    @app.get('/api/practice')
    async def practice_list(request: Request, game_name: str, tag_line: str, platform: str = 'kr'):
        puuid = await practice_identity(request, game_name, tag_line, platform)
        try:
            return {'targets': await run_in_threadpool(lambda: request.app.state.practice.list(puuid,request.app.state.match_store.records()))}
        except (OSError, ValueError, sqlite3.Error):
            raise HTTPException(503, 'Private practice storage is unavailable.') from None

    @app.post('/api/practice', status_code=201)
    async def practice_create(request: Request, game_name: str, tag_line: str, platform: str = 'kr'):
        puuid = await practice_identity(request, game_name, tag_line, platform)
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content)>3000:
                raise HTTPException(413, 'Practice target is too large.')
        try:
            value = PracticeInput.model_validate_json(content)
            return await run_in_threadpool(lambda: request.app.state.practice.create(puuid,value,request.app.state.match_store.records()))
        except ValueError as error:
            message = str(error) if not hasattr(error, 'errors') else 'Choose a supported role, metric and finite target.'
            raise HTTPException(422, message) from None
        except (OSError, sqlite3.Error):
            raise HTTPException(503, 'Private practice storage is unavailable.') from None

    @app.delete('/api/practice/{target_id}')
    async def practice_delete(request: Request, target_id: str, game_name: str, tag_line: str, platform: str = 'kr'):
        puuid = await practice_identity(request, game_name, tag_line, platform)
        try:
            if not re.fullmatch(r'[a-f0-9]{32}',target_id) or not request.app.state.practice.delete(puuid,target_id):
                raise HTTPException(404, 'Practice target not found.')
        except sqlite3.Error:
            raise HTTPException(503, 'Private practice storage is unavailable.') from None
        return {'deleted':True}

    @app.get('/api/providers')
    def providers():
        return {'providers': PROVIDERS}

    @app.get('/api/champions')
    def champions():
        store = getattr(app.state, 'match_store', None)
        if store is not None:
            try:
                view = store.view()
                if view['catalog'] and view['unique_matches']:
                    return {**view['catalog'], 'status': 'available', 'dataset': dataset_state(view)}
            except (OSError, ValueError, sqlite3.Error):
                pass
        return get_catalog()

    @app.get('/api/providers/opgg/schema')
    def provider_schema(request: Request):
        require_local(request)
        try:
            return request.app.state.providers.schemas()
        except (ValueError, httpx.HTTPError):
            raise HTTPException(503, 'OP.GG is unavailable. No provider data was loaded.') from None

    @app.post('/api/providers/opgg/call')
    async def provider_call(request: Request):
        from starlette.concurrency import run_in_threadpool
        require_local(request)
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > 10000:
                raise HTTPException(413, 'Provider request is too large.')
        try:
            body = json.loads(content)
            if not isinstance(body, dict) or set(body) != {'tool', 'arguments'} or not isinstance(body['tool'], str):
                raise ValueError('Choose a supported provider tool and its arguments.')
            return await run_in_threadpool(request.app.state.providers.call, body['tool'], body['arguments'])
        except ValueError:
            raise HTTPException(422, 'OP.GG rejected the input or returned an invalid response. Check the current schema.') from None
        except httpx.HTTPError:
            raise HTTPException(503, 'OP.GG is unavailable. No provider data was loaded.') from None

    @app.get('/api/private-feedback')
    def private_feedback(request: Request, match_id: str = Query(min_length=1, max_length=40)):
        require_local(request)
        return {'entries': request.app.state.feedback.list(match_id)}

    @app.post('/api/private-feedback', status_code=201)
    async def add_private_feedback(request: Request):
        require_local(request)
        content = bytearray()
        async for chunk in request.stream():
            content.extend(chunk)
            if len(content) > 5000:
                raise HTTPException(413, 'Feedback is too large.')
        try:
            value = FeedbackInput.model_validate_json(bytes(content))
            return request.app.state.feedback.add(value)
        except ValueError:
            raise HTTPException(422, 'Check the match, consent, scores (1–5) and note (500 characters maximum).') from None

    @app.delete('/api/private-feedback/{entry_id}')
    def delete_private_feedback(entry_id: str, request: Request):
        require_local(request)
        if not re.fullmatch(r'[a-f0-9]{32}', entry_id) or not request.app.state.feedback.delete(entry_id):
            raise HTTPException(404, 'Feedback entry not found.')
        return {'deleted': True}

    @app.get('/api/live-self')
    async def live_self(request: Request, mode: Literal['client', 'demo'] = 'client'):
        require_local(request)
        return demo_snapshot() if mode == 'demo' else await request.app.state.live_client.snapshot()

    @app.get('/api/research-evidence')
    def research_evidence(champion_id: int = Query(ge=1, le=100000), role: str = Query(max_length=20), patch: str = Query(max_length=12)):
        if role not in {'TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY'} or not re.fullmatch(r'\d{1,2}\.\d{1,2}', patch):
            raise HTTPException(422, 'Choose a champion, role and patch.')
        output = {}
        for name in ('item_evidence', 'low_elo_evaluation'):
            path = BACKEND_DIR / 'data' / (name + '.json')
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                if name == 'item_evidence':
                    output['items'] = data['groups'].get(f'{champion_id}:{role}:{patch}')
                    output['item_evaluation'] = data['evaluation']
                else:
                    output['low_elo'] = data
            except (OSError, ValueError, KeyError, TypeError):
                output[name] = None
        return output

    @app.get('/api/videos')
    async def videos(request: Request,
                     champion: str = Query(min_length=1, max_length=40),
                     role: str = Query(min_length=1, max_length=20),
                     patch: str = Query('', max_length=12),
                     order: Literal['viewCount', 'date'] = 'viewCount',
                     days: int = Query(30, ge=14, le=90)):
        champion, role, patch = champion.strip(), role.strip(), patch.strip()
        if (days not in (14, 30, 90) or not champion or not role or any(ord(char) < 32 for char in champion + role)
                or (patch and not re.fullmatch(r'[1-9]\d?\.(?:0|[1-9]\d?)', patch))):
            raise HTTPException(422, 'Enter a champion, role and a patch such as 16.21.')
        return await request.app.state.videos.search(champion, role, patch, order, days)

    @app.get('/api/player-context')
    async def player_context(request: Request,
                             game_name: str = Query(min_length=1, max_length=32),
                             tag_line: str = Query(min_length=1, max_length=16),
                             platform: str = Query('kr'),
                             champion_id: int | None = Query(None, ge=1, le=100000)):
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        if (platform not in PLATFORMS or not game_name or not tag_line
                or any(ord(char) < 32 for char in game_name + tag_line) or '#' in game_name + tag_line):
            raise HTTPException(422, 'Enter a valid Riot ID and supported region.')
        return await get_player_context(request.app.state.riot, platform, game_name, tag_line, champion_id, getattr(request.app.state, 'rank_history', None))

    @app.get('/api/providers/opgg/rank-history')
    async def provider_rank_history(request: Request,
                                    game_name: str = Query(min_length=1, max_length=32),
                                    tag_line: str = Query(min_length=1, max_length=16),
                                    platform: str = 'kr'):
        from starlette.concurrency import run_in_threadpool
        require_local(request)
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        if (not game_name or not tag_line or len(game_name)>32 or len(tag_line)>16
                or any(ord(char)<32 for char in game_name+tag_line) or '#' in game_name+tag_line):
            raise HTTPException(422, 'Enter a valid Riot ID.')
        if platform != 'kr':
            raise HTTPException(422, 'OP.GG archived-rank lookup currently supports Korea only.')
        store = request.app.state.rank_history
        try:
            archive = await run_in_threadpool(request.app.state.providers.rank_history, game_name, tag_line, 'KR')
        except (ValueError, httpx.HTTPError):
            try:
                archive = store.saved_archive(platform, game_name, tag_line)
            except (sqlite3.Error, ValueError, OSError):
                archive = None
            if archive is None:
                raise HTTPException(503, 'OP.GG rank history is unavailable; no past-season rank is inferred.') from None
            return {**archive, 'served_from': 'saved_archive', 'cached': True,
                    'warning': 'OP.GG is currently unavailable. Showing a previously saved provider archive with its original fetch date.'}
        try:
            store.save_archive(platform, game_name, tag_line, archive)
            storage = 'saved'
        except (sqlite3.Error, ValueError, OSError):
            storage = 'unavailable'
        return {**archive, 'served_from': 'provider_cache' if archive['cached'] else 'provider', 'storage_status': storage}

    async def fetch_match_record(riot, platform, match_id, warnings):
        store = getattr(app.state, 'match_store', None)
        saved = None
        if store is not None:
            try:
                saved = store.get(match_id)
            except (OSError, ValueError, sqlite3.Error):
                pass
        network = False
        if saved:
            match = saved['match']
            frames = (saved.get('timeline') or {}).get('info', {}).get('frames', [])
            participants = {str(player['participantId']) for player in match['info']['participants']}
            if any(isinstance(frame, dict) and type(frame.get('timestamp')) in (int, float)
                   and match['info']['gameDuration']*1000-120000 <= frame['timestamp'] <= match['info']['gameDuration']*1000+120000
                   and isinstance(frame.get('participantFrames'), dict) and set(frame['participantFrames']) == participants for frame in frames):
                return saved, network
        else:
            match, cached = await riot.match(platform, match_id)
            network |= not cached
        if not eligible_match(match) or match['metadata']['matchId'] != match_id:
            raise RiotError('ineligible_match', 'Ineligible or incomplete match records were skipped.', 422)
        timeline = None
        try:
            timeline, cached = await riot.timeline(platform, match_id)
            network |= not cached
            if (not isinstance(timeline, dict) or not isinstance(timeline.get('metadata'), dict)
                    or timeline['metadata'].get('matchId') != match_id
                    or not isinstance(timeline.get('info'), dict) or not isinstance(timeline['info'].get('frames'), list)):
                timeline = None
                warnings.append('Some timelines are incomplete; those matches have no historical prediction.')
        except RiotError as error:
            if error.code == 'invalid_key':
                raise
            warnings.append('Some timelines are unavailable; those matches have no historical prediction. '+error.message)
        return {'match': match, 'timeline': timeline, 'source': 'riot'}, network

    def pagination(start, count, consumed, has_more):
        next_start = start+consumed if has_more and consumed and start+consumed <= 10000 else None
        return {'start': start, 'count': count, 'consumed_ids': consumed,
                'has_more': next_start is not None, 'next_start': next_start}

    def demo_page(start, count, notice):
        available = min(count, max(0, 20-start))
        records = demo_records(start+available)[start:] if available else []
        payload = analysis_payload(DEMO_ACCOUNT, records, 'kr', 'demo', notice)
        payload['pagination'] = pagination(start, count, available, start+available < 20)
        payload['ingestion'] = {'status': 'synthetic_not_collected'}
        return payload

    @app.get('/api/matches/{match_id}')
    async def match_detail(request: Request, match_id: str,
                           game_name: str = Query(min_length=1, max_length=32),
                           tag_line: str = Query(min_length=1, max_length=16),
                           platform: str = 'kr'):
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        prefix = match_id.split('_', 1)[0].lower()
        if (platform not in PLATFORMS or prefix not in PLATFORMS
                or PLATFORMS[prefix][1] != PLATFORMS[platform][1]
                or not re.fullmatch(r'[A-Z0-9]+_\d{1,20}', match_id)
                or not game_name or not tag_line or len(game_name)>32 or len(tag_line)>16
                or '#' in game_name+tag_line or any(ord(char)<32 for char in game_name+tag_line)):
            raise HTTPException(422, 'Use a valid Riot ID, platform and regional match ID.')
        riot = request.app.state.riot
        account, cached = await riot.account(platform, game_name, tag_line)
        if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
            raise RiotError('invalid_response', 'Riot returned an incomplete player record.')
        warnings = []
        record, network = await fetch_match_record(riot, platform, match_id, warnings)
        if not any(player['puuid'] == account['puuid'] for player in record['match']['info']['participants']):
            raise HTTPException(404, 'The selected player did not participate in this match.')
        ingestion, view = await save_records([record])
        if ingestion['status'] in ('save_failed', 'refresh_failed', 'unavailable'):
            warnings.append('Match analysis is available, but shared-data saving or refresh did not finish.')
        result = analysis_payload(account, [record], platform, 'live' if network or not cached else 'cache',
                                  ' '.join(warnings) or None, benchmarks=view['benchmarks'] if view else None)
        return {'source': result['source'], 'player': result['player'], 'match': result['matches'][0],
                'warning': result['warning'], 'ingestion': ingestion, 'dataset': dataset_state(view)}

    @app.get('/api/analysis')
    async def analysis(
        request: Request,
        game_name: str = Query('DemoPlayer', min_length=1, max_length=32),
        tag_line: str = Query('SKKU', min_length=1, max_length=16),
        platform: str = Query('kr'),
        mode: Literal['demo', 'auto', 'live'] = 'auto',
        count: int = Query(10, ge=1, le=20),
        start: Annotated[int, Query(ge=0, le=10000)] = 0,
    ):
        game_name, tag_line, platform = game_name.strip(), tag_line.strip(), platform.lower()
        if platform not in PLATFORMS:
            raise HTTPException(422, detail={'code': 'invalid_platform', 'message': 'Choose a supported platform.'})
        if not game_name or not tag_line or any(ord(c)<32 for c in game_name+tag_line) or '#' in game_name+tag_line:
            raise HTTPException(422, detail={'code': 'invalid_riot_id', 'message': 'Enter a game name and tagline without the # separator.'})
        if type(start) is not int or not 0 <= start <= 10000:
            raise HTTPException(422, 'History start must be between 0 and 10000.')
        if mode == 'demo':
            return demo_page(start, count, DEMO_NOTICE)
        cache, riot = request.app.state.cache, request.app.state.riot
        model_version, temporal_version = get_model_cache_version(), get_temporal_cache_version()
        comparison_version, tips_version = get_comparison_cache_version(), get_tips_cache_version()
        def cache_key(state):
            return 'analysis:v6:'+json.dumps([platform, game_name.casefold(), tag_line.casefold(), count, start,
                model_version, temporal_version, comparison_version, tips_version, state['revision'], state['aggregate_revision']])
        analysis_key = cache_key(dataset_state())
        cached = cache.get(analysis_key)
        if cached is not None:
            cached['source'] = 'cache'
            cached['warning'] = 'Showing a saved Riot analysis (cached for up to five minutes). '+(cached.get('warning') or '')
            cached['ingestion'] = {'status':'cached_analysis','added':0,'upgraded':0,'duplicates':0,'skipped':0}
            return cached
        records, warnings, any_network, consumed, interrupted = [], [], False, 0, False
        try:
            account, from_cache = await riot.account(platform, game_name, tag_line)
            any_network |= not from_cache
            if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
                raise RiotError('invalid_response', 'Riot returned an incomplete player record.')
            account['gameName'] = account.get('gameName') if isinstance(account.get('gameName'), str) and account['gameName'] else game_name
            account['tagLine'] = account.get('tagLine') if isinstance(account.get('tagLine'), str) and account['tagLine'] else tag_line
            match_ids, from_cache = await riot.match_ids(platform, account['puuid'], count, start=start)
            any_network |= not from_cache
            if not isinstance(match_ids, list) or not all(isinstance(value, str) for value in match_ids):
                raise RiotError('invalid_response', 'Riot returned an incomplete match list.')
            page_ids, seen = match_ids[:count], set()
            for index, match_id in enumerate(page_ids):
                if match_id in seen:
                    consumed = index+1
                    continue
                seen.add(match_id)
                try:
                    record, network = await fetch_match_record(riot, platform, match_id, warnings)
                    any_network |= network
                    if not any(player['puuid'] == account['puuid'] for player in record['match']['info']['participants']):
                        warnings.append('Ineligible or incomplete match records were skipped.')
                    else:
                        records.append(record)
                    consumed = index+1
                except RiotError as error:
                    if error.code in ('not_found','ineligible_match'):
                        warnings.append('One match was no longer available from Riot and was skipped.' if error.code == 'not_found' else error.message)
                        consumed = index+1
                        continue
                    if records and error.code != 'invalid_key':
                        warnings.append('Only part of the match history loaded. '+error.message)
                        interrupted = True
                        break
                    raise
            if not records:
                warnings.append("No eligible ranked Summoner's Rift games were found in the requested recent history. Remakes and other queues are excluded.")
            ingestion, view = await save_records(records)
            if ingestion['status'] in ('save_failed','refresh_failed','unavailable'):
                warnings.append('Match analysis is available, but shared-data saving or refresh did not finish.')
            state = dataset_state(view)
            payload = analysis_payload(account, records, platform, 'live' if any_network else 'cache',
                ' '.join(dict.fromkeys(warnings)) or None, benchmarks=view['benchmarks'] if view else None)
            payload.update(ingestion=ingestion, dataset=state,
                pagination=pagination(start, count, consumed, interrupted or len(page_ids)>=count))
            if (get_model_cache_version() == model_version and get_temporal_cache_version() == temporal_version
                    and get_comparison_cache_version() == comparison_version and get_tips_cache_version() == tips_version
                    and ingestion['status'] not in ('save_failed','refresh_failed','unavailable')):
                cache.put(cache_key(state), payload, 300)
            return payload
        except RiotError as error:
            if mode == 'live' or error.code == 'not_found':
                raise
            stale = cache.get(analysis_key, stale=True) if (get_model_cache_version() == model_version and get_temporal_cache_version() == temporal_version and get_comparison_cache_version() == comparison_version) else None
            if stale is not None:
                stale['source'] = 'cache'
                stale['warning'] = 'Riot lookup failed; showing previously saved data, up to seven days old. '+error.message+' '+(stale.get('warning') or '')
                stale['ingestion'] = {'status':'cached_analysis','added':0,'upgraded':0,'duplicates':0,'skipped':0}
                return stale
            payload = demo_page(start, count, error.message+' '+DEMO_NOTICE)
            payload['requested_player'] = {'game_name':game_name,'tag_line':tag_line,'platform':platform}
            return payload

    # A built frontend can be served from the same origin with a single Python process.
    dist = BACKEND_DIR.parent / 'frontend' / 'dist'

    @app.get('/{path:path}', include_in_schema=False)
    async def frontend(path: str):
        if path == 'api' or path.startswith('api/'):
            raise HTTPException(404, 'Unknown API endpoint')
        if not (dist / 'index.html').is_file():
            raise HTTPException(404, 'Frontend is not built. Run the frontend build or use the Vite development server.')
        candidate = (dist / path).resolve()
        if not candidate.is_relative_to(dist.resolve()):
            raise HTTPException(404, 'Not found')
        if candidate.is_file():
            return FileResponse(candidate)
        if Path(path).suffix:
            raise HTTPException(404, 'Not found')
        return FileResponse(dist / 'index.html')

    return app


app = create_app()
