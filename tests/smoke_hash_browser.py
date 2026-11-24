"""Real browser SHA-256, file integrity, races and isolated app workflows."""
import argparse
import hashlib
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def check(url, screenshots):
    output = Path(screenshots)
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator('#identify')).to_be_enabled(timeout=90000)
        # Preserve a real cipher result and in-progress campaign across lab use.
        page.locator('#manual-tab').click()
        page.locator('#message').fill('Keep my cipher work.')
        page.locator('#key').fill('7')
        page.locator('#encrypt').click()
        expect(page.locator('#status')).to_have_text('Encryption complete.')
        cipher_result = page.locator('#result').text_content()
        page.locator('#play-tab').click()
        page.locator('#guess-A').fill('T')
        page.locator('#hash-tab').click()
        expect(page.locator('#hash-content')).to_be_visible()
        expect(page.locator('#tools-workspace')).to_be_hidden()
        expect(page.locator('#play-panel')).to_be_hidden()
        context.set_offline(True)
        for text in ('', 'abc', 'ABC', 'abc ', 'Café, 日本語.\nSecond line.'):
            page.locator('#hash-text').fill(text)
            page.locator('#hash-text-run').click()
            expect(page.locator('#hash-text-digest')).to_have_text(sha(text))
            expect(page.locator('#hash-text-bytes')).to_contain_text(str(len(text.encode('utf-8'))))
        page.locator('#hash-example').click()
        expect(page.locator('#hash-text-digest')).to_have_text(sha('Meet at dawn.'))
        expect(page.locator('#hash-changed-digest')).to_have_text(sha('Meet at Dawn.'))
        difference = (int(sha('Meet at dawn.'), 16) ^ int(sha('Meet at Dawn.'), 16)).bit_count()
        expect(page.locator('#hash-difference')).to_have_text(f'{difference} of 256 output bits changed ({difference / 256 * 100:.1f}%)')
        expect(page.locator('#hash-bits span')).to_have_count(256)
        expect(page.locator('#hash-bits [data-changed="true"]')).to_have_count(difference)
        page.locator('#hash-changed').fill('Meet at dawn.')
        expect(page.locator('#hash-text-results')).to_be_hidden()
        page.locator('#hash-text-run').click()
        expect(page.locator('#hash-difference')).to_contain_text('0 of 256')
        page.locator('#hash-bits-details').evaluate('(e)=>e.open=true')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(output / f'hash-text-{width}.png'), full_page=True)
        # Clipboard success/failure leaves selectable results available.
        context.grant_permissions(['clipboard-read', 'clipboard-write'])
        page.locator('#hash-text-copy').click()
        expect(page.locator('#hash-status')).to_have_text('SHA-256 copied to clipboard.')
        assert page.evaluate('navigator.clipboard.readText()') == sha('Meet at dawn.')
        page.evaluate("Object.defineProperty(navigator.clipboard,'writeText',{configurable:true,value:()=>Promise.reject(new Error('blocked'))})")
        page.locator('#hash-changed-copy').click()
        expect(page.locator('#hash-status')).to_contain_text('Copy is unavailable')
        expect(page.locator('#hash-changed-digest')).to_be_focused()
        page.evaluate('delete navigator.clipboard.writeText')
        # An older digest must not overwrite a newer input.
        page.evaluate('''window.originalDigest=crypto.subtle.digest.bind(crypto.subtle);
            Object.defineProperty(crypto.subtle,'digest',{configurable:true,value:async(...args)=>{
              await new Promise(resolve=>window.releaseDigest=resolve); return window.originalDigest(...args);}});''')
        page.locator('#hash-compare-toggle').click()
        page.locator('#hash-text-run').click()
        page.locator('#hash-text').fill('Newer input')
        page.evaluate('window.releaseDigest()')
        expect(page.locator('#hash-text-results')).to_be_hidden()
        expect(page.locator('#hash-status')).to_contain_text('Text changed')
        page.evaluate('delete crypto.subtle.digest')
        page.locator('#hash-text-run').click()
        expect(page.locator('#hash-text-digest')).to_have_text(sha('Newer input'))
        page.locator('#hash-file-tab').click()
        contents = b'First\r\nSecond\n\xff\x00'
        expected = hashlib.sha256(contents).hexdigest()
        page.locator('#hash-file').set_input_files({'name': 'evidence.bin', 'mimeType': 'application/octet-stream', 'buffer': contents})
        page.locator('#hash-expected').fill('  ' + expected.upper() + '  ')
        page.locator('#hash-file-run').click()
        expect(page.locator('#hash-file-digest')).to_have_text(expected)
        expect(page.locator('#hash-verification')).to_contain_text('Match —')
        page.locator('#hash-expected').fill('0' * 64)
        expect(page.locator('#hash-verification')).to_contain_text('Mismatch —')
        page.locator('#hash-expected').fill('not-a-digest')
        expect(page.locator('#hash-expected')).to_have_attribute('aria-invalid', 'true')
        expect(page.locator('#hash-verification')).to_be_hidden()
        expect(page.locator('#hash-file-digest')).to_have_text(expected)
        page.locator('#hash-expected').fill(expected)
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(output / f'hash-file-{width}.png'), full_page=True)
        page.locator('#hash-file').set_input_files({'name': 'empty.bin', 'mimeType': 'application/octet-stream', 'buffer': b''})
        expect(page.locator('#hash-file-results')).to_be_hidden()
        page.locator('#hash-expected').fill('')
        page.locator('#hash-file-run').click()
        expect(page.locator('#hash-file-digest')).to_have_text(sha(''))
        # Oversized files are rejected before reading them into memory.
        page.evaluate('''()=>{const f=new File(['x'],'oversized.bin'); Object.defineProperty(f,'size',{value:20*1024*1024+1});
            const dt=new DataTransfer();dt.items.add(f);const input=document.querySelector('#hash-file');input.files=dt.files;input.dispatchEvent(new Event('change'));}''')
        expect(page.locator('#hash-status')).to_contain_text('no larger than 20 MiB')
        expect(page.locator('#hash-file-run')).to_be_disabled()
        # A delayed file read cannot replace the newly selected file.
        page.locator('#hash-file').set_input_files({'name': 'old.bin', 'mimeType': 'application/octet-stream', 'buffer': b'old'})
        page.evaluate('''()=>{window.delayedFile=document.querySelector('#hash-file').files[0];
            window.delayedFile.arrayBuffer=()=>new Promise(resolve=>window.releaseFile=resolve);}''')
        page.locator('#hash-file-run').click()
        page.locator('#hash-file').set_input_files({'name': 'new.bin', 'mimeType': 'application/octet-stream', 'buffer': b'new'})
        page.evaluate('window.releaseFile(new TextEncoder().encode("old").buffer);delete window.delayedFile.arrayBuffer')
        expect(page.locator('#hash-file-results')).to_be_hidden()
        expect(page.locator('#hash-file-info')).to_contain_text('new.bin')
        page.locator('#hash-file-run').click()
        expect(page.locator('#hash-file-digest')).to_have_text(sha('new'))
        # Mode and workflow switches preserve successful independent results.
        page.locator('#hash-text-tab').click()
        expect(page.locator('#hash-text-digest')).to_have_text(sha('Newer input'))
        page.locator('#manual-tab').click()
        expect(page.locator('#message')).to_have_value('Keep my cipher work.')
        expect(page.locator('#key')).to_have_value('7')
        expect(page.locator('#result')).to_have_text(cipher_result)
        page.locator('#play-tab').click()
        expect(page.locator('#guess-A')).to_have_value('T')
        page.locator('#play-tab').focus()
        page.keyboard.press('End')
        expect(page.locator('#learn-tab')).to_be_focused()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#crack-tab')).to_be_focused()
        # A failed Python engine must not prevent native browser hashing.
        separate = browser.new_context()
        separate.route('**/worker.js', lambda route: route.abort())
        independent = separate.new_page()
        independent.goto(url)
        independent.locator('#hash-tab').click()
        independent.locator('#hash-text').fill('abc')
        independent.locator('#hash-text-run').click()
        expect(independent.locator('#hash-text-digest')).to_have_text(sha('abc'))
        # A failed lazy module can be retried without reloading other work.
        retry_context = browser.new_context()
        retry_context.route('**/hash-lab.js*', lambda route: route.abort())
        retry = retry_context.new_page()
        retry.goto(url)
        retry.locator('#hash-tab').click()
        expect(retry.locator('#hash-error')).to_be_visible()
        retry_context.unroute('**/hash-lab.js*')
        retry.locator('#hash-retry').click()
        expect(retry.locator('#hash-content')).to_be_visible()
        retry.locator('#hash-text').fill('abc')
        retry.locator('#hash-text-run').click()
        expect(retry.locator('#hash-text-digest')).to_have_text(sha('abc'))
        no_api = browser.new_context()
        no_api.add_init_script("Object.defineProperty(Crypto.prototype,'subtle',{get:()=>undefined})")
        unsupported = no_api.new_page()
        unsupported.goto(url)
        unsupported.locator('#hash-tab').click()
        expect(unsupported.locator('#hash-status')).to_contain_text('cannot calculate SHA-256')
        expect(unsupported.locator('#hash-text-run')).to_be_disabled()
        expect(unsupported.locator('#hash-example')).to_be_disabled()
        assert not errors, errors
        browser.close()
    print('Hash Lab passed: SHA-256 vectors, UTF-8, exact file bytes, bit differences, verification, async guards, clipboard, offline operation and workflow isolation at four widths.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:8502')
    parser.add_argument('--screenshots', default='dist/hash-checks')
    args = parser.parse_args()
    check(args.url, args.screenshots)
