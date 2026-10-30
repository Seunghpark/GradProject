"""Private, prospective practice targets with frozen baselines and no efficacy claim."""
from datetime import datetime, timezone
import json
import math
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, field_validator

from .analytics import eligible_match
from .tips_engine import identity


class PracticeInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    role: Literal['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    metric: Literal['cs_per_min', 'vision_per_min', 'kill_participation', 'deaths']
    target: float

    @field_validator('target', mode='before')
    @classmethod
    def numeric_target(cls, value):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('Use a nonnegative finite target.')
        return value


def player_samples(records, puuid, role):
    samples, seen = [], set()
    for record in records:
        match = record.get('match')
        if record.get('source') != 'riot' or not eligible_match(match):
            continue
        info, mid = match['info'], match['metadata']['matchId']
        player = next((person for person in info['participants'] if person['puuid'] == puuid and person.get('teamPosition') == role), None)
        if player is None or mid in seen:
            continue
        seen.add(mid)
        duration = info['gameDuration']/60
        kills = sum(person['kills'] for person in info['participants'] if person['teamId']==player['teamId'])
        samples.append({'id':mid, 'started_at_ms':info.get('gameStartTimestamp') or info['gameCreation'],
            'duration_ms':info['gameDuration']*1000, 'queue_id':info['queueId'],
            'patch':'.'.join(str(info.get('gameVersion','')).split('.')[:2]),
            'cs_per_min':(player['totalMinionsKilled']+player['neutralMinionsKilled'])/duration,
            'vision_per_min':player['visionScore']/duration,
            'kill_participation':100*min(1,(player['kills']+player['assists'])/kills) if kills else 0,
            'deaths':player['deaths']})
    return sorted(samples,key=lambda row:(row['started_at_ms'],row['id']))


class PracticeTracker:
    def __init__(self, store):
        self.store = store
        with store.lock, store.db:
            store.db.execute('''CREATE TABLE IF NOT EXISTS practice_targets (
                id TEXT PRIMARY KEY, player_hash TEXT NOT NULL, payload TEXT NOT NULL)''')

    def create(self, puuid, value, records, now_ms=None):
        limit = 100 if value.metric=='kill_participation' else 10 if value.metric=='vision_per_min' else 30
        if value.target > limit:
            raise ValueError('Target is outside the supported metric range.')
        now = now_ms if now_ms is not None else int(datetime.now(timezone.utc).timestamp()*1000)
        samples = [row for row in player_samples(records,puuid,value.role)
                   if row['started_at_ms']+row['duration_ms'] <= now]
        if not samples:
            raise ValueError('Collect at least three earlier same-role, patch and queue games first.')
        latest = samples[-1]
        baseline = [row for row in samples if row['patch']==latest['patch'] and row['queue_id']==latest['queue_id']][-10:]
        if len(baseline)<3:
            raise ValueError('Collect at least three earlier same-role, patch and queue games first.')
        row = {'id':uuid4().hex, **value.model_dump(), 'created_at_ms':now, 'patch':latest['patch'],
               'queue_id':latest['queue_id'], 'baseline_ids':[game['id'] for game in baseline],
               'baseline_games':len(baseline), 'baseline_average':sum(game[value.metric] for game in baseline)/len(baseline)}
        with self.store.lock, self.store.db:
            if self.store.db.execute('SELECT count(*) FROM practice_targets').fetchone()[0]>=500:
                raise ValueError('The private target notebook is full; remove old targets first.')
            self.store.db.execute('INSERT INTO practice_targets VALUES (?,?,?)',
                (row['id'],identity(puuid),json.dumps(row,allow_nan=False)))
        return self.progress(row,samples)

    def progress(self, row, samples):
        later = [game for game in samples if game['started_at_ms']>row['created_at_ms']
                 and game['id'] not in row['baseline_ids'] and game['patch']==row['patch']
                 and game['queue_id']==row['queue_id']][:3]
        metric = row['metric']
        future = [{'id':game['id'],'actual':game[metric],
                   'met':game[metric]<=row['target'] if metric=='deaths' else game[metric]>=row['target']} for game in later]
        average = sum(game['actual'] for game in future)/len(future) if future else None
        return {**row,'status':'complete' if len(future)==3 else 'awaiting_future_games',
            'future_games':future,'followup_average':average,
            'observed_change':average-row['baseline_average'] if average is not None else None,
            'notice':'Same-role, patch and queue. First three later stored games only. Observed change does not establish that advice caused improvement.'}

    def list(self, puuid, records):
        with self.store.lock:
            rows = [json.loads(row[0]) for row in self.store.db.execute(
                'SELECT payload FROM practice_targets WHERE player_hash=? ORDER BY rowid DESC LIMIT 100',(identity(puuid),))]
        samples = {role:player_samples(records,puuid,role) for role in {row['role'] for row in rows}}
        return [self.progress(row,samples[row['role']]) for row in rows]

    def delete(self, puuid, target_id):
        with self.store.lock, self.store.db:
            return self.store.db.execute('DELETE FROM practice_targets WHERE id=? AND player_hash=?',
                (target_id,identity(puuid))).rowcount>0
