"""Two independent sessions exchange authenticated messages without sharing keys in URLs."""
import base64
import json
from pathlib import Path
import subprocess
from playwright.sync_api import sync_playwright, expect


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def unb64(value):
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def check():
    out = Path('dist/message-checks'); out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        sender = browser.new_context(viewport={'width': 1440, 'height': 1000})
        receiver = browser.new_context()
        page = sender.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://localhost:8502')
        page.locator('#manual-tab').click()
        page.locator('#message').fill('Preserve this cipher input.')
        page.locator('#messages-tab').click()
        page.locator('#msg-links-details').evaluate('(e)=>{e.open=true;}')
        page.locator('#msg-encrypt').click()
        expect(page.locator('#msg-status')).to_contain_text('Write a message')
        text = 'Meet at the lighthouse.\nCafé 🔐 <img src=x onerror=alert(1)>'
        page.locator('#msg-plain').fill(text)
        page.locator('#msg-encrypt').click()
        expect(page.locator('#msg-package')).to_be_visible()
        link = page.locator('#msg-link').input_value()
        key = page.locator('#msg-out-key').input_value()
        token = link.split('#message=')[1]
        envelope = json.loads(unb64(token))
        assert set(envelope) == {'v', 'alg', 'iv', 'ct'}
        assert key not in link and text not in link and len(key) == 43
        # Verify browser encryption independently with Node's crypto API.
        script = '''import {createDecipheriv} from 'node:crypto';
let data=''; for await (const chunk of process.stdin) data+=chunk;
const {envelope,key}=JSON.parse(data), ct=Buffer.from(envelope.ct,'base64url');
const cipher=createDecipheriv('aes-256-gcm',Buffer.from(key,'base64url'),Buffer.from(envelope.iv,'base64url'));
cipher.setAAD(Buffer.from('CipherCraft message v1')); cipher.setAuthTag(ct.subarray(-16));
process.stdout.write(Buffer.concat([cipher.update(ct.subarray(0,-16)),cipher.final()]));'''
        actual = subprocess.run(['node', '--input-type=module', '-e', script], input=json.dumps({'envelope': envelope, 'key': key}).encode(), capture_output=True, check=True)
        assert actual.stdout.decode() == text
        other = receiver.new_page()
        other.on('pageerror', lambda e: errors.append(str(e)))
        other.goto(link)
        expect(other.locator('#msg-receive')).to_be_visible()
        assert '#' not in other.url
        expect(other.locator('#msg-in-key')).to_have_value('')
        other.locator('#msg-in-key').fill(b64(bytes(32)))
        other.locator('#msg-decrypt').click()
        expect(other.locator('#msg-status')).to_contain_text('Could not decrypt')
        expect(other.locator('#msg-opened')).to_be_hidden()
        other.locator('#msg-in-key').fill(key)
        other.locator('#msg-decrypt').click()
        expect(other.locator('#msg-cleartext')).to_have_text(text)
        assert other.locator('#msg-cleartext img').count() == 0
        # No application storage contains message or key material.
        for pg in (page, other):
            saved = pg.evaluate('JSON.stringify([localStorage,sessionStorage])')
            assert key not in saved and token not in saved and 'lighthouse' not in saved
        # Authenticated encryption rejects modified ciphertext and IV.
        for field in ('ct', 'iv'):
            modified = dict(envelope)
            raw = bytearray(unb64(modified[field])); raw[0] ^= 1
            modified[field] = b64(raw)
            other.locator('#msg-incoming').fill(b64(json.dumps(modified).encode()))
            other.locator('#msg-decrypt').click()
            expect(other.locator('#msg-status')).to_contain_text('Could not decrypt')
            expect(other.locator('#msg-cleartext')).to_have_text('')
        for invalid in ('not-a-message', b64(b'{"v":2}'), b64(json.dumps(dict(envelope, key=key)).encode())):
            other.locator('#msg-incoming').fill(invalid)
            other.locator('#msg-decrypt').click()
            expect(other.locator('#msg-status')).to_contain_text('Could not decrypt')
        other.locator('#msg-incoming').fill(link)
        receiver.set_offline(True)
        other.locator('#msg-decrypt').click()
        expect(other.locator('#msg-cleartext')).to_have_text(text)
        receiver.set_offline(False)
        # Explicit web sharing includes ciphertext only; clipboard failure is recoverable.
        page.evaluate('''() => { navigator.share = async data => { window.shared = data; }; }''')
        # Module feature detection occurred before our stub, so expose the control for this test.
        page.locator('#msg-share').evaluate('(e)=>{e.hidden=false;}')
        page.locator('#msg-share').click()
        shared = page.evaluate('window.shared')
        assert shared['url'] == link and key not in json.dumps(shared)
        page.evaluate('''()=>{navigator.clipboard.writeText=async()=>{throw new Error('denied');};}''')
        page.locator('#msg-copy-link').click()
        expect(page.locator('#msg-status')).to_contain_text('copy it manually')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(out / f'send-{width}.png'), full_page=True)
            other.set_viewport_size({'width': width, 'height': 1000})
            assert other.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            other.screenshot(path=str(out / f'receive-{width}.png'), full_page=True)
        axe = Path('.venv/a11y-tools/node_modules/axe-core/axe.min.js')
        if axe.exists():
            for pg in (page, other):
                pg.add_script_tag(path=str(axe))
                violations = pg.evaluate("async()=> (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})).violations")
                assert not violations, [(v['id'], v['description']) for v in violations]
        page.locator('#msg-plain').fill('Changed message')
        expect(page.locator('#msg-package')).to_be_hidden()
        expect(page.locator('#msg-out-key')).to_have_value('')
        page.locator('#msg-plain').fill('🔐' * 600)
        page.locator('#msg-encrypt').click()
        expect(page.locator('#msg-status')).to_contain_text('UTF-8 bytes')
        page.locator('#msg-plain').fill(text)
        page.locator('#msg-encrypt').click()
        expect(page.locator('#msg-package')).to_be_visible()
        assert page.locator('#msg-link').input_value() != link
        assert page.locator('#msg-out-key').input_value() != key
        other.locator('#msg-clear').click()
        expect(other.locator('#msg-cleartext')).to_have_text('')
        expect(other.locator('#msg-in-key')).to_have_value('')
        other.reload()
        other.locator('#messages-tab').click()
        expect(other.locator('#msg-plain')).to_have_value('')
        # Editing/resetting while async work is pending must discard stale output.
        page.evaluate('''()=>{window.realEncrypt=crypto.subtle.encrypt.bind(crypto.subtle); crypto.subtle.encrypt=()=>new Promise(r=>{window.finishEncrypt=r;});}''')
        page.locator('#msg-encrypt').click()
        page.wait_for_function('!!window.finishEncrypt')
        page.locator('#msg-clear').click()
        page.evaluate('''()=>{window.finishEncrypt(new ArrayBuffer(16));crypto.subtle.encrypt=window.realEncrypt;}''')
        expect(page.locator('#msg-package')).to_be_hidden()
        page.locator('#manual-tab').click()
        expect(page.locator('#message')).to_have_value('Preserve this cipher input.')
        # Capacitor's generated Android listener handle is synchronous.
        native_context = browser.new_context()
        native_context.add_init_script("""window.Capacitor={isNativePlatform:()=>true,Plugins:{CipherFiles:{
            addListener:(name,cb)=>{window.nativeReceive=cb;return {remove:()=>{}};},
            takeSharedMessage:async()=>({text:""}),
            shareText:async(data)=>{window.nativeShared=data;},
            copyText:async(data)=>{window.nativeCopied=data;}
        }}};""")
        native_page = native_context.new_page()
        native_page.on('pageerror', lambda e: errors.append(str(e)))
        native_page.goto('http://localhost:8502')
        expect(native_page.locator('#identify')).to_be_enabled(timeout=90000)
        native_page.evaluate('(text)=>window.nativeReceive({text})', link)
        expect(native_page.locator('#msg-incoming')).to_have_value(link)
        native_page.locator('#msg-in-key').fill(key)
        native_page.locator('#msg-decrypt').click()
        expect(native_page.locator('#msg-cleartext')).to_have_text(text)
        native_page.evaluate('(text)=>window.nativeReceive({text})', link)
        expect(native_page.locator('#msg-in-key')).to_have_value('')
        expect(native_page.locator('#msg-cleartext')).to_have_text('')
        native_page.locator('#msg-send-tab').click()
        native_page.locator('#msg-plain').fill('Native share test')
        native_page.locator('#msg-encrypt').click()
        expect(native_page.locator('#msg-package')).to_be_visible()
        native_page.locator('#msg-share').click()
        native_shared = native_page.evaluate('window.nativeShared')
        assert native_shared['text'].startswith('https://cipher.drewclark.io/#message=')
        native_page.locator('#msg-copy-key').click()
        native_copied = native_page.evaluate('window.nativeCopied')
        assert native_copied['sensitive'] is True
        assert native_copied['text'] not in native_shared['text']
        unsupported = browser.new_context()
        unsupported.add_init_script("Object.defineProperty(crypto,'subtle',{value:undefined});")
        limited = unsupported.new_page()
        limited.goto('http://localhost:8502')
        limited.locator('#messages-tab').click()
        limited.locator('#msg-links-details').evaluate('(e)=>{e.open=true;}')
        expect(limited.locator('#msg-unavailable')).to_be_visible()
        expect(limited.locator('#msg-encrypt')).to_be_disabled()
        assert not errors, errors
        browser.close()
    print('Messages passed: two sessions, independent AES-GCM decryption, tamper/wrong-key rejection, Unicode, privacy, offline, sharing, reset races and four widths.')


if __name__ == '__main__':
    check()
