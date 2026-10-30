from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from app.demo import demo_records
from scripts import evaluate_new_matches as audit


STAMP = int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp()*1000)


@pytest.fixture
def plan(monkeypatch):
    monkeypatch.setattr(audit,'_validate_model',lambda model:model)
    monkeypatch.setattr(audit,'extract_features',lambda *args:{'ok':1})
    monkeypatch.setattr(audit,'_predict_probability',lambda *args:.6)
    model = {'trained_on':'riot','algorithm':'mlp','created_at':'2026-10-01T00:00:00+00:00',
        'report':{'train':{'match_ids':['train'],'count':2,'blue_wins':1},'test':{'match_ids':['viewed']}}}
    baseline = {**model,'algorithm':'logistic_regression'}
    return audit.freeze([],json.dumps(model).encode(),json.dumps(baseline).encode())


def games(count):
    rows = deepcopy(demo_records(count))
    for index,row in enumerate(rows):
        row['source'] = 'riot'
        row['match']['metadata']['matchId'] = f'KR_{1000+index}'
        row['match']['info']['gameStartTimestamp'] = STAMP+3600000*(index+1)
    return rows


def test_later_audit_deduplicates_excludes_seen_and_old_games_and_never_fits_models(plan):
    rows = games(20)
    old = deepcopy(rows[0])
    old['match']['metadata']['matchId'] = 'KR_5'
    old['match']['info']['gameStartTimestamp'] = STAMP
    viewed = deepcopy(rows[0])
    viewed['match']['metadata']['matchId'] = 'viewed'
    result = audit.evaluate(rows+[rows[0],old,viewed],plan)
    assert result['status']=='evaluated' and result['eligible_unique_matches']==20
    assert set(result['metrics'])=={'mlp','logistic'}
    assert result['constant_training_prior']['probability']==.5
    assert result['skipped']['before_model_freeze']==1
    assert result['skipped']['excluded_or_duplicate']==2
    assert 'retrospective' in result['notice'].lower()
    assert all('puuid' not in key for key in result)


def test_insufficient_data_does_not_present_a_tiny_sample_as_validation(plan):
    result = audit.evaluate(games(19),plan)
    assert result['status']=='insufficient_later_data' and result['metrics'] is None
    assert result['constant_training_prior']['metrics'] is None


def test_frozen_plan_rejects_model_changes_and_missing_exclusions(plan):
    changed = deepcopy(plan)
    changed['models']['mlp']['model']['unexpected_change'] = 1
    with pytest.raises(ValueError,match='integrity'):
        audit.evaluate(games(20),changed)
    changed = {**plan,'excluded_match_ids':[]}
    with pytest.raises(ValueError,match='must stay excluded'):
        audit.evaluate([],changed)


def test_freeze_preserves_seen_collection_ids_and_refuses_mixed_splits(monkeypatch):
    monkeypatch.setattr(audit,'_validate_model',lambda model:model)
    model = {'trained_on':'riot','algorithm':'mlp','report':{'train':{'match_ids':['a']},'test':{'match_ids':['b']}}}
    other = {**model,'algorithm':'logistic_regression'}
    result = audit.freeze(games(1),json.dumps(model).encode(),json.dumps(other).encode())
    assert set(result['excluded_match_ids'])=={'a','b','KR_1000'}
    other['report'] = {'train':{'match_ids':['x']},'test':{'match_ids':['b']}}
    with pytest.raises(ValueError,match='same fixed split'):
        audit.freeze([],json.dumps(model).encode(),json.dumps(other).encode())


def test_saved_audit_api_refuses_mismatched_models_and_invalid_artifacts(tmp_path,monkeypatch):
    import app.main as main
    from app.config import Settings
    folder = tmp_path/'data'
    folder.mkdir()
    monkeypatch.setattr(main,'BACKEND_DIR',tmp_path)
    monkeypatch.setattr(main,'get_model_cache_version',lambda:'inference-v3:locked')
    app = main.create_app(Settings(cache_path=':memory:'))
    route = next(route.endpoint for route in app.routes if route.path=='/api/model-validation')
    assert route()['status']=='not_run'
    report = {'schema_version':1,'mode':'retrospective_later_period','status':'insufficient_later_data',
              'model_hashes':{'mlp':'locked'},'eligible_unique_matches':8,'metrics':None}
    path = folder/'later_validation.json'
    path.write_text(json.dumps(report),encoding='utf8')
    assert route()['eligible_unique_matches']==8
    report['model_hashes']['mlp'] = 'different'
    path.write_text(json.dumps(report),encoding='utf8')
    assert route()['status']=='different_model'
    path.write_text('{"schema_version":NaN}',encoding='utf8')
    assert route()['status']=='not_run'
