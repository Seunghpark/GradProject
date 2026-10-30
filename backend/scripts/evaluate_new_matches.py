"""Freeze unchanged models, then audit newly collected later-period games.

This is a retrospective temporal audit, not a randomized coaching study or an
independent external population. No fitting or parameter selection occurs here.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BACKEND))
from app.analytics import eligible_match
from app.ml import _validate_model, _predict_probability, extract_features
from scripts.benchmark_models import measure


def canonical_hash(model):
    return hashlib.sha256(json.dumps(model,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read_collection(path):
    with sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True) as db:
        return [json.loads(row[0]) for row in db.execute('SELECT record FROM collected_matches ORDER BY match_id')]


def freeze(records, model_bytes, baseline_bytes):
    models = {'mlp':model_bytes,'logistic':baseline_bytes}
    frozen = {}
    for name,raw in models.items():
        model = _validate_model(json.loads(raw))
        if model['trained_on']!='riot' or model['algorithm'] != ('mlp' if name=='mlp' else 'logistic_regression'):
            raise ValueError('Use genuine saved MLP and logistic models.')
        frozen[name] = {'sha256':hashlib.sha256(raw).hexdigest(),'canonical_sha256':canonical_hash(model),'model':model}
    reports = [value['model']['report'] for value in frozen.values()]
    partitions = [{group:report[group]['match_ids'] for group in ('train','test')} for report in reports]
    if partitions[0] != partitions[1]:
        raise ValueError('Baseline and neural model must use the same fixed split.')
    known = set(partitions[0]['train'])|set(partitions[0]['test'])
    excluded = known|{row['match']['metadata']['matchId'] for row in records}
    return {'schema_version':1,'created_at':datetime.now(timezone.utc).isoformat(),
        'mode':'retrospective_later_period','primary_metric':'brier_score','minimum_matches':20,
        'excluded_match_ids':sorted(excluded),'models':frozen,
        'notice':'Fixed models and exclusions saved before this additional collection. Games must postdate both model files. Same-player overlap, convenience sampling and retrospective protocol choice limit independence. No model selection or coaching efficacy claim.'}


def evaluate(records, plan):
    if plan.get('schema_version')!=1 or plan.get('mode')!='retrospective_later_period' or plan.get('minimum_matches')!=20:
        raise ValueError('Use the locked later-period audit plan.')
    models = {name:_validate_model(value['model']) for name,value in plan['models'].items()}
    if any(canonical_hash(model)!=plan['models'][name].get('canonical_sha256') for name,model in models.items()):
        raise ValueError('Frozen model integrity check failed.')
    if set(models)!={'mlp','logistic'} or any(model['trained_on']!='riot' for model in models.values()):
        raise ValueError('Two genuine frozen models are required.')
    excluded = set(plan['excluded_match_ids'])
    reference = models['mlp']['report']
    known = set(reference['train']['match_ids'])|set(reference['test']['match_ids'])
    if not known <= excluded:
        raise ValueError('Original training and viewed-holdout games must stay excluded.')
    cutoff = max(datetime.fromisoformat(model['created_at'].replace('Z','+00:00')).timestamp()*1000 for model in models.values())
    seen, labels, probabilities, dates, players, original_players = set(), [], {name:[] for name in models}, [], set(), set()
    skipped = {'excluded_or_duplicate':0,'before_model_freeze':0,'ineligible':0}
    for record in records:
        match = record.get('match')
        if record.get('source')!='riot' or not eligible_match(match):
            skipped['ineligible'] += 1
            continue
        info, mid = match['info'],match['metadata']['matchId']
        if mid in known:
            original_players.update(player['puuid'] for player in info['participants'])
        if mid in excluded or mid in seen:
            skipped['excluded_or_duplicate'] += 1
            continue
        start = info.get('gameStartTimestamp') or info['gameCreation']
        if start<=cutoff:
            skipped['before_model_freeze'] += 1
            continue
        features = extract_features(match,record.get('timeline'))
        teams = info.get('teams')
        outcomes = {row.get('teamId'):row.get('win') for row in teams if isinstance(row,dict)} if isinstance(teams,list) else {}
        if (features is None or set(outcomes)!={100,200} or any(type(value) is not bool for value in outcomes.values())
                or outcomes[100]==outcomes[200] or info['queueId']!=420):
            skipped['ineligible'] += 1
            continue
        seen.add(mid)
        labels.append(int(outcomes[100]))
        dates.append(start)
        players.update(player['puuid'] for player in info['participants'])
        for name,model in models.items():
            probabilities[name].append(_predict_probability(model,features,100))
    ready = len(seen)>=20 and len(set(labels))==2
    prior = reference['train']['blue_wins']/reference['train']['count']
    return {'schema_version':1,'mode':plan['mode'],'status':'evaluated' if ready else 'insufficient_later_data',
        'evaluated_at':datetime.now(timezone.utc).isoformat(),'plan_created_at':plan['created_at'],
        'plan_sha256':canonical_hash(plan),
        'minimum_matches':20,'eligible_unique_matches':len(seen),'blue_wins':sum(labels),'red_wins':len(labels)-sum(labels),
        'first_match_at':datetime.fromtimestamp(min(dates)/1000,timezone.utc).isoformat() if dates else None,
        'last_match_at':datetime.fromtimestamp(max(dates)/1000,timezone.utc).isoformat() if dates else None,
        'model_hashes':{name:value['sha256'] for name,value in plan['models'].items()},'skipped':skipped,
        'participant_overlap':{'unique_players':len(players),'also_in_original_snapshot':len(players&original_players)},
        'metrics':{name:measure(labels,values) for name,values in probabilities.items()} if ready else None,
        'constant_training_prior':{'probability':prior,'metrics':measure(labels,[prior]*len(labels)) if ready else None},
        'notice':plan['notice']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,default=BACKEND/'data/match_store.sqlite3')
    parser.add_argument('--plan',type=Path,default=BACKEND/'data/later_validation_plan.json')
    parser.add_argument('--output',type=Path,default=BACKEND/'data/later_validation.json')
    parser.add_argument('--freeze',action='store_true')
    args = parser.parse_args()
    protected = {args.store.resolve(),(BACKEND/'data/model.json').resolve(),(BACKEND/'data/riot_model.json').resolve()}
    reserved = {'model.json','riot_model.json','riot_mlp_model.json','timeline_models.json','model_comparison.json',
                'native_champions.json','tip_benchmarks.json','item_evidence.json','low_elo_evaluation.json'}
    if (args.plan.resolve() in protected or args.output.resolve() in protected|{args.plan.resolve()}
            or args.plan.name in reserved or args.output.name in reserved):
        parser.error('Preserve the collection, plan and trained models.')
    records = read_collection(args.store)
    if args.freeze:
        plan = freeze(records,(BACKEND/'data/model.json').read_bytes(),(BACKEND/'data/riot_model.json').read_bytes())
        args.plan.parent.mkdir(parents=True,exist_ok=True)
        with args.plan.open('x',encoding='utf-8') as handle:
            handle.write(json.dumps(plan,indent=2,allow_nan=False)+'\n')
        print('Frozen model copies and exclusions saved. No model was trained or replaced.')
    else:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        result = evaluate(records,plan)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
        print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':
    main()
