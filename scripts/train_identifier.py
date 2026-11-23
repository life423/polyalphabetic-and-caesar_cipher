"""Train our own tiny neural network from generated examples; no pretrained models.

Run: python -m scripts.train_identifier
Training alone needs NumPy. Runtime inference has no added dependencies.
"""
import hashlib
import json
from pathlib import Path
import random
import re
from urllib.request import urlopen

import numpy as np

from src.ai.identifier import FEATURE_VERSION, LABELS, extract_features, letters_only
from src.core.ciphers import (AffineCipher, CaesarCipher, PolyalphabeticCipher,
                             RailFenceCipher, SubstitutionCipher, TranspositionCipher)


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.venv/training-corpus'
SOURCES = {
    'train': [(1342, 'Pride and Prejudice'), (1661, 'The Adventures of Sherlock Holmes'),
              (84, 'Frankenstein')],
    'validation': [(11, "Alice's Adventures in Wonderland")],
    'test': [(35, 'The Time Machine'), (74, 'The Adventures of Tom Sawyer')],
}
MIRRORS = {
    1342: ('Pride-and-Prejudice_1342', '1342-0.txt'),
    1661: ('The-Adventures-of-Sherlock-Holmes_1661', '1661.txt'),
    84: ('Frankenstein_84', '84-0.txt'),
    11: ('Alice-s-Adventures-in-Wonderland_11', '11-0.txt'),
    35: ('The-Time-Machine_35', '35-0.txt'),
    74: ('The-Adventures-of-Tom-Sawyer_74', '74-0.txt'),
}


def source_text(book_id):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f'{book_id}.txt'
    repo, filename = MIRRORS[book_id]
    url = f'https://raw.githubusercontent.com/GITenberg/{repo}/master/{filename}'
    if not path.exists():
        with urlopen(url, timeout=60) as response:
            path.write_bytes(response.read())
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    reference = ROOT / 'docs/IDENTIFIER_EVALUATION.json'
    if reference.exists():
        recorded = json.loads(reference.read_text(encoding='utf-8'))
        expected = {source['book_id']: source['sha256']
                    for split in recorded['splits'].values() for source in split['sources']}
        if book_id in expected and digest != expected[book_id]:
            raise ValueError(f'Book {book_id} differs from the recorded corpus. Review the source before retraining.')
    text = raw.decode('utf-8-sig')
    start = re.search(r'\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*', text)
    end = re.search(r'\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK', text)
    if not start or not end:
        raise ValueError(f'Cannot locate book content for {book_id}')
    # Keep headers, notes and license boilerplate out of generated examples.
    return letters_only(text[start.end():end.start()])[5000:-5000], {
        'url': url, 'sha256': digest, 'book_id': book_id,
    }


def encrypt_example(text, label, rng):
    if label == 'Caesar':
        return CaesarCipher.transform(text, rng.randrange(1, 26))
    if label == 'Affine':
        return AffineCipher.transform(text, (rng.choice((3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25)), rng.randrange(26)))
    if label == 'Vigenère':
        key = ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rng.randint(2, 16)))
        return PolyalphabeticCipher.transform(text, key)
    if label == 'Substitution':
        key = list('abcdefghijklmnopqrstuvwxyz')
        rng.shuffle(key)
        return SubstitutionCipher.transform(text, ''.join(key))
    if label == 'Rail Fence':
        return RailFenceCipher.transform(text, rng.randint(2, 20))
    key = list(range(rng.randint(2, 16)))
    rng.shuffle(key)
    return TranspositionCipher.transform(text, key)


def make_dataset(split, seed, passages):
    rng = random.Random(seed)
    x, y, lengths, sources = [], [], [], []
    for book_id, title in SOURCES[split]:
        text, provenance = source_text(book_id)
        sources.append(dict(provenance, title=title))
        starts = list(range(0, len(text) - 1500, 1500))
        rng.shuffle(starts)
        for start in starts[:passages]:
            length = rng.choice((100, 150, 250, 400, 700, 1200))
            plain = text[start:start + length]
            for label_index, label in enumerate(LABELS):
                encrypted = encrypt_example(plain, label, rng)
                x.append(extract_features(encrypted))
                y.append(label_index)
                lengths.append(length)
        print(f'{split}: {title}, {len(x)} examples so far', flush=True)
    return np.array(x), np.array(y), np.array(lengths), sources


def probabilities(x, parameters):
    w1, b1, w2, b2 = parameters
    hidden = np.tanh(x @ w1 + b1)
    logits = hidden @ w2 + b2
    exps = np.exp(logits - logits.max(axis=1, keepdims=True))
    return hidden, exps / exps.sum(axis=1, keepdims=True)


def evaluate(x, y, lengths, parameters):
    _, scores = probabilities(x, parameters)
    prediction = scores.argmax(axis=1)
    confusion = np.zeros((6, 6), dtype=int)
    np.add.at(confusion, (y, prediction), 1)
    return {
        'examples': len(y), 'top1_accuracy': float((prediction == y).mean()),
        'top3_accuracy': float((np.argsort(scores, axis=1)[:, -3:] == y[:, None]).any(axis=1).mean()),
        'confusion_matrix': confusion.tolist(),
        'by_length': {str(n): float((prediction[lengths == n] == y[lengths == n]).mean())
                      for n in sorted(set(lengths.tolist()))},
        'per_cipher': {label: float((prediction[y == i] == i).mean()) for i, label in enumerate(LABELS)},
    }


def train():
    datasets = {split: make_dataset(split, 423 + i, 350 if split == 'train' else 140)
                for i, split in enumerate(SOURCES)}
    x, y, _, _ = datasets['train']
    mean, scale = x.mean(axis=0), np.maximum(x.std(axis=0), 1e-6)
    standardized = {split: (values[0] - mean) / scale for split, values in datasets.items()}
    x = standardized['train']
    rng = np.random.default_rng(423)
    parameters = [rng.normal(0, .1, (x.shape[1], 48)), np.zeros(48),
                  rng.normal(0, .1, (48, 6)), np.zeros(6)]
    first = [np.zeros_like(p) for p in parameters]
    second = [np.zeros_like(p) for p in parameters]
    best_loss, best, step = float('inf'), None, 0
    for epoch in range(120):
        for batch in np.array_split(rng.permutation(len(y)), max(1, len(y) // 128)):
            step += 1
            xb, yb = x[batch], y[batch]
            hidden, delta = probabilities(xb, parameters)
            delta[np.arange(len(batch)), yb] -= 1
            delta /= len(batch)
            dh = (delta @ parameters[2].T) * (1 - hidden ** 2)
            gradients = [xb.T @ dh + .0001 * parameters[0], dh.sum(axis=0),
                         hidden.T @ delta + .0001 * parameters[2], delta.sum(axis=0)]
            for i, gradient in enumerate(gradients):
                first[i] = .9 * first[i] + .1 * gradient
                second[i] = .999 * second[i] + .001 * gradient ** 2
                parameters[i] -= .002 * (first[i] / (1 - .9 ** step)) / (np.sqrt(second[i] / (1 - .999 ** step)) + 1e-8)
        _, scores = probabilities(standardized['validation'], parameters)
        loss = -np.log(scores[np.arange(len(scores)), datasets['validation'][1]] + 1e-12).mean()
        if loss < best_loss:
            best_loss, best = loss, [p.copy() for p in parameters]
        if epoch % 20 == 0:
            print(f'epoch {epoch}: validation loss {loss:.4f}', flush=True)
    w1, b1, w2, b2 = best
    normalized_train = standardized['train']
    centroids = np.array([normalized_train[y == index].mean(axis=0) for index in range(len(LABELS))])
    test_x, test_y, _, _ = datasets['test']
    distances = ((((test_x - mean) / scale)[:, None] - centroids[None]) ** 2).sum(axis=2)
    baseline_accuracy = float((distances.argmin(axis=1) == test_y).mean())
    model = {'feature_version': FEATURE_VERSION, 'labels': LABELS,
             'mean': mean.tolist(), 'scale': scale.tolist(),
             'hidden_weights': w1.T.tolist(), 'hidden_bias': b1.tolist(),
             'output_weights': w2.T.tolist(), 'output_bias': b2.tolist()}
    report = {'seed': 423, 'labels': LABELS, 'features': x.shape[1], 'hidden_units': 48,
              'epochs': 120, 'selection': 'lowest validation cross-entropy; test never selects weights',
              'numpy_version': np.__version__,
              'baseline': {'method': 'nearest training-class centroid on the same standardized features',
                           'test_top1_accuracy': baseline_accuracy},
              'generation': {'letters_only': True, 'lengths': [100, 150, 250, 400, 700, 1200],
                             'vigenere_key_lengths': [2, 16], 'rails': [2, 20], 'columns': [2, 16],
                             'affine_excludes_caesar_multiplier': True,
                             'examples_per_plaintext_passage': 6},
              'splits': {split: {'sources': values[3], **evaluate(standardized[split], values[1], values[2], best)}
                         for split, values in datasets.items()}}
    content = json.dumps(model, separators=(',', ':'))
    report['model_sha256'] = hashlib.sha256(content.encode('utf-8')).hexdigest()
    (ROOT / 'src/ai/cipher_identifier.json').write_text(content, encoding='utf-8')
    (ROOT / 'docs/IDENTIFIER_EVALUATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['splits']['test'], indent=2))


if __name__ == '__main__':
    train()
