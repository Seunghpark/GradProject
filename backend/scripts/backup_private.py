"""Create a private, consistent SQLite/data backup without API keys or caches."""
from datetime import datetime, timezone
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

BACKEND = Path(__file__).resolve().parents[1]
NAMES = ('riot_matches.jsonl','model.json','riot_model.json','timeline_models.json',
    'model_comparison.json','native_champions.json','tip_benchmarks.json','item_evidence.json',
    'low_elo_enrollments.jsonl','low_elo_evaluation.json','later_validation_plan.json','later_validation.json',
    'match_store.sqlite3','rank_history.sqlite3','private_feedback.sqlite3')


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def backup(data, destination):
    data, destination = data.resolve(), destination.resolve()
    if destination.exists() or destination==data or data.is_relative_to(destination) or destination.is_relative_to(data):
        raise ValueError('Use a new backup folder separate from the data folder.')
    destination.mkdir(parents=True)
    files = {}
    for name in NAMES:
        source, target = data/name,destination/name
        if not source.is_file():
            continue
        if source.is_symlink() or source.resolve().parent!=data:
            raise ValueError('Unexpected redirected data file; backup stopped.')
        if name.endswith('.sqlite3'):
            with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original:
                with closing(sqlite3.connect(target)) as copy:
                    original.backup(copy)
                    if copy.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                        raise ValueError('SQLite backup did not pass its integrity check.')
        else:
            before = digest(source)
            shutil.copyfile(source,target)
            if digest(source)!=before or digest(target)!=before:
                raise ValueError('A source changed during backup; create a new backup after it finishes.')
        files[name] = {'bytes':target.stat().st_size,'sha256':digest(target)}
    manifest = {'created_at':datetime.now(timezone.utc).isoformat(),'files':files,
        'contains_private_player_records':True,'keys_and_cache_excluded':True,
        'notice':'SQLite databases are consistent individual snapshots, not one atomic snapshot across files. Keep this folder private. Copy it to an off-computer location; a local copy alone does not protect against computer loss.'}
    (destination/'BACKUP_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return manifest


if __name__=='__main__':
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination = BACKEND.parent/'.private-backups'/stamp
    result = backup(BACKEND/'data',destination)
    print(f'Private backup saved: {destination}\nVerified files: {len(result["files"])}. API keys and response caches are excluded.')
