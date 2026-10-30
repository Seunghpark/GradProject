"""Build local review benchmarks; optional fresh pre-match rank observations enable tier cohorts."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.tips_engine import build_benchmarks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BACKEND / 'data/riot_matches.jsonl')
    parser.add_argument('--enrollments', type=Path, default=BACKEND / 'data/low_elo_enrollments.jsonl')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data/tip_benchmarks.json')
    args = parser.parse_args()
    if (args.output.resolve() in {args.input.resolve(), args.enrollments.resolve()} or args.output.name in
            {'model.json', 'riot_model.json', 'riot_mlp_model.json', 'timeline_models.json', 'model_comparison.json', 'native_champions.json', 'item_evidence.json'}):
        parser.error('Preserve source records and existing research artifacts')
    content = args.input.read_bytes()
    records = [json.loads(line) for line in content.decode('utf-8-sig').splitlines() if line.strip()]
    observations = [json.loads(line) for line in args.enrollments.read_text(encoding='utf-8-sig').splitlines() if line.strip()] if args.enrollments.exists() else []
    result = build_benchmarks(records, observations)
    result['input_sha256'] = hashlib.sha256(content).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(args.output)
    print(json.dumps({'source': result['source'], 'unique_matches': result['unique_matches'],
                      'participant_rows': len(result['rows']), 'tier_labeled_rows': sum(row['tier'] is not None for row in result['rows'])}))


if __name__ == '__main__':
    main()
