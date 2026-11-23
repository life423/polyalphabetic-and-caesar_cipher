"""Our locally trained next-character neural language model, with fast table inference."""
from array import array
import base64
from functools import lru_cache
import json
import math
from pathlib import Path
import random
import sys
import zlib


ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
CONTEXT = 3
TABLE_SIZE = 26 ** (CONTEXT + 1)
SCALE = 1000


def encode_letters(text):
    return [ord(c.lower()) - 97 for c in text if c.isascii() and c.isalpha()]


@lru_cache(maxsize=1)
def load_language_model():
    data = json.loads(Path(__file__).with_name('english_language_model.json').read_text(encoding='utf-8'))
    if (data['format_version'] != 1 or data['context'] != CONTEXT
            or data['alphabet'] != ALPHABET or data['cost_scale'] != SCALE):
        raise ValueError('The English language model needs rebuilding.')
    costs = array('H')
    costs.frombytes(zlib.decompress(base64.b64decode(data['cost_table'])))
    if sys.byteorder != 'little':
        costs.byteswap()
    if len(costs) != TABLE_SIZE or costs.itemsize != 2:
        raise ValueError('The English language model table is invalid.')
    return costs, data['unigram_costs']


def language_score(text):
    """Mean next-letter negative log likelihood in nats; lower is more English-like.

    All possible three-letter contexts are compiled from the trained neural
    network. Table entries are quantized to .001 nats, avoiding thousands of
    repeated matrix multiplications during key search. No user text is cached.
    """
    letters = encode_letters(text)
    if not letters:
        return float('inf')
    costs, unigrams = load_language_model()
    if len(letters) <= CONTEXT:
        return sum(unigrams[index] for index in letters) / len(letters)
    state = letters[0] * 676 + letters[1] * 26 + letters[2]
    total = 0
    for letter in letters[CONTEXT:]:
        index = state * 26 + letter
        total += costs[index]
        state = index % 17576
    return total / (SCALE * (len(letters) - CONTEXT))


def generate_letters(prompt='the', length=120, seed=423):
    """Diagnostic sampling, not a chatbot: produce an unspaced letter sequence."""
    letters = encode_letters(prompt)
    if len(letters) < CONTEXT:
        raise ValueError('Provide a prompt with at least three English letters.')
    if not 0 <= length <= 1000:
        raise ValueError('Generate between 0 and 1,000 letters.')
    costs, _ = load_language_model()
    rng = random.Random(seed)
    for _ in range(length):
        state = letters[-3] * 676 + letters[-2] * 26 + letters[-1]
        weights = [math.exp(-cost / SCALE) for cost in costs[state * 26:(state + 1) * 26]]
        letters.append(rng.choices(range(26), weights=weights)[0])
    return ''.join(ALPHABET[index] for index in letters)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Sample our small, unspaced next-letter language model.')
    parser.add_argument('--prompt', default='the')
    parser.add_argument('--length', type=int, default=120)
    args = parser.parse_args()
    print(generate_letters(args.prompt, args.length))
