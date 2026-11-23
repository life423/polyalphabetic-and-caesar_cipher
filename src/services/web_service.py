"""Browser operations over the shared cipher engine; uploaded files stay in memory."""
from hashlib import sha256
from io import StringIO
from pathlib import PurePosixPath
import re

from src.services.cipher_service import CipherService
from src.services.file_service import FileService


CIPHERS = {
    'Caesar': 'caesar',
    'Vigenère': 'polyalphabetic',
    'Substitution': 'substitution',
    'Columnar transposition': 'transposition',
    'Rail Fence': 'rail_fence',
    'Affine': 'affine',
}
ANALYZABLE = {'Caesar', 'Vigenère', 'Rail Fence', 'Affine'}
MAX_TEXT_LENGTH = 100_000
MAX_ANALYSIS_LENGTH = 5_000
MAX_UPLOAD_BYTES = 1_048_576


def validate_text(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Enter a message or upload a text file first.')
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError('Messages can contain up to 100,000 characters.')


def decode_upload(content):
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError('Choose a text file smaller than 1 MB.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValueError('This file is not UTF-8 text. Save it as a UTF-8 .txt file and try again.') from exc
    validate_text(text)
    return text


def parse_key(cipher, value):
    """Parse browser fields once, using the core ciphers for algorithm validation."""
    if cipher not in CIPHERS:
        raise ValueError('Choose a supported cipher.')
    if cipher in ('Caesar', 'Rail Fence'):
        try:
            number = int(value)
        except (ValueError, TypeError) as exc:
            raise ValueError('Enter a whole number for the key.') from exc
        if cipher == 'Caesar' and not 0 <= number <= 25:
            raise ValueError('Choose a shift between 0 and 25.')
        if cipher == 'Rail Fence' and not 2 <= number <= 100:
            raise ValueError('Choose between 2 and 100 rails.')
        return number
    if cipher == 'Affine':
        try:
            a, b = value
            return int(a), int(b)
        except (ValueError, TypeError) as exc:
            raise ValueError('Enter whole numbers for both Affine key values.') from exc
    if not isinstance(value, str) or not value:
        raise ValueError('Enter a keyword.' if cipher == 'Vigenère' else 'Enter a key.')
    if cipher == 'Columnar transposition' and ',' in value:
        try:
            return [int(part.strip()) for part in value.split(',')]
        except ValueError as exc:
            raise ValueError('Use a keyword or comma-separated column numbers, such as 2,0,1.') from exc
    return value


def transform_message(text, cipher, operation, key, file_mode=False):
    validate_text(text)
    if operation not in ('Encrypt', 'Decrypt'):
        raise ValueError('Choose Encrypt or Decrypt.')
    parsed = parse_key(cipher, key)
    service = CipherService()
    transform = getattr(service, f'{operation.lower()}_{CIPHERS[cipher]}')
    if file_mode:
        return ''.join(FileService.transform_lines(StringIO(text, newline=''), lambda line: transform(line, parsed)))
    return transform(text, parsed)


def analyze_message(text, cipher, file_mode=False):
    validate_text(text)
    if cipher not in ANALYZABLE:
        raise ValueError('Key analysis supports Caesar, Vigenère, Rail Fence, and Affine.')
    if file_mode and cipher in ('Vigenère', 'Rail Fence'):
        text = max(
            StringIO(text, newline=''),
            key=lambda line: sum(char.isascii() and char.isalpha() for char in line),
            default='',
        ).rstrip('\r\n')
    if len(text) > MAX_ANALYSIS_LENGTH:
        raise ValueError('Analyze up to 5,000 characters at a time. Use a shorter ciphertext sample.')
    letters = sum(char.isascii() and char.isalpha() for char in text)
    if not letters:
        raise ValueError('Key analysis needs ciphertext containing English letters.')
    if cipher == 'Vigenère' and letters < 20:
        raise ValueError('Vigenère analysis needs at least 20 English letters. Longer messages work better.')
    from src.ai.neural_analyzer import NeuralCipherAnalyzer

    return getattr(NeuralCipherAnalyzer, f'analyze_{CIPHERS[cipher]}')(text)


def identify_message(text, file_mode=False):
    """Identify an unknown cipher without needing a selected cipher or key."""
    from src.ai.identifier import identify_cipher

    validate_text(text)
    if file_mode:
        text = max(StringIO(text, newline=''),
                   key=lambda line: sum(char.isascii() and char.isalpha() for char in line),
                   default='').rstrip('\r\n')
    return identify_cipher(text)


def candidate_key(cipher, candidate):
    if cipher == 'Caesar':
        return candidate['shift']
    if cipher == 'Vigenère':
        return candidate['keyword']
    if cipher == 'Rail Fence':
        return candidate['rails']
    if cipher == 'Affine':
        return candidate['a'], candidate['b']
    raise ValueError('This cipher does not support key suggestions.')


def describe_key(cipher, key):
    if cipher == 'Caesar':
        return f'Shift {key}'
    if cipher == 'Rail Fence':
        return f'{key} rails'
    if cipher == 'Affine':
        return f'a = {key[0]}, b = {key[1]}'
    return f'Keyword: {key}'


def context_id(text, cipher, file_mode, operation='', key=''):
    """Identify which inputs a result belongs to without storing text in a cache."""
    return sha256(repr((text, cipher, file_mode, operation, key)).encode('utf-8')).hexdigest()


def download_name(filename, operation):
    name = PurePosixPath((filename or 'message.txt').replace('\\', '/')).stem
    name = re.sub(r'[^\w.-]', '_', name)[:80] or 'message'
    return f'{name}_{operation.lower()}ed.txt'
