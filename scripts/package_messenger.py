"""Build an allowlisted backend-only ZIP; never changes Azure configuration."""
import argparse
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
STARTUP = '''#!/bin/sh
set -eu
exec gunicorn --bind "0.0.0.0:${PORT:-8000}" --workers 1 --threads 4 --timeout 60 --access-logfile /dev/null src.messenger.wsgi:application
'''


def package(output):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = [(ROOT / name, name) for name in (
        'src/messenger/__init__.py', 'src/messenger/app.py',
        'src/messenger/wsgi.py', 'src/messenger/push.py', 'src/messenger/admin.py', 'src/messenger/README.md',
        'scripts/run_messenger.py', 'messenger-requirements.txt')]
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path, name in files:
            archive.write(path, name)
        archive.writestr('requirements.txt', (ROOT / 'messenger-requirements.txt').read_text())
        archive.writestr('startup.sh', STARTUP)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/messenger-api.zip')
    print(package(parser.parse_args().output))
