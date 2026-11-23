"""Verify learned inference, validation, line semantics and deployable model assets."""
import json
import hashlib
import math
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.build_static import build
from src.ai.identifier import (LABELS, extract_features, identify_cipher, letters_only,
                               load_model, predict_scores)
from src.core.ciphers import CaesarCipher
from src.services.web_service import identify_message


TEXT = (
    'We planted carrots beside the garden fence and watered them each morning. '
    'The children measured the green leaves while their teacher recorded the weather. '
    'After several weeks we carried a basket of fresh vegetables into the kitchen. '
    'Everyone helped prepare a warm meal and shared stories around the table.'
)


@pytest.mark.parametrize('text', [None, '', '   ', 'abc' * 33, '日本語' * 100, 'İ' * 100])
def test_identifier_requires_enough_ascii_letters(text):
    with pytest.raises(ValueError):
        identify_cipher(text)


def test_identifier_rejects_oversized_sample_before_inference():
    with pytest.raises(ValueError, match='5,000'):
        identify_cipher('a' * 5001)


def test_features_ignore_case_and_formatting():
    plain = letters_only(TEXT)
    formatted = '\n '.join(plain.upper()) + '123日本語'
    assert extract_features(plain) == extract_features(formatted)


def test_trained_inference_returns_finite_normalized_scores_and_known_labels():
    features = extract_features(TEXT)
    model = load_model()
    scores = predict_scores(features, model)
    assert len(features) == len(model['mean']) == len(model['scale'])
    assert all(len(row) == len(features) for row in model['hidden_weights'])
    assert len(scores) == len(LABELS)
    assert all(math.isfinite(score) and 0 <= score <= 1 for score in scores)
    assert sum(scores) == pytest.approx(1)
    features = extract_features(CaesarCipher.transform(TEXT, 11))
    scores = predict_scores(features, load_model())
    assert len(scores) == len(LABELS)
    assert all(math.isfinite(score) and 0 <= score <= 1 for score in scores)
    assert sum(scores) == pytest.approx(1)
    guesses = identify_cipher(CaesarCipher.transform(TEXT, 11))
    assert guesses[0]['cipher'] == 'Caesar'
    assert len({guess['cipher'] for guess in guesses}) == 3
    assert all(guess['cipher'] in LABELS for guess in guesses)
    assert 'confidence' not in guesses[0]


def test_exported_network_matches_vectorized_training_math():
    np = pytest.importorskip('numpy')
    model = load_model()
    features = extract_features(TEXT)
    x = (np.array(features) - model['mean']) / model['scale']
    hidden = np.tanh(x @ np.array(model['hidden_weights']).T + model['hidden_bias'])
    logits = hidden @ np.array(model['output_weights']).T + model['output_bias']
    expected = np.exp(logits - logits.max())
    expected /= expected.sum()
    assert predict_scores(features, model) == pytest.approx(expected.tolist(), abs=1e-12)


def test_file_identification_uses_longest_letter_bearing_line(monkeypatch):
    captured = []
    monkeypatch.setattr('src.ai.identifier.identify_cipher', lambda text: captured.append(text) or [])
    assert identify_message('x' * 90 + '\r\n' + TEXT + '\n' + '9' * 1000, file_mode=True) == []
    assert captured == [TEXT]


def test_file_identification_does_not_join_independent_short_lines():
    with pytest.raises(ValueError, match='at least 100'):
        identify_message(('small independent line\r\n' * 30), file_mode=True)


def test_static_bundle_contains_model_but_not_training_data(tmp_path):
    runtime = tmp_path / 'runtime'
    runtime.mkdir()
    for filename in ('pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm',
                     'python_stdlib.zip', 'pyodide-lock.json'):
        (runtime / filename).write_bytes(b'fake runtime fixture')
    output = build(tmp_path / 'output', runtime)
    with ZipFile(output / 'engine.zip') as package:
        model = json.loads(package.read('src/ai/cipher_identifier.json'))
        assert model['labels'] == list(LABELS)
        assert 'src/ai/identifier.py' in package.namelist()
        assert 'src/ai/english_language_model.json' in package.namelist()
        assert not any('training-corpus' in name or name.endswith('.txt') for name in package.namelist())


def test_recorded_evaluation_uses_disjoint_source_books():
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / 'docs/IDENTIFIER_EVALUATION.json').read_text())
    assert report['model_sha256'] == hashlib.sha256((root / 'src/ai/cipher_identifier.json').read_bytes()).hexdigest()
    splits = report['splits']
    ids = [{source['book_id'] for source in splits[split]['sources']} for split in ('train', 'validation', 'test')]
    assert not ids[0] & ids[1] and not ids[0] & ids[2] and not ids[1] & ids[2]
    assert splits['test']['examples'] == 1362
    assert splits['test']['top1_accuracy'] > report['baseline']['test_top1_accuracy']
