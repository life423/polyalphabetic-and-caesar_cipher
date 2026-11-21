"""Create the App Service deployment ZIP without local files or desktop binaries."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]


def build_package(output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sources = [ROOT / name for name in (
        'web_app.py', 'requirements.txt', 'startup.sh', '.streamlit/config.toml',
    )]
    sources.extend(sorted((ROOT / 'src').rglob('*.py')))
    with ZipFile(output, 'w', compression=ZIP_DEFLATED) as archive:
        for source in sources:
            content = source.read_bytes()
            if source.name == 'startup.sh':
                content = content.replace(b'\r\n', b'\n')
            archive.writestr(source.relative_to(ROOT).as_posix(), content)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(build_package(args.output))
