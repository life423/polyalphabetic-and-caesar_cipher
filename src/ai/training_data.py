"""Generate reproducible, balanced ciphertext classification data entirely offline.

Data format: train/validation/test JSONL contain ONLY ciphertext and cipher labels.
Separate *_answers.jsonl hold plaintext, key, and source group for auditing and
future key-recovery tasks. Never train a classifier on the answers files.

Corpus files are grouped by source document BEFORE sampling to avoid split leakage.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import random
import re
import string
import unicodedata

from src.core.ciphers import (
    AffineCipher,
    CaesarCipher,
    PolyalphabeticCipher,
    RailFenceCipher,
    SubstitutionCipher,
    TranspositionCipher,
)

LABELS = ("caesar", "vigenere", "substitution", "transposition", "rail_fence", "affine")
SPLITS = ("train", "validation", "test")
ALPHABET = string.ascii_uppercase
AFFINE_MULTIPLIERS = (3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25)
VERSION = 1


def normalize_text(text: str) -> str:
    """Normalize every source and ciphertext to uppercase ASCII A-Z only."""
    plain_ascii = unicodedata.normalize("NFKD", text).encode("ascii", "ignore")
    return re.sub(r"[^A-Z]", "", plain_ascii.decode("ascii").upper())


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_corpus(corpus_dir: Path | None, demo: bool, min_length: int) -> list[tuple[str, str]]:
    """One file is one source group. No lines from a file cross dataset splits."""
    if demo:
        from src.ai.demo_corpus import DEMO_DOCUMENTS
        documents = [(f"demo-{index:03d}", normalize_text(text))
                     for index, text in enumerate(DEMO_DOCUMENTS)]
    else:
        if corpus_dir is None or not corpus_dir.is_dir():
            raise ValueError("--corpus-dir must point to an existing folder of UTF-8 .txt files")
        files = sorted(path for path in corpus_dir.rglob("*.txt") if path.is_file())
        if not files:
            raise ValueError("No .txt documents found in corpus folder")
        documents = [
            (path.relative_to(corpus_dir).as_posix(),
             normalize_text(path.read_text(encoding="utf-8")))
            for path in files
        ]

    valid = [(name, text) for name, text in documents if len(text) >= min_length]
    if len(valid) < 3:
        raise ValueError("Need at least three separate documents with sufficient ASCII letters")
    fingerprints = [sha256(content) for _, content in valid]
    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError("Duplicate normalized source documents: remove copies before splitting")
    return valid


def split_documents(
    documents: list[tuple[str, str]], rng: random.Random
) -> dict[str, list[tuple[str, str]]]:
    """Assign WHOLE documents; test/validation never see training source files."""
    shuffled = sorted(documents)
    rng.shuffle(shuffled)
    count = len(shuffled)
    train_n = min(count - 2, max(1, round(count * 0.8)))
    validation_n = min(count - train_n - 1, max(1, round(count * 0.1)))
    return {
        "train": shuffled[:train_n],
        "validation": shuffled[train_n:train_n + validation_n],
        "test": shuffled[train_n + validation_n:],
    }


def group_counts(n: int) -> dict[str, int]:
    """Each group yields exactly one example of each of the six labels."""
    if n < 3:
        raise ValueError("--samples-per-class must be at least 3")
    train = min(n - 2, max(1, round(n * 0.8)))
    validation = min(n - train - 1, max(1, round(n * 0.1)))
    return {"train": train, "validation": validation, "test": n - train - validation}


def draw_plaintext(
    docs: list[tuple[str, str]], rng: random.Random,
    minimum: int, maximum: int, seen: set[str],
) -> tuple[str, str, int]:
    """Pick a unique passage and width that yields *no transposition padding*."""
    for _ in range(1000):
        source, body = rng.choice(docs)
        width = rng.randint(3, 10)
        min_rows = math.ceil(minimum / width)
        max_rows = min(maximum, len(body)) // width
        if min_rows > max_rows:
            continue
        length = width * rng.randint(min_rows, max_rows)
        start = rng.randrange(len(body) - length + 1)
        passage = body[start:start + length]
        fingerprint = sha256(passage)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        return source, passage, width
    raise ValueError(
        "Corpus exhausted: insufficient distinct plaintext windows. "
        "Add more diverse, independently sourced documents or reduce sample count."
    )


def encrypt_example(
    label: str, plain: str, width: int, rng: random.Random,
) -> tuple[str, int | str | list[int]]:
    """Use the application's real encryption functions; store keys separately."""
    if label == "caesar":
        key = rng.randint(1, 25)
        encrypted = CaesarCipher.transform(plain, key)
    elif label == "vigenere":
        size = rng.randint(3, 12)
        key = "".join(rng.choices(ALPHABET, k=size))
        while len(set(key)) == 1:  # a one-letter repeat is actually Caesar
            key = "".join(rng.choices(ALPHABET, k=size))
        encrypted = PolyalphabeticCipher.transform(plain, key)
    elif label == "substitution":
        alphabet = list(string.ascii_lowercase)
        rng.shuffle(alphabet)
        key = "".join(alphabet)
        encrypted = SubstitutionCipher.transform(plain, key)
    elif label == "transposition":
        key = list(range(width))
        rng.shuffle(key)
        while key == list(range(width)):
            rng.shuffle(key)
        encrypted = TranspositionCipher.transform(plain, key)
    elif label == "rail_fence":
        key = rng.randint(2, min(12, len(plain) // 4))
        encrypted = RailFenceCipher.transform(plain, key)
    elif label == "affine":
        # a=1 reduces Affine to Caesar; exclude the trivial overlap.
        key = [rng.choice(AFFINE_MULTIPLIERS), rng.randrange(26)]
        encrypted = AffineCipher.transform(plain, key)
    else:
        raise ValueError(f"Unknown cipher type: {label}")

    if (len(encrypted) != len(plain) or
            not encrypted.isascii() or
            not encrypted.isalpha() or
            not encrypted.isupper()):
        raise RuntimeError(f"Unexpected ciphertext format for {label}")
    return encrypted, key


def generate_dataset(
    *,
    output_dir: Path,
    corpus_dir: Path | None = None,
    demo: bool = False,
    samples_per_class: int = 1000,
    seed: int = 2026,
    min_length: int = 64,
    max_length: int = 192,
) -> dict:
    """Write six-class, grouped and reproducible JSONL splits plus a manifest.

    Does not overwrite a directory; never commits/generated samples to Git.
    """
    if demo == (corpus_dir is not None):
        raise ValueError("Choose exactly one: --demo or --corpus-dir")
    if min_length < 16 or max_length < min_length:
        raise ValueError("Lengths must satisfy 16 <= min-length <= max-length")
    counts = group_counts(samples_per_class)
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise FileExistsError(f"Output directory already exists: {output_dir}")
    if corpus_dir is not None:
        corpus_dir = Path(corpus_dir).expanduser().resolve()
        if output_dir == corpus_dir or corpus_dir in output_dir.parents:
            raise ValueError("Output directory must not be inside the source corpus")
    docs = read_corpus(corpus_dir, demo, min_length)
    rng = random.Random(seed)
    partitions = split_documents(docs, rng)

    # No publication timestamp or absolute file paths: identical input + seed => identical output.
    corpus_digest = sha256(
        "".join(name + ":" + sha256(text) + "\n" for name, text in sorted(docs))
    )
    manifest = {
        "schema_version": VERSION,
        "purpose": "six-class ciphertext identification, NOT model training",
        "labels": list(LABELS),
        "seed": seed,
        "demo": demo,
        "corpus_sha256": corpus_digest,
        "normalization": "uppercase ASCII A-Z; no spaces, punctuation or padding",
        "samples_per_class": samples_per_class,
        "min_length": min_length,
        "max_length": max_length,
        "splits": {},
        "warnings": [
            "Demo corpus is for pipeline tests, not training a deployable classifier.",
            "Document groups are disjoint; near-duplicate source documents must still be removed.",
            "Affine, Caesar, and substitution are related families; some ciphertexts are inherently ambiguous.",
            "Use only the split JSONL ciphertext/label fields as model inputs. Answers contain keys and plaintext.",
        ],
    }
    # Keep a global fingerprint set to also reject identical plaintext across partitions.
    seen_plaintexts: set[str] = set()
    output_dir.mkdir(parents=True, exist_ok=False)
    for split in SPLITS:
        split_docs = partitions[split]
        labels_count: Counter[str] = Counter()
        with ExitStack() as stack:
            examples = stack.enter_context((output_dir / f"{split}.jsonl").open("w", encoding="utf-8"))
            answers = stack.enter_context((output_dir / f"{split}_answers.jsonl").open("w", encoding="utf-8"))
            for index in range(counts[split]):
                source, plain, width = draw_plaintext(
                    split_docs, rng, min_length, max_length, seen_plaintexts
                )
                group = f"{split}-{index:07d}"
                for label in LABELS:
                    ciphertext, key = encrypt_example(label, plain, width, rng)
                    sample_id = f"{group}-{label}"
                    examples.write(json.dumps({
                        "sample_id": sample_id, "group_id": group,
                        "ciphertext": ciphertext, "label": label,
                    }, separators=(",", ":"), sort_keys=True) + "\n")
                    answers.write(json.dumps({
                        "sample_id": sample_id, "source_id": source,
                        "plaintext": plain, "key": key,
                        "plaintext_sha256": sha256(plain),
                    }, separators=(",", ":"), sort_keys=True) + "\n")
                    labels_count[label] += 1
        manifest["splits"][split] = {
            "documents": len(split_docs),
            "groups": counts[split],
            "rows": counts[split] * len(LABELS),
            "label_counts": dict(sorted(labels_count.items())),
            "sources_sha256": sorted(sha256(content) for _, content in split_docs),
        }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate balanced, reproducible offline classical-cipher datasets."
    )
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--demo", action="store_true", help="Tiny built-in pipeline-validation corpus")
    sources.add_argument("--corpus-dir", type=Path, help="Folder with independently sourced UTF-8 .txt documents")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--samples-per-class", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--min-length", type=int, default=64)
    parser.add_argument("--max-length", type=int, default=192)
    args = parser.parse_args(argv)
    try:
        manifest = generate_dataset(
            output_dir=args.output_dir, corpus_dir=args.corpus_dir,
            demo=args.demo, samples_per_class=args.samples_per_class,
            seed=args.seed, min_length=args.min_length, max_length=args.max_length,
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({
        "output": str(args.output_dir),
        "rows": {split: entry["rows"] for split, entry in manifest["splits"].items()},
        "labels": manifest["labels"], "seed": manifest["seed"],
    }, indent=2))


if __name__ == "__main__":
    main()
