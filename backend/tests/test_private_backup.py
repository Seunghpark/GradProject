import json
import sqlite3

import pytest

from scripts.backup_private import backup,digest


def test_private_backup_preserves_wal_data_models_and_hashes_but_never_keys_or_cache(tmp_path):
    source = tmp_path/'data'
    source.mkdir()
    (source/'riot_matches.jsonl').write_text('{"source":"riot"}\n',encoding='utf8')
    (source/'model.json').write_text('{}',encoding='utf8')
    (source/'.env').write_text('secret',encoding='utf8')
    (source/'cache.sqlite3').write_text('not-needed',encoding='utf8')
    db = sqlite3.connect(source/'match_store.sqlite3')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE rows(value INTEGER)')
    db.execute('INSERT INTO rows VALUES(42)')
    db.commit()
    destination = tmp_path/'private-copy'
    result = backup(source,destination)
    assert set(result['files'])=={'riot_matches.jsonl','model.json','match_store.sqlite3'}
    with sqlite3.connect(destination/'match_store.sqlite3') as copied:
        assert copied.execute('SELECT value FROM rows').fetchone()[0]==42
    manifest = json.loads((destination/'BACKUP_MANIFEST.json').read_text())
    assert manifest['contains_private_player_records'] and manifest['keys_and_cache_excluded']
    assert all(digest(destination/name)==row['sha256'] for name,row in result['files'].items())
    with pytest.raises(ValueError,match='new backup folder'):
        backup(source,destination)
    db.close()
