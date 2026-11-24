"""Exercise administration against an isolated API, never production accounts."""
import hashlib
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4
from playwright.sync_api import sync_playwright, expect
from tests.test_messenger import enc, KEY, BACKUP, ENVELOPE

BASE = 'http://localhost:8504'
PASSWORD = 'fictional-admin-test-password'


def check():
    for attempt in range(40):
        try:
            with urlopen(BASE + '/api/health', timeout=2):
                break
        except OSError:
            if attempt == 39:
                raise
            time.sleep(0.25)
    for name in ('preview_owner', 'preview_student', 'other_student'):
        secret = enc(hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(),
                     ('CipherCraft sign-in v1:' + name).encode(), 600000, 32))
        request = Request(BASE + '/api/register', data=json.dumps(dict(username=name, password=secret, publicKey=KEY, keyBackup=BACKUP)).encode(), headers={'Content-Type': 'application/json'})
        try:
            with urlopen(request) as response:
                assert response.status == 200
        except HTTPError as error:
            if error.code != 409:
                raise
    out = Path('dist/admin-checks'); out.mkdir(exist_ok=True)
    def api(path, body, token=None):
        request = Request(BASE + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **({'Authorization': 'Bearer '+token} if token else {})})
        with urlopen(request) as response:
            return json.load(response)
    secret = enc(hashlib.pbkdf2_hmac('sha256', PASSWORD.encode(), b'CipherCraft sign-in v1:preview_owner', 600000, 32))
    token = api('/api/login', {'username': 'preview_owner', 'password': secret})['token']
    cid = api('/api/conversations', {'username': 'preview_student'}, token)['conversation']['id']
    for _ in range(2):
        api(f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE}, token)
    api('/api/logout', {}, token)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        def proxy(route):
            result = route.fetch(url=BASE + route.request.url.split('http://localhost:8503', 1)[1])
            route.fulfill(response=result)
        context.route('http://localhost:8503/**', proxy)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://localhost:8502/admin.html?messenger=local')
        page.locator('#username').fill('preview_student')
        page.locator('#password').fill(PASSWORD)
        page.locator('#show-password').click()
        expect(page.locator('#password')).to_have_attribute('type', 'text')
        page.locator('#show-password').click()
        expect(page.locator('#password')).to_have_attribute('type', 'password')
        page.locator('#login-submit').click()
        expect(page.locator('#status')).to_contain_text('does not have administrator')
        expect(page.locator('#admin-workspace')).to_be_hidden()
        page.locator('#username').fill('preview_owner')
        page.locator('#password').fill(PASSWORD)
        page.locator('#login-submit').click()
        expect(page.locator('#admin-workspace')).to_be_visible(timeout=30000)
        expect(page.locator('#accounts>li')).to_have_count(3)
        expect(page.locator('#messages>li')).to_have_count(2)
        for width in (390, 1440):
            page.set_viewport_size({'width': width, 'height': 950})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/f'message-records-{width}.png'), full_page=True)
        delete_button = page.locator('#messages button').first
        mid = delete_button.get_attribute('aria-label').split('#')[1]
        delete_button.click()
        expect(page.locator('#action-description')).to_contain_text('cannot be undone')
        page.locator('#confirmation').fill('wrong')
        page.locator('#reason').fill('Remove synthetic test message')
        page.locator('#confirm-action').click()
        expect(page.locator('#action-error')).to_contain_text('exact confirmation')
        page.set_viewport_size({'width': 320, 'height': 844})
        page.screenshot(path=str(out/'delete-message-confirmation-320.png'))
        page.locator('#confirmation').fill(mid)
        page.locator('#confirm-action').click()
        expect(page.locator('#messages>li')).to_have_count(1)
        page.locator('#delete-all-messages').click()
        page.locator('#confirmation').fill('DELETE ALL MESSAGES')
        page.locator('#reason').fill('Remove remaining synthetic history')
        page.locator('#confirm-action').click()
        expect(page.locator('#messages-empty')).to_be_visible()
        expect(page.locator('#delete-all-messages')).to_be_disabled()
        expect(page.locator('#accounts>li')).to_have_count(3)
        expect(page.locator('#password')).to_have_value('')
        assert page.evaluate('Object.keys(localStorage).length') == 0
        expect(page.locator('#accounts>li').filter(has_text='preview_owner')).to_contain_text('Protected account')
        page.locator('#search').fill('missing')
        page.get_by_role('button', name='Search', exact=True).click()
        expect(page.locator('#empty')).to_be_visible()
        page.locator('#search').fill('preview_student')
        page.get_by_role('button', name='Search', exact=True).click()
        expect(page.locator('#accounts>li')).to_have_count(1)
        page.get_by_role('button', name='Suspend account: preview_student', exact=True).click()
        expect(page.locator('#confirmation')).to_be_focused()
        page.locator('#confirmation').fill('wrong')
        page.locator('#reason').fill('Browser regression test')
        page.locator('#confirm-action').click()
        expect(page.locator('#action-error')).to_contain_text('exact username')
        page.keyboard.press('Escape')
        expect(page.locator('#action-dialog')).not_to_be_visible()
        expect(page.get_by_role('button', name='Suspend account: preview_student', exact=True)).to_be_focused()
        page.get_by_role('button', name='Suspend account: preview_student', exact=True).click()
        page.locator('#confirmation').fill('preview_student')
        page.locator('#reason').fill('Browser regression test')
        page.locator('#confirm-action').click()
        expect(page.locator('#accounts')).to_contain_text('Suspended')
        expect(page.locator('#audit')).to_contain_text('Browser regression test')
        for width in (320, 390, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 950})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(out/f'accounts-{width}.png'), full_page=True)
            page.get_by_role('button', name='Restore account: preview_student', exact=True).click()
            expect(page.locator('#confirmation')).to_be_focused()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            page.screenshot(path=str(out/f'confirmation-{width}.png'))
            page.locator('#cancel-action').click()
        page.get_by_role('button', name='Restore account: preview_student', exact=True).click()
        page.locator('#confirmation').fill('preview_student')
        page.locator('#reason').fill('Restore after verified review')
        page.locator('#confirm-action').click()
        expect(page.locator('#accounts')).to_contain_text('Active')
        page.get_by_role('button', name='Sign out all devices: preview_student', exact=True).click()
        page.locator('#confirmation').fill('preview_student')
        page.locator('#reason').fill('Lost test device')
        page.locator('#confirm-action').click()
        expect(page.locator('#audit')).to_contain_text('Lost test device')
        context.route('http://localhost:8503/api/admin/**', lambda route: route.abort('internetdisconnected'))
        page.locator('#refresh').click()
        expect(page.locator('#status')).to_have_attribute('data-error', 'true')
        context.unroute('http://localhost:8503/api/admin/**')
        page.locator('#sign-out').click()
        expect(page.locator('#admin-workspace')).to_be_hidden()
        expect(page.locator('#status')).to_have_text('Signed out.')
        assert not errors, errors
        browser.close()
    print('Admin browser checks passed: role denial, individual/all-message deletion, metadata, actions, confirmation, audit, offline, keyboard and 320/390/768/1440px.')


if __name__ == '__main__':
    check()
