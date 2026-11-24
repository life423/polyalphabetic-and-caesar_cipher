"""Manual hosted storage/restart check. Requires explicit --restart and Azure CLI sign-in."""
import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
import uuid
from playwright.sync_api import sync_playwright


def check(restart):
    if not restart:
        raise SystemExit('Pass --restart to authorize restarting the CipherCraft beta API.')
    base = 'https://ciphercraft-drewclark.azurewebsites.net'
    def api(path, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        request = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    suffix = uuid.uuid4().hex[:8]
    names = ['persist_a_' + suffix, 'persist_b_' + suffix]
    password = 'fictional-hosted-verification-password'
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(); page.goto('http://localhost:8502')
        # Exercise real browser CORS, not just the test's server-side API client.
        assert page.evaluate("async(base)=>(await (await fetch(base+'/api/health')).json()).ok", base)
        identities = page.evaluate('''async({password,names})=>{
            const m=await import('./messenger-crypto.js');window.checkIdentities=[];
            for(const name of names)window.checkIdentities.push(await m.createIdentity(password,name));
            return window.checkIdentities.map(({publicKey,keyBackup,authSecret})=>({publicKey,keyBackup,authSecret}));
        }''', {'password': password, 'names': names})
        accounts = [api('/api/register', {'username': name, 'password': identity['authSecret'], 'publicKey': identity['publicKey'], 'keyBackup': identity['keyBackup']}) for name, identity in zip(names, identities)]
        token = accounts[0]['token']
        conversation = api('/api/conversations', {'username': names[1]}, token)['conversation']
        payload = {'v': 1, 'kind': 'message', 'text': 'Hosted persistence verification, fictional test data.'}
        envelope = page.evaluate('''async({cid,sid,payload})=>{
            const m=await import('./messenger-crypto.js');
            return m.encryptChat(window.checkIdentities[0].privateKey,window.checkIdentities[1].publicKey,cid,sid,payload);
        }''', {'cid': conversation['id'], 'sid': accounts[0]['user']['id'], 'payload': payload})
        sent = api(f"/api/conversations/{conversation['id']}/messages", {'clientId': str(uuid.uuid4()), 'envelope': envelope}, token)['message']
        for account in accounts: api('/api/logout', {}, account['token'])
        command = shutil.which('az.cmd') or shutil.which('az')
        assert command
        subprocess.run([command, 'webapp', 'restart', '-g', 'rg-ciphercraft', '-n', 'ciphercraft-drewclark', '--output', 'none'], check=True, capture_output=True)
        for attempt in range(30):
            try:
                if api('/api/health').get('ok'): break
            except Exception: pass
            time.sleep(2)
        else: raise AssertionError('API did not recover after restart')
        restored = api('/api/login', {'username': names[0], 'password': identities[0]['authSecret']})
        history = api(f"/api/conversations/{conversation['id']}/messages", token=restored['token'])['messages']
        assert history[0] == sent
        actual = page.evaluate('''async({password,user,peer,cid,message})=>{
            const m=await import('./messenger-crypto.js');
            const privateKey=await m.unlockIdentity(password,user.keyBackup,user.publicKey);
            return m.decryptChat(privateKey,peer,cid,message.senderId,message.envelope);
        }''', {'password': password, 'user': restored['user'], 'peer': identities[1]['publicKey'], 'cid': conversation['id'], 'message': history[0]})
        assert actual == payload
        api('/api/logout', {}, restored['token'])
        browser.close()
    print('Azure passed: HTTPS browser CORS, real accounts and encrypted delivery, App Service restart, durable history and password-unlocked identity recovery.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--restart', action='store_true')
    check(parser.parse_args().restart)
