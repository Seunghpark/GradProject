"""Dated official Riot rank observations, separate from the expiring API cache."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import threading


class RankHistory:
    def __init__(self, path):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('''CREATE TABLE IF NOT EXISTS rank_checks (
            id INTEGER PRIMARY KEY, account TEXT NOT NULL, observed_at TEXT NOT NULL,
            entries TEXT NOT NULL)''')
        self.db.execute('CREATE INDEX IF NOT EXISTS rank_checks_account ON rank_checks(account, id DESC)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS provider_rank_archives (
            account TEXT NOT NULL, fetched_at TEXT NOT NULL, payload TEXT NOT NULL,
            PRIMARY KEY(account, fetched_at))''')
        self.db.commit()

    def observe(self, platform, puuid, entries, *, cached):
        if not cached and not isinstance(entries, list):
            raise ValueError('Fresh observations require validated rank entries')
        # Cache hits are not newly observed ranks and must not gain a fresh timestamp.
        key = sha256(f'{platform}:{puuid}'.encode('utf-8')).hexdigest()
        payload = json.dumps(entries, sort_keys=True, allow_nan=False)
        with self.lock, self.db:
            if not cached:
                self.db.execute('INSERT INTO rank_checks(account,observed_at,entries) VALUES (?,?,?)',
                                (key, datetime.now(timezone.utc).isoformat(), payload))
            rows = self.db.execute('SELECT observed_at,entries FROM rank_checks WHERE account=? ORDER BY id DESC LIMIT 20', (key,)).fetchall()
            count, first = self.db.execute('SELECT count(*),min(observed_at) FROM rank_checks WHERE account=?', (key,)).fetchone()
        observations = [{'observed_at': stamp, 'entries': json.loads(value)} for stamp, value in rows]
        matches_current = bool(rows and rows[0][1] == payload)
        return {'status': 'available' if observations else 'no_observations',
                'source': 'riot_observed', 'recorded_checks': count, 'first_observed_at': first,
                'current_observation': observations[0] if matches_current else None,
                'previous_observation': observations[1] if matches_current and len(observations) > 1 else None,
                'observations': observations, 'cached_lookup': cached,
                'previous_season_status': 'not_verified'}

    def close(self):
        self.db.close()

    def save_archive(self, platform, game_name, tag_line, archive):
        key = sha256(f'{platform}:{game_name.casefold()}#{tag_line.casefold()}'.encode()).hexdigest()
        with self.lock, self.db:
            self.db.execute('INSERT OR REPLACE INTO provider_rank_archives VALUES (?,?,?)',
                            (key, archive['fetched_at'], json.dumps(archive, allow_nan=False)))

    def saved_archive(self, platform, game_name, tag_line):
        key = sha256(f'{platform}:{game_name.casefold()}#{tag_line.casefold()}'.encode()).hexdigest()
        with self.lock:
            row = self.db.execute('SELECT payload FROM provider_rank_archives WHERE account=? ORDER BY fetched_at DESC LIMIT 1', (key,)).fetchone()
        return json.loads(row[0]) if row else None
