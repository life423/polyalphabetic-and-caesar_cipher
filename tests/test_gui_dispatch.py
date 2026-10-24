"""Exercise GUI dispatch without opening a real desktop window."""
from types import SimpleNamespace

import pytest

pytest.importorskip("tkinter")
from src.ui.gui import CipherGUI
from src.services.cipher_service import CipherService


class FakeResultText:
    def __init__(self):
        self.value = ""

    def delete(self, *_):
        self.value = ""

    def insert(self, _, value):
        self.value += value


def _entry(value):
    return SimpleNamespace(get=lambda: value)


def gui(cipher, source, key, output="", delete_input=False, action="e"):
    app = CipherGUI.__new__(CipherGUI)
    app.cipher_service = CipherService()
    app.cipher_var = _entry(cipher)
    app.action_var = _entry(action)
    app.input_entry = _entry(source)
    app.output_entry = _entry(output)
    app.delete_input_var = _entry(delete_input)
    app.result_text = FakeResultText()
    app.caesar_key_entry = _entry(key)
    app.poly_key_entry = _entry(key)
    app.sub_key_entry = _entry(key)
    app.trans_key_entry = _entry(key)
    app.rail_key_entry = _entry(key)
    app.affine_a_entry = _entry("5")
    app.affine_b_entry = _entry("8")
    return app


@pytest.mark.parametrize("cipher,text,key,expected", [
    ("c", "Hello", "3", "Khoor"),
    ("p", "HELLO", "KEY", "RIJVS"),
    ("s", "HELLO", "zyxwvutsrqponmlkjihgfedcba", "SVOOL"),
    ("t", "WEAREDISCOVEREDFLEEATONCE", "ZEBRAS", "EVLNXACDTXESEAXROFOXDEECXWIREE"),
    ("r", "WEAREDISCOVEREDFLEEATONCE", "3", "WECRLTEERDSOEEFEAOCAIVDEN"),
    ("a", "AFFINECIPHER", "", "IHHWVCSWFRCP"),
])
def test_gui_encrypt_dispatch(cipher, text, key, expected):
    app = gui(cipher, text, key)
    app._process_text()
    assert app.result_text.value == expected


def test_gui_file_mode_preserves_input(tmp_path):
    source = tmp_path / "source.txt"
    destination = tmp_path / "destination.txt"
    source.write_text("Hello", encoding="utf-8")
    app = gui("c", str(source), "3", output=str(destination))
    app._process_text()
    assert app.result_text.value.startswith("Successfully")
    assert destination.read_text(encoding="utf-8") == "Khoor"
    assert source.read_text(encoding="utf-8") == "Hello"


def test_gui_invalid_key_displays_error():
    app = gui("s", "Hello", "a" * 26)
    app._process_text()
    assert app.result_text.value.startswith("Error:")
