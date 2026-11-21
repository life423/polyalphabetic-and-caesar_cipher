"""Test the real web app locally or on Azure, including touch layouts and downloads."""
import argparse
from pathlib import Path
import tempfile
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def choose_cipher(page, cipher):
    page.get_by_role('combobox').click()
    page.get_by_role('option', name=cipher, exact=True).click()
    expect(page.get_by_role('combobox')).to_have_value(cipher)


def check_web_app(url, screenshots):
    screenshots = Path(screenshots)
    screenshots.mkdir(parents=True, exist_ok=True)
    deadline = monotonic() + 90
    while True:
        try:
            with urlopen(url.rstrip('/') + '/_stcore/health', timeout=5) as response:
                if response.status == 200 and response.read().strip() == b'ok':
                    break
        except (URLError, OSError):
            pass
        if monotonic() >= deadline:
            raise TimeoutError(f'The web app did not become healthy: {url}')
        sleep(0.5)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={'width':1440, 'height':1000}, accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        expect(page.get_by_role('heading', name='CipherCraft', exact=True)).to_be_visible(timeout=90000)
        expect(page.get_by_role('button', name='Encrypt message', exact=True)).to_be_visible()
        page.screenshot(path=str(screenshots / 'desktop.png'), full_page=True)

        page.get_by_label('Your message', exact=True).fill('Hello café Ω!')
        page.get_by_role('button', name='Encrypt message', exact=True).click()
        expect(page.get_by_text('Khoor fdié Ω!', exact=True)).to_be_visible()
        with page.expect_download() as download:
            page.get_by_role('button', name='Download .txt', exact=True).click()
        item = download.value
        assert item.suggested_filename == 'message_encrypted.txt'
        assert Path(item.path()).read_text(encoding='utf-8') == 'Khoor fdié Ω!'
        page.get_by_role('button', name='Use result as input', exact=True).click()
        page.get_by_role('button', name='Decrypt message', exact=True).click()
        expect(page.get_by_text('Hello café Ω!', exact=True)).to_be_visible()

        # A real keyword -> encrypt -> analyze -> apply -> decrypt workflow.
        choose_cipher(page, 'Vigenère')
        page.get_by_text('Encrypt', exact=True).click()
        page.get_by_label('Keyword', exact=True).fill('larder')
        plaintext = ('When in the Course of human events it becomes necessary for one people '
                     'to dissolve the political bands which have connected them with another '
                     'and to assume among the powers of the earth the separate and equal '
                     'station to which the Laws of Nature and of Natures God entitle them.')
        page.get_by_label('Your message', exact=True).fill(plaintext)
        page.get_by_role('button', name='Encrypt message', exact=True).click()
        expect(page.locator('[data-testid="stCode"]')).to_be_visible()
        ciphertext = page.locator('[data-testid="stCode"]').inner_text()
        page.get_by_label('Your message', exact=True).fill(ciphertext)
        page.get_by_role('button', name='Analyze ciphertext', exact=True).click()
        expect(page.get_by_role('heading', name='Key suggestions', exact=True)).to_be_visible(timeout=30000)
        page.get_by_role('button', name='Use key & decrypt', exact=True).click()
        expect(page.get_by_text(plaintext, exact=True)).to_be_visible()
        page.screenshot(path=str(screenshots / 'vigenere-result.png'), full_page=True)
        page.get_by_label('Your message', exact=True).fill('ABC')
        page.get_by_role('button', name='Analyze ciphertext', exact=True).click()
        expect(page.get_by_text('Vigenère analysis needs at least 20 English letters. Longer messages work better.',
                                exact=True)).to_be_visible()
        expect(page.get_by_role('button', name='Use key & decrypt', exact=True)).to_have_count(0)

        # Upload line boundaries survive encryption and downloaded output.
        choose_cipher(page, 'Rail Fence')
        page.get_by_text('Encrypt', exact=True).click()
        page.get_by_text('Text file', exact=True).click()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'message.txt'
            source.write_bytes(b'HELLO\r\nWORLD\n')
            page.locator('input[type=file]').set_input_files(str(source))
            expect(page.get_by_label('File preview', exact=True)).to_have_value('HELLO\nWORLD\n')
            page.get_by_role('button', name='Encrypt message', exact=True).click()
            with page.expect_download() as download:
                page.get_by_role('button', name='Download .txt', exact=True).click()
            assert Path(download.value.path()).read_bytes() == b'HOELL\r\nWDOLR\n'

        # A separate visitor sees no data or results from the first session.
        for name, width, height in [('phone',390,844), ('tablet',768,1024), ('narrow-phone',320,740)]:
            mobile = browser.new_context(viewport={'width':width,'height':height},
                                         is_mobile=True, has_touch=True, device_scale_factor=1)
            view = mobile.new_page()
            view.goto(url, wait_until='domcontentloaded', timeout=90000)
            expect(view.get_by_label('Your message', exact=True)).to_have_value('', timeout=90000)
            assert view.evaluate('document.documentElement.scrollWidth') <= width
            view.get_by_label('Your message', exact=True).fill('HELLO')
            view.get_by_role('button', name='Encrypt message', exact=True).click()
            expect(view.get_by_text('KHOOR', exact=True)).to_be_visible()
            assert view.evaluate('document.documentElement.scrollWidth') <= width
            view.screenshot(path=str(screenshots / f'{name}.png'), full_page=True)
            mobile.close()

        # Native keyboard focus is visible and reachable without a mouse.
        page.keyboard.press('Tab')
        assert page.evaluate('document.activeElement !== document.body')
        assert not errors, errors
        browser.close()
    print('Web browser checks passed: encryption, analysis, key application, UTF-8 downloads, '
          'multiline uploads, session isolation, keyboard focus, and three touch layouts.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8501')
    parser.add_argument('--screenshots', default='.venv/web-browser-checks')
    args = parser.parse_args()
    check_web_app(args.url, args.screenshots)
