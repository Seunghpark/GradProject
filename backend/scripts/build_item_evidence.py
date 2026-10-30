"""Describe final inventories; evaluate train-only item frequency on the fixed old holdout.

This tests item-choice coverage, not whether buying an item improves a match outcome.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from scripts.benchmark_models import fixed_rows


def patch(value):
    return '.'.join(str(value).split('.')[:2])


def group_key(player, version):
    return f"{player['championId']}:{player.get('teamPosition', 'UNKNOWN')}:{patch(version)}"


def inventories(record):
    for player in record['match']['info']['participants']:
        items = sorted({player.get(f'item{index}', 0) for index in range(6)} - {0})
        if items:
            yield player, items


def build(input_path, reference_path, output_path):
    if (output_path.resolve() in (input_path.resolve(), reference_path.resolve())
            or output_path.name in {'model.json', 'riot_model.json', 'riot_mlp_model.json', 'timeline_models.json', 'model_comparison.json'}):
        raise ValueError('Preserve input and model files')
    earlier, later, reference, audit = fixed_rows(input_path, reference_path)
    train_ids, test_ids = {row['match_id'] for row in earlier}, {row['match_id'] for row in later}
    groups, all_items, seen, test = {}, Counter(), set(), []
    for line in input_path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        match = record['match']
        match_id = match['metadata']['matchId']
        if match_id in seen or match_id not in train_ids | test_ids:
            continue
        seen.add(match_id)
        if match_id in test_ids:
            test.append(record)
            continue
        for player, items in inventories(record):
            key = group_key(player, match['info']['gameVersion'])
            group = groups.setdefault(key, {'champion': player['championName'], 'samples': 0,
                                            'counts': Counter(), 'matches': set()})
            group['samples'] += 1
            group['matches'].add(match_id)
            group['counts'].update(items)
            all_items.update(items)
    output_groups = {}
    for key, value in groups.items():
        if len(value['matches']) < 5:
            continue
        output_groups[key] = {'champion': value['champion'], 'samples': value['samples'],
                              'unique_matches': len(value['matches']), 'items': [
                                  {'id': item, 'count': count, 'frequency': count / value['samples']}
                                  for item, count in sorted(value['counts'].items(), key=lambda pair: (-pair[1], pair[0]))[:3]]}
    baseline = {item for item, _ in sorted(all_items.items(), key=lambda pair: (-pair[1], pair[0]))[:3]}
    trials, covered_games, game_scores = 0, set(), defaultdict(list)
    player_rows = 0
    for record in test:
        match = record['match']
        for player, items in inventories(record):
            player_rows += 1
            group = output_groups.get(group_key(player, match['info']['gameVersion']))
            if group is None:
                continue
            candidates = {item['id'] for item in group['items']}
            trials += 1
            covered_games.add(match['metadata']['matchId'])
            game_scores[match['metadata']['matchId']].append((len(candidates & set(items)) / len(candidates),
                                                            len(baseline & set(items)) / len(baseline)))
    # Average within a match first; ten participants are not ten independent matches.
    means = [tuple(sum(row[i] for row in rows) / len(rows) for i in (0, 1)) for rows in game_scores.values()]
    report = {'status': 'exploratory_item_choice_coverage', 'train_matches': len(train_ids),
              'holdout_matches': len(test_ids), 'holdout_player_rows': player_rows,
              'covered_player_rows': trials, 'covered_matches': len(covered_games),
              'coverage': trials / player_rows if player_rows else 0,
              'candidate_precision_at_3': sum(row[0] for row in means) / len(means) if means else None,
              'global_baseline_precision_at_3': sum(row[1] for row in means) / len(means) if means else None,
              'validated_win_improvement': False,
              'notice': 'Final inventory frequencies, not purchase order or causal item advice. Same champion/role/patch; groups need five training matches. Already-viewed holdout; participants overlap. Metrics describe item-choice coverage only.'}
    payload = {'created_at': datetime.now(timezone.utc).isoformat(), **audit,
               'minimum_group_matches': 5, 'groups': output_groups, 'evaluation': report}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BACKEND / 'data/riot_matches.jsonl')
    parser.add_argument('--reference', type=Path, default=BACKEND / 'data/model.json')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data/item_evidence.json')
    args = parser.parse_args()
    print(json.dumps(build(args.input, args.reference, args.output), indent=2))


if __name__ == '__main__':
    main()
