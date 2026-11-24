"""Push registration and durable delivery tests, with no external network calls."""
import base64
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from uuid import uuid4

from src.messenger.app import create_app
from src.messenger.push import FirebaseSender, SendError


def enc(value):
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


KEY = dict(kty='EC', crv='P-256', x=enc(bytes.fromhex('6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296')), y=enc(bytes.fromhex('4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5')))
BACKUP = dict(salt=enc(b's'*16), iv=enc(b'i'*12), ct=enc(b'b'*32))
ENVELOPE = dict(v=1, iv=enc(b'v'*12), ct=enc(b'c'*32))


class PushTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1800000000
        self.sent = []
        self.delivered = threading.Event()
        self.failure = None
        def sender(token, data):
            with self.app.connect() as db:
                self.assertIsNotNone(db.execute('SELECT id FROM messages WHERE id=?', (data['messageId'],)).fetchone())
            if self.failure:
                raise self.failure
            self.sent.append((token, data))
            self.delivered.set()
        self.app = create_app(Path(self.tmp.name)/'push.sqlite3', clock=lambda: self.now, push_sender=sender)
        self.a = self.register('sender_a')
        self.b = self.register('recipient_b')
        self.cid = self.call('/api/conversations', {'username':'recipient_b'}, self.a)[1]['conversation']['id']
        self.installation = str(uuid4())
        self.token = 'FCM:fictional_token_' + uuid4().hex

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, path, body=None, account=None):
        raw = json.dumps(body).encode() if body is not None else b''
        env = {'REQUEST_METHOD':'POST' if body is not None else 'GET', 'PATH_INFO':path,
               'CONTENT_LENGTH':str(len(raw)), 'CONTENT_TYPE':'application/json', 'wsgi.input':io.BytesIO(raw), 'REMOTE_ADDR':'127.0.0.1'}
        if account: env['HTTP_AUTHORIZATION'] = 'Bearer ' + account['token']
        response=[]
        data = b''.join(self.app(env, lambda status, headers: response.append(status)))
        return int(response[0].split()[0]), json.loads(data)

    def register(self, name):
        code, account = self.call('/api/register', {'username':name,'password':'fictional-derived-secret-12345','publicKey':KEY,'keyBackup':BACKUP})
        self.assertEqual(code,200)
        return account

    def device(self, account=None, installation=None, token=None):
        return self.call('/api/push/register', {'installationId':installation or self.installation,'token':token or self.token}, account or self.b)

    def message(self, client=None):
        return self.call(f'/api/conversations/{self.cid}/messages', {'clientId':client or str(uuid4()),'envelope':ENVELOPE}, self.a)

    def count(self, table):
        with self.app.connect() as db:
            return db.execute('SELECT count(*) FROM '+table).fetchone()[0]

    def test_authenticated_registration_and_idempotent_delivery(self):
        self.assertEqual(self.call('/api/push/status')[0],401)
        self.assertEqual(self.call('/api/push/status',account=self.b),(200,{'configured':True}))
        self.assertEqual(self.device()[0],200)
        self.assertEqual(self.device()[0],200)
        identity=str(uuid4())
        first=self.message(identity); second=self.message(identity)
        self.assertEqual(first,second)
        self.assertEqual(self.count('push_outbox'),1)
        self.app.push.drain(); self.app.push.drain()
        self.assertEqual(len(self.sent),1)
        token,data=self.sent[0]
        self.assertEqual(token,self.token)
        self.assertEqual(set(data),{'conversationId','recipientId','messageId'})
        self.assertEqual(data['recipientId'],self.b['user']['id'])
        self.assertEqual(self.count('push_outbox'),0)

    def test_background_worker_dispatches_after_commit_without_browser_polling(self):
        self.device()
        self.app.push.start()
        try:
            self.assertEqual(self.message()[0],200)
            self.assertTrue(self.delivered.wait(3), 'Background worker did not deliver the queued alert')
        finally:
            self.app.push.stop()
        self.assertEqual(len(self.sent),1)
        self.assertEqual(self.count('push_outbox'),0)

    def test_latest_pending_message_coalesces_and_read_skips_alert(self):
        self.device();self.message();mid=self.message()[1]['message']['id']
        self.assertEqual(self.count('push_outbox'),1)
        self.call(f'/api/conversations/{self.cid}/read',{'messageId':mid},self.b)
        self.app.push.drain()
        self.assertEqual(self.sent,[])
        self.assertEqual(self.count('push_outbox'),0)

    def test_sender_is_not_notified_and_block_suppresses_pending(self):
        self.device(account=self.a,installation=str(uuid4()),token='sender_'+uuid4().hex)
        self.device();self.message()
        self.assertEqual(self.count('push_outbox'),1)
        self.call(f'/api/conversations/{self.cid}/block',{'blocked':True},self.b)
        self.app.push.drain()
        self.assertEqual(self.sent,[])

    def test_logout_only_revokes_its_own_phone(self):
        self.device(); other=self.register('another_recipient')
        self.device(account=other,installation=str(uuid4()),token='other_'+uuid4().hex)
        self.message()
        self.assertEqual(self.call('/api/logout',{},self.b)[0],200)
        self.assertEqual(self.count('push_devices'),1)
        self.assertEqual(self.count('push_outbox'),0)
        self.app.push.drain();self.assertEqual(self.sent,[])
        self.assertEqual(self.device()[0],401)

    def test_unregistration_cannot_remove_other_users_device(self):
        self.device();self.message()
        self.assertEqual(self.call('/api/push/unregister',{'installationId':self.installation},self.a)[0],200)
        self.assertEqual(self.count('push_devices'),1)
        self.call('/api/push/unregister',{'installationId':self.installation},self.b)
        self.assertEqual(self.count('push_devices'),0)
        self.assertEqual(self.count('push_outbox'),0)

    def test_token_theft_rejected_and_account_switch_clears_old_queue(self):
        self.device();self.message()
        self.assertEqual(self.device(account=self.a,installation=str(uuid4()))[0],409)
        self.assertEqual(self.device(account=self.a)[0],200)
        self.assertEqual(self.count('push_outbox'),0)
        self.message();self.app.push.drain();self.assertEqual(self.sent,[])

    def test_registration_validation_and_device_limit(self):
        self.assertEqual(self.device(installation='not-a-uuid')[0],400)
        self.assertEqual(self.device(token='wrong token')[0],400)
        for _ in range(5): self.assertEqual(self.device(installation=str(uuid4()),token='token_'+uuid4().hex)[0],200)
        self.assertEqual(self.device()[0],429)

    def test_failure_retry_permanent_removal_and_message_success(self):
        self.device();self.failure=SendError()
        self.assertEqual(self.message()[0],200)
        self.app.push.drain();self.assertEqual(self.sent,[])
        self.assertEqual(self.count('push_outbox'),1)
        self.failure=None;self.app.push.drain();self.assertEqual(self.sent,[])
        self.now+=31;self.app.push.drain();self.assertEqual(len(self.sent),1)
        self.message();self.failure=SendError(True);self.app.push.drain()
        self.assertEqual(self.count('push_devices'),0)

    def test_retry_budget_and_device_expiry(self):
        self.device();self.message();self.failure=SendError()
        for _ in range(6): self.app.push.drain();self.now+=4000
        self.assertEqual(self.count('push_outbox'),0)
        self.now+=31*86400
        self.message();self.app.push.drain()
        self.assertEqual(self.sent,[])

    def test_background_binding_outlives_memory_session_but_logout_revokes(self):
        self.device()
        self.now+=8*86400
        # Sender signs back in; recipient app remains closed with no session.
        self.a=self.call('/api/login',{'username':'sender_a','password':'fictional-derived-secret-12345'})[1]
        self.assertEqual(self.message()[0],200)
        self.app.push.drain();self.assertEqual(len(self.sent),1)


class FirebasePayloadTests(unittest.TestCase):
    def test_private_payload_and_permanent_error_handling(self):
        sender=FirebaseSender({'project_id':'ciphercraft-test'})
        sender.credentials=type('Credential',(),{'valid':True,'token':'fixture-oauth-token'})()
        captured=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'{}'
        def send(request,timeout):captured.append(json.loads(request.data));return Response()
        with patch('src.messenger.push.urlopen',send):
            sender('fixture-device-token',{'conversationId':1,'recipientId':2,'messageId':3})
        message=captured[0]['message']
        self.assertEqual(message['notification'],{'title':'CipherCraft','body':'You have a new encrypted message.'})
        self.assertEqual(message['data'],{'conversationId':'1','recipientId':'2','messageId':'3'})
        self.assertEqual(message['android']['notification']['channel_id'],'ciphercraft_messages')
        error=HTTPError('https://fcm.googleapis.com/',404,'error',{},io.BytesIO(b'{"error":{"details":[{"errorCode":"UNREGISTERED"}]}}'))
        with patch('src.messenger.push.urlopen',side_effect=error):
            with self.assertRaises(SendError) as result:sender('fixture-token',{'conversationId':1,'recipientId':2,'messageId':3})
        self.assertTrue(result.exception.permanent)

    def test_untrusted_credential_token_url_is_rejected(self):
        info={'type':'service_account','project_id':'ciphercraft-test','client_email':'sender@example.invalid','private_key':'test-only','token_uri':'https://attacker.invalid/token'}
        with patch.dict('os.environ',{'CIPHER_FCM_SERVICE_ACCOUNT':json.dumps(info)}):
            self.assertIsNone(FirebaseSender.from_environment())


if __name__=='__main__':unittest.main()
