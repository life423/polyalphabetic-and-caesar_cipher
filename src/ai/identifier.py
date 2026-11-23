"""Small trained cipher classifier. Inference uses only the Python standard library."""
from collections import Counter
from functools import lru_cache
import json
import math
from pathlib import Path

from src.ai.analyzer import CipherAnalyzer


LABELS = ('Caesar', 'Vigenère', 'Substitution', 'Columnar transposition', 'Rail Fence', 'Affine')
FEATURE_VERSION = 1
MIN_LETTERS = 100
MAX_CHARACTERS = 5000
FREQUENCIES = [CipherAnalyzer.ENGLISH_FREQ_MAP[c] for c in 'abcdefghijklmnopqrstuvwxyz']
FREQUENCIES = [value / sum(FREQUENCIES) for value in FREQUENCIES]
BIGRAMS = tuple(CipherAnalyzer.ENGLISH_BIGRAMS)


def letters_only(text):
    return ''.join(c.lower() for c in text if c.isascii() and c.isalpha())


def extract_features(text):
    """Ignore formatting so whitespace/case cannot leak the generator's label."""
    text = letters_only(text)
    n = len(text)
    if n < 2:
        raise ValueError('At least two English letters are needed for features.')
    counts = Counter(text)
    freq = [counts[chr(97 + i)] / n for i in range(26)]
    ic = sum(count * (count - 1) for count in counts.values()) / (n * (n - 1))
    entropy = -sum(p * math.log(p) for p in freq if p)

    def distance(order):
        return sum((freq[index] - expected) ** 2 / expected
                   for index, expected in zip(order, FREQUENCIES))

    shift_fit = min(distance([(i + shift) % 26 for i in range(26)]) for shift in range(26))
    affine_fit = min(distance([(a * i + b) % 26 for i in range(26)])
                     for a in (3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25) for b in range(26))
    features = freq + sorted(freq, reverse=True) + [ic, entropy, distance(range(26)), shift_fit, affine_fit]
    features += [sum(a == b for a, b in zip(text, text[lag:])) / max(1, n - lag)
                 for lag in range(1, 33)]
    # Repeated-key ciphers restore the coincidence rate inside their key columns.
    for period in range(2, 21):
        numerator = denominator = 0
        for offset in range(period):
            column = text[offset::period]
            numerator += sum(v * (v - 1) for v in Counter(column).values())
            denominator += len(column) * (len(column) - 1)
        features.append(numerator / max(1, denominator))
    pairs = Counter(text[i:i + 2] for i in range(n - 1))
    features += [pairs[pair] / (n - 1) for pair in BIGRAMS]
    return features


@lru_cache(maxsize=1)
def load_model():
    model = json.loads(Path(__file__).with_name('cipher_identifier.json').read_text(encoding='utf-8'))
    if model['feature_version'] != FEATURE_VERSION or tuple(model['labels']) != LABELS:
        raise ValueError('The cipher identification model needs rebuilding.')
    return model


def predict_scores(features, model):
    normalized = [(x - mean) / scale for x, mean, scale in
                  zip(features, model['mean'], model['scale'])]
    hidden = [math.tanh(sum(x * w for x, w in zip(normalized, weights)) + bias)
              for weights, bias in zip(model['hidden_weights'], model['hidden_bias'])]
    logits = [sum(x * w for x, w in zip(hidden, weights)) + bias
              for weights, bias in zip(model['output_weights'], model['output_bias'])]
    exp = [math.exp(value - max(logits)) for value in logits]
    return [value / sum(exp) for value in exp]


def identify_cipher(text):
    """Return a ranked shortlist, not calibrated probabilities or a key recovery."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError('Enter ciphertext or upload a text file first.')
    if len(text) > MAX_CHARACTERS:
        raise ValueError('Identify up to 5,000 characters at a time. Use a shorter sample.')
    if len(letters_only(text)) < MIN_LETTERS:
        raise ValueError('Cipher identification needs at least 100 English letters. Longer samples work better.')
    scores = predict_scores(extract_features(text), load_model())
    ranked = sorted(zip(LABELS, scores), key=lambda item: item[1], reverse=True)
    return [{'cipher': label} for label, _ in ranked[:3]]
