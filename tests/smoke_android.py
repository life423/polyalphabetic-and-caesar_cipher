"""Check the installed beta through its debug WebView. Leave the phone unlocked.

Forward the app's own webview_devtools_remote_<PID> socket to port 9224 first.
This script never inspects other apps or closes the Android app.
"""
import argparse

from playwright.sync_api import expect, sync_playwright


def check(endpoint):
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(endpoint)
        page = next(p for c in browser.contexts for p in c.pages if p.url == 'https://localhost/')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        assert page.evaluate('Capacitor.isNativePlatform()')
        expect(page.locator('#identify')).to_be_enabled(timeout=90000)
        page.locator('#crack-tab').click()
        page.locator('#message').fill('')
        page.locator('#example').click()
        page.locator('#identify').click()
        expect(page.locator('#key')).to_have_value('orbit', timeout=90000)
        expect(page.locator('#result')).to_contain_text('The old observatory')
        page.locator('#copy').click()
        expect(page.locator('#status')).to_have_text('Copied to clipboard.')
        page.locator('#manual-tab').click()
        text = 'Hello world!\nAnother line.'
        for cipher, key in [('Caesar', '7'), ('Vigenère', 'LEMON'),
                            ('Substitution', 'QWERTYUIOPASDFGHJKLZXCVBNM'),
                            ('Rail Fence', '3'), ('Affine', '5')]:
            page.locator('#cipher').select_option(cipher)
            page.locator('#key').fill(key)
            page.locator('#message').fill(text)
            page.locator('#encrypt').click()
            expect(page.locator('#status')).to_have_text('Encryption complete.')
            page.locator('#reuse').click()
            # Reuse focuses the message, opening Android's keyboard. Let its
            # viewport animation finish before targeting the next button.
            page.wait_for_timeout(450)
            page.locator('#decrypt').click()
            expect(page.locator('#status')).to_have_text('Decryption complete.')
            expected = ''.join(text.split()) if cipher == 'Rail Fence' else text
            assert page.locator('#result').text_content() == expected, cipher
        page.locator('#cipher').select_option('Columnar transposition')
        page.locator('#key').fill('ZEBRAS')
        page.locator('#message').fill('WEAREDISCOVEREDFLEEATONCE')
        page.locator('#encrypt').click()
        expect(page.locator('#result')).to_have_text('EVLNXACDTXESEAXROFOXDEECXWIREE')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors, errors
        page.locator('#crack-tab').click()
        page.locator('#message').fill('')
        page.locator('#example').click()
        page.locator('#identify').click()
        expect(page.locator('#key')).to_have_value('orbit', timeout=90000)
    print('Android WebView checks passed: bundled AI, six ciphers, native Copy, no horizontal overflow.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--endpoint', default='http://127.0.0.1:9224')
    check(parser.parse_args().endpoint)
