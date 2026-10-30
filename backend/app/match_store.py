"""Persistent genuine-match collection and coherent native-statistics snapshots."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import threading

from .analytics import eligible_match
from .config import PLATFORMS
from .native_catalog import build_catalog, CATALOG_VERSION
from .tips_engine import build_benchmarks


def validated_record(record):
    if not isinstance(record, dict) or record.get('source') != 'riot':
        return None
    match = record.get('match')
    if not eligible_match(match):
        return None
    match_id = match['metadata']['matchId']
    identity = re.fullmatch(r'([A-Z0-9]+)_\d{1,20}', match_id)
    if not identity or identity[1].lower() not in PLATFORMS:
        return None
    timeline = record.get('timeline')
    if (not isinstance(timeline, dict) or not isinstance(timeline.get('metadata'), dict)
            or timeline['metadata'].get('matchId') != match_id
            or not isinstance(timeline.get('info'), dict)
            or not isinstance(timeline['info'].get('frames'), list)
            or not any(isinstance(frame, dict) for frame in timeline['info']['frames'])):
        timeline = None
    value = {'source': 'riot', 'match': match, 'timeline': timeline}
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (ValueError, TypeError, OverflowError):
        return None
    participant_ids = {str(player['participantId']) for player in match['info']['participants']}
    quality = sum(isinstance(frame, dict) and isinstance(frame.get('participantFrames'), dict)
                  and set(frame['participantFrames']) == participant_ids
                  for frame in timeline['info']['frames']) if timeline else 0
    return match_id, encoded, quality


class MatchStore:
    def __init__(self, path):
        if str(path) != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.refresh_lock = threading.Lock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('''CREATE TABLE IF NOT EXISTS collected_matches (
            match_id TEXT PRIMARY KEY, record TEXT NOT NULL, quality INTEGER NOT NULL,
            collected_at TEXT NOT NULL)''')
        self.db.execute('CREATE TABLE IF NOT EXISTS collection_state (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS native_snapshots (
            name TEXT PRIMARY KEY,revision INTEGER NOT NULL,payload TEXT NOT NULL)''')
        self.db.execute("INSERT OR IGNORE INTO collection_state VALUES ('revision','0')")
        self.db.commit()

    def ingest(self, records):
        counts = {'added': 0, 'upgraded': 0, 'duplicates': 0, 'skipped': 0}
        now = datetime.now(timezone.utc).isoformat()
        with self.lock, self.db:
            for record in records:
                value = validated_record(record)
                if value is None:
                    counts['skipped'] += 1
                    continue
                match_id, encoded, quality = value
                existing = self.db.execute('SELECT quality FROM collected_matches WHERE match_id=?', (match_id,)).fetchone()
                if existing is None:
                    self.db.execute('INSERT INTO collected_matches VALUES (?,?,?,?)', (match_id, encoded, quality, now))
                    counts['added'] += 1
                elif quality > existing[0]:
                    # shortcut: prefer longer timelines; compare same-length upstream corrections if they become necessary.
                    self.db.execute('UPDATE collected_matches SET record=?,quality=?,collected_at=? WHERE match_id=?', (encoded, quality, now, match_id))
                    counts['upgraded'] += 1
                else:
                    counts['duplicates'] += 1
            if counts['added'] or counts['upgraded']:
                self.db.execute("UPDATE collection_state SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
        return counts

    def seed(self, path):
        path = Path(path)
        if not path.is_file():
            return {'status': 'not_found', 'added': 0}
        stat = path.stat()
        signature = f'{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}'
        with self.lock:
            previous = self.db.execute("SELECT value FROM collection_state WHERE key='seed' ").fetchone()
            if previous and previous[0] == signature:
                return {'status': 'unchanged', 'added': 0}
            with path.open(encoding='utf-8-sig') as handle:
                counts = self.ingest(json.loads(line) for line in handle if line.strip())
            with self.db:
                self.db.execute("INSERT OR REPLACE INTO collection_state VALUES ('seed',?)", (signature,))
        return {'status': 'imported', **counts}

    def refresh(self):
        # shortcut: full rebuilds suit this local dataset; use incremental aggregates before scaling to many thousands of matches.
        with self.refresh_lock:
            with self.lock:
                revision = int(self.db.execute("SELECT value FROM collection_state WHERE key='revision'").fetchone()[0])
                previous = self.db.execute("SELECT revision,payload FROM native_snapshots WHERE name='catalog'").fetchone()
                if previous and previous[0] == revision and json.loads(previous[1]).get('computation_version') == CATALOG_VERSION:
                    return False
                raw = self.db.execute('SELECT record FROM collected_matches ORDER BY match_id').fetchall()
            records = [json.loads(row[0]) for row in raw]
            catalog, benchmarks = build_catalog(records), build_benchmarks(records)
            for value in (catalog, benchmarks):
                value['collection_revision'] = revision
            # Both derived views are published in one transaction; models and source JSONL stay untouched.
            with self.lock, self.db:
                self.db.executemany('INSERT OR REPLACE INTO native_snapshots VALUES (?,?,?)', [
                    ('catalog', revision, json.dumps(catalog, ensure_ascii=False, allow_nan=False)),
                    ('benchmarks', revision, json.dumps(benchmarks, ensure_ascii=False, allow_nan=False))])
        return True

    def view(self):
        with self.lock:
            state = self.stats()
            snapshots = {name: json.loads(payload) for name, payload in self.db.execute('SELECT name,payload FROM native_snapshots')}
        return {**state, 'catalog': snapshots.get('catalog'), 'benchmarks': snapshots.get('benchmarks')}

    def stats(self):
        with self.lock:
            revision = int(self.db.execute("SELECT value FROM collection_state WHERE key='revision'").fetchone()[0])
            aggregate = self.db.execute("SELECT revision FROM native_snapshots WHERE name='catalog'").fetchone()
            count = self.db.execute('SELECT count(*) FROM collected_matches').fetchone()[0]
        return {'unique_matches': count, 'revision': revision,
                'aggregate_revision': aggregate[0] if aggregate else None,
                'aggregates_current': bool(aggregate and aggregate[0] == revision)}

    def get(self, match_id):
        with self.lock:
            row = self.db.execute('SELECT record FROM collected_matches WHERE match_id=?', (match_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def records(self):
        with self.lock:
            rows = self.db.execute('SELECT record FROM collected_matches ORDER BY match_id').fetchall()
        return [json.loads(row[0]) for row in rows]

    def close(self):
        self.db.close()
