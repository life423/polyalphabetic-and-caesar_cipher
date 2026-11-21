"""Browser parity, upload safety, and meaningful cipher/analysis workflows."""
import pytest

from src.services.web_service import (
    MAX_ANALYSIS_LENGTH, MAX_TEXT_LENGTH, MAX_UPLOAD_BYTES,
    analyze_message, candidate_key, decode_upload, download_name, transform_message,
)


@pytest.mark.parametrize('cipher,key,plaintext,expected', [
    ('Caesar', 3, 'Hello café Ω!', 'Khoor fdié Ω!'),
    ('Vigenère', 'KEY', 'HELLO', 'RIJVS'),
    ('Substitution', 'zyxwvutsrqponmlkjihgfedcba', 'HELLO', 'SVOOL'),
    ('Columnar transposition', 'ZEBRAS', 'WEAREDISCOVEREDFLEEATONCE', 'EVLNXACDTXESEAXROFOXDEECXWIREE'),
    ('Rail Fence', 3, 'WEAREDISCOVEREDFLEEATONCE', 'WECRLTEERDSOEEFEAOCAIVDEN'),
    ('Affine', (5, 8), 'AFFINECIPHER', 'IHHWVCSWFRCP'),
])
def test_web_cipher_known_vectors(cipher, key, plaintext, expected):
    encrypted = transform_message(plaintext, cipher, 'Encrypt', key)
    assert encrypted == expected
    decrypted = transform_message(encrypted, cipher, 'Decrypt', key)
    assert decrypted == plaintext + ('XXXXX' if cipher == 'Columnar transposition' else '')


@pytest.mark.parametrize('cipher,key,expected', [
    ('Rail Fence', 3, 'HELLO\r\nWORLD\n\nLAST'),
    ('Columnar transposition', 'KEY', 'HELLOX\r\nWORLDX\n\nLASTXX'),
    ('Vigenère', 'LEMON', 'HELLO\r\nWORLD\n\nLAST'),
])
def test_upload_multiline_round_trip(cipher, key, expected):
    text = decode_upload(b'HELLO\r\nWORLD\n\nLAST')
    encrypted = transform_message(text, cipher, 'Encrypt', key, file_mode=True)
    assert transform_message(encrypted, cipher, 'Decrypt', key, file_mode=True) == expected


def test_upload_vigenere_resets_keyword_at_each_line():
    assert transform_message('ATTACK\nATTACK', 'Vigenère', 'Encrypt', 'LEMON', True) == 'LXFOPV\nLXFOPV'


def test_numeric_transposition_and_negative_affine_keys():
    for cipher, key in [('Columnar transposition', '2,0,1'), ('Affine', (-5, 8))]:
        text = 'HELLOWORLDXX'
        encrypted = transform_message(text, cipher, 'Encrypt', key)
        assert transform_message(encrypted, cipher, 'Decrypt', key) == text


@pytest.mark.parametrize('content', [b'\xff\xfe\x00', b''])
def test_upload_rejects_invalid_text(content):
    with pytest.raises(ValueError):
        decode_upload(content)


def test_upload_accepts_utf8_bom_without_changing_newlines():
    assert decode_upload(b'\xef\xbb\xbfHello\r\nWorld') == 'Hello\r\nWorld'


def test_public_resource_limits():
    with pytest.raises(ValueError, match='1 MB'):
        decode_upload(b'a' * (MAX_UPLOAD_BYTES + 1))
    with pytest.raises(ValueError, match='100,000'):
        transform_message('a' * (MAX_TEXT_LENGTH + 1), 'Caesar', 'Encrypt', 3)
    with pytest.raises(ValueError, match='5,000'):
        analyze_message('a' * (MAX_ANALYSIS_LENGTH + 1), 'Caesar')


@pytest.mark.parametrize('cipher,key', [
    ('Caesar', 26), ('Caesar', 'NaN'), ('Rail Fence', 101), ('Rail Fence', 1),
    ('Vigenère', ''), ('Vigenère', 'café'), ('Substitution', 'a' * 26),
    ('Columnar transposition', '2,2,0'), ('Columnar transposition', '0,a'), ('Affine', (2, 8)),
])
def test_invalid_keys_are_user_errors(cipher, key):
    with pytest.raises(ValueError):
        transform_message('Hello World', cipher, 'Encrypt', key)


def test_analysis_to_full_decryption_preserves_unicode():
    text = 'The important information about the café is something we should understand together.'
    encrypted = transform_message(text, 'Caesar', 'Encrypt', 7)
    candidates = analyze_message(encrypted, 'Caesar')
    key = candidate_key('Caesar', candidates[0])
    assert key == 7
    assert transform_message(encrypted, 'Caesar', 'Decrypt', key) == text


def test_multiline_analysis_uses_independent_cipher_line():
    plain = 'When in the Course of human events it becomes necessary for one people to dissolve the political bands.'
    encrypted = transform_message(plain + '\nHI', 'Rail Fence', 'Encrypt', 4, True)
    candidates = analyze_message(encrypted, 'Rail Fence', True)
    assert candidate_key('Rail Fence', candidates[0]) == 4


@pytest.mark.parametrize('cipher,text', [('Vigenère', 'ABC'), ('Caesar', '123!'), ('Substitution', 'ABC')])
def test_unusable_analysis_is_explained(cipher, text):
    with pytest.raises(ValueError):
        analyze_message(text, cipher)


def test_download_name_is_a_safe_text_filename():
    assert download_name('../../private/story.txt', 'Encrypt') == 'story_encrypted.txt'
    assert download_name('C:\\private\\story.txt', 'Decrypt') == 'story_decrypted.txt'

