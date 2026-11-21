"""Stateful browser workflows, including errors, stale results, and session isolation."""
from pathlib import Path

import pytest

pytest.importorskip('streamlit')
from streamlit.testing.v1 import AppTest


ENTRYPOINT = Path(__file__).resolve().parents[1] / 'web_app.py'


def app():
    result = AppTest.from_file(str(ENTRYPOINT), default_timeout=10).run()
    assert not result.exception
    return result


def button(at, label):
    return next(item for item in at.button if item.label == label)


def test_encrypt_and_reuse_result_to_decrypt():
    at = app()
    at.text_area(key='message').set_value('Hello café Ω!')
    button(at, 'Encrypt message').click().run()
    assert at.code[0].value == 'Khoor fdié Ω!'
    button(at, 'Use result as input').click().run()
    assert at.text_area(key='message').value == 'Khoor fdié Ω!'
    button(at, 'Decrypt message').click().run()
    assert at.code[0].value == 'Hello café Ω!'
    assert not at.exception


def test_keyword_is_required_before_vigenere_encryption():
    at = app()
    at.selectbox(key='cipher').select('Vigenère').run()
    at.text_area(key='message').set_value('HELLO')
    button(at, 'Encrypt message').click().run()
    assert 'keyword' in at.error[0].value.lower()
    at.text_input(key='keyword').set_value('KEY')
    button(at, 'Encrypt message').click().run()
    assert at.code[0].value == 'RIJVS'


def test_analysis_can_apply_key_and_decrypt():
    at = app()
    plain = 'The important information is something we should understand together and share with the people.'
    encrypted = ''.join(chr((ord(c) - 97 + 7) % 26 + 97) if 'a' <= c <= 'z'
                        else chr((ord(c) - 65 + 7) % 26 + 65) if 'A' <= c <= 'Z' else c for c in plain)
    at.text_area(key='message').set_value(encrypted)
    button(at, 'Analyze ciphertext').click().run()
    assert at.radio(key='candidate_choice').value == 0
    button(at, 'Use key & decrypt').click().run()
    assert at.number_input(key='shift').value == 7
    assert at.code[0].value == plain
    assert not at.exception


def test_result_and_analysis_are_hidden_after_input_changes():
    at = app()
    at.text_area(key='message').set_value('Hello World')
    button(at, 'Encrypt message').click().run()
    assert at.code
    at.text_area(key='message').set_value('different input').run()
    assert not at.code
    button(at, 'Analyze ciphertext').click().run()
    assert at.radio(key='candidate_choice')
    at.text_area(key='message').set_value('changed again').run()
    assert not at.code
    assert not any(b.label == 'Use key & decrypt' for b in at.button)


def test_short_vigenere_never_offers_an_invalid_key():
    at = app()
    at.selectbox(key='cipher').select('Vigenère').run()
    at.text_area(key='message').set_value('ABC')
    button(at, 'Analyze ciphertext').click().run()
    assert '20 English letters' in at.error[0].value
    assert not any(b.label == 'Use key & decrypt' for b in at.button)


def test_substitution_key_generation_and_browser_session_isolation():
    first = app()
    first.selectbox(key='cipher').select('Substitution').run()
    button(first, 'Generate a random key').click().run()
    assert len(set(first.text_input(key='alphabet').value)) == 26
    first.text_area(key='message').set_value('private session message')
    button(first, 'Encrypt message').click().run()
    second = app()
    assert second.text_area(key='message').value == ''
    assert not second.code
    assert not second.session_state['alphabet']

