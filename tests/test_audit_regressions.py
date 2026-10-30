"""Regression coverage for data loss and analyzer/core inconsistencies."""
import os

import pytest

from src.ai.analyzer import CipherAnalyzer
from src.core.ciphers import AffineCipher, CaesarCipher, PolyalphabeticCipher
from src.services.cipher_service import CipherService
from src.services.file_service import FileService


def test_failed_output_never_deletes_source_named_successfully(tmp_path):
    source = tmp_path / 'Successfully.txt'
    source.write_text('keep this', encoding='utf-8')
    output = tmp_path / 'missing' / 'cipher.txt'
    result = CipherService().process_file_with_cipher(
        source, output, lambda text: CaesarCipher.transform(text, 3), delete_input=True,
    )
    assert result.startswith('Error:')
    assert source.read_text(encoding='utf-8') == 'keep this'
    assert not output.exists()


def test_hard_link_output_cannot_overwrite_source(tmp_path):
    source = tmp_path / 'source.txt'
    output = tmp_path / 'alias.txt'
    source.write_text('keep this', encoding='utf-8')
    try:
        os.link(source, output)
    except OSError as exc:
        pytest.skip(f'Hard links unavailable: {exc}')
    result = FileService.process_file(source, output, str.upper)
    assert result.startswith('Error:')
    assert source.read_text(encoding='utf-8') == 'keep this'


@pytest.mark.parametrize('algorithm,key,expected', [
    ('rail_fence', 3, b'HELLO\r\nWORLD\n\nLAST'),
    ('transposition', 'KEY', b'HELLOX\r\nWORLDX\n\nLASTXX'),
])
def test_multiline_transposition_file_round_trip(tmp_path, algorithm, key, expected):
    source, encrypted, decrypted = (tmp_path / name for name in ('source', 'cipher', 'plain'))
    source.write_bytes(b'HELLO\r\nWORLD\n\nLAST')
    service = CipherService()
    encrypt = getattr(service, f'encrypt_{algorithm}')
    decrypt = getattr(service, f'decrypt_{algorithm}')
    assert service.process_file_with_cipher(
        source, encrypted, lambda line: encrypt(line, key),
    ).startswith('Successfully')
    assert service.process_file_with_cipher(
        encrypted, decrypted, lambda line: decrypt(line, key),
    ).startswith('Successfully')
    assert decrypted.read_bytes() == expected


def test_partial_transform_error_preserves_existing_output_and_source(tmp_path):
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.write_text('first\nsecond\n', encoding='utf-8')
    output.write_text('previous output', encoding='utf-8')

    def transform(line):
        if line == 'second':
            raise ValueError('invalid key')
        return line.upper()

    result = CipherService().process_file_with_cipher(source, output, transform, True)
    assert result.startswith('Error:')
    assert source.read_text(encoding='utf-8') == 'first\nsecond\n'
    assert output.read_text(encoding='utf-8') == 'previous output'
    assert not list(tmp_path.glob('.ciphercraft-*'))


@pytest.mark.parametrize('failure', ['fsync', 'replace'])
def test_failed_publish_preserves_output_and_source(tmp_path, monkeypatch, failure):
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.write_text('source data', encoding='utf-8')
    output.write_text('previous output', encoding='utf-8')

    def fail_replace(*_):
        raise OSError('disk error')

    monkeypatch.setattr(f'src.services.file_service.os.{failure}', fail_replace)
    result = CipherService().process_file_with_cipher(source, output, str.upper, True)
    assert result.startswith('Error:')
    assert source.read_text(encoding='utf-8') == 'source data'
    assert output.read_text(encoding='utf-8') == 'previous output'
    assert not list(tmp_path.glob('.ciphercraft-*'))


def test_failed_source_deletion_is_reported(tmp_path, monkeypatch):
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.write_text('source data', encoding='utf-8')
    monkeypatch.setattr(FileService, 'delete_file_after_processing', staticmethod(lambda _: False))
    result = CipherService().process_file_with_cipher(source, output, str.upper, True)
    assert 'Warning:' in result
    assert source.exists()
    assert output.read_text(encoding='utf-8') == 'SOURCE DATA'


@pytest.mark.parametrize('cipher,key,decrypt', [
    (CaesarCipher, 3, CipherAnalyzer._decrypt_caesar),
    (PolyalphabeticCipher, 'KEY', CipherAnalyzer._decrypt_polyalphabetic),
])
def test_analyzer_decryption_preserves_unicode_and_keyword_alignment(cipher, key, decrypt):
    plaintext = 'Hello café Ω! This is the important information people need.'
    ciphertext = cipher.transform(plaintext, key)
    assert decrypt(ciphertext, key) == plaintext


def test_caesar_analysis_sample_matches_core_decryption_with_unicode():
    plaintext = 'This café has the important information people need to understand.'
    ciphertext = CaesarCipher.transform(plaintext, 3)
    for result in CipherAnalyzer.analyze_caesar(ciphertext):
        assert result['sample'] == CaesarCipher.transform(ciphertext, result['shift'], False)


@pytest.mark.parametrize('text', ['', 'ABC', '1234 !?', 'éΩ'])
def test_short_vigenere_has_no_invalid_candidates(text):
    assert CipherAnalyzer.analyze_polyalphabetic(text) == []


def test_known_plaintext_can_recover_zero_shift():
    result = CipherAnalyzer.analyze_with_known_plaintext('HELLO WORLD', 'HELLO')
    assert result == {'success': True, 'key': 0, 'decrypted': 'HELLO WORLD'}


@pytest.mark.parametrize('ciphertext,known', [('KHOOR', '!!!'), ('!!!', 'HELLO'), ('é', 'Ω')])
def test_known_plaintext_rejects_inputs_without_ascii_letters(ciphertext, known):
    assert not CipherAnalyzer.analyze_with_known_plaintext(ciphertext, known)['success']


@pytest.mark.parametrize('key', [(-5, 8), (-31, -18), (31, 34)])
def test_affine_normalizes_negative_and_large_keys(key):
    plaintext = 'Hello café Ω!'
    assert AffineCipher.transform(AffineCipher.transform(plaintext, key), key, False) == plaintext


def test_rail_analysis_rejects_nonletter_input():
    assert CipherAnalyzer.analyze_rail_fence('123456 !?') == []
