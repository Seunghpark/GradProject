"""Persistent TTL cache; tokens and upstream errors are never stored."""
import json
from pathlib import Path
import sqlite3
import time

class Cache:
    def __init__(self, path: str):
        self.path = path
        if path != ':memory:':
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.execute('PRAGMA journal_mode=WAL')
        self.connection.execute('CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT NOT NULL, created REAL NOT NULL, expires REAL NOT NULL)')
        self.connection.commit()

    def get(self, key: str, *, stale: bool = False, max_age: float = 604800):
        row = self.connection.execute('SELECT value, created, expires FROM cache WHERE key = ?', (key,)).fetchone()
        if not row:
            return None
        now = time.time()
        if (not stale and row[2] <= now) or now - row[1] > max_age:
            return None
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            return None

    def put(self, key: str, value, ttl: float):
        now = time.time()
        self.connection.execute('INSERT OR REPLACE INTO cache (key,value,created,expires) VALUES (?,?,?,?)', (key, json.dumps(value, ensure_ascii=False), now, now + ttl))
        self.connection.execute('DELETE FROM cache WHERE created < ?', (now - 604800,))
        self.connection.commit()

    def close(self):
        self.connection.close()
