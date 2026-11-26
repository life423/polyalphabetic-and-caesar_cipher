"""Rasterize our code-owned store SVGs at their required Google Play sizes."""
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / 'dist/play-store'
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for name, width, height in [('icon', 512, 512), ('feature', 1024, 500)]:
            page = browser.new_page(viewport={'width': width, 'height': height},
                                    device_scale_factor=1)
            page.set_content('<style>body{margin:0}</style>' +
                             (root / f'mobile/store/{name}.svg').read_text(encoding='utf-8'))
            page.screenshot(path=str(output / f'{name}.png'))
            page.close()
        browser.close()
    print(output)


if __name__ == '__main__':
    main()
