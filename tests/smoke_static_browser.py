"""Exercise the actual WebAssembly engine, downloads, analysis and layouts."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def check(url, screenshots):
    screenshots = Path(screenshots)
    screenshots.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator('#encrypt')).to_be_enabled(timeout=90000)
        expect(page.get_by_role('button', name='Find key', exact=True)).to_be_visible()
        expect(page.get_by_role('button', name='Analyze cipher', exact=True)).to_have_count(0)
        # Once loaded, cipher operations must work without a network connection.
        context.set_offline(True)
        unknown_plaintext = (
            'We planted carrots beside the garden fence and watered them each morning. '
            'The children measured the green leaves while their teacher recorded the weather. '
            'After several weeks we carried a basket of fresh vegetables into the kitchen. '
            'Everyone helped prepare a warm meal and shared stories around the table.'
        )
        page.locator('#key').fill('7')
        page.locator('#message').fill(unknown_plaintext)
        page.locator('#encrypt').click()
        expect(page.locator('#status')).to_have_text('Encryption complete.')
        unknown_ciphertext = page.locator('#result').input_value()
        page.locator('#reuse').click()
        page.locator('#cipher').select_option('Vigenère')
        # Automatic recovery ignores the selected cipher and its empty key.
        page.locator('#identify').click()
        expect(page.locator('#result')).to_have_value(unknown_plaintext, timeout=60000)
        expect(page.locator('#cipher')).to_have_value('Caesar')
        expect(page.locator('#key')).to_have_value('7')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(screenshots / f'identification-{width}.png'), full_page=True)
        page.locator('#analyze').click()
        expect(page.locator('#suggestions button')).not_to_have_count(0)
        expect(page.locator('#suggestions')).to_contain_text('locally trained English language model')
        for width in (390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(screenshots / f'language-model-{width}.png'), full_page=True)
        page.locator('#suggestions button').first.click()
        expect(page.locator('#result')).to_have_value(unknown_plaintext)
        page.locator('#message').fill('too short')
        page.locator('#identify').click()
        expect(page.locator('#status')).to_contain_text('at least 100 English letters')
        expect(page.locator('#identification button')).to_have_count(0)
        page.locator('#upload').set_input_files({
            'name': 'unknown.txt', 'mimeType': 'text/plain',
            'buffer': ('zovya\r\n' + unknown_ciphertext + '\n').encode('utf-8')})
        expect(page.locator('#status')).to_contain_text('File opened')
        page.locator('#identify').click()
        expect(page.locator('#result')).to_have_value('short\n' + unknown_plaintext + '\n', timeout=60000)
        with page.expect_download() as automatic_download:
            page.locator('#download').click()
        assert automatic_download.value.suggested_filename == 'unknown_decrypted.txt'
        assert Path(automatic_download.value.path()).read_bytes() == ('short\r\n' + unknown_plaintext + '\n').encode('utf-8')
        # Regression: the user's ORBIT example must crack directly from default Caesar controls.
        orbit_ciphertext = ('Hyf wer fcaxfmbbhfp tbhcu bjhjv upx eljmm jrmtxm, nimks r tqgucf ttbkfzg plsvxr sfabrv upx bfsbasio ebbupe. '
                            'Th djlgwxib, mvv dikskbsxf ujavcmfzxr r gwerve vhhv cmgsrup mvv umesjdwis. '
                            'Zu lxgtsqusu b pbrufv kcfn jxvzol mvv mqufrsg tbu b ehcufv uco dwghrjvbbx upx aztabbx ffisujbbce smvciea. '
                            'Mvv gqgoc jvlhivkmwfo etg jjuizv: czbbx upx pibal qfnxtgj bvw krjb nbkjt mvv nwkbzoo uscma usxjv mc ijvz.')
        orbit_plaintext = ('The old observatory stood above the quiet valley, where a single lantern burned beside the northern window. '
                           'At midnight, the caretaker discovered a folded note beneath the telescope. '
                           'It described a hidden room behind the library and a wooden box containing the missing expedition records. '
                           'The final instruction was simple: bring the brass compass and wait until the morning bells begin to ring.')
        page.locator('#cipher').select_option('Caesar')
        page.locator('#key').fill('3')
        page.locator('#message').fill(orbit_ciphertext)
        page.get_by_role('button', name='Identify & crack', exact=True).focus()
        page.keyboard.press('Enter')
        expect(page.locator('#result')).to_have_value(orbit_plaintext, timeout=60000)
        expect(page.locator('#cipher')).to_have_value('Vigenère')
        expect(page.locator('#key')).to_have_value('orbit')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(screenshots / f'auto-crack-{width}.png'), full_page=True)
        page.locator('#identify').click()
        page.locator('#message').fill('A newer message must not be overwritten by an older request.')
        expect(page.locator('#identify')).to_be_enabled(timeout=60000)
        expect(page.locator('#result')).to_have_value('')
        expect(page.locator('#message')).to_have_value('A newer message must not be overwritten by an older request.')
        message = 'Hello world! Café, 日本語.\nAnother line.'
        for cipher, key in [('Caesar', '7'), ('Vigenère', 'LEMON'),
                            ('Substitution', 'QWERTYUIOPASDFGHJKLZXCVBNM'),
                            ('Rail Fence', '3'), ('Affine', '5')]:
            page.locator('#cipher').select_option(cipher)
            page.locator('#key').fill(key)
            page.locator('#message').fill(message)
            page.locator('#encrypt').click()
            expect(page.locator('#status')).to_have_text('Encryption complete.')
            assert page.locator('#result').input_value() != message
            page.locator('#reuse').click()
            page.locator('#decrypt').click()
            expect(page.locator('#status')).to_have_text('Decryption complete.')
            assert page.locator('#result').input_value() == (''.join(message.split()) if cipher == 'Rail Fence' else message), cipher
        page.locator('#cipher').select_option('Columnar transposition')
        page.locator('#key').fill('ZEBRAS')
        page.locator('#message').fill('WEAREDISCOVEREDFLEEATONCE')
        page.locator('#encrypt').click()
        expect(page.locator('#result')).to_have_value('EVLNXACDTXESEAXROFOXDEECXWIREE')
        page.locator('#cipher').select_option('Substitution')
        page.locator('#generate').click()
        expect(page.locator('#status')).to_contain_text('key generated')
        assert len(set(page.locator('#key').input_value().upper())) == 26
        text = 'The quick brown fox jumps over the lazy dog. This secret message is written in English. ' * 3
        for cipher, key in [('Caesar', '7'), ('Vigenère', 'LEMON'),
                            ('Rail Fence', '3'), ('Affine', '5')]:
            page.locator('#cipher').select_option(cipher)
            page.locator('#key').fill(key)
            page.locator('#message').fill(text)
            page.locator('#encrypt').click()
            expect(page.locator('#status')).to_have_text('Encryption complete.')
            page.locator('#reuse').click()
            page.locator('#analyze').click()
            expect(page.locator('#suggestions button')).not_to_have_count(0, timeout=60000)
            page.locator('#suggestions button').first.click()
            expect(page.locator('#status')).to_have_text('Decryption complete.')
            assert page.locator('#result').input_value() == (''.join(text.split()) if cipher == 'Rail Fence' else text), cipher
        page.locator('#cipher').select_option('Vigenère')
        page.locator('#message').fill('short')
        page.locator('#analyze').click()
        expect(page.locator('#status')).to_contain_text('at least 20 English letters')
        page.locator('#cipher').select_option('Rail Fence')
        page.locator('#message').fill('A')
        page.locator('#analyze').click()
        expect(page.locator('#status')).to_contain_text('No key suggestions were found')
        expect(page.locator('#suggestions button')).to_have_count(0)
        page.locator('#upload').set_input_files({
            'name': 'story.txt', 'mimeType': 'text/plain',
            'buffer': b'HELLOWORLD\r\nSECONDLINE\n\r\nLASTLINE\r'})
        expect(page.locator('#status')).to_contain_text('File opened')
        for name, content, error in [('broken.txt', b'\xff\xfe', 'not UTF-8'),
                                     ('empty.txt', b' \r\n', 'empty'),
                                     ('large.txt', b'A' * 1048577, 'smaller than 1 MB')]:
            page.locator('#upload').set_input_files({'name': name, 'mimeType': 'text/plain', 'buffer': content})
            expect(page.locator('#status')).to_contain_text(error)
            expect(page.locator('#status')).to_contain_text('previous message has been kept')
            expect(page.locator('#message')).to_have_value('HELLOWORLD\nSECONDLINE\n\nLASTLINE\n')
        page.locator('#encrypt').click()
        expect(page.locator('#status')).to_have_text('Encryption complete.')
        page.locator('#reuse').click()
        page.locator('#decrypt').click()
        expect(page.locator('#status')).to_have_text('Decryption complete.')
        with page.expect_download() as download:
            page.locator('#download').click()
        assert Path(download.value.path()).read_bytes() == b'HELLOWORLD\r\nSECONDLINE\n\r\nLASTLINE\r'
        page.locator('#message').fill('changed')
        expect(page.locator('#download')).to_be_disabled()
        expect(page.locator('#result')).to_have_value('')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(screenshots / f'static-{width}.png'), full_page=True)
        page.locator('#cipher').focus()
        page.keyboard.press('Tab')
        assert page.locator('#key').evaluate('(element) => element === document.activeElement')
        context.set_offline(False)
        other = browser.new_page()
        other.goto(url)
        expect(other.locator('#message')).to_have_value('')
        assert not errors, errors
        isolated = browser.new_context()
        other = isolated.new_page()
        other.route('**/engine.zip', lambda route: route.abort())
        other.goto(url)
        expect(other.locator('#retry')).to_be_visible(timeout=90000)
        expect(other.locator('#encrypt')).to_be_disabled()
        other.unroute('**/engine.zip')
        other.locator('#retry').click()
        expect(other.locator('#encrypt')).to_be_enabled(timeout=90000)
        expect(other.locator('#message')).to_have_value('')
        expect(other.locator('#result')).to_have_value('')
        other.locator('#message').focus()
        other.keyboard.press('Tab')
        assert other.evaluate('document.activeElement.id') == 'upload'
        browser.close()
    print('Static browser checks passed: six ciphers, four analyzers, exact file downloads, offline operations, isolated sessions and four viewport widths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8502')
    parser.add_argument('--screenshots', default='dist/static-checks')
    args = parser.parse_args()
    check(args.url, args.screenshots)
