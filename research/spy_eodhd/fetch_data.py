"""Read EODHD bars using the existing Fractal credential; never log the token."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import requests


def credential(fractal_dir=None):
    key = os.getenv('EODHD_API_KEY', '')
    if not key and fractal_dir:
        for line in (Path(fractal_dir) / '.env').read_text(encoding='utf-8-sig').splitlines():
            if line.strip().startswith('EODHD_API_KEY='):
                key = line.split('=', 1)[1].strip().strip('"').strip("'")
    if not key:
        raise ValueError('Set EODHD_API_KEY or provide --fractal-dir containing the existing .env.')
    return key


def download(symbol, start, end, destination, fractal_dir=None):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cached = destination.exists()
    if not cached:
        key = credential(fractal_dir)
        seconds = lambda s: int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())
        try:
            response = requests.get('https://eodhd.com/api/intraday/' + symbol,
                params={'api_token': key, 'fmt': 'json', 'interval': '5m',
                        'from': seconds(start), 'to': seconds(end)}, timeout=60)
        except requests.RequestException as error:
            raise RuntimeError('EODHD request failed: ' + type(error).__name__) from None
        if response.status_code != 200:
            raise RuntimeError('EODHD returned HTTP ' + str(response.status_code))
        payload = response.json()
        if not isinstance(payload, list) or not payload:
            raise ValueError('EODHD did not return a nonempty bar list.')
        destination.write_text(json.dumps(payload, separators=(',', ':')), encoding='utf-8')
    else:
        payload = json.loads(destination.read_text(encoding='utf-8'))
    metadata = dict(provider='EODHD', symbol=symbol, interval='5m', from_utc=start,
        to_utc=end, inspected_at=datetime.now(timezone.utc).isoformat(), cached=cached,
        rows=len(payload), sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        endpoint='https://eodhd.com/api/intraday/{symbol}', credential_saved=False)
    destination.with_suffix('.metadata.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fractal-dir')
    parser.add_argument('--symbol', default='SPY.US')
    parser.add_argument('--start', default='2025-09-26T00:00:00Z')
    parser.add_argument('--end', default='2026-09-26T00:00:00Z')
    parser.add_argument('--output', default=str(Path(__file__).parent/'private/raw/SPY.US-5m.json'))
    args = parser.parse_args()
    print(json.dumps(download(args.symbol, args.start, args.end, args.output, args.fractal_dir)))
