"""Enroll a consenting player's current solo rank for future-only evaluation."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.cache import Cache
from app.config import Settings, PLATFORMS
from app.riot import RiotClient, RiotError
from scripts.validate_low_elo import LOW_TIERS


async def enroll(args):
    if args.output.suffix != '.jsonl' or args.output.name == 'riot_matches.jsonl':
        raise ValueError('Use a separate enrollment JSONL file; preserve the match dataset and models.')
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and json.loads(line).get('source') != 'riot_rank_at_enrollment':
                raise ValueError('Existing output is not an enrollment file; nothing was appended.')
    settings = Settings.from_env()
    cache, client = Cache(settings.cache_path), None
    try:
        client = RiotClient(settings, cache)
        name, tag = args.riot_id.rsplit('#', 1)
        account, _ = await client.account(args.platform, name.strip(), tag.strip())
        # Do not stamp cached rank information with a new observation time.
        path = f"/lol/league/v4/entries/by-puuid/{account['puuid']}"
        cache.connection.execute('DELETE FROM cache WHERE key=?', (f'riot:{args.platform}:{path}',))
        cache.connection.commit()
        ranks, cached = await client.ranks(args.platform, account['puuid'])
        rank = next((row for row in ranks if row.get('queueType') == 'RANKED_SOLO_5x5'), None)
        if cached or not rank or rank.get('tier') not in LOW_TIERS:
            raise ValueError('A fresh Iron/Bronze/Silver solo rank is required for this cohort.')
        model_hash = hashlib.sha256((BACKEND / 'data/model.json').read_bytes()).hexdigest()
        row = {'source': 'riot_rank_at_enrollment', 'puuid': account['puuid'], 'platform': args.platform,
               'tier': rank['tier'], 'queue': rank['queueType'], 'model_sha256': model_hash,
               'observed_at_ms': int(datetime.now(timezone.utc).timestamp() * 1000)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(row) + '\n')
        print('Enrolled current rank. Only later matches can enter the prospective evaluation; old games remain excluded.')
    except (RiotError, ValueError) as error:
        raise SystemExit(error.message if isinstance(error, RiotError) else str(error)) from None
    finally:
        if client:
            await client.close()
        cache.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--riot-id', required=True)
    parser.add_argument('--platform', choices=PLATFORMS, default='kr')
    parser.add_argument('--consent', action='store_true', required=True, help='Confirm the player consents to this private research enrollment.')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data/low_elo_enrollments.jsonl')
    args = parser.parse_args()
    if '#' not in args.riot_id or not all(args.riot_id.rsplit('#', 1)):
        parser.error('Use GameName#TAG')
    asyncio.run(enroll(args))


if __name__ == '__main__':
    main()
