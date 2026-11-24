"""Account administration; privileges come only from server-owned numeric IDs."""
import re
from urllib.parse import parse_qs

SCHEMA = '''
CREATE TABLE IF NOT EXISTS account_status(user_id INTEGER PRIMARY KEY REFERENCES users(id), suspended INTEGER NOT NULL DEFAULT 0, created INTEGER, last_login INTEGER);
CREATE TABLE IF NOT EXISTS admin_audit(id INTEGER PRIMARY KEY, actor_id INTEGER NOT NULL, target_id INTEGER NOT NULL, action TEXT NOT NULL, reason TEXT NOT NULL, created INTEGER NOT NULL);
'''


class AdminError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code


def check(condition, code='invalid_request', status=400):
    if not condition:
        raise AdminError(status, code)


def admin_ids(raw):
    if not raw.strip():
        return frozenset()
    values = raw.split(',')
    if not all(re.fullmatch(r'[1-9][0-9]{0,17}', v.strip()) for v in values):
        raise ValueError('CIPHER_MESSENGER_ADMIN_IDS must contain positive numeric account IDs')
    return frozenset(int(v.strip()) for v in values)


def dispatch(app, db, env, body, uid, token_hash, now):
    check(uid in app.admin_ids, 'admin_required', 403)
    path, method = env.get('PATH_INFO', ''), env['REQUEST_METHOD']
    if path == '/api/admin/me' and method == 'GET':
        return {'id': uid, 'isAdmin': True}
    if path == '/api/admin/messages' and method == 'GET':
        app.limit('admin_read', str(uid), 120, 60)
        query = parse_qs(env.get('QUERY_STRING', ''), keep_blank_values=True, max_num_fields=3)
        check(set(query) <= {'page'} and all(len(v) == 1 for v in query.values()))
        page = query.get('page', ['1'])[0]
        check(bool(re.fullmatch(r'[1-9][0-9]{0,4}', page)))
        rows = db.execute('''SELECT m.id,m.created,s.username sender,r.username recipient
            FROM messages m JOIN users s ON s.id=m.sender_id JOIN conversations c ON c.id=m.conversation_id
            JOIN users r ON r.id=CASE WHEN c.low=m.sender_id THEN c.high ELSE c.low END
            ORDER BY m.id DESC LIMIT 25 OFFSET ?''', ((int(page)-1)*25,)).fetchall()
        return {'messages': [dict(r) for r in rows], 'total': db.execute('SELECT count(*) FROM messages').fetchone()[0], 'page': int(page), 'pageSize': 25}
    if path in ('/api/admin/messages/delete-all', '/api/admin/accounts/delete-others') or re.fullmatch(r'/api/admin/messages/[1-9][0-9]{0,17}/delete', path):
        return delete_records(app, db, env, body, uid, token_hash, now)
    if path == '/api/admin/accounts' and method == 'GET':
        app.limit('admin_read', str(uid), 120, 60)
        query = parse_qs(env.get('QUERY_STRING', ''), keep_blank_values=True, max_num_fields=5)
        check(set(query) <= {'q', 'page'})
        check(all(len(v) == 1 for v in query.values()))
        term, page = query.get('q', [''])[0], query.get('page', ['1'])[0]
        check(bool(re.fullmatch(r'[a-z0-9_]{0,24}', term)))
        check(bool(re.fullmatch(r'[1-9][0-9]{0,4}', page)))
        # instr treats underscores literally, unlike SQL LIKE patterns.
        where, params = 'instr(u.username,?)>0', (term,)
        total = db.execute('SELECT count(*) FROM users u WHERE ' + where, params).fetchone()[0]
        rows = db.execute('''SELECT u.id,u.username,COALESCE(s.suspended,0) suspended,s.created,s.last_login,
            (SELECT count(*) FROM sessions t WHERE t.user_id=u.id AND t.expires>?) sessions,
            (SELECT count(*) FROM push_devices d WHERE d.user_id=u.id AND d.expires>?) devices,
            (SELECT count(*) FROM conversations c WHERE c.low=u.id OR c.high=u.id) conversations,
            (SELECT count(*) FROM messages m WHERE m.sender_id=u.id) messages
            FROM users u LEFT JOIN account_status s ON s.user_id=u.id WHERE ''' + where +
            ' ORDER BY u.id LIMIT 25 OFFSET ?', (now, now, term, (int(page)-1)*25)).fetchall()
        summary = dict(db.execute('''SELECT (SELECT count(*) FROM users) accounts,
            (SELECT count(*) FROM account_status WHERE suspended=1) suspended,
            (SELECT count(*) FROM sessions WHERE expires>?) sessions,
            (SELECT count(*) FROM messages) messages''', (now,)).fetchone())
        return {'accounts': [dict(r, isAdmin=r['id'] in app.admin_ids) for r in rows],
                'total': total, 'page': int(page), 'pageSize': 25, 'summary': summary}
    if path == '/api/admin/audit' and method == 'GET':
        app.limit('admin_read', str(uid), 120, 60)
        rows = db.execute('''SELECT a.id,a.action,a.reason,a.created,actor.username actor,target.username target
            FROM admin_audit a JOIN users actor ON actor.id=a.actor_id JOIN users target ON target.id=a.target_id
            ORDER BY a.id DESC LIMIT 100''').fetchall()
        return {'events': [dict(r) for r in rows]}
    match = re.fullmatch(r'/api/admin/accounts/([1-9][0-9]{0,17})/(suspend|restore|revoke-sessions)', path)
    check(match is not None, 'not_found', 404)
    check(method == 'POST', 'method_not_allowed', 405)
    app.limit('admin_write', str(uid), 30, 60)
    target, action = int(match[1]), match[2]
    check(set(body) == {'username', 'reason'})
    reason = body.get('reason')
    check(isinstance(reason, str) and 3 <= len(reason.strip()) <= 240, 'reason_required')
    check(not any(ord(c) < 32 for c in reason), 'invalid_reason')
    check(target not in app.admin_ids, 'protected_admin', 409)
    db.execute('BEGIN IMMEDIATE')
    # Recheck authority/session inside the write transaction, after any concurrent revocation.
    check(db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND user_id=? AND expires>?',
                     (token_hash, uid, now)).fetchone() is not None, 'unauthorized', 401)
    account = db.execute('SELECT username FROM users WHERE id=?', (target,)).fetchone()
    check(account is not None, 'not_found', 404)
    check(body.get('username') == account['username'], 'confirmation_mismatch', 409)
    if action in ('suspend', 'restore'):
        db.execute('INSERT INTO account_status(user_id,suspended) VALUES(?,?) ON CONFLICT(user_id) DO UPDATE SET suspended=excluded.suspended',
                   (target, int(action == 'suspend')))
    if action != 'restore':
        db.execute('DELETE FROM push_devices WHERE user_id=?', (target,))
        db.execute('DELETE FROM sessions WHERE user_id=?', (target,))
    db.execute('INSERT INTO admin_audit(actor_id,target_id,action,reason,created) VALUES(?,?,?,?,?)',
               (uid, target, action, reason.strip(), now))
    return {'ok': True}


def delete_records(app, db, env, body, uid, token_hash, now):
    check(env['REQUEST_METHOD'] == 'POST', 'method_not_allowed', 405)
    app.limit('admin_delete', str(uid), 30, 60)
    check(set(body) == {'confirmation', 'reason'})
    reason = body.get('reason')
    check(isinstance(reason, str) and 3 <= len(reason.strip()) <= 240 and not any(ord(c) < 32 for c in reason), 'reason_required')
    path = env['PATH_INFO']
    db.execute('BEGIN IMMEDIATE')
    check(db.execute('SELECT 1 FROM sessions WHERE token_hash=? AND user_id=? AND expires>?', (token_hash, uid, now)).fetchone() is not None, 'unauthorized', 401)
    if path == '/api/admin/accounts/delete-others':
        owner = db.execute('SELECT username FROM users WHERE id=?', (uid,)).fetchone()[0]
        check(app.admin_ids == frozenset({uid}), 'protected_admin', 409)
        check(body['confirmation'] == 'KEEP ' + owner + ' DELETE OTHER ACCOUNTS', 'confirmation_mismatch', 409)
        counts = {'accounts': db.execute('SELECT count(*) FROM users WHERE id<>?', (uid,)).fetchone()[0],
                  'messages': db.execute('SELECT count(*) FROM messages').fetchone()[0]}
        db.execute('INSERT OR IGNORE INTO message_tombstones SELECT sender_id,client_id FROM messages WHERE sender_id=?', (uid,))
        db.execute('DELETE FROM push_outbox')
        db.execute('DELETE FROM messages')
        db.execute('DELETE FROM members')
        db.execute('DELETE FROM conversations')
        db.execute('DELETE FROM push_devices WHERE user_id<>?', (uid,))
        db.execute('DELETE FROM sessions WHERE user_id<>?', (uid,))
        db.execute('DELETE FROM account_status WHERE user_id<>?', (uid,))
        db.execute('DELETE FROM message_tombstones WHERE sender_id<>?', (uid,))
        db.execute('DELETE FROM admin_audit WHERE actor_id<>? OR target_id<>?', (uid, uid))
        db.execute('DELETE FROM users WHERE id<>?', (uid,))
        action = 'delete-other-accounts'
    elif path.endswith('/delete-all'):
        check(body['confirmation'] == 'DELETE ALL MESSAGES', 'confirmation_mismatch', 409)
        counts = {'messages': db.execute('SELECT count(*) FROM messages').fetchone()[0]}
        db.execute('INSERT OR IGNORE INTO message_tombstones SELECT sender_id,client_id FROM messages')
        db.execute('DELETE FROM push_outbox')
        db.execute('DELETE FROM messages')
        db.execute('UPDATE members SET read_id=0')
        action = 'delete-all-messages'
    else:
        mid = int(path.split('/')[-2])
        check(body['confirmation'] == str(mid), 'confirmation_mismatch', 409)
        check(db.execute('SELECT 1 FROM messages WHERE id=?', (mid,)).fetchone() is not None, 'not_found', 404)
        db.execute('INSERT OR IGNORE INTO message_tombstones SELECT sender_id,client_id FROM messages WHERE id=?', (mid,))
        db.execute('DELETE FROM push_outbox WHERE message_id=?', (mid,))
        db.execute('DELETE FROM messages WHERE id=?', (mid,))
        counts, action = {'messages': 1}, 'delete-message'
        reason = f'Message #{mid}: ' + reason
    # No message bodies or deleted account names are retained in the audit.
    db.execute('INSERT INTO admin_audit(actor_id,target_id,action,reason,created) VALUES(?,?,?,?,?)',
               (uid, uid, action, reason.strip(), now))
    return {'ok': True, 'deleted': counts}
