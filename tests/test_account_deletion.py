"""Self-deletion uses synthetic identities; never calls a hosted database."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from src.messenger.app import create_app
from tests.test_messenger import KEY, BACKUP, ENVELOPE, SECRET
from tests import test_messenger as helpers


@pytest.fixture
def accounts(tmp_path, monkeypatch):
    monkeypatch.setenv('CIPHER_MESSENGER_ADMIN_IDS', '1')
    app = create_app(tmp_path/'deletion.sqlite', push_sender=lambda *args: None)
    tokens = {}
    def call(method, path, body=None, who=None, **extra):
        return helpers.MessengerTests.call(app, method, path, body, tokens.get(who), **extra)
    for name in ('protected_owner', 'disposable_user', 'remaining_peer'):
        code, data = call('POST', '/api/register', dict(username=name, password=SECRET, publicKey=KEY, keyBackup=BACKUP))
        assert code == 200
        tokens[name] = data['token']
    return app, tokens, call


def deletion(name='disposable_user', **changes):
    return dict(username=name, password=SECRET, confirmation=name, **changes)


def test_admin_protected_and_invalid_confirmation_cannot_delete(accounts):
    app, _, call = accounts
    assert call('GET', '/api/account/deletion-status', who='protected_owner') == (200, {'allowed': False})
    assert call('GET', '/api/account/deletion-status', who='disposable_user') == (200, {'allowed': True})
    assert call('POST', '/api/account/delete', deletion('protected_owner')) == (409, {'error': 'protected_admin'})
    for body, code in (
        ({**deletion(), 'password': 'wrong-but-long-password'}, 401),
        ({**deletion(), 'confirmation': 'remaining_peer'}, 409),
        ({**deletion(), 'targetId': 1}, 400),
        ({'username': 'disposable_user', 'confirmation': 'disposable_user'}, 400),
        (deletion('missing_user'), 401),
    ):
        assert call('POST', '/api/account/delete', body)[0] == code
    assert call('POST', '/api/account/delete', deletion(), HTTP_ORIGIN='https://untrusted.example')[0] == 403
    assert call('GET', '/api/admin/accounts', who='protected_owner')[1]['total'] == 3
    assert call('GET', '/api/me', who='protected_owner')[0] == 200


def test_deletes_both_sides_of_own_history_without_touching_other_accounts(accounts):
    app, tokens, call = accounts
    def conversation(who, peer):
        return call('POST', '/api/conversations', {'username': peer}, who)[1]['conversation']['id']
    def send(cid, who):
        return call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE}, who)[1]['message']['id']
    def device(who, uid):
        app.push.register(uid, hashlib.sha256(tokens[who].encode()).hexdigest(),
                          {'installationId': str(uuid4()), 'token': 'fictional_push_token_' + str(uuid4())})
    device('disposable_user', 2)
    device('remaining_peer', 3)
    own = conversation('disposable_user', 'remaining_peer')
    other = conversation('protected_owner', 'remaining_peer')
    send(own, 'disposable_user')
    send(own, 'remaining_peer')
    surviving = send(other, 'protected_owner')
    extra_token = call('POST', '/api/login', {'username': 'disposable_user', 'password': SECRET})[1]['token']
    with app.connect() as db:
        db.execute('INSERT INTO message_tombstones VALUES(?,?)', (2, str(uuid4())))
        db.execute('INSERT INTO admin_audit(actor_id,target_id,action,reason,created) VALUES(1,2,?,?,?)', ('restore', 'Synthetic deletion fixture', 1))
    assert call('POST', '/api/account/delete', deletion(), HTTP_ORIGIN='http://localhost:8502') == (200, {'deleted': True})
    with app.connect() as db:
        assert not db.execute('SELECT 1 FROM rate_limits WHERE subject=?', (hashlib.sha256(b'disposable_user').hexdigest(),)).fetchone()
    assert call('GET', '/api/me', who='disposable_user')[0] == 401
    assert helpers.MessengerTests.call(app, 'GET', '/api/me', token=extra_token)[0] == 401
    assert call('POST', '/api/login', {'username': 'disposable_user', 'password': SECRET})[0] == 401
    assert call('GET', '/api/me', who='protected_owner')[0] == 200
    assert call('GET', '/api/me', who='remaining_peer')[0] == 200
    assert call('GET', '/api/conversations', who='remaining_peer')[1]['conversations'][0]['id'] == other
    with app.connect() as db:
        assert [r[0] for r in db.execute('SELECT id FROM users ORDER BY id')] == [1, 3]
        assert [r[0] for r in db.execute('SELECT id FROM messages')] == [surviving]
        assert db.execute('SELECT count(*) FROM push_devices WHERE user_id=3').fetchone()[0] == 1
        for table, where in [('account_status', 'user_id=2'), ('sessions', 'user_id=2'), ('push_devices', 'user_id=2'),
                             ('message_tombstones', 'sender_id=2'), ('admin_audit', 'target_id=2 OR actor_id=2')]:
            assert db.execute('SELECT count(*) FROM ' + table + ' WHERE ' + where).fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM push_outbox WHERE conversation_id=?', (own,)).fetchone()[0] == 0
        assert not db.execute('PRAGMA foreign_key_check').fetchall()
    # A reclaimed username creates a new identity, with no access to removed history.
    recreated = call('POST', '/api/register', dict(username='disposable_user', password=SECRET, publicKey=KEY, keyBackup=BACKUP))[1]
    assert recreated['user']['id'] > 3
    assert helpers.MessengerTests.call(app, 'GET', '/api/conversations', token=recreated['token'])[1]['conversations'] == []


def test_suspended_account_can_still_delete_without_a_login_session(accounts):
    _, _, call = accounts
    assert call('POST', '/api/admin/accounts/2/suspend', {'username': 'disposable_user', 'reason': 'Synthetic fixture'}, 'protected_owner')[0] == 200
    assert call('POST', '/api/login', {'username': 'disposable_user', 'password': SECRET})[0] == 403
    assert call('POST', '/api/account/delete', deletion())[0] == 200
    assert call('GET', '/api/me', who='protected_owner')[0] == 200


def test_deletion_transaction_rolls_back_on_failure(accounts):
    app, _, call = accounts
    cid = call('POST', '/api/conversations', {'username': 'remaining_peer'}, 'disposable_user')[1]['conversation']['id']
    call('POST', f'/api/conversations/{cid}/messages', {'clientId': str(uuid4()), 'envelope': ENVELOPE}, 'disposable_user')
    with app.connect() as db:
        db.execute("CREATE TRIGGER deny_fixture_delete BEFORE DELETE ON users WHEN OLD.id=2 BEGIN SELECT RAISE(ABORT,'fixture failure'); END")
    assert call('POST', '/api/account/delete', deletion()) == (500, {'error': 'internal_error'})
    assert call('GET', '/api/me', who='disposable_user')[0] == 200
    assert len(call('GET', f'/api/conversations/{cid}/messages', who='remaining_peer')[1]['messages']) == 1
    assert call('GET', '/api/me', who='protected_owner')[0] == 200


def test_concurrent_deletion_is_atomic_and_does_not_delete_admin(accounts):
    app, _, call = accounts
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: call('POST', '/api/account/delete', deletion()), range(2)))
    assert sorted(code for code, _ in results) == [200, 401]
    assert call('GET', '/api/me', who='protected_owner')[0] == 200
    with app.connect() as db:
        assert db.execute('SELECT count(*) FROM users').fetchone()[0] == 2
