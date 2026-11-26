"""Public legal pages remain readable and reachable without a Messages login."""
from pathlib import Path
from playwright.sync_api import expect, sync_playwright


def check():
    output = Path('dist/legal-checks')
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        for width, height in [(390, 844), (768, 1024), (1440, 1000)]:
            page.set_viewport_size({'width': width, 'height': height})
            for name, title in [('terms', 'Terms of Service'), ('privacy', 'Privacy policy')]:
                response = page.goto(f'http://localhost:8502/{name}.html')
                assert response.status == 200
                expect(page.get_by_role('heading', name=title, exact=True)).to_be_visible()
                expect(page.get_by_role('link', name='drew@drewclark.io').first).to_have_attribute('href', 'mailto:drew@drewclark.io')
                assert page.locator('input[type=password]').count() == 0
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                if width == 390:
                    page.add_style_tag(content='html {font-size: 200%}')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    page.reload()
                page.screenshot(path=str(output / f'{name}-{width}.png'), full_page=True)
        assert not errors, errors
        browser.close()
    print('Terms/privacy: public access, support links, phone/tablet/desktop and enlarged-text checks passed.')


if __name__ == '__main__':
    check()
