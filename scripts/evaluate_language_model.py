"""Compare recovered plaintext using the existing heuristic and our trained LM."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import re
from time import perf_counter

from scripts.train_identifier import CACHE, SOURCES, source_text
from src.ai.analyzer import CipherAnalyzer
from src.ai.neural_analyzer import NeuralCipherAnalyzer as LearnedAnalyzer
from src.ai.language_model import language_score
from src.core.ciphers import AffineCipher, CaesarCipher, PolyalphabeticCipher, RailFenceCipher


ROOT = Path(__file__).resolve().parents[1]


def compare(split, count):
    rng = random.Random(234)
    totals = {}
    cases = []
    for book_id, _ in SOURCES[split]:
        source_text(book_id)  # Validate the cached full-file fingerprint first.
        text = (CACHE / f'{book_id}.txt').read_text(encoding='utf-8-sig')
        text = re.split(r'\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*', text)[1]
        text = re.split(r'\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK', text)[0][5000:-5000]
        starts = list(range(0, len(text) - 600, 800))
        rng.shuffle(starts)
        for index, start in enumerate(starts[:count]):
            passage = text[start:start + (80, 180, 400)[index % 3]]
            for formatting in ('original', 'letters_only'):
                plain = passage if formatting == 'original' else ''.join(c.lower() for c in passage if c.isascii() and c.isalpha())
                for cipher in ('Caesar', 'Affine', 'Rail Fence', 'Vigenère'):
                    started = perf_counter()
                    if cipher == 'Caesar':
                        key = rng.randint(1, 25)
                        encrypted = CaesarCipher.transform(plain, key)
                        legacy = CipherAnalyzer.analyze_caesar(encrypted)[0]['shift']
                        learned = min(range(26), key=lambda k: language_score(CaesarCipher.transform(encrypted, k, False)))
                        baseline_text = CaesarCipher.transform(encrypted, legacy, False)
                        model_text = CaesarCipher.transform(encrypted, learned, False)
                        target = plain
                    elif cipher == 'Affine':
                        key = (rng.choice((3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25)), rng.randrange(26))
                        encrypted = AffineCipher.transform(plain, key)
                        legacy = CipherAnalyzer.analyze_affine(encrypted)[0]
                        learned = LearnedAnalyzer.analyze_affine(encrypted)[0]
                        baseline_text = AffineCipher.transform(encrypted, (legacy['a'], legacy['b']), False)
                        model_text = AffineCipher.transform(encrypted, (learned['a'], learned['b']), False)
                        target = plain
                    elif cipher == 'Rail Fence':
                        key = rng.randint(2, 12)
                        encrypted = RailFenceCipher.transform(plain, key)
                        legacy = CipherAnalyzer.analyze_rail_fence(encrypted)[0]['rails']
                        learned = LearnedAnalyzer.analyze_rail_fence(encrypted)[0]['rails']
                        baseline_text = RailFenceCipher.transform(encrypted, legacy, False)
                        model_text = RailFenceCipher.transform(encrypted, learned, False)
                        target = ''.join(plain.split())
                    else:
                        key = ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(rng.randint(2, 8)))
                        encrypted = PolyalphabeticCipher.transform(plain, key)
                        legacy = CipherAnalyzer.analyze_polyalphabetic(encrypted)[0]['keyword']
                        learned = LearnedAnalyzer.analyze_polyalphabetic(encrypted)[0]['keyword']
                        baseline_text = PolyalphabeticCipher.transform(encrypted, legacy, False)
                        model_text = PolyalphabeticCipher.transform(encrypted, learned, False)
                        target = plain
                    result = {'cipher': cipher, 'formatting': formatting, 'characters': len(plain),
                              'book_id': book_id, 'source_start': start, 'key': key,
                              'legacy_exact': baseline_text == target, 'learned_exact': model_text == target,
                              'comparison_seconds': perf_counter() - started}
                    cases.append(result)
                    name = f'{cipher}/{formatting}'
                    summary = totals.setdefault(name, {'examples': 0, 'legacy_exact': 0, 'learned_exact': 0})
                    for field in summary:
                        summary[field] += 1 if field == 'examples' else int(result[field])
            print(f'{split} book {book_id}: passage {index + 1}/{min(count, len(starts))}', flush=True)
    return {'split': split, 'examples': len(cases), 'totals': totals, 'cases': cases}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=('validation', 'test'), default='validation')
    parser.add_argument('--passages', type=int, default=12)
    parser.add_argument('--output', type=Path, help='Write an independent report without replacing the recorded benchmark.')
    args = parser.parse_args()
    if args.passages < 1:
        parser.error('--passages must be positive')
    report = compare(args.split, args.passages)
    report['model_sha256'] = hashlib.sha256((ROOT / 'src/ai/english_language_model.json').read_bytes()).hexdigest()
    output = args.output or ROOT / f'docs/LANGUAGE_MODEL_{args.split.upper()}.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['totals'], indent=2))
