"""Build LolAi's native champion explorer without third-party analytics APIs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
from app.native_catalog import build_catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=BACKEND / 'data/riot_matches.jsonl')
    parser.add_argument('--output', type=Path, default=BACKEND / 'data/native_champions.json')
    args = parser.parse_args()
    if (args.input.resolve() == args.output.resolve() or args.output.name in
            {'model.json', 'riot_model.json', 'riot_mlp_model.json', 'timeline_models.json', 'model_comparison.json'}):
        parser.error('Preserve source records and model artifacts')
    content = args.input.read_bytes()
    data = build_catalog(json.loads(line) for line in content.decode('utf-8-sig').splitlines() if line.strip())
    data['input_sha256'] = hashlib.sha256(content).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(args.output)
    print(json.dumps({'source': data['source'], 'unique_matches': data['unique_matches'],
                      'champion_role_patch_groups': len(data['groups']), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
