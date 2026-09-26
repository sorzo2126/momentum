"""Inventory the complete publication; default mode only verifies saved hashes."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'__pycache__', '.ipynb_checkpoints', 'node_modules', '.venv', '.git'}


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inventory():
    rows = []
    for path in sorted(ROOT.rglob('*')):
        relative = path.relative_to(ROOT)
        if not path.is_file() or EXCLUDED_DIRS.intersection(relative.parts):
            continue
        if relative.as_posix() in {'manifest.json', 'file-index.csv'} or path.suffix == '.pyc':
            continue
        rows.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': digest(path)})
    return rows


def check_model_sources():
    manifests = sorted((ROOT / 'results').glob('*/frozen-model/manifest.json'))
    if len(manifests) != 7:
        raise ValueError(f'Expected seven fitted models, found {len(manifests)}')
    for path in manifests:
        for name, expected in json.loads(path.read_text())['code_sha256'].items():
            if digest(ROOT / 'model_snapshot/momentum' / name) != expected:
                raise ValueError(f'Model source mismatch: {path.parent.name}/{name}')
    return len(manifests)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Deliberately replace inventory after reviewed changes.')
    args = parser.parse_args()
    rows = inventory()
    models = check_model_sources()
    if args.write:
        manifest = {
            'synthetic': True, 'market_calibrated': False,
            'python': sys.version, 'platform': platform.platform(),
            'experiments': 11, 'forecast_metric_rows': 33, 'execution_books': 132,
            'model_source_commit': 'a7d07563ee79fa7d7b951e0f49e312c42c14a375',
            'inventory_scope': 'All bundle deliverables except manifest.json and file-index.csv; caches and installed dependencies excluded.',
            'files': rows,
        }
        (ROOT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
        with (ROOT / 'file-index.csv').open('w', encoding='utf8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['path', 'bytes', 'sha256'])
            writer.writeheader()
            writer.writerows(rows)
    else:
        expected = json.loads((ROOT / 'manifest.json').read_text())['files']
        actual = {row['path']: row for row in rows}
        saved = {row['path']: row for row in expected}
        problems = sorted(name for name in actual.keys() | saved.keys() if actual.get(name) != saved.get(name))
        if problems:
            raise ValueError('Inventory mismatches: ' + ', '.join(problems))
        with (ROOT / 'file-index.csv').open(encoding='utf8', newline='') as stream:
            index = [{**r, 'bytes': int(r['bytes'])} for r in csv.DictReader(stream)]
        if index != expected:
            raise ValueError('file-index.csv differs from manifest.json')
    print(json.dumps({'status': 'PASS', 'mode': 'write' if args.write else 'verify',
                      'inventoried_files': len(rows), 'bytes': sum(r['bytes'] for r in rows),
                      'frozen_models_matching_snapshot': models}))


if __name__ == '__main__':
    main()
