"""Server configuration; credentials never leave the backend."""
from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / '.env', override=False)
PLATFORMS = {
    'kr': ('asia', 'asia'), 'jp1': ('asia', 'asia'),
    'na1': ('americas', 'americas'), 'br1': ('americas', 'americas'),
    'la1': ('americas', 'americas'), 'la2': ('americas', 'americas'),
    'euw1': ('europe', 'europe'), 'eun1': ('europe', 'europe'),
    'tr1': ('europe', 'europe'), 'ru': ('europe', 'europe'),
    'me1': ('europe', 'europe'), 'oc1': ('asia', 'sea'),
    'sg2': ('asia', 'sea'), 'tw2': ('asia', 'sea'), 'vn2': ('asia', 'sea'),
}

@dataclass(frozen=True)
class Settings:
    riot_api_key: str = ''
    cache_path: str = str(BACKEND_DIR / 'data' / 'cache.sqlite3')
    request_interval: float = 1.25
    timeout: float = 12.0
    youtube_api_key: str = ''
    match_store_path: str | None = None
    match_seed_path: str | None = None

    @classmethod
    def from_env(cls):
        return cls(
            riot_api_key=os.getenv('RIOT_API_KEY', '').strip(),
            cache_path=os.getenv('CACHE_PATH', str(BACKEND_DIR / 'data' / 'cache.sqlite3')),
            request_interval=max(0.0, float(os.getenv('RIOT_REQUEST_INTERVAL', '1.25'))),
            timeout=max(1.0, float(os.getenv('RIOT_TIMEOUT_SECONDS', '12'))),
            youtube_api_key=os.getenv('YOUTUBE_API_KEY', '').strip(),
            match_store_path=os.getenv('MATCH_STORE_PATH', str(BACKEND_DIR / 'data' / 'match_store.sqlite3')).strip() or None,
            match_seed_path=os.getenv('MATCH_SEED_PATH', str(BACKEND_DIR / 'data' / 'riot_matches.jsonl')).strip() or None,
        )
