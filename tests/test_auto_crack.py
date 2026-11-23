"""Unknown-cipher recovery must not depend on UI-selected cipher or key values."""
import pytest

from src.services.web_service import crack_message, transform_message


PLAIN = (
    'The old observatory stood above the quiet valley, where a single lantern burned beside the northern window. '
    'At midnight, the caretaker discovered a folded note beneath the telescope. '
    'It described a hidden room behind the library and a wooden box containing the missing expedition records. '
    'The final instruction was simple: bring the brass compass and wait until the morning bells begin to ring.'
)


@pytest.mark.parametrize('cipher,key', [('Caesar', 7), ('Vigenère', 'ORBIT'),
                                      ('Affine', (5, 8)), ('Rail Fence', 3)])
def test_automatic_recovery_finds_cipher_key_and_full_message(cipher, key):
    result = crack_message(transform_message(PLAIN, cipher, 'Encrypt', key))
    assert result['status'] == 'suggested'
    assert result['candidates'][0]['cipher'] == cipher
    assert result['plaintext'] == (''.join(PLAIN.split()) if cipher == 'Rail Fence' else PLAIN)
    assert len(result['candidates']) <= 3


def test_search_recovers_even_when_identifier_prefers_wrong_cipher(monkeypatch):
    monkeypatch.setattr('src.services.web_service.identify_message',
                        lambda *args: [{'cipher': 'Substitution'}, {'cipher': 'Caesar'}, {'cipher': 'Affine'}])
    result = crack_message(transform_message(PLAIN, 'Vigenère', 'Encrypt', 'ORBIT'))
    assert result['status'] == 'suggested'
    assert result['candidates'][0]['key'] == 'orbit'
    assert result['plaintext'] == PLAIN


@pytest.mark.parametrize('cipher,key', [('Substitution', 'QWERTYUIOPASDFGHJKLZXCVBNM'),
                                      ('Columnar transposition', 'ZEBRAS')])
def test_unsupported_ciphers_do_not_return_gibberish_as_recovered_plaintext(cipher, key):
    result = crack_message(transform_message(PLAIN, cipher, 'Encrypt', key))
    assert result['status'] == 'unsupported'
    assert result['plaintext'] is None


def test_automatic_file_recovery_preserves_independent_lines_and_exact_separators():
    original = PLAIN + '\r\nSecond line.\n\r\nFinal line.\r'
    encrypted = transform_message(original, 'Vigenère', 'Encrypt', 'ORBIT', True)
    result = crack_message(encrypted, True)
    assert result['status'] == 'suggested'
    assert result['plaintext'] == original


@pytest.mark.parametrize('text', ['', 'short text', 'A' * 5001, '日本語' * 100])
def test_unusable_samples_are_rejected(text):
    with pytest.raises(ValueError):
        crack_message(text)
