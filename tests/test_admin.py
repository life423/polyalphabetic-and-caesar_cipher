"""Admin authority, migration, suspension and privacy across real SQLite requests."""
import hashlib
from uuid import uuid4
import pytest
from src.messenger.app import create_app
from src.messenger.admin import admin_ids
from tests import test_messenger as helpers
from tests.test_messenger import KEY, BACKUP, ENVELOPE, SECRET


@pytest.fixture
def setup_admin(tmp_path, monkeypatch):
    monkeypatch.setenv('CIPHER_MESSENGER_ADMIN_IDS', '1')
    app = create_app(tmp_path / 'admin.sqlite', clock=lambda: 1000000000, push_sender=lambda *args: None)
    tokens = {}
    call = helpers.MessengerTests.call
    for name in ('owner', 'student', 'other_student'):
        code, data = call(app, 'POST', '/api/register', dict(username=name, password=SECRET, publicKey=KEY, keyBackup=BACKUP))
        assert code == 200
        tokens[name] = data['token']
    def request(method, path, body=None, who='owner'):
        return call(app, method, path, body, tokens.get(who))
    return app, tokens, request


def test_authority_is_server_only(setup_admin):
    app, tokens, call = setup_admin
    for path in ('/api/admin/me', '/api/admin/accounts', '/api/admin/audit'):
        assert call('GET', path, who='student')[0] == 403
        assert call('GET', path, who=None)[0] == 401
    assert call('GET', '/api/admin/me')[1] == {'id': 1, 'isAdmin': True}
    assert call('POST', '/api/admin/accounts/2/promote', {'isAdmin': True})[0] == 404
    app.admin_ids = frozenset()
    assert call('GET', '/api/admin/me')[0] == 403
    with pytest.raises(ValueError):
        admin_ids('1,not-an-id')


def test_directory_is_metadata_only_and_literal_search(setup_admin):
    _, _, call = setup_admin
    code, data = call('GET', '/api/admin/accounts?q=other_')
    assert code == 200 and data['total'] == 1
    assert data['accounts'][0]['username'] == 'other_student'
    assert set(data['accounts'][0]) == {'id', 'username', 'suspended', 'created', 'last_login', 'sessions', 'devices', 'conversations', 'messages', 'isAdmin'}
    assert data['summary']['accounts'] == 3
    for query in ('page=0', 'q=%25', 'page=2&page=3', 'q=x&q=y'):
        assert call('GET', '/api/admin/accounts?' + query)[0] == 400
    assert call('GET', '/api/admin/accounts?page=99')[1]['accounts'] == []
    with setup_admin[0].connect() as db:
        for i in range(26):
            db.execute('INSERT INTO users(username,salt,password_hash,public_key,key_backup) SELECT ?,salt,password_hash,public_key,key_backup FROM users WHERE id=2', ('page_' + str(i),))
    first = call('GET', '/api/admin/accounts?q=page_')[1]
    second = call('GET', '/api/admin/accounts?q=page_&page=2')[1]
    assert first['total'] == 26 and len(first['accounts']) == 25
    assert len(second['accounts']) == 1
    assert not ({a['id'] for a in first['accounts']} & {a['id'] for a in second['accounts']})


def test_suspend_revokes_login_sessions_push_and_blocks_sends(setup_admin):
    app, tokens, call = setup_admin
    cid = call('POST', '/api/conversations', {'username': 'student'})[1]['conversation']['id']
    app.push.register(2, hashlib.sha256(tokens['student'].encode()).hexdigest(),
                      {'installationId': str(uuid4()), 'token': 'a_valid_device_token_for_student'})
    assert call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE})[0] == 200
    assert call('POST', '/api/admin/accounts/2/suspend', {'username': 'student', 'reason': 'Abuse report review'})[0] == 200
    assert call('GET', '/api/me', who='student')[0] == 401
    assert helpers.MessengerTests.call(app, 'POST', '/api/login', {'username': 'student', 'password': SECRET}) == (403, {'error': 'account_suspended'})
    assert call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE}) == (403, {'error': 'account_unavailable'})
    with app.connect() as db:
        assert db.execute('SELECT count(*) FROM push_devices WHERE user_id=2').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM push_outbox').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM messages').fetchone()[0] == 1
    assert call('POST', '/api/admin/accounts/2/restore', {'username': 'student', 'reason': 'Review completed'})[0] == 200
    assert helpers.MessengerTests.call(app, 'POST', '/api/login', {'username': 'student', 'password': SECRET})[0] == 200
    assert call('GET', '/api/me', who='student')[0] == 401  # Old tokens stay revoked.
    events = call('GET', '/api/admin/audit')[1]['events']
    assert [e['action'] for e in events] == ['restore', 'suspend']
    assert events[0]['actor'] == 'owner' and events[0]['target'] == 'student'


def test_revocation_without_suspension_and_confirmation_guards(setup_admin):
    app, _, call = setup_admin
    for target, body, expected in (
        (1, {'username': 'owner', 'reason': 'Test self protection'}, 409),
        (2, {'username': 'other_student', 'reason': 'Wrong selection'}, 409),
        (2, {'username': 'student', 'reason': ''}, 400),
        (2, {'username': 'student', 'reason': 'x'*241}, 400),
        (2, {'username': 'student', 'reason': 'Review', 'isAdmin': True}, 400),
        (99, {'username': 'missing', 'reason': 'Review'}, 404),
    ):
        assert call('POST', f'/api/admin/accounts/{target}/suspend', body)[0] == expected
    assert call('POST', '/api/admin/accounts/2/revoke-sessions', {'username': 'student', 'reason': 'Lost device'})[0] == 200
    assert call('GET', '/api/me', who='student')[0] == 401
    assert helpers.MessengerTests.call(app, 'POST', '/api/login', {'username': 'student', 'password': SECRET})[0] == 200
    assert call('GET', '/api/admin/accounts')[1]['summary']['suspended'] == 0
    assert len(call('GET', '/api/admin/audit')[1]['events']) == 1


def test_existing_users_migrate_without_invented_dates(setup_admin, monkeypatch):
    app, _, call = setup_admin
    with app.connect() as db:
        db.execute('DELETE FROM account_status')
    restarted = create_app(app.path, clock=app.clock)
    assert helpers.MessengerTests.call(restarted, 'GET', '/api/admin/accounts', token=setup_admin[1]['owner'])[1]['accounts'][0]['created'] is None
    assert call('GET', '/api/me')[0] == 200


def test_message_deletion_is_private_confirmed_and_never_reuses_ids(setup_admin):
    app, tokens, call = setup_admin
    cid = call('POST', '/api/conversations', {'username': 'student'})[1]['conversation']['id']
    body = {'clientId': str(uuid4()), 'envelope': ENVELOPE}
    mid = call('POST', f'/api/conversations/{cid}/messages', body)[1]['message']['id']
    listing = call('GET', '/api/admin/messages')[1]
    assert listing['messages'] == [{'id': mid, 'created': 1000000000, 'sender': 'owner', 'recipient': 'student'}]
    delete = f'/api/admin/messages/{mid}/delete'
    assert call('GET', '/api/admin/messages', who='student')[0] == 403
    assert call('POST', delete, {'confirmation': str(mid), 'reason': 'Review'}, who='student')[0] == 403
    assert call('POST', delete, {'confirmation': 'wrong', 'reason': 'Review'})[0] == 409
    app.push.register(2, hashlib.sha256(tokens['student'].encode()).hexdigest(),
                      {'installationId': str(uuid4()), 'token': 'valid_device_token_for_deletion'})
    # The next pending message points at the one being deleted.
    with app.connect() as db:
        app.push.enqueue(db, cid, mid, 1)
    assert call('POST', delete, {'confirmation': str(mid), 'reason': 'Remove test message'})[1]['deleted'] == {'messages': 1}
    with app.connect() as db:
        assert db.execute('SELECT count(*) FROM push_outbox').fetchone()[0] == 0
    assert call('POST', f'/api/conversations/{cid}/messages', body) == (410, {'error': 'message_deleted'})
    assert call('POST', delete, {'confirmation': str(mid), 'reason': 'Already gone'})[0] == 404
    newer = call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE})[1]['message']['id']
    assert newer > mid
    assert call('GET', f'/api/conversations/{cid}/messages', who='student')[1]['messages'][0]['id'] == newer


def test_delete_all_preserves_accounts_and_new_unread_delivery(setup_admin):
    app, _, call = setup_admin
    cid = call('POST', '/api/conversations', {'username': 'student'})[1]['conversation']['id']
    body = {'clientId': str(uuid4()), 'envelope': ENVELOPE}
    old = call('POST', f'/api/conversations/{cid}/messages', body)[1]['message']['id']
    call('POST', f'/api/conversations/{cid}/read', {'messageId': old}, who='student')
    endpoint = '/api/admin/messages/delete-all'
    assert call('POST', endpoint, {'confirmation': '', 'reason': 'Review'})[0] == 409
    assert call('POST', endpoint, {'confirmation': 'DELETE ALL MESSAGES', 'reason': 'Remove test history'})[1]['deleted']['messages'] == 1
    assert call('GET', '/api/admin/messages')[1]['total'] == 0
    assert call('GET', '/api/admin/accounts')[1]['total'] == 3
    assert call('POST', f'/api/conversations/{cid}/messages', body)[0] == 410
    new = call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE})[1]['message']['id']
    assert new > old
    assert call('GET', '/api/conversations', who='student')[1]['conversations'][0]['unread'] == 1


def test_delete_other_accounts_keeps_owner_and_removes_related_records(setup_admin):
    app, _, call = setup_admin
    cid = call('POST', '/api/conversations', {'username': 'student'})[1]['conversation']['id']
    call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE})
    endpoint = '/api/admin/accounts/delete-others'
    assert call('POST', endpoint, {'confirmation': 'KEEP student DELETE OTHER ACCOUNTS', 'reason': 'Clean test accounts'})[0] == 409
    app.admin_ids = frozenset({1, 2})
    assert call('POST', endpoint, {'confirmation': 'KEEP owner DELETE OTHER ACCOUNTS', 'reason': 'Clean test accounts'})[0] == 409
    app.admin_ids = frozenset({1})
    result = call('POST', endpoint, {'confirmation': 'KEEP owner DELETE OTHER ACCOUNTS', 'reason': 'Clean test accounts'})
    assert result == (200, {'ok': True, 'deleted': {'accounts': 2, 'messages': 1}})
    assert call('GET', '/api/me')[1]['user']['username'] == 'owner'
    assert call('GET', '/api/me', who='student')[0] == 401
    assert call('GET', '/api/admin/accounts')[1]['total'] == 1
    with app.connect() as db:
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
        for table in ('messages', 'members', 'conversations', 'push_devices', 'push_outbox'):
            assert db.execute('SELECT count(*) FROM ' + table).fetchone()[0] == 0
    created = helpers.MessengerTests.call(app, 'POST', '/api/register', dict(username='fresh_student', password=SECRET, publicKey=KEY, keyBackup=BACKUP))
    assert created[1]['user']['id'] > 3
    newcid = call('POST', '/api/conversations', {'username': 'fresh_student'})[1]['conversation']['id']
    assert newcid > cid
