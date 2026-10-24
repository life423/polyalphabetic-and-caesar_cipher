"""Offline ML dataset quality tests: class balance, reversibility and leakage."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from src.ai.training_data import (
    LABELS, SPLITS, draw_plaintext, encrypt_example, generate_dataset,
    group_counts, normalize_text, read_corpus, sha256, split_documents,
)
from src.core.ciphers import (
    AffineCipher, CaesarCipher, PolyalphabeticCipher, RailFenceCipher,
    SubstitutionCipher, TranspositionCipher,
)


DECODERS = {
    "caesar": CaesarCipher,
    "vigenere": PolyalphabeticCipher,
    "substitution": SubstitutionCipher,
    "transposition": TranspositionCipher,
    "rail_fence": RailFenceCipher,
    "affine": AffineCipher,
}


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def make_corpus(root: Path):
    root.mkdir()
    # Distinct source documents, sufficiently long for independent windows.
    identifiers = ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot",
                   "golf", "hotel", "india", "juliet", "kilo", "lima")
    for number, marker in enumerate(identifiers):
        text = (
            f"The {marker} survey covers local history and careful field research. "
            f"The author visited the {marker} district to record city observations. "
            f"Several residents described how the {marker} neighborhood looked in summer. "
            f"Field teams gathered unusual results near the {marker} instrument station. "
            f"These findings raised specific questions about urban development. "
        ) * 3
        (root / f"document-{number:02d}.txt").write_text(text, encoding="utf-8")
    return root


def test_normalization_and_counts():
    assert normalize_text("Café—42; z! Ω") == "CAFEZ"
    assert group_counts(3) == {"train": 1, "validation": 1, "test": 1}
    assert sum(group_counts(21).values()) == 21
    with pytest.raises(ValueError):
        group_counts(2)


def test_demo_generator_balanced_and_recoverable(tmp_path):
    output = tmp_path / "dataset"
    manifest = generate_dataset(
        output_dir=output, demo=True, samples_per_class=30,
        seed=919, min_length=64, max_length=145,
    )
    assert manifest["demo"] is True
    assert set(manifest["labels"]) == set(LABELS)
    assert manifest["schema_version"] == 1
    assert len(manifest["corpus_sha256"]) == 64

    seen_sources = set()
    seen_plaintexts = set()
    for split in SPLITS:
        examples = rows(output / f"{split}.jsonl")
        answers = rows(output / f"{split}_answers.jsonl")
        assert len(examples) == len(answers) == manifest["splits"][split]["rows"]
        assert manifest["splits"][split]["label_counts"] == {
            cipher: manifest["splits"][split]["groups"] for cipher in LABELS
        }
        answer_by_id = {entry["sample_id"]: entry for entry in answers}
        assert len(answer_by_id) == len(answers)
        samples = {}
        for example in examples:
            assert set(example) == {"sample_id", "group_id", "ciphertext", "label"}
            sample_id = example["sample_id"]
            answer = answer_by_id[sample_id]
            assert sample_id.startswith(split + "-")
            assert not any(sample_id.endswith("-" + name) for name in LABELS)
            assert example["label"] in LABELS
            assert example["ciphertext"].isascii()
            assert example["ciphertext"].isalpha()
            assert example["ciphertext"].isupper()
            assert 64 <= len(example["ciphertext"]) <= 145
            plain = answer["plaintext"]
            assert len(plain) == len(example["ciphertext"])
            assert sha256(plain) == answer["plaintext_sha256"]
            assert DECODERS[example["label"]].transform(
                example["ciphertext"], answer["key"], encrypt=False
            ) == plain
            samples.setdefault(example["group_id"], []).append((example, answer))

        assert len(samples) == manifest["splits"][split]["groups"]
        split_sources = set()
        for group_entries in samples.values():
            assert set(e["label"] for e, _ in group_entries) == set(LABELS)
            assert len(set(len(e["ciphertext"]) for e, _ in group_entries)) == 1
            assert len(set(a["plaintext"] for _, a in group_entries)) == 1
            plain = group_entries[0][1]["plaintext"]
            assert plain not in seen_plaintexts
            seen_plaintexts.add(plain)
            split_sources.add(group_entries[0][1]["source_id"])
        assert seen_sources.isdisjoint(split_sources), "Document leakage across splits"
        seen_sources.update(split_sources)
    assert len(seen_sources) >= 3


def test_seed_recreates_byte_identical_files(tmp_path):
    outputs = [tmp_path / "first", tmp_path / "second"]
    for out in outputs:
        generate_dataset(output_dir=out, demo=True, seed=42, samples_per_class=24)
    filenames = sorted(p.name for p in outputs[0].iterdir())
    assert filenames == sorted(p.name for p in outputs[1].iterdir())
    for name in filenames:
        assert (outputs[0] / name).read_bytes() == (outputs[1] / name).read_bytes()


def test_real_corpus_is_grouped_by_document(tmp_path):
    source = make_corpus(tmp_path / "corpus")
    output = tmp_path / "dataset"
    manifest = generate_dataset(
        output_dir=output, corpus_dir=source,
        samples_per_class=36, seed=104,
    )
    sources = [
        set(row["source_id"] for row in rows(output / f"{split}_answers.jsonl"))
        for split in SPLITS
    ]
    assert all(sources)
    assert not (sources[0] & sources[1])
    assert not (sources[0] & sources[2])
    assert not (sources[1] & sources[2])
    assert sum(item["rows"] for item in manifest["splits"].values()) == 36 * 6


def test_duplicate_documents_rejected_before_writing(tmp_path):
    corpus = make_corpus(tmp_path / "corpus")
    (corpus / "copied.txt").write_text(
        (corpus / "document-00.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    dest = tmp_path / "dataset"
    with pytest.raises(ValueError, match="Duplicate normalized"):
        generate_dataset(output_dir=dest, corpus_dir=corpus, samples_per_class=9)
    assert not dest.exists()


def test_no_overwrite_and_no_output_inside_corpus(tmp_path):
    corpus = make_corpus(tmp_path / "corpus")
    created = tmp_path / "data"
    created.mkdir()
    with pytest.raises(FileExistsError):
        generate_dataset(output_dir=created, corpus_dir=corpus, samples_per_class=9)
    with pytest.raises(ValueError, match="inside the source corpus"):
        generate_dataset(
            output_dir=corpus / "nested" / "output", corpus_dir=corpus,
            samples_per_class=9,
        )


def test_invalid_configuration_rejected(tmp_path):
    with pytest.raises(ValueError, match="exactly one"):
        generate_dataset(output_dir=tmp_path / "none")
    with pytest.raises(ValueError, match="Lengths"):
        generate_dataset(output_dir=tmp_path / "short", demo=True, min_length=2)
    with pytest.raises(ValueError, match="at least 3"):
        generate_dataset(output_dir=tmp_path / "few", demo=True, samples_per_class=2)


@pytest.mark.parametrize("cipher", LABELS)
def test_nontrivial_keys_and_expected_ciphertext_shapes(cipher):
    import random

    text = "THEUNIQUEPLAINTEXTISLONGENOUGHTOTEST"
    width = 3
    if len(text) % width:
        text += "A" * (-len(text) % width)
    encrypted, key = encrypt_example(cipher, text, width, random.Random(77))
    assert encrypted.isalpha() and encrypted.isupper()
    assert len(encrypted) == len(text)
    assert DECODERS[cipher].transform(encrypted, key, False) == text
    if cipher == "affine":
        assert key[0] != 1
    if cipher == "transposition":
        assert key != list(range(width))
    if cipher == "vigenere":
        assert len(key) >= 3 and len(set(key)) > 1


def test_cli_generates_dataset_without_network(tmp_path):
    out = tmp_path / "cli_data"
    result = subprocess.run(
        [
            sys.executable, "-m", "src.ai.training_data",
            "--demo", "--output-dir", str(out),
            "--samples-per-class", "6", "--seed", "19",
        ],
        capture_output=True, text=True, check=True,
    )
    result_json = json.loads(result.stdout)
    assert result_json["labels"] == list(LABELS)
    assert sum(result_json["rows"].values()) == 36
    assert (out / "manifest.json").is_file()
