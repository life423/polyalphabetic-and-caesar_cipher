"""Password lesson: real derivation vectors, feedback, privacy and responsive layout."""
import hashlib
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def check():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://localhost:8502')
        page.locator('#learn-tab').click()
        page.locator('#learn-lesson-select').select_option('password')
        expect(page.locator('#password-lesson')).to_be_visible()
        page.locator('[name=pw-quiz-1][value=decrypt]').check()
        page.locator('#pw-check-1').click()
        expect(page.locator('#pw-next-1')).to_be_disabled()
        page.locator('[name=pw-quiz-1][value=fast]').check()
        page.locator('#pw-check-1').click()
        page.locator('#pw-next-1').click()
        page.locator('#pw-generate').click()
        expect(page.locator('#pw-derived-0')).to_have_text(__import__('re').compile('[0-9a-f]{64}'), timeout=30000)
        salts = []
        for i in range(2):
            salt = page.locator(f'#pw-salt-{i}').inner_text()
            salts.append(salt)
            assert len(salt) == 32
            value = hashlib.pbkdf2_hmac('sha256', b'harbor-lantern', bytes.fromhex(salt), 600000).hex()
            expect(page.locator(f'#pw-derived-{i}')).to_have_text(value)
            expect(page.locator(f'#pw-fast-{i}')).to_have_text(hashlib.sha256(b'harbor-lantern').hexdigest())
        assert salts[0] != salts[1]
        page.locator('[name=pw-quiz-2][value=guesses]').check()
        page.locator('#pw-check-2').click()
        page.locator('#pw-next-2').click()
        page.locator('#pw-guess').fill('incorrect-guess')
        page.locator('#pw-verify').click()
        expect(page.locator('#pw-verify-feedback')).to_contain_text('No match', timeout=30000)
        page.locator('#pw-guess').fill('harbor-lantern')
        page.locator('#pw-verify').click()
        expect(page.locator('#pw-complete')).to_be_visible(timeout=30000)
        saved = page.evaluate('JSON.stringify(localStorage)')
        assert 'harbor-lantern' not in saved and salts[0] not in saved
        out = Path('dist/password-checks'); out.mkdir(exist_ok=True)
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(out / f'password-{width}.png'), full_page=True)
        page.reload()
        page.locator('#learn-tab').click()
        expect(page.locator('#pw-complete')).to_be_visible()
        expect(page.locator('#pw-verify')).to_be_disabled()
        page.locator('#pw-recreate').click()
        expect(page.locator('#pw-verify')).to_be_enabled(timeout=30000)
        page.locator('#pw-reset').click()
        page.locator('#pw-reset-yes').click()
        expect(page.locator('#pw-progress')).to_contain_text('0 of 3')
        page.locator('#learn-lesson-select').select_option('integrity')
        expect(page.locator('#learn-content')).to_be_visible()
        # Reset during a pending derivation must not restore discarded records.
        page.locator('#learn-lesson-select').select_option('password')
        page.locator('[name=pw-quiz-1][value=fast]').check()
        page.locator('#pw-check-1').click()
        page.locator('#pw-next-1').click()
        page.evaluate("""() => {
            window.savedDerive = crypto.subtle.deriveBits.bind(crypto.subtle);
            crypto.subtle.deriveBits = () => new Promise(resolve => { window.releaseDerive = resolve; });
        }""")
        page.locator('#pw-generate').click()
        page.wait_for_function('!!window.releaseDerive')
        page.locator('#pw-reset').click()
        page.locator('#pw-reset-yes').click()
        page.evaluate('() => { window.releaseDerive(new ArrayBuffer(32)); crypto.subtle.deriveBits = window.savedDerive; }')
        expect(page.locator('#pw-progress')).to_contain_text('0 of 3')
        expect(page.locator('#pw-records')).to_be_hidden()
        # Both lesson units remain usable without a network connection.
        page.context.set_offline(True)
        page.locator('[name=pw-quiz-1][value=fast]').check()
        page.locator('#pw-check-1').click()
        page.locator('#pw-next-1').click()
        page.locator('#pw-generate').click()
        expect(page.locator('#pw-derived-0')).to_have_text(__import__('re').compile('[0-9a-f]{64}'), timeout=30000)
        page.context.set_offline(False)
        # Run WCAG automated checks against the visible comparison stage.
        axe = Path('.venv/a11y-tools/node_modules/axe-core/axe.min.js')
        if axe.exists():
            page.add_script_tag(path=str(axe))
            audit = page.evaluate("async () => (await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations")
            assert not audit, [(v['id'], v['description']) for v in audit]
        assert not errors, errors
        browser.close()
    print('Password lesson passed: independent PBKDF2 vectors, feedback, privacy, reload, reset, four widths.')


if __name__ == '__main__':
    check()
