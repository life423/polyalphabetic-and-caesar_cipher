"""Generic Android alerts: durable outbox; no conversation content leaves Azure."""
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID

SCHEMA = '''
CREATE TABLE IF NOT EXISTS push_devices(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), installation_hash TEXT UNIQUE NOT NULL, token TEXT UNIQUE NOT NULL, session_hash TEXT NOT NULL, expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS push_outbox(id INTEGER PRIMARY KEY, device_id INTEGER NOT NULL REFERENCES push_devices(id) ON DELETE CASCADE, message_id INTEGER NOT NULL REFERENCES messages(id), conversation_id INTEGER NOT NULL REFERENCES conversations(id), recipient_id INTEGER NOT NULL REFERENCES users(id), attempts INTEGER NOT NULL DEFAULT 0, next_attempt INTEGER NOT NULL, expires INTEGER NOT NULL, lease_until INTEGER NOT NULL DEFAULT 0, UNIQUE(device_id,conversation_id));
CREATE INDEX IF NOT EXISTS push_due ON push_outbox(next_attempt,lease_until);
'''


class PushError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


class SendError(Exception):
    def __init__(self, permanent=False):
        self.permanent = permanent


def installation_hash(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
        if parsed is None or parsed.version != 4 or str(parsed) != value:
            raise ValueError()
    except ValueError:
        raise PushError(400, 'invalid_installation')
    return hashlib.sha256(value.encode()).hexdigest()


class FirebaseSender:
    def __init__(self, info):
        self.info, self.credentials = info, None

    @classmethod
    def from_environment(cls):
        try:
            raw = os.environ.get('CIPHER_FCM_SERVICE_ACCOUNT', '')
            if not raw and os.environ.get('CIPHER_FCM_CREDENTIALS_FILE'):
                raw = Path(os.environ['CIPHER_FCM_CREDENTIALS_FILE']).read_text(encoding='utf-8')
            if not raw:
                return None
            info = json.loads(raw)
            if (info.get('type') != 'service_account' or not isinstance(info.get('project_id'), str)
                    or not re.fullmatch(r'[a-z][a-z0-9-]{4,61}[a-z0-9]', info['project_id'])
                    or not info.get('client_email') or not info.get('private_key')):
                return None
            # Prevent credential-provided token URLs from sending a signed assertion elsewhere.
            if info.get('token_uri') != 'https://oauth2.googleapis.com/token':
                return None
            return cls(info)
        except (ValueError, OSError, TypeError):
            return None

    def __call__(self, token, data):
        try:
            if self.credentials is None:
                from google.oauth2 import service_account
                self.credentials = service_account.Credentials.from_service_account_info(
                    self.info, scopes=['https://www.googleapis.com/auth/firebase.messaging'])
            if not self.credentials.valid:
                from google.auth.transport.requests import Request as GoogleRequest
                transport = GoogleRequest()

                def bounded_request(url, method='GET', body=None, headers=None, timeout=5, **kwargs):
                    return transport(url=url, method=method, body=body, headers=headers, timeout=min(timeout or 5, 5), **kwargs)

                self.credentials.refresh(bounded_request)
            body = {'message': {
                'token': token,
                'notification': {'title': 'CipherCraft', 'body': 'You have a new encrypted message.'},
                'data': {key: str(data[key]) for key in ('conversationId', 'recipientId', 'messageId')},
                'android': {'priority': 'HIGH', 'ttl': '86400s', 'notification': {
                    'channel_id': 'ciphercraft_messages', 'tag': 'conversation-' + str(data['conversationId']),
                    'icon': 'ic_stat_ciphercraft', 'sound': 'default', 'visibility': 'PRIVATE'}}}}
            request = Request('https://fcm.googleapis.com/v1/projects/' + self.info['project_id'] + '/messages:send',
                              data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + self.credentials.token,
                                                                        'Content-Type': 'application/json'})
            with urlopen(request, timeout=5) as response:
                response.read(65536)
        except HTTPError as error:
            permanent = False
            try:
                result = json.loads(error.read(65536))
                permanent = any(d.get('errorCode') == 'UNREGISTERED' for d in result.get('error', {}).get('details', []))
            except (ValueError, TypeError, AttributeError):
                pass
            raise SendError(permanent) from None
        except Exception:
            # Never log tokens, credentials, content, provider error bodies or request headers.
            raise SendError() from None


class PushDelivery:
    def __init__(self, connect, clock=time.time, sender=None):
        self.connect, self.clock, self.sender = connect, clock, sender
        self.event = threading.Event()
        self.stopping = threading.Event()
        self.worker = None

    @property
    def configured(self):
        return self.sender is not None

    def register(self, uid, session_hash, body):
        if not self.configured:
            raise PushError(503, 'notifications_unavailable')
        identity = installation_hash(body.get('installationId'))
        token = body.get('token')
        if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_:.-]{20,4096}', token):
            raise PushError(400, 'invalid_push_token')
        now = int(self.clock())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND user_id=? AND expires>?', (session_hash, uid, now)).fetchone():
                raise PushError(401, 'unauthorized')
            db.execute('DELETE FROM push_devices WHERE expires<=?', (now,))
            existing = db.execute('SELECT * FROM push_devices WHERE token=?', (token,)).fetchone()
            if existing and existing['installation_hash'] != identity:
                raise PushError(409, 'push_device_conflict')
            current = db.execute('SELECT * FROM push_devices WHERE installation_hash=?', (identity,)).fetchone()
            if not current or current['user_id'] != uid:
                if db.execute('SELECT count(*) FROM push_devices WHERE user_id=?', (uid,)).fetchone()[0] >= 5:
                    raise PushError(429, 'push_device_limit')
            if current:
                # A new login/owner cannot inherit a previous session's queued alerts.
                if current['user_id'] != uid or current['session_hash'] != session_hash or current['token'] != token:
                    db.execute('DELETE FROM push_outbox WHERE device_id=?', (current['id'],))
                db.execute('UPDATE push_devices SET user_id=?,token=?,session_hash=?,expires=? WHERE id=?',
                           (uid, token, session_hash, now + 30 * 86400, current['id']))
            else:
                db.execute('INSERT INTO push_devices(user_id,installation_hash,token,session_hash,expires) VALUES(?,?,?,?,?)',
                           (uid, identity, token, session_hash, now + 30 * 86400))
        return {'enabled': True}

    def unregister(self, uid, session_hash, body):
        identity = installation_hash(body.get('installationId'))
        with self.connect() as db:
            db.execute('DELETE FROM push_devices WHERE user_id=? AND installation_hash=? AND session_hash=?', (uid, identity, session_hash))
        return {'enabled': False}

    def enqueue(self, db, cid, mid, sender_id):
        now = int(self.clock())
        db.execute('DELETE FROM push_outbox WHERE expires<=?', (now,))
        if db.execute('SELECT count(*) FROM push_outbox').fetchone()[0] >= 10000:
            return
        db.execute('''INSERT INTO push_outbox(device_id,message_id,conversation_id,recipient_id,next_attempt,expires)
            SELECT d.id,?,?,d.user_id,?,? FROM push_devices d JOIN members m ON m.user_id=d.user_id
            WHERE m.conversation_id=? AND d.user_id<>? AND d.expires>?
            ON CONFLICT(device_id,conversation_id) DO UPDATE SET message_id=excluded.message_id,
            next_attempt=excluded.next_attempt,expires=excluded.expires,attempts=0,lease_until=0''',
                   (mid, cid, now, now + 86400, cid, sender_id, now))

    def drain(self, limit=10):
        if not self.configured:
            return
        for _ in range(limit):
            now = int(self.clock())
            with self.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('DELETE FROM push_outbox WHERE expires<=? OR attempts>=5', (now,))
                row = db.execute('''SELECT o.*,d.token,d.user_id,d.expires device_expires,m.read_id
                    FROM push_outbox o JOIN push_devices d ON d.id=o.device_id
                    JOIN members m ON m.conversation_id=o.conversation_id AND m.user_id=o.recipient_id
                    WHERE o.next_attempt<=? AND o.lease_until<=? ORDER BY o.id LIMIT 1''', (now, now)).fetchone()
                if not row:
                    return
                if (row['device_expires'] <= now or row['user_id'] != row['recipient_id'] or row['read_id'] >= row['message_id']
                        or db.execute('SELECT 1 FROM members WHERE conversation_id=? AND blocked=1', (row['conversation_id'],)).fetchone()):
                    db.execute('DELETE FROM push_outbox WHERE id=?', (row['id'],))
                    continue
                db.execute('UPDATE push_outbox SET lease_until=? WHERE id=?', (now + 30, row['id']))
            error = None
            try:
                self.sender(row['token'], {'conversationId': row['conversation_id'], 'recipientId': row['recipient_id'], 'messageId': row['message_id']})
            except SendError as exc:
                error = exc
            except Exception:
                error = SendError()
            with self.connect() as db:
                if error and error.permanent:
                    db.execute('DELETE FROM push_devices WHERE id=? AND token=?', (row['device_id'], row['token']))
                elif error:
                    db.execute('UPDATE push_outbox SET attempts=attempts+1,next_attempt=?,lease_until=0 WHERE id=? AND message_id=?',
                               (now + min(3600, 30 * 2 ** row['attempts']), row['id'], row['message_id']))
                else:
                    db.execute('DELETE FROM push_outbox WHERE id=? AND message_id=?', (row['id'], row['message_id']))

    def wake(self):
        self.event.set()

    def start(self):
        if not self.configured or self.worker is not None:
            return

        def run():
            while not self.stopping.is_set():
                try:
                    self.drain()
                except Exception:
                    pass
                self.event.wait(15)
                self.event.clear()

        self.worker = threading.Thread(target=run, name='ciphercraft-push', daemon=True)
        self.worker.start()

    def stop(self):
        self.stopping.set()
        self.event.set()
        if self.worker:
            self.worker.join(timeout=1)
