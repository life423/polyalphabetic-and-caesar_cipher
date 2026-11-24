"""Focused backend integration/security tests; no network or external services."""
import base64
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.messenger.app import create_app, SESSION_SECONDS


def enc(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


KEY = dict(kty='EC', crv='P-256', x=enc(bytes.fromhex('6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296')), y=enc(bytes.fromhex('4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5')))
BACKUP = dict(salt=enc(b's'*16), iv=enc(b'i'*12), ct=enc(b'c'*32))
ENVELOPE = dict(v=1, iv=enc(b'v'*12), ct=enc(b'x'*32))
SECRET = enc(b'client derived auth secret!!!!!!!')


class MessengerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.tmp.name) / 'seed.sqlite'
        cls.now = 1000000000
        cls.seed = create_app(cls.path, clock=lambda: cls.now)
        cls.tokens = {}
        for name in ('alice', 'bobby', 'carol'):
            status, body = cls.call(cls.seed, 'POST', '/api/register', dict(username=name, password=SECRET, publicKey=KEY, keyBackup=BACKUP))
            assert status == 200, body
            cls.tokens[name] = body['token']

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.local = tempfile.TemporaryDirectory()
        self.dbpath = Path(self.local.name) / 'test.sqlite'
        with closing(sqlite3.connect(self.path)) as source, closing(sqlite3.connect(self.dbpath)) as target:
            source.backup(target)
        self.app = create_app(self.dbpath, clock=lambda: self.now)
        self.addCleanup(self.local.cleanup)

    @staticmethod
    def call(app, method, path, body=None, token=None, **extra):
        path, _, query = path.partition('?')
        raw = json.dumps(body).encode() if body is not None else b''
        env = dict(REQUEST_METHOD=method, PATH_INFO=path, QUERY_STRING=query, CONTENT_LENGTH=str(len(raw)), CONTENT_TYPE='application/json', REMOTE_ADDR='127.0.0.1', **{'wsgi.input': io.BytesIO(raw)})
        if token:
            env['HTTP_AUTHORIZATION'] = 'Bearer ' + token
        env.update(extra)
        responses = []
        payload = b''.join(app(env, lambda status, headers: responses.append((status, headers))))
        return int(responses[0][0].split()[0]), json.loads(payload)

    def request(self, method, path, body=None, who='alice', **extra):
        return self.call(self.app, method, path, body, self.tokens[who] if who else None, **extra)

    def conversation(self, who='alice', peer='bobby'):
        status, body = self.request('POST', '/api/conversations', {'username': peer}, who)
        self.assertEqual(status, 200, body)
        return body['conversation']['id']

    def send(self, cid, who='alice', client_id=None):
        return self.request('POST', f'/api/conversations/{cid}/messages', dict(clientId=client_id or str(uuid4()), envelope=ENVELOPE), who)

    def test_auth_storage_logout_expiry_and_restart(self):
        status, data = self.request('POST', '/api/login', dict(username='alice', password=SECRET), None)
        self.assertEqual(status, 200)
        token = data['token']
        self.assertEqual(set(data['user']), {'id','username','publicKey','keyBackup'})
        with closing(sqlite3.connect(self.dbpath)) as db, db:
            row = db.execute('SELECT salt,password_hash FROM users LIMIT 1').fetchone()
            self.assertEqual((len(row[0]), len(row[1])), (16,32))
            self.assertNotIn(token, str(db.execute('SELECT * FROM sessions').fetchall()))
            self.assertNotIn(SECRET, str(db.execute('SELECT * FROM users').fetchall()))
        restarted = create_app(self.dbpath, clock=lambda: self.now)
        self.assertEqual(self.call(restarted, 'GET','/api/me', token=token)[0], 200)
        expired = create_app(self.dbpath, clock=lambda: self.now + SESSION_SECONDS)
        self.assertEqual(self.call(expired, 'GET','/api/me', token=token)[0], 401)
        self.assertEqual(self.call(self.app, 'POST','/api/logout', {}, token)[0], 200)
        self.assertEqual(self.call(self.app, 'GET','/api/me', token=token)[0], 401)
        self.assertEqual(self.request('GET','/api/me',who=None)[0],401)
        for name in ('alice','unknown'):
            self.assertEqual(self.request('POST','/api/login',dict(username=name,password='wrong credential'),None), (401,{'error':'invalid_credentials'}))

    def test_validation_and_no_key_update(self):
        for key in (dict(KEY, x=enc(b'0'*31)), dict(KEY, y=enc(b'0'*32)), dict(KEY, d='secret'), dict(KEY, crv='P-384')):
            status, _ = self.request('POST','/api/register',dict(username='new_user',password=SECRET,publicKey=key,keyBackup=BACKUP),None)
            self.assertEqual(status,400)
        self.assertEqual(self.request('POST','/api/register',dict(username='Alice',password=SECRET,publicKey=KEY,keyBackup=BACKUP),None)[0],400)
        self.assertEqual(self.request('POST','/api/register',dict(username='new_user',password='short',publicKey=KEY,keyBackup=BACKUP),None)[0],400)
        self.assertEqual(self.request('POST','/api/register',dict(username='new_user',password=SECRET,publicKey=KEY,keyBackup=dict(BACKUP,ct=enc(b'a'*4097))),None)[0],400)
        self.assertEqual(self.request('POST','/api/me',dict(publicKey=KEY))[0],404)

    def test_lookup_pairs_member_isolation(self):
        self.assertEqual(self.request('GET','/api/people?username=absent')[0],404)
        self.assertEqual(self.request('GET','/api/people')[0],400)
        status, data = self.request('GET','/api/people?username=bobby')
        self.assertEqual(status,200)
        self.assertEqual(set(data['user']),{'id','username','publicKey'})
        cid = self.conversation()
        self.assertEqual(cid,self.conversation('bobby','alice'))
        for suffix, method, body in [('messages','GET',None),('messages','POST',dict(clientId=str(uuid4()),envelope=ENVELOPE)),('read','POST',dict(messageId=1)),('block','POST',dict(blocked=True))]:
            self.assertEqual(self.request(method,f'/api/conversations/{cid}/{suffix}',body,'carol')[0],404)
        self.assertEqual(self.request('GET','/api/conversations',who='carol')[1], {'conversations':[]})

    def test_idempotency_concurrency_and_conflict(self):
        cid = self.conversation()
        client_id = str(uuid4())
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.send(cid,client_id=client_id),range(8)))
        self.assertTrue(all(status == 200 for status, _ in results),results)
        self.assertEqual(len({r['message']['id'] for _,r in results}),1)
        other = self.conversation(peer='carol')
        self.assertEqual(self.send(other,client_id=client_id)[0],409)
        status, body = self.request('GET',f'/api/conversations/{cid}/messages',who='bobby')
        self.assertEqual(len(body['messages']),1)
        self.assertEqual(set(body['messages'][0]), {'id','senderId','envelope','createdAt'})

    def test_read_unread_pagination_and_block(self):
        cid = self.conversation()
        for _ in range(51):
            self.assertEqual(self.send(cid)[0],200)
        listed = self.request('GET','/api/conversations',who='bobby')[1]['conversations'][0]
        self.assertEqual(listed['unread'],51)
        page = self.request('GET',f'/api/conversations/{cid}/messages',who='bobby')[1]
        self.assertEqual(len(page['messages']),50)
        self.assertTrue(page['hasMore'])
        after = page['messages'][-1]['id']
        page2 = self.request('GET',f'/api/conversations/{cid}/messages?after={after}',who='bobby')[1]
        self.assertEqual(len(page2['messages']),1)
        self.assertFalse(page2['hasMore'])
        self.assertEqual(self.request('POST',f'/api/conversations/{cid}/read',dict(messageId=999999),'bobby')[0],200)
        self.send(cid)
        self.assertEqual(self.request('GET','/api/conversations',who='bobby')[1]['conversations'][0]['unread'],1)
        self.request('POST',f'/api/conversations/{cid}/read',dict(messageId=0),'bobby')
        self.assertEqual(self.request('GET','/api/conversations',who='bobby')[1]['conversations'][0]['unread'],1)
        result = self.request('POST',f'/api/conversations/{cid}/block',dict(blocked=True),'bobby')
        self.assertTrue(result[1]['conversation']['blocked'])
        self.assertEqual(self.send(cid)[0],403)
        self.assertEqual(self.send(cid,'bobby')[0],403)
        self.request('POST',f'/api/conversations/{cid}/block',dict(blocked=False))
        self.assertEqual(self.send(cid)[0],403)
        self.request('POST',f'/api/conversations/{cid}/block',dict(blocked=False),'bobby')
        self.assertEqual(self.send(cid)[0],200)

    def test_rate_proxy_and_request_limits(self):
        for _ in range(10):
            self.app.limit('auth_account','attacker',10,900)
        with self.assertRaises(Exception):
            self.app.limit('auth_account','attacker',10,900)
        restarted = create_app(self.dbpath, clock=lambda:self.now)
        with self.assertRaises(Exception):
            restarted.limit('auth_account','attacker',10,900)
        cid = self.conversation()
        for _ in range(120):
            self.app.limit('send_account','1',120,60)
        self.assertEqual(self.send(cid)[0],429)
        self.assertEqual(self.request('POST','/api/logout',{},CONTENT_LENGTH='65537')[0],413)
        self.assertEqual(self.request('GET','/api/me',HTTP_ORIGIN='https://evil.example')[0],403)
        self.assertEqual(self.request('OPTIONS','/api/me',HTTP_ORIGIN='https://localhost',HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',HTTP_ACCESS_CONTROL_REQUEST_HEADERS='authorization,content-type')[0],200)
        # Inspect subjects fed to persistent counters, not secret material.
        observed=[]
        original=self.app.limit
        self.app.limit=lambda bucket,subject,*args: observed.append((bucket,subject))
        with patch.dict(os.environ,{'CIPHER_MESSENGER_TRUST_PROXY':'0'}):
            self.request('POST','/api/login',dict(username='alice',password='wrong credential'),None,HTTP_X_FORWARDED_FOR='1.2.3.4, 5.6.7.8')
        self.assertIn(('auth_ip','127.0.0.1'),observed)
        observed.clear()
        with patch.dict(os.environ,{'CIPHER_MESSENGER_TRUST_PROXY':'1'}):
            self.request('POST','/api/login',dict(username='alice',password='wrong credential'),None,HTTP_X_FORWARDED_FOR='1.2.3.4, 5.6.7.8')
        self.assertIn(('auth_ip','5.6.7.8'),observed)
        self.app.limit=original

    def test_ciphertext_validation(self):
        cid=self.conversation()
        for envelope in (dict(ENVELOPE,v=True),dict(ENVELOPE,iv=enc(b'a'*11)),dict(ENVELOPE,ct=enc(b'a'*30721)),dict(ENVELOPE,ct='plaintext!')):
            self.assertEqual(self.request('POST',f'/api/conversations/{cid}/messages',dict(clientId=str(uuid4()),envelope=envelope))[0],400)

    def test_storage_caps_and_retry_at_capacity(self):
        cid=self.conversation()
        client_id=str(uuid4())
        first=self.send(cid,client_id=client_id)
        with closing(sqlite3.connect(self.dbpath)) as db, db:
            db.executemany('INSERT INTO messages(conversation_id,sender_id,client_id,envelope,created) VALUES(?,?,?,?,?)', ((cid,1,str(uuid4()),json.dumps(ENVELOPE),self.now) for _ in range(19999)))
            db.executemany('INSERT INTO users(username,salt,password_hash,public_key,key_backup) VALUES(?,?,?,?,?)', ((f'user_{i}',b's'*16,b'h'*32,json.dumps(KEY),json.dumps(BACKUP)) for i in range(497)))
        self.assertEqual(self.send(cid)[0],429)
        self.assertEqual(self.send(cid,client_id=client_id),first)
        self.assertEqual(self.request('POST','/api/register',dict(username='overflow',password=SECRET,publicKey=KEY,keyBackup=BACKUP),None)[0],429)


if __name__ == '__main__':
    unittest.main()
