"""Private local notes, explicitly unverified reports, never reputation scores."""
from datetime import datetime, timezone
import re
import sqlite3
import threading
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal


class FeedbackInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    match_id: str = Field(min_length=1, max_length=40)
    perspective: Literal['self', 'peer_report']
    teamwork: int = Field(ge=1, le=5, strict=True)
    communication: int = Field(ge=1, le=5, strict=True)
    note: str = Field(max_length=500)
    consent: Literal[True]

    @field_validator('consent', mode='before')
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError('Explicit consent is required.')
        return value

    @field_validator('match_id')
    @classmethod
    def valid_match(cls, value):
        if not re.fullmatch(r'(?:[A-Z0-9]+_\d+|DEMO_\d+)', value):
            raise ValueError('Use a match ID from the selected analysis.')
        return value

    @field_validator('note')
    @classmethod
    def valid_note(cls, value):
        if any(ord(char) < 32 and char not in '\n\t' for char in value):
            raise ValueError('Remove control characters.')
        return value.strip()


class FeedbackStore:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('''CREATE TABLE IF NOT EXISTS private_feedback (
            id TEXT PRIMARY KEY, match_id TEXT, perspective TEXT, teamwork INTEGER,
            communication INTEGER, note TEXT, created_at TEXT)''')
        self.db.commit()

    def add(self, value: FeedbackInput):
        row = {'id': uuid4().hex, **value.model_dump(exclude={'consent'}),
               'created_at': datetime.now(timezone.utc).isoformat()}
        with self.lock, self.db:
            if self.db.execute('SELECT count(*) FROM private_feedback').fetchone()[0] >= 5000:
                raise ValueError('The private notebook is full. Export and delete old entries first.')
            self.db.execute('INSERT INTO private_feedback VALUES (:id,:match_id,:perspective,:teamwork,:communication,:note,:created_at)', row)
        return row

    def list(self, match_id):
        with self.lock:
            self.db.row_factory = sqlite3.Row
            return [dict(row) for row in self.db.execute(
                'SELECT * FROM private_feedback WHERE match_id=? ORDER BY created_at DESC LIMIT 100', (match_id,))]

    def delete(self, row_id):
        with self.lock, self.db:
            return self.db.execute('DELETE FROM private_feedback WHERE id=?', (row_id,)).rowcount > 0

    def close(self):
        self.db.close()
