"""Download Riot's official public root certificate over verified HTTPS."""
from pathlib import Path
import ssl
from urllib.request import urlopen
from urllib.error import URLError

URL = 'https://static.developer.riotgames.com/docs/lol/riotgames.pem'


def main():
    path = Path(__file__).resolve().parents[1] / 'data' / 'riotgames.pem'
    with urlopen(URL, timeout=12, context=ssl.create_default_context()) as response:
        if response.geturl() != URL:
            raise ValueError('Unexpected certificate redirect; no file saved')
        content = response.read(100001)
    if len(content) > 100000 or b'-----BEGIN CERTIFICATE-----' not in content:
        raise ValueError('Unexpected certificate response; no file saved')
    ssl.create_default_context(cadata=content.decode('ascii'))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.pem.tmp')
    temporary.write_bytes(content)
    temporary.replace(path)
    print('Riot public root certificate installed. Start an actual League game, then connect Own live stats in LolAi.')


if __name__ == '__main__':
    try:
        main()
    except (URLError, OSError, ValueError):
        raise SystemExit('Certificate setup failed; no existing certificate was replaced. Check your connection and run setup-live.cmd in your normal Cursor terminal.') from None
