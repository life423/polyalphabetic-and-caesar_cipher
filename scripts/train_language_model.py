"""Train a next-character neural LM from scratch on this machine (NumPy only).

Run with: python -m scripts.train_language_model
No pretrained weights, model APIs, GPU, or paid services are involved.
"""
from array import array
import base64
import hashlib
import json
from pathlib import Path
import sys
import zlib

import numpy as np

from scripts.train_identifier import SOURCES, source_text
from src.ai.language_model import ALPHABET, CONTEXT, SCALE


ROOT = Path(__file__).resolve().parents[1]


def dataset(split, maximum, seed):
    contexts, targets, provenance = [], [], []
    rng = np.random.default_rng(seed)
    for book_id, title in SOURCES[split]:
        text, record = source_text(book_id)
        values = np.frombuffer(text.encode('ascii'), dtype=np.uint8).astype(np.int64) - 97
        windows = np.lib.stride_tricks.sliding_window_view(values, CONTEXT + 1)
        indices = rng.choice(len(windows), min(maximum // len(SOURCES[split]), len(windows)), replace=False)
        contexts.append(windows[indices, :CONTEXT].copy())
        targets.append(windows[indices, CONTEXT].copy())
        provenance.append(dict(record, title=title))
    return np.concatenate(contexts), np.concatenate(targets), provenance


def forward(x, parameters):
    embedding, w1, b1, w2, b2 = parameters
    embedded = embedding[x].reshape(len(x), -1)
    hidden = np.tanh(embedded @ w1 + b1)
    logits = hidden @ w2 + b2
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return embedded, hidden, exp / exp.sum(axis=1, keepdims=True)


def nll(x, y, parameters):
    total = 0.
    for start in range(0, len(y), 2048):
        _, _, scores = forward(x[start:start + 2048], parameters)
        truth = y[start:start + 2048]
        total -= np.log(scores[np.arange(len(truth)), truth] + 1e-15).sum()
    return float(total / len(y))


def train():
    splits = {split: dataset(split, 240000 if split == 'train' else 16000, 901 + i)
              for i, split in enumerate(SOURCES)}
    x, y, _ = splits['train']
    rng = np.random.default_rng(901)
    parameters = [rng.normal(0, .15, (26, 8)), rng.normal(0, .15, (24, 64)),
                  np.zeros(64), rng.normal(0, .1, (64, 26)), np.zeros(26)]
    first = [np.zeros_like(p) for p in parameters]
    second = [np.zeros_like(p) for p in parameters]
    best_loss, best, step, best_epoch = float('inf'), None, 0, 0
    history = []
    for epoch in range(24):
        for batch in np.array_split(rng.permutation(len(y)), max(1, len(y) // 1024)):
            step += 1
            xb, truth = x[batch], y[batch]
            embedded, hidden, delta = forward(xb, parameters)
            delta[np.arange(len(truth)), truth] -= 1
            delta /= len(truth)
            dh = (delta @ parameters[3].T) * (1 - hidden ** 2)
            de = (dh @ parameters[1].T).reshape(len(truth), CONTEXT, 8)
            embedding_gradient = np.zeros_like(parameters[0])
            np.add.at(embedding_gradient, xb.reshape(-1), de.reshape(-1, 8))
            gradients = [embedding_gradient, embedded.T @ dh, dh.sum(axis=0),
                         hidden.T @ delta, delta.sum(axis=0)]
            for i, gradient in enumerate(gradients):
                first[i] = .9 * first[i] + .1 * gradient
                second[i] = .999 * second[i] + .001 * gradient ** 2
                parameters[i] -= .003 * (first[i] / (1 - .9 ** step)) / (np.sqrt(second[i] / (1 - .999 ** step)) + 1e-8)
        validation = nll(*splits['validation'][:2], parameters)
        history.append({'epoch': epoch + 1, 'validation_nll': validation})
        print(f'epoch {epoch + 1}: validation NLL {validation:.4f}', flush=True)
        if validation < best_loss:
            best_loss, best, best_epoch = validation, [p.copy() for p in parameters], epoch + 1

    all_contexts = np.array([[a, b, c] for a in range(26) for b in range(26) for c in range(26)])
    compiled = []
    for start in range(0, len(all_contexts), 1024):
        scores = forward(all_contexts[start:start + 1024], best)[2]
        compiled.extend(np.rint(-np.log(np.maximum(scores, 1e-15)) * SCALE).astype(np.uint16).reshape(-1).tolist())
    costs = array('H', compiled)
    if sys.byteorder != 'little':
        costs.byteswap()
    counts = np.bincount(y, minlength=26) + 1
    unigram_costs = (-np.log(counts / counts.sum())).tolist()
    model = {'format_version': 1, 'alphabet': ALPHABET, 'context': CONTEXT,
             'architecture': 'embedding8-tanh64-softmax26', 'cost_scale': SCALE,
             'parameters': [p.tolist() for p in best], 'unigram_costs': unigram_costs,
             'cost_table': base64.b64encode(zlib.compress(costs.tobytes(), 9)).decode('ascii')}
    content = json.dumps(model, separators=(',', ':')).encode('utf-8')
    output = ROOT / 'src/ai/english_language_model.json'
    output.write_bytes(content)
    report = {'seed': 901, 'numpy_version': np.__version__, 'context': CONTEXT,
              'architecture': model['architecture'], 'parameters': sum(p.size for p in best),
              'epochs': 24, 'selected_epoch': best_epoch, 'selection': 'minimum validation NLL',
              'history': history, 'model_sha256': hashlib.sha256(content).hexdigest(),
              'splits': {split: {'examples': len(values[1]), 'sources': values[2],
                                 'next_character_nll_nats': nll(*values[:2], best),
                                 'unigram_nll_nats': float(np.array(unigram_costs)[values[1]].mean())}
                         for split, values in splits.items()}}
    (ROOT / 'docs/LANGUAGE_MODEL_TRAINING.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({split: record['next_character_nll_nats'] for split, record in report['splits'].items()}))
    print(f'Model written: {output} ({len(content)} bytes)', flush=True)


if __name__ == '__main__':
    train()
