"""Check the learned distribution, compiled inference, ranking and model provenance."""
import hashlib
import json
import math
from pathlib import Path
import random

import pytest

from src.ai.language_model import (CONTEXT, SCALE, TABLE_SIZE, encode_letters,
                                   generate_letters, language_score, load_language_model)
from src.ai.neural_analyzer import NeuralCipherAnalyzer
from src.core.ciphers import CaesarCipher


ROOT = Path(__file__).resolve().parents[1]
TEXT = ('The scientist recorded the temperature before opening the laboratory window. '
        'Her assistant carefully checked the measurements and wrote down the results.')


def test_model_scores_character_order_not_just_letter_frequencies():
    letters = list(TEXT)
    random.Random(413).shuffle(letters)
    assert language_score(TEXT) < language_score(''.join(letters))
    assert language_score(TEXT) == language_score(TEXT.upper() + ' 日本語 123!')


def test_short_and_non_english_inputs_are_explicit():
    assert math.isinf(language_score('123日本語'))
    assert math.isfinite(language_score('a'))
    assert math.isfinite(language_score('abc'))
    assert encode_letters('Aİé日本語z') == [0, 25]


def test_compiled_contexts_form_next_character_distributions():
    costs, _ = load_language_model()
    assert len(costs) == TABLE_SIZE
    for context in (0, 234, 5678, 17575):
        assert sum(math.exp(-value / SCALE) for value in costs[context * 26:(context + 1) * 26]) == pytest.approx(1, abs=.001)


def test_compiled_table_matches_actual_neural_network():
    np = pytest.importorskip('numpy')
    from scripts.train_language_model import forward

    data = json.loads((ROOT / 'src/ai/english_language_model.json').read_text())
    parameters = [np.array(p) for p in data['parameters']]
    contexts = np.random.default_rng(61).integers(0, 26, (100, CONTEXT))
    probabilities = forward(contexts, parameters)[2]
    costs, _ = load_language_model()
    for context, scores in zip(contexts, probabilities):
        offset = int(context[0] * 676 + context[1] * 26 + context[2]) * 26
        for letter in range(26):
            assert costs[offset + letter] / SCALE == pytest.approx(-math.log(scores[letter]), abs=.000501)


def test_sampling_is_reproducible_and_does_not_change_global_random_state():
    state = random.getstate()
    output = generate_letters('the', 50, 4)
    assert output == generate_letters('the', 50, 4)
    assert len(output) == 53 and output.isascii() and output.isalpha()
    assert random.getstate() == state
    with pytest.raises(ValueError):
        generate_letters('ab')
    with pytest.raises(ValueError):
        generate_letters('the', 1001)


def test_neural_key_search_recovers_message():
    ciphertext = CaesarCipher.transform(TEXT, 13)
    candidates = NeuralCipherAnalyzer.analyze_caesar(ciphertext)
    assert candidates[0]['shift'] == 13
    assert all(candidate['score'] > 0 for candidate in candidates)
    assert NeuralCipherAnalyzer.analyze_caesar('123') == []


def test_reports_match_model_and_have_disjoint_books():
    digest = hashlib.sha256((ROOT / 'src/ai/english_language_model.json').read_bytes()).hexdigest()
    training = json.loads((ROOT / 'docs/LANGUAGE_MODEL_TRAINING.json').read_text())
    assert training['model_sha256'] == digest
    splits = [{source['book_id'] for source in training['splits'][split]['sources']}
              for split in ('train', 'validation', 'test')]
    assert not splits[0] & splits[1] and not splits[0] & splits[2] and not splits[1] & splits[2]
    assert training['splits']['test']['next_character_nll_nats'] < training['splits']['test']['unigram_nll_nats']
    benchmark = json.loads((ROOT / 'docs/LANGUAGE_MODEL_TEST.json').read_text())
    assert benchmark['model_sha256'] == digest
    assert benchmark['examples'] == len(benchmark['cases']) == 384
    assert sum(c['learned_exact'] for c in benchmark['cases']) > sum(c['legacy_exact'] for c in benchmark['cases'])
