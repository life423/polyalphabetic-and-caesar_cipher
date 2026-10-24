"""Regression tests for safety and documented classical cipher behavior."""
import random
import string

import pytest

from src.core.ciphers import (
    CaesarCipher, PolyalphabeticCipher, SubstitutionCipher,
    TranspositionCipher, RailFenceCipher, AffineCipher,
)
from src.services.file_service import FileService


def test_standard_rail_fence_vector():
    plaintext = "WEAREDISCOVEREDFLEEATONCE"
    ciphertext = "WECRLTEERDSOEEFEAOCAIVDEN"
    assert RailFenceCipher.transform(plaintext, 3) == ciphertext
    assert RailFenceCipher.transform(ciphertext, 3, encrypt=False) == plaintext


@pytest.mark.parametrize("rails", [2, 3, 4, 5, 8])
def test_rail_fence_round_trip(rails):
    text = "SOMENEWTEXTTOAVOIDHARDCODEDSAMPLES"
    result = RailFenceCipher.transform(text, rails)
    assert RailFenceCipher.transform(result, rails, encrypt=False) == text


def test_transposition_keyword_vector():
    plaintext = "WEAREDISCOVEREDFLEEATONCE"
    ciphertext = "EVLNXACDTXESEAXROFOXDEECXWIREE"
    assert TranspositionCipher.transform(plaintext, "ZEBRAS") == ciphertext
    assert TranspositionCipher.transform(ciphertext, "ZEBRAS", encrypt=False) == plaintext + "XXXXX"


@pytest.mark.parametrize("key", ["ZEBRAS", "BALLOON", [2, 0, 3, 1]])
def test_transposition_round_trip(key):
    text = "PLAINENGLISHTEXT"
    encrypted = TranspositionCipher.transform(text, key)
    assert TranspositionCipher.transform(encrypted, key, False).rstrip("X") == text


@pytest.mark.parametrize("key", ["", "X", [1, 1], [0, 2], [-1, 0], [True, 0]])
def test_transposition_rejects_invalid_keys(key):
    with pytest.raises(ValueError):
        TranspositionCipher.transform("TEST", key)


def test_substitution_key_must_be_permutation():
    with pytest.raises(ValueError):
        SubstitutionCipher.transform("TEST", "a" * 26)


def test_seeded_substitution_does_not_modify_global_random_state():
    random.seed(2026)
    before = random.getstate()
    key = SubstitutionCipher.generate_key("fixture")
    assert set(key) == set(string.ascii_lowercase)
    assert random.getstate() == before


@pytest.mark.parametrize("transform,key", [
    (CaesarCipher.transform, 3),
    (PolyalphabeticCipher.transform, "KEY"),
    (AffineCipher.transform, (5, 8)),
])
def test_ascii_only_transform_keeps_unicode_intact(transform, key):
    text = "Hi café Ω!"
    result = transform(text, key)
    assert "é" in result and "Ω" in result
    assert transform(result, key, False) == text


def test_file_input_output_same_path_is_rejected(tmp_path):
    file = tmp_path / "message.txt"
    file.write_text("preserve this", encoding="utf-8")
    result = FileService.process_file(file, file, lambda content: content[::-1])
    assert result.startswith("Error:")
    assert file.read_text(encoding="utf-8") == "preserve this"


def test_file_transform_failure_does_not_truncate_destination(tmp_path):
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    source.write_text("input", encoding="utf-8")
    destination.write_text("original output", encoding="utf-8")

    def fail(_):
        raise ValueError("invalid key")

    assert FileService.process_file(source, destination, fail).startswith("Error:")
    assert destination.read_text(encoding="utf-8") == "original output"

def test_file_processing_preserves_per_line_keyword_reset(tmp_path):
    source = tmp_path / "input.txt"
    destination = tmp_path / "output.txt"
    source.write_text("ATTACK\nATDAWN\n", encoding="utf-8")
    result = FileService.process_file(
        source, destination,
        lambda line: PolyalphabeticCipher.transform(line, "LEMON")
    )
    assert result.startswith("Successfully")
    expected = (
        PolyalphabeticCipher.transform("ATTACK\n", "LEMON")
        + PolyalphabeticCipher.transform("ATDAWN\n", "LEMON")
    )
    assert destination.read_text(encoding="utf-8") == expected


def test_cli_does_not_import_gui_or_tk(monkeypatch):
    import importlib
    import sys
    import src.ui.cli as cli

    called = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))
    monkeypatch.setattr(sys, "argv", ["run.py", "--cli"])
    monkeypatch.setitem(sys.modules, "tkinter", None)
    app = importlib.import_module("run")
    app.main()
    assert called == [True]


def test_interactive_cli_never_deletes_existing_txt(tmp_path, monkeypatch, capsys):
    from src.ui.cli import main as cli_main

    victim = tmp_path / "preserve.txt"
    victim.write_text("original", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    answers = iter(["e", "c", "1", "Hello", "3"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli_main()
    assert "Khoor" in capsys.readouterr().out
    assert victim.read_text(encoding="utf-8") == "original"
