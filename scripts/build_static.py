"""Build the self-contained Azure Static Web Apps distribution."""
from pathlib import Path
import shutil
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def build():
    output = ROOT / 'dist/static'
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'static', output, dirs_exist_ok=True)
    runtime = output / 'runtime'
    runtime.mkdir(exist_ok=True)
    package = ROOT / 'tools/runtime/node_modules/pyodide'
    for name in ('pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
                 'python_stdlib.zip', 'pyodide-lock.json'):
        shutil.copy2(package / name, runtime / name)
    with zipfile.ZipFile(output / 'engine.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in (ROOT / 'src').rglob('*.py'):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(output)


if __name__ == '__main__':
    build()
