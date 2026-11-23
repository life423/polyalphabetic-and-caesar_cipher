"""The deployment includes its runtime/configuration but no local files."""
from zipfile import ZipFile

from scripts.package_web import build_package


def test_web_deployment_package_is_complete_and_does_not_include_local_files(tmp_path):
    path = build_package(tmp_path / 'web.zip')
    with ZipFile(path) as package:
        names = set(package.namelist())
        assert {'web_app.py', 'requirements.txt', 'startup.sh', '.streamlit/config.toml',
                'src/services/web_service.py', 'src/core/ciphers.py'} <= names
        assert not any(name.startswith(('.venv/', 'tests/', '.git/')) for name in names)
        assert 'src/ai/english_language_model.json' in names
        assert not any(name.endswith(('.exe', '.pyc', '.env')) for name in names)
        assert b'\r' not in package.read('startup.sh')
        assert package.testzip() is None
