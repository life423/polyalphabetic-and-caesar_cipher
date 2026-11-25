import base64
from contextlib import contextmanager
import ipaddress
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from urllib.parse import parse_qs, urlsplit
from uuid import UUID
from .push import FirebaseSender, PushDelivery, PushError, SCHEMA as PUSH_SCHEMA
from . import admin

ITERATIONS = 600_000
SESSION_SECONDS = 7 * 86400
DEFAULT_ORIGINS = 'http://localhost:8502,https://cipher.drewclark.io,https://localhost'
P = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
B = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, password_hash BLOB NOT NULL, public_key TEXT NOT NULL, key_backup TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS session_expiry ON sessions(expires);
CREATE TABLE IF NOT EXISTS conversations(id INTEGER PRIMARY KEY, low INTEGER NOT NULL REFERENCES users(id), high INTEGER NOT NULL REFERENCES users(id), updated INTEGER NOT NULL, UNIQUE(low, high));
CREATE TABLE IF NOT EXISTS members(conversation_id INTEGER NOT NULL REFERENCES conversations(id), user_id INTEGER NOT NULL REFERENCES users(id), read_id INTEGER NOT NULL DEFAULT 0, blocked INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(conversation_id,user_id));
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id), sender_id INTEGER NOT NULL REFERENCES users(id), client_id TEXT NOT NULL, envelope TEXT NOT NULL, created INTEGER NOT NULL, UNIQUE(sender_id,client_id));
CREATE INDEX IF NOT EXISTS message_conversation ON messages(conversation_id,id);
CREATE TABLE IF NOT EXISTS record_counters(name TEXT PRIMARY KEY, value INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS message_tombstones(sender_id INTEGER NOT NULL REFERENCES users(id), client_id TEXT NOT NULL, PRIMARY KEY(sender_id,client_id));
CREATE TABLE IF NOT EXISTS rate_limits(bucket TEXT NOT NULL, subject TEXT NOT NULL, window INTEGER NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(bucket,subject));
'''


class APIError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


def require(condition, code='invalid_request', status=400):
    if not condition:
        raise APIError(status, code)


def b64(value, size=None, maximum=None):
    require(isinstance(value, str) and bool(re.fullmatch(r'[A-Za-z0-9_-]+', value)), 'invalid_encoding')
    require(len(value) <= ((maximum or size or 30720) * 4 + 2) // 3, 'invalid_encoding')
    try:
        raw = base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))
    except (ValueError, base64.binascii.Error):
        raise APIError(400, 'invalid_encoding')
    require(base64.urlsafe_b64encode(raw).decode().rstrip('=') == value, 'invalid_encoding')
    require(size is None or len(raw) == size, 'invalid_encoding')
    require(maximum is None or len(raw) <= maximum, 'invalid_encoding')
    return raw


def public_key(value):
    require(isinstance(value, dict) and set(value) == {'kty', 'crv', 'x', 'y'}, 'invalid_public_key')
    require(value['kty'] == 'EC' and value['crv'] == 'P-256', 'invalid_public_key')
    x, y = (int.from_bytes(b64(value[k], size=32), 'big') for k in ('x', 'y'))
    require(x < P and y < P and (y*y - (x*x*x - 3*x + B)) % P == 0, 'invalid_public_key')
    return value


def opaque(value, backup=False):
    keys = {'salt', 'iv', 'ct'} if backup else {'v', 'iv', 'ct'}
    require(isinstance(value, dict) and set(value) == keys, 'invalid_envelope')
    if backup:
        b64(value['salt'], size=16)
    else:
        require(type(value['v']) is int and value['v'] == 1, 'invalid_envelope')
    b64(value['iv'], size=12)
    require(len(b64(value['ct'], maximum=4096 if backup else 30720)) >= 16, 'invalid_envelope')
    return value


def username(value):
    require(isinstance(value, str) and re.fullmatch(r'[a-z0-9_]{3,24}', value), 'invalid_username')
    return value


def message(row):
    return dict(id=row['id'], senderId=row['sender_id'], envelope=json.loads(row['envelope']), createdAt=row['created'])


class Messenger:
    def __init__(self, db_path=None, origins=None, clock=time.time, push_sender=None):
        self.path = str(db_path or os.environ.get('CIPHER_MESSENGER_DB') or ('/home/data/cipher-messenger.sqlite3' if os.environ.get('WEBSITE_SITE_NAME') else Path(__file__).resolve().parents[2] / '.venv/messenger.sqlite3'))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.admin_ids = admin.admin_ids(os.environ.get('CIPHER_MESSENGER_ADMIN_IDS', ''))
        self.origins = set((origins if origins is not None else os.environ.get('CIPHER_MESSENGER_ORIGINS', DEFAULT_ORIGINS)).split(','))
        self.origins = {o.strip() for o in self.origins if o.strip()}
        for origin in self.origins:
            parsed = urlsplit(origin)
            if origin == '*' or parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
                raise ValueError('Origins must be exact http(s) origins')
        with self.connect() as db:
            db.execute('PRAGMA journal_mode=DELETE')
            db.executescript(SCHEMA + PUSH_SCHEMA + admin.SCHEMA)
            for table in ('users', 'conversations', 'messages'):
                db.execute('INSERT INTO record_counters(name,value) SELECT ?,COALESCE(MAX(id),0) FROM ' + table + ' WHERE 1 ON CONFLICT(name) DO UPDATE SET value=MAX(value,excluded.value)', (table,))
        self.push = PushDelivery(self.connect, self.clock, push_sender or FirebaseSender.from_environment())

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def limit(self, bucket, subject, maximum, seconds):
        now = int(self.clock())
        # Hash identifiers to avoid retaining IPs or entered account names.
        subject = hashlib.sha256(subject.encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM rate_limits WHERE window < ?', (now - 3600,))
            db.execute('DELETE FROM sessions WHERE expires <= ?', (now,))
            window = now // seconds * seconds
            db.execute('INSERT INTO rate_limits VALUES(?,?,?,1) ON CONFLICT(bucket,subject) DO UPDATE SET count=CASE WHEN window=excluded.window THEN count+1 ELSE 1 END, window=excluded.window', (bucket, subject, window))
            count = db.execute('SELECT count FROM rate_limits WHERE bucket=? AND subject=?', (bucket, subject)).fetchone()[0]
            # A hard cap bounds cardinality even with hostile account/IP churn.
            db.execute('DELETE FROM rate_limits WHERE rowid IN (SELECT rowid FROM rate_limits ORDER BY window DESC,rowid DESC LIMIT -1 OFFSET 10000)')
        require(count <= maximum, 'rate_limited', 429)

    def user(self, row, private=False):
        result = dict(id=row['id'], username=row['username'], publicKey=json.loads(row['public_key']))
        if private:
            result['keyBackup'] = json.loads(row['key_backup'])
        return result

    def next_id(self, db, table):
        if table not in ('users', 'conversations', 'messages'):
            raise ValueError('Unknown record counter')
        return db.execute('UPDATE record_counters SET value=MAX(value,(SELECT COALESCE(MAX(id),0) FROM ' + table + '))+1 WHERE name=? RETURNING value', (table,)).fetchone()[0]

    def member(self, db, cid, uid):
        row = db.execute('SELECT * FROM members WHERE conversation_id=? AND user_id=?', (cid, uid)).fetchone()
        require(row is not None, 'not_found', 404)
        return row

    def conversation(self, db, cid, uid):
        member = self.member(db, cid, uid)
        row = db.execute('SELECT * FROM conversations WHERE id=?', (cid,)).fetchone()
        peer_id = row['high'] if row['low'] == uid else row['low']
        peer = db.execute('SELECT * FROM users WHERE id=?', (peer_id,)).fetchone()
        unread = db.execute('SELECT count(*) FROM messages WHERE conversation_id=? AND sender_id!=? AND id>?', (cid, uid, member['read_id'])).fetchone()[0]
        return dict(id=cid, peer=self.user(peer), updatedAt=row['updated'], unread=unread, blocked=bool(member['blocked']))

    def delete_account(self, body, ip, now):
        # Reauthentication also works for suspended accounts and from the public page.
        self.limit('auth_ip', ip, 30, 900)
        name = username(body.get('username'))
        self.limit('auth_account', name, 10, 900)
        require(set(body) == {'username', 'password', 'confirmation'})
        secret = body.get('password')
        require(isinstance(secret, str) and 12 <= len(secret) <= 1024, 'invalid_password')
        require(body.get('confirmation') == name, 'confirmation_mismatch', 409)
        with self.connect() as db:
            db.execute('PRAGMA secure_delete=ON')
            db.execute('BEGIN IMMEDIATE')
            account = db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
            digest = hashlib.pbkdf2_hmac('sha256', secret.encode(), account['salt'] if account else b'\0'*16, ITERATIONS)
            require(account is not None and hmac.compare_digest(digest, account['password_hash']), 'invalid_credentials', 401)
            uid = account['id']
            require(uid not in self.admin_ids, 'protected_admin', 409)
            related = 'SELECT id FROM conversations WHERE low=? OR high=?'
            db.execute('DELETE FROM push_outbox WHERE conversation_id IN (' + related + ') OR recipient_id=?', (uid, uid, uid))
            db.execute('DELETE FROM messages WHERE conversation_id IN (' + related + ')', (uid, uid))
            db.execute('DELETE FROM members WHERE conversation_id IN (' + related + ')', (uid, uid))
            db.execute('DELETE FROM conversations WHERE low=? OR high=?', (uid, uid))
            db.execute('DELETE FROM push_devices WHERE user_id=?', (uid,))
            db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            db.execute('DELETE FROM account_status WHERE user_id=?', (uid,))
            db.execute('DELETE FROM message_tombstones WHERE sender_id=?', (uid,))
            db.execute('DELETE FROM admin_audit WHERE actor_id=? OR target_id=?', (uid, uid))
            # Keep only network-based abuse limits, not the removed account's identifiers.
            db.execute('DELETE FROM rate_limits WHERE subject IN (?,?)',
                       (hashlib.sha256(name.encode()).hexdigest(), hashlib.sha256(str(uid).encode()).hexdigest()))
            db.execute('DELETE FROM users WHERE id=?', (uid,))
        return {'deleted': True}

    def dispatch(self, env, body):
        method, path = env['REQUEST_METHOD'], env.get('PATH_INFO', '')
        now = int(self.clock())
        ip = env.get('REMOTE_ADDR', 'unknown')
        if os.environ.get('CIPHER_MESSENGER_TRUST_PROXY') == '1':
            forwarded = env.get('HTTP_X_FORWARDED_FOR', '').split(',')[-1].strip()
            if forwarded:
                try:
                    ip = str(ipaddress.ip_address(forwarded))
                except ValueError:
                    pass # Malformed trusted-proxy header falls back to REMOTE_ADDR.
        if path == '/api/health' and method == 'GET':
            with self.connect() as db:
                db.execute('SELECT 1').fetchone()
            return {'ok': True}
        if path == '/api/account/delete' and method == 'POST':
            return self.delete_account(body, ip, now)
        if path in ('/api/register', '/api/login') and method == 'POST':
            self.limit('auth_ip', ip, 30, 900)
            name = username(body.get('username'))
            self.limit('auth_account', name, 10, 900)
            password = body.get('password')
            require(isinstance(password, str) and 12 <= len(password) <= 1024, 'invalid_password')
            with self.connect() as db:
                if path == '/api/register':
                    key = public_key(body.get('publicKey'))
                    backup = opaque(body.get('keyBackup'), True)
                    salt = secrets.token_bytes(16)
                    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
                    db.execute('BEGIN IMMEDIATE')
                    require(db.execute('SELECT count(*) FROM users').fetchone()[0] < 500, 'user_capacity_reached', 429)
                    try:
                        cur = db.execute('INSERT INTO users(id,username,salt,password_hash,public_key,key_backup) VALUES(?,?,?,?,?,?)', (self.next_id(db, 'users'), name, salt, digest, json.dumps(key), json.dumps(backup)))
                    except sqlite3.IntegrityError:
                        raise APIError(409, 'username_taken')
                    row = db.execute('SELECT * FROM users WHERE id=?', (cur.lastrowid,)).fetchone()
                else:
                    db.execute('BEGIN IMMEDIATE')
                    row = db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
                    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), row['salt'] if row else b'\0'*16, ITERATIONS)
                    require(row is not None and hmac.compare_digest(digest, row['password_hash']), 'invalid_credentials', 401)
                    require(not db.execute('SELECT 1 FROM account_status WHERE user_id=? AND suspended=1', (row['id'],)).fetchone(), 'account_suspended', 403)
                db.execute('INSERT INTO account_status(user_id,created,last_login) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET last_login=excluded.last_login',
                           (row['id'], now if path == '/api/register' else None, now))
                token = secrets.token_urlsafe(32)
                db.execute('INSERT INTO sessions VALUES(?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), row['id'], now + SESSION_SECONDS))
                return {'token': token, 'user': self.user(row, True)}
        auth = env.get('HTTP_AUTHORIZATION', '')
        require(bool(re.fullmatch(r'Bearer [A-Za-z0-9_-]{43}', auth)), 'unauthorized', 401)
        token_hash = hashlib.sha256(auth[7:].encode()).hexdigest()
        with self.connect() as db:
            row = db.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE token_hash=? AND expires>?', (token_hash, now)).fetchone()
            require(row is not None, 'unauthorized', 401)
            uid = row['id']
            require(not db.execute('SELECT 1 FROM account_status WHERE user_id=? AND suspended=1', (uid,)).fetchone(), 'account_suspended', 403)
            if path.startswith('/api/admin/'):
                return admin.dispatch(self, db, env, body, uid, token_hash, now)
            if path == '/api/push/status' and method == 'GET':
                return {'configured': self.push.configured}
            if path in ('/api/push/register', '/api/push/unregister') and method == 'POST':
                self.limit('push_devices', str(uid), 20, 60)
                if path.endswith('/register'):
                    return self.push.register(uid, token_hash, body)
                return self.push.unregister(uid, token_hash, body)
            if path == '/api/me' and method == 'GET':
                return {'user': self.user(row, True)}
            if path == '/api/account/deletion-status' and method == 'GET':
                return {'allowed': uid not in self.admin_ids}
            if path == '/api/logout' and method == 'POST':
                db.execute('DELETE FROM push_devices WHERE session_hash=?', (token_hash,))
                db.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash,))
                return {'ok': True}
            if path == '/api/people' and method == 'GET':
                self.limit('lookup', str(uid), 60, 60)
                query = parse_qs(env.get('QUERY_STRING', ''), max_num_fields=10)
                require(len(query.get('username', [])) == 1, 'invalid_username')
                name = username(query['username'][0])
                person = db.execute('SELECT * FROM users WHERE username=?', (name,)).fetchone()
                require(person is not None, 'not_found', 404)
                return {'user': self.user(person)}
            if path == '/api/conversations':
                if method == 'GET':
                    ids = db.execute('SELECT c.id FROM conversations c JOIN members m ON m.conversation_id=c.id WHERE m.user_id=? ORDER BY c.updated DESC,c.id DESC', (uid,)).fetchall()
                    return {'conversations': [self.conversation(db, r['id'], uid) for r in ids]}
                if method == 'POST':
                    self.limit('conversation', str(uid), 30, 60)
                    name = username(body.get('username'))
                    db.execute('BEGIN IMMEDIATE')
                    require(db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND expires>?', (token_hash, now)).fetchone() is not None, 'unauthorized', 401)
                    peer = db.execute('SELECT id FROM users WHERE username=?', (name,)).fetchone()
                    require(peer is not None, 'not_found', 404)
                    require(peer['id'] != uid, 'self_conversation')
                    low, high = sorted((uid, peer['id']))
                    db.execute('INSERT OR IGNORE INTO conversations(id,low,high,updated) VALUES(?,?,?,?)', (self.next_id(db, 'conversations'), low, high, now))
                    cid = db.execute('SELECT id FROM conversations WHERE low=? AND high=?', (low, high)).fetchone()[0]
                    for member in (low, high):
                        db.execute('INSERT OR IGNORE INTO members(conversation_id,user_id) VALUES(?,?)', (cid, member))
                    return {'conversation': self.conversation(db, cid, uid)}
            match = re.fullmatch(r'/api/conversations/([1-9][0-9]{0,17})/(messages|read|block)', path)
            require(match is not None, 'not_found', 404)
            cid, action = int(match[1]), match[2]
            self.member(db, cid, uid)
            if action == 'messages' and method == 'GET':
                query = parse_qs(env.get('QUERY_STRING', ''), max_num_fields=10)
                after = query.get('after', ['0'])
                require(len(after) == 1 and re.fullmatch(r'[0-9]{1,18}', after[0]), 'invalid_cursor')
                rows = db.execute('SELECT * FROM messages WHERE conversation_id=? AND id>? ORDER BY id LIMIT 51', (cid, int(after[0]))).fetchall()
                return {'messages': [message(r) for r in rows[:50]], 'hasMore': len(rows) > 50}
            if action == 'messages' and method == 'POST':
                self.limit('send_account', str(uid), 120, 60)
                self.limit('send_ip', ip, 240, 60)
                client_id = body.get('clientId')
                require(isinstance(client_id, str) and len(client_id) == 36, 'invalid_client_id')
                try:
                    parsed = UUID(client_id)
                except ValueError:
                    raise APIError(400, 'invalid_client_id')
                require(parsed.version == 4 and str(parsed) == client_id, 'invalid_client_id')
                envelope = opaque(body.get('envelope'))
                # Serialize block checks and insertion with block updates and competing retries.
                db.execute('BEGIN IMMEDIATE')
                require(db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND expires>?', (token_hash, now)).fetchone() is not None, 'unauthorized', 401)
                self.member(db, cid, uid)
                require(not db.execute('SELECT 1 FROM account_status WHERE user_id IN (SELECT user_id FROM members WHERE conversation_id=?) AND suspended=1', (cid,)).fetchone(), 'account_unavailable', 403)
                require(not db.execute('SELECT 1 FROM message_tombstones WHERE sender_id=? AND client_id=?', (uid, client_id)).fetchone(), 'message_deleted', 410)
                require(not db.execute('SELECT 1 FROM members WHERE conversation_id=? AND blocked=1', (cid,)).fetchone(), 'blocked', 403)
                existing = db.execute('SELECT * FROM messages WHERE sender_id=? AND client_id=?', (uid, client_id)).fetchone()
                if existing:
                    require(existing['conversation_id'] == cid and json.loads(existing['envelope']) == envelope, 'client_id_conflict', 409)
                    return {'message': message(existing)}
                require(db.execute('SELECT count(*) FROM messages').fetchone()[0] < 20000, 'message_capacity_reached', 429)
                cur = db.execute('INSERT INTO messages(id,conversation_id,sender_id,client_id,envelope,created) VALUES(?,?,?,?,?,?)', (self.next_id(db, 'messages'), cid, uid, client_id, json.dumps(envelope), now))
                self.push.enqueue(db, cid, cur.lastrowid, uid)
                db.execute('UPDATE conversations SET updated=? WHERE id=?', (now, cid))
                return {'message': message(db.execute('SELECT * FROM messages WHERE id=?', (cur.lastrowid,)).fetchone())}
            if action == 'read' and method == 'POST':
                mid = body.get('messageId')
                require(type(mid) is int and 0 <= mid <= 9223372036854775807, 'invalid_message_id')
                actual = db.execute('SELECT MAX(id) FROM messages WHERE conversation_id=? AND id<=?', (cid, mid)).fetchone()[0] or 0
                db.execute('UPDATE members SET read_id=MAX(read_id,?) WHERE conversation_id=? AND user_id=?', (actual, cid, uid))
                return {'ok': True}
            if action == 'block' and method == 'POST':
                require(type(body.get('blocked')) is bool, 'invalid_blocked')
                db.execute('UPDATE members SET blocked=? WHERE conversation_id=? AND user_id=?', (int(body['blocked']), cid, uid))
                return {'conversation': self.conversation(db, cid, uid)}
            raise APIError(405, 'method_not_allowed')

    def __call__(self, env, start_response):
        origin = env.get('HTTP_ORIGIN')
        headers = [('Content-Type', 'application/json; charset=utf-8'), ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'), ('Vary', 'Origin')]
        status = 200
        try:
            require(origin is None or origin in self.origins, 'origin_forbidden', 403)
            if origin:
                headers.append(('Access-Control-Allow-Origin', origin))
            if env['REQUEST_METHOD'] == 'OPTIONS':
                require(origin is not None, 'origin_required', 403)
                require(env.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD') in ('GET', 'POST'), 'method_not_allowed', 405)
                requested = {s.strip().lower() for s in env.get('HTTP_ACCESS_CONTROL_REQUEST_HEADERS', '').split(',') if s.strip()}
                require(requested <= {'authorization', 'content-type'}, 'headers_forbidden', 403)
                headers += [('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'), ('Access-Control-Allow-Headers', 'Authorization, Content-Type'), ('Access-Control-Max-Age', '600')]
                result = {'ok': True}
            else:
                length = env.get('CONTENT_LENGTH', '')
                require(not length or bool(re.fullmatch(r'[0-9]{1,9}', length)), 'invalid_content_length')
                length = int(length or 0)
                require(length <= 65536, 'request_too_large', 413)
                body = {}
                if env['REQUEST_METHOD'] == 'POST':
                    require(length > 0, 'body_required')
                    require(env.get('CONTENT_TYPE', '').split(';')[0].strip().lower() == 'application/json', 'unsupported_media_type', 415)
                    raw = env['wsgi.input'].read(length)
                    require(len(raw) == length, 'invalid_body')
                    body = json.loads(raw)
                    require(isinstance(body, dict), 'invalid_body')
                result = self.dispatch(env, body)
        except (APIError, PushError, admin.AdminError) as error:
            status, result = error.status, {'error': error.code}
        except (ValueError, UnicodeError, RecursionError):
            status, result = 400, {'error': 'invalid_request'}
        except sqlite3.OperationalError:
            status, result = 503, {'error': 'temporarily_unavailable'}
        except Exception:
            # Never expose/log bodies, credentials, tokens or SQL parameters.
            status, result = 500, {'error': 'internal_error'}
        if status == 429:
            headers.append(('Retry-After', '900'))
        if status == 200:
            self.push.wake()
        payload = json.dumps(result, separators=(',', ':')).encode()
        headers.append(('Content-Length', str(len(payload))))
        from http import HTTPStatus
        start_response(f'{status} {HTTPStatus(status).phrase}', headers)
        return [payload]


def create_app(db_path=None, origins=None, clock=time.time, push_sender=None):
    return Messenger(db_path, origins, clock, push_sender)
