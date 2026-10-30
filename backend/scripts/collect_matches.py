"""Collect completed ranked match/timeline pairs for reproducible local research."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.cache import Cache
from app.config import Settings, PLATFORMS
from app.riot import RiotClient, RiotError
from app.ml import extract_features

async def collect(args):
    start, pages = getattr(args, 'start', 0), getattr(args, 'pages', 1)
    if (type(args.count) is not int or not 1 <= args.count <= 100 or type(start) is not int
            or not 0 <= start <= 10000 or type(pages) is not int or not 1 <= pages <= 20
            or start+(pages-1)*args.count > 10000):
        raise SystemExit('Use count 1..100, start 0..10000 and pages 1..20 within the history limit.')
    settings = Settings.from_env()
    if not settings.riot_api_key:
        raise SystemExit('Set RIOT_API_KEY in backend/.env before collecting real data.')
    seen = set()
    if args.output.exists():
        for number, line in enumerate(args.output.read_text(encoding='utf-8-sig').splitlines(), 1):
            if line.strip():
                try:
                    seen.add(json.loads(line)['match']['metadata']['matchId'])
                except (ValueError, KeyError, TypeError):
                    raise SystemExit(f'Invalid existing JSONL at line {number}; repair before appending.')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cache = Cache(settings.cache_path)
    client = RiotClient(settings, cache)
    added = 0
    try:
        with args.output.open('a', encoding='utf-8') as handle:
            for riot_id in args.riot_id:
                game_name, tag_line = riot_id.rsplit('#', 1)
                account, _ = await client.account(args.platform, game_name, tag_line)
                if not isinstance(account, dict) or not isinstance(account.get('puuid'), str) or not account['puuid']:
                    raise RiotError('invalid_response', 'Riot returned an invalid account record.')
                for page in range(pages):
                    offset = start + page * args.count
                    ids, _ = await client.match_ids(args.platform, account['puuid'], args.count, start=offset)
                    if not isinstance(ids, list) or len(ids)>args.count or not all(isinstance(value, str) and 0<len(value)<=80 for value in ids):
                        raise RiotError('invalid_response', 'Riot returned an invalid history page.')
                    for match_id in ids:
                        if match_id in seen:
                            continue
                        match, _ = await client.match(args.platform, match_id)
                        timeline, _ = await client.timeline(args.platform, match_id)
                        if (not isinstance(match, dict) or not isinstance(match.get('metadata'), dict)
                                or match['metadata'].get('matchId') != match_id):
                            raise RiotError('invalid_response', 'A returned match did not match the requested ID.')
                        if extract_features(match, timeline) is None:
                            continue
                        handle.write(json.dumps({'source': 'riot', 'match': match, 'timeline': timeline}, ensure_ascii=False) + '\n')
                        handle.flush()
                        seen.add(match_id)
                        added += 1
                        print(f'Saved {added} new eligible matches; {len(seen)} unique total.', flush=True)
                    if len(ids) < args.count:
                        break
    except RiotError as error:
        raise SystemExit(error.message + ' Existing records are preserved; rerun to resume.') from None
    finally:
        await client.close()
        cache.close()
    print(f'Done: {added} added. Dataset: {args.output}')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--riot-id', action='append', required=True, help='GameName#TAG; repeat for more players.')
    parser.add_argument('--platform', choices=PLATFORMS, default='kr')
    parser.add_argument('--count', type=int, default=50, help='Ranked matches per page, 1 to 100.')
    parser.add_argument('--start', type=int, default=0, help='First match history offset, 0 to 10000.')
    parser.add_argument('--pages', type=int, default=1, help='Maximum pages per player in this run, 1 to 20.')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data' / 'riot_matches.jsonl')
    args = parser.parse_args()
    if not 1 <= args.count <= 100:
        parser.error('--count must be between 1 and 100.')
    if not 0 <= args.start <= 10000:
        parser.error('--start must be between 0 and 10000.')
    if not 1 <= args.pages <= 20:
        parser.error('--pages must be between 1 and 20.')
    if args.start + (args.pages - 1) * args.count > 10000:
        parser.error('The last page offset must not exceed 10000; reduce --start or --pages.')
    if any('#' not in value or not all(value.rsplit('#', 1)) for value in args.riot_id):
        parser.error('Each --riot-id must have the form GameName#TAG.')
    asyncio.run(collect(args))

if __name__ == '__main__':
    main()
