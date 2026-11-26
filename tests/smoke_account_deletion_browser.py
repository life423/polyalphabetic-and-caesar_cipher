"""Real UI/crypto against an isolated API; no production accounts are used."""
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen
from uuid import uuid4
from playwright.sync_api import sync_playwright, expect

BASE = 'http://localhost:8505'
PASSWORD = 'fictional-deletion-test-password'


def request(path, body=None, token=None):
    raw = json.dumps(body).encode() if body is not None else None
    req = Request(BASE + path, data=raw, headers={'Content-Type': 'application/json', **({'Authorization': 'Bearer '+token} if token else {})})
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def check():
    for attempt in range(40):
        try:
            request('/api/health'); break
        except OSError:
            if attempt == 39: raise
            time.sleep(.25)
    suffix = uuid4().hex[:6]
    owner, public, inapp = 'guard_'+suffix, 'public_'+suffix, 'inapp_'+suffix
    # Use real encrypted identities in the browser for app login/unlock coverage.
    out = Path('dist/account-deletion-checks'); out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width':1440,'height':1000})
        def proxy(route):
            route.fulfill(response=route.fetch(url=BASE+route.request.url.split('http://localhost:8503',1)[1]))
        context.route('http://localhost:8503/**',proxy)
        page = context.new_page()
        errors, sent = [], []
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r: sent.append(r.post_data) if r.method=='POST' and r.url.endswith('/api/account/delete') else None)
        page.goto('http://localhost:8502/?messenger=local')
        expect(page.locator('#identify')).to_be_enabled(timeout=90000)
        # First fixture receives ID 1, protected by this isolated server configuration.
        for name in (owner, public, inapp):
            data = page.evaluate('''async ({name,password})=>{
              const {createIdentity}=await import('/messenger-crypto.js');
              const identity=await createIdentity(password,name);
              const response=await fetch('http://localhost:8503/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:name,password:identity.authSecret,publicKey:identity.publicKey,keyBackup:identity.keyBackup})});
              if(!response.ok)throw new Error('Synthetic fixture registration failed');return response.json();
            }''',dict(name=name,password=PASSWORD))
            if name == owner:
                assert data['user']['id']==1, 'Use a fresh isolated deletion-test database'
                owner_token=data['token']
        page.goto('http://localhost:8502/delete-account.html?messenger=local')
        page.locator('#delete-username').fill(public)
        page.locator('#delete-password').fill(PASSWORD)
        page.locator('#delete-confirmation').fill('wrong')
        page.locator('#delete-submit').click()
        expect(page.locator('#delete-status')).to_contain_text('exact username')
        page.locator('#delete-confirmation').fill(public)
        page.locator('#delete-password').fill('wrong-password-for-test')
        page.locator('#delete-submit').click()
        expect(page.locator('#delete-status')).to_contain_text('Could not verify')
        expect(page.locator('#delete-password')).to_have_value('')
        # Simulated offline request must not claim deletion; the account still exists.
        context.route('http://localhost:8503/api/account/delete',lambda r:r.abort('internetdisconnected'))
        page.locator('#delete-password').fill(PASSWORD)
        page.locator('#delete-submit').click()
        expect(page.locator('#delete-status')).to_contain_text('not confirmed')
        context.unroute('http://localhost:8503/api/account/delete')
        page.locator('#delete-password').fill(PASSWORD)
        for width in (320,390,768,1440):
            page.set_viewport_size({'width':width,'height':950})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
            page.screenshot(path=str(out/f'public-page-{width}.png'),full_page=True)
        page.locator('#delete-show-password').click()
        expect(page.locator('#delete-password')).to_have_attribute('type','text')
        page.locator('#delete-show-password').click()
        page.locator('#delete-submit').click()
        expect(page.locator('#deleted-title')).to_be_visible(timeout=30000)
        expect(page.locator('#deleted-title')).to_be_focused()
        expect(page.locator('#delete-password')).to_have_value('')
        assert request('/api/me',token=owner_token)['user']['username']==owner
        assert PASSWORD not in ''.join(sent)
        assert all(set(json.loads(body))=={'username','password','confirmation'} for body in sent)
        page.goto('http://localhost:8502/?messenger=local')
        expect(page.locator('#identify')).to_be_enabled(timeout=90000)
        page.locator('#manual-tab').click();page.locator('#message').fill('Keep my unrelated cipher work.')
        page.locator('#messages-tab').click()
        page.locator('#chat-username').fill(inapp);page.locator('#chat-password').fill(PASSWORD)
        page.locator('#chat-terms').check()
        page.get_by_role('button',name='Log in',exact=True).click()
        expect(page.locator('#chat-account-settings')).to_be_visible(timeout=30000)
        page.locator('#chat-account-settings summary').click()
        page.locator('#chat-delete-account').click()
        expect(page.locator('#delete-password')).to_be_focused()
        page.locator('#delete-password').fill(PASSWORD)
        page.locator('#delete-cancel').click()
        expect(page.locator('#chat-delete-dialog')).to_have_count(0)
        expect(page.locator('#chat-workspace')).to_be_visible()
        page.locator('#chat-delete-account').click()
        for width in (320,390,768,1440):
            page.set_viewport_size({'width':width,'height':950})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), width
            page.screenshot(path=str(out/f'app-dialog-{width}.png'))
        expect(page.locator('#delete-username')).to_have_attribute('readonly','')
        page.locator('#delete-password').fill(PASSWORD);page.locator('#delete-confirmation').fill(inapp)
        page.locator('#delete-submit').click()
        expect(page.locator('#chat-status')).to_contain_text('Your account has been deleted',timeout=30000)
        expect(page.locator('#chat-workspace')).to_be_hidden()
        expect(page.locator('#chat-thread')).to_have_text('')
        expect(page.locator('#chat-account-settings')).to_be_hidden()
        page.locator('#manual-tab').click();expect(page.locator('#message')).to_have_value('Keep my unrelated cipher work.')
        page.locator('#messages-tab').click()
        page.locator('#chat-username').fill(owner);page.locator('#chat-password').fill(PASSWORD)
        page.locator('#chat-terms').check()
        page.get_by_role('button',name='Log in',exact=True).click();expect(page.locator('#chat-workspace')).to_be_visible(timeout=30000)
        page.locator('#chat-account-settings summary').click();page.locator('#chat-delete-account').click()
        expect(page.locator('#chat-status')).to_contain_text('protected from self-deletion')
        expect(page.locator('#chat-delete-dialog')).to_have_count(0)
        assert request('/api/me',token=owner_token)['user']['username']==owner
        # The public route also rejects deletion of the synthetic protected admin.
        page.goto('http://localhost:8502/delete-account.html?messenger=local')
        page.locator('#delete-username').fill(owner);page.locator('#delete-password').fill(PASSWORD);page.locator('#delete-confirmation').fill(owner)
        page.locator('#delete-submit').click();expect(page.locator('#delete-status')).to_contain_text('protected from self-deletion')
        assert request('/api/me',token=owner_token)['user']['username']==owner
        assert not errors, errors
        browser.close()
    print('Self-deletion passed: public page, in-app reauthentication, wrong password/confirmation, offline safety, cancellation, protected synthetic admin, unrelated-work preservation and four widths.')


if __name__=='__main__':
    check()
