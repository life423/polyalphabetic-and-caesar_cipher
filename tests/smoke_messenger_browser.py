"""Two real accounts exchange cipher challenges, solve by key/AI and reply in-app."""
import json
import os
import uuid
from pathlib import Path
from playwright.sync_api import expect, sync_playwright


def check():
    suffix = uuid.uuid4().hex[:8]
    names = ['alice_' + suffix, 'bob_' + suffix]
    password = 'fictional-messenger-test-password'
    plain = ('The lighthouse keeper watched the harbor as the evening boats returned. '
             'A friend had left a secret message beside the old wooden gate. '
             'Read each clue carefully and bring the lantern to the quiet garden before sunset. '
             'We will meet there to begin another adventure together.')
    key = 7
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    shifted = 'HIJKLMNOPQRSTUVWXYZABCDEFGhijklmnopqrstuvwxyzabcdefg'
    cipher = plain.translate(str.maketrans(alphabet, shifted))
    out = Path('dist/messenger-checks'); out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        contexts = [browser.new_context(viewport={'width': 1440, 'height': 1000}) for _ in range(2)]
        pages = [c.new_page() for c in contexts]
        hosted = os.environ.get('CIPHER_MESSENGER_TEST_API')
        if hosted:
            def proxy(route):
                if not route.request.frame.page.evaluate('navigator.onLine'):
                    route.abort('internetdisconnected')
                    return
                response = route.fetch(url=hosted.rstrip('/') + route.request.url.split('http://localhost:8503', 1)[1], timeout=60000)
                route.fulfill(response=response)
            for context in contexts:
                context.route('http://localhost:8503/**', proxy)

        errors, posted = [], []
        for page, name in zip(pages, names):
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda r: posted.append(r.post_data) if r.method == 'POST' and '/api/' in r.url else None)
            page.goto('http://localhost:8502/?messenger=local')
            page.locator('#messages-tab').click()
            page.locator('#chat-username').fill(name)
            page.locator('#chat-password').fill(password)
            # Messages requires explicit consent; offline tools remain usable.
            before = len(posted)
            page.get_by_role('button', name='Create account', exact=True).click()
            expect(page.locator('#chat-workspace')).to_be_hidden()
            assert len(posted) == before, 'No authentication request before consent'
            page.locator('#chat-terms').check()
            page.get_by_role('button', name='Create account', exact=True).click()
            expect(page.locator('#chat-workspace')).to_be_visible(timeout=30000)
            expect(page.locator('#chat-password')).to_have_value('')
        alice, bob = pages
        alice.locator('#chat-peer').fill(names[1])
        alice.get_by_role('button', name='Start conversation', exact=True).click()
        expect(alice.locator('#chat-peer-name')).to_have_text(names[1])
        alice.locator('#chat-key-fields input').fill(str(key))
        alice.locator('#chat-text').fill(plain)
        alice.locator('#chat-hint').fill('Seven steps around the alphabet')
        alice.locator('#chat-send').click()
        expect(alice.locator('#chat-send-status')).to_have_text('Sent.', timeout=90000)
        expect(alice.locator('#chat-thread')).to_contain_text(cipher)
        expect(bob.locator('#chat-conversations')).to_contain_text(names[0], timeout=15000)
        bob.locator('#chat-conversations button').first.click()
        expect(bob.locator('#chat-thread')).to_contain_text(cipher, timeout=15000)
        bubble = bob.locator('#chat-thread .chat-bubble').first
        bubble.locator('.chat-fields input').fill(str(key))
        bubble.get_by_role('button', name='Decode', exact=True).click()
        expect(bubble.locator('.chat-decoded-text')).to_have_text(plain, timeout=90000)
        bubble.get_by_role('button', name='Try AI', exact=True).click()
        expect(bubble.get_by_role('button', name='Try this key', exact=True).first).to_be_visible(timeout=90000)
        bubble.get_by_role('button', name='Try this key', exact=True).first.click()
        expect(bubble.locator('.chat-decoded-text')).to_have_text(plain, timeout=90000)
        # Hide the cipher for an automatic identify-and-crack challenge.
        alice.locator('#chat-key-fields input').fill('7')
        alice.locator('#chat-text').fill(plain)
        alice.locator('#chat-hide').check()
        alice.locator('#chat-send').click()
        expect(alice.locator('#chat-send-status')).to_have_text('Sent.', timeout=90000)
        expect(bob.locator('#chat-thread .chat-bubble')).to_have_count(2, timeout=15000)
        hidden = bob.locator('#chat-thread .chat-bubble').last
        expect(hidden).to_contain_text('cipher hidden')
        hidden.get_by_role('button', name='Try AI', exact=True).click()
        expect(hidden.get_by_role('button', name='Try this key', exact=True).first).to_be_visible(timeout=90000)
        hidden.get_by_role('button', name='Try this key', exact=True).first.click()
        expect(hidden.locator('.chat-decoded-text')).to_have_text(plain, timeout=90000)
        # Every offered challenge cipher supports a known-key solve in the thread.
        for algorithm, values in [('Vigenère', ['LANTERN']), ('Rail Fence', ['3']), ('Affine', ['5', '8'])]:
            alice.locator('#chat-cipher').select_option(algorithm)
            inputs = alice.locator('#chat-key-fields input')
            for index, value in enumerate(values):
                inputs.nth(index).fill(value)
            alice.locator('#chat-text').fill(plain)
            alice.locator('#chat-send').click()
            expect(alice.locator('#chat-send-status')).to_have_text('Sent.', timeout=90000)
            count = {'Vigenère': 3, 'Rail Fence': 4, 'Affine': 5}[algorithm]
            expect(bob.locator('#chat-thread .chat-bubble')).to_have_count(count, timeout=15000)
            challenge = bob.locator('#chat-thread .chat-bubble').last
            decode_inputs = challenge.locator('.chat-fields input')
            for index, value in enumerate(values):
                decode_inputs.nth(index).fill(value)
            challenge.get_by_role('button', name='Decode', exact=True).click()
            expect(challenge.locator('.chat-decoded-text')).to_have_text(''.join(plain.split()) if algorithm == 'Rail Fence' else plain, timeout=90000)
            expect(challenge.locator('.chat-solved')).to_contain_text('You cracked it')
        bob.locator('#chat-kind').select_option('message')
        bob.locator('#chat-text').fill('Cracked it! Meet you in the garden. 🔐')
        bob.locator('#chat-send').click()
        expect(bob.locator('#chat-send-status')).to_have_text('Sent.', timeout=30000)
        expect(alice.locator('#chat-thread')).to_contain_text('Cracked it! Meet you in the garden. 🔐', timeout=15000)
        for width in (320, 390, 768, 1440):
            bob.set_viewport_size({'width': width, 'height': 1000})
            assert bob.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
            bob.screenshot(path=str(out / f'conversation-{width}.png'), full_page=True)
        bob.set_viewport_size({'width': 390, 'height': 1000})
        bob.locator('#chat-back').click()
        expect(bob.locator('.chat-inbox')).to_be_visible()
        expect(bob.locator('.chat-main')).to_be_hidden()
        bob.locator('#chat-conversations button').first.click()
        expect(bob.locator('.chat-inbox')).to_be_hidden()
        expect(bob.locator('#chat-thread')).to_contain_text(cipher)
        bob.set_viewport_size({'width': 1440, 'height': 1000})
        axe = Path('.venv/a11y-tools/node_modules/axe-core/axe.min.js')
        if axe.exists():
            bob.add_script_tag(path=str(axe))
            issues = bob.evaluate("async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations")
            assert not issues, [(v['id'], v['description']) for v in issues]
        assert not any(password in body for body in posted if body)
        sends = [json.loads(body) for body in posted if body and 'clientId' in body]
        assert sends and all(set(payload) == {'clientId', 'envelope'} for payload in sends)
        assert all(plain not in json.dumps(payload) and 'Seven steps' not in json.dumps(payload) for payload in sends)
        saved = bob.evaluate('JSON.stringify([localStorage,sessionStorage])')
        assert password not in saved and plain not in saved and 'Cracked it!' not in saved
        bob.locator('#chat-signout').click()
        expect(bob.locator('#chat-thread')).to_have_text('')
        bob.locator('#chat-username').fill(names[1]); bob.locator('#chat-password').fill(password)
        bob.locator('#chat-terms').check()
        bob.get_by_role('button', name='Log in', exact=True).click()
        expect(bob.locator('#chat-workspace')).to_be_visible(timeout=30000)
        expect(bob.locator('#chat-conversations button').first).to_be_visible()
        bob.locator('#chat-conversations button').first.click()
        expect(bob.locator('#chat-thread')).to_contain_text(cipher)
        # Blocking is reversible and prevents delivery from either participant.
        bob.locator('#chat-block').click()
        expect(bob.locator('#chat-block')).to_have_text('Unblock')
        expect(bob.locator('#chat-send')).to_be_disabled()
        bob.locator('#chat-block').click()
        expect(bob.locator('#chat-send')).to_be_enabled()
        contexts[0].set_offline(True)
        alice.locator('#chat-text').fill('Keep this offline draft.')
        alice.locator('#chat-kind').select_option('message')
        alice.locator('#chat-send').click()
        expect(alice.locator('#chat-send-status')).to_contain_text('offline', timeout=15000)
        expect(alice.locator('#chat-text')).to_have_value('Keep this offline draft.')
        contexts[0].set_offline(False)
        for page in pages:
            page.locator('#chat-signout').click()
            expect(page.locator('#chat-thread')).to_have_text('')
        assert not errors, errors
        if hosted:
            for context in contexts:
                context.unroute_all(behavior='wait')
        browser.close()
    print('Messenger passed: real signup, encrypted two-person inbox/replies, challenge decoding by key and local AI, backup login, block/unblock, offline draft, privacy and four widths.')


if __name__ == '__main__':
    check()
