"""Build the self-contained Azure Static Web Apps distribution."""
from pathlib import Path
import shutil
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def build(output=None, runtime_package=None):
    output = Path(output) if output is not None else ROOT / 'dist/static'
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'static', output, dirs_exist_ok=True)
    runtime = output / 'runtime'
    runtime.mkdir(exist_ok=True)
    package = Path(runtime_package) if runtime_package is not None else ROOT / 'tools/runtime/node_modules/pyodide'
    for name in ('pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
                 'python_stdlib.zip', 'pyodide-lock.json'):
        shutil.copy2(package / name, runtime / name)
    with zipfile.ZipFile(output / 'engine.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in (ROOT / 'src').rglob('*.py'):
            if 'messenger' in path.relative_to(ROOT / 'src').parts:
                continue  # The network service is deployed separately from the offline engine.
            archive.write(path, path.relative_to(ROOT).as_posix())
        for name in ('cipher_identifier.json', 'english_language_model.json'):
            model = ROOT / 'src/ai' / name
            archive.write(model, model.relative_to(ROOT).as_posix())
    print(output)
    return output


if __name__ == '__main__':
    build()
