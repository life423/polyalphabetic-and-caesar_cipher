"""Exercise analysis delivery, invalidation, and recovery without a display."""
from collections import deque
from threading import Event, get_ident
from time import monotonic, sleep
from types import SimpleNamespace

import pytest

pytest.importorskip('tkinter')
from src.ui.gui import CipherGUI
from src.services.cipher_service import CipherService


class Widget:
    def __init__(self, value=''):
        self.value = value
        self.options = {}

    def get(self, *_):
        return self.value

    def set(self, value):
        self.value = value

    def delete(self, *_):
        self.value = ''

    def insert(self, _, value):
        self.value += str(value)

    def configure(self, **options):
        self.options.update(options)

    config = configure


class Scheduler:
    def __init__(self):
        self.callbacks = deque()

    def after(self, _, callback):
        self.callbacks.append(callback)

    def step(self):
        if self.callbacks:
            self.callbacks.popleft()()


def app_for(cipher, text):
    app = CipherGUI.__new__(CipherGUI)
    app.root = Scheduler()
    app.cipher_service = CipherService()
    app._analysis_generation = 0
    app._analysis_running = False
    app.analysis_results = []
    app.cipher_var = Widget(cipher)
    app.input_mode_var = Widget('text')
    app.input_entry = Widget(text)
    app.analysis_result = Widget()
    app.apply_button = Widget()
    app.analyze_button = Widget()
    app.result_text = Widget()
    app.action_var = Widget('e')
    app.output_entry = Widget()
    app.delete_input_var = Widget(False)
    app.caesar_key_entry = Widget()
    app.poly_key_entry = Widget()
    app.results_frame, app.analysis_frame = object(), object()
    app.selected_tab = None

    def select(tab):
        app.selected_tab = tab

    app.output_tabs = SimpleNamespace(select=select)
    return app


def finish(app):
    deadline = monotonic() + 5
    while app._analysis_running and monotonic() < deadline:
        app.root.step()
        sleep(0.001)
    assert not app._analysis_running, 'Analysis failed to finish'


def test_short_vigenere_shows_explanation_without_applicable_key():
    app = app_for('p', 'ABC')
    app._analyze_text()
    finish(app)
    assert 'at least 20 ASCII letters' in app.analysis_result.value
    assert app.analysis_results == []
    assert app.apply_button.options['state'] == 'disabled'
    app._apply_suggested_key()
    assert app.poly_key_entry.get() == ''


def test_vigenere_encryption_requires_an_entered_keyword():
    app = app_for('p', 'Plaintext to encrypt')
    app._process_text()
    assert app.result_text.value == 'Error: Please enter a keyword.'
    assert app.selected_tab is app.results_frame
    assert app.input_entry.value == 'Plaintext to encrypt'


def test_caesar_zero_shift_can_be_analyzed_applied_and_processed(monkeypatch):
    text = 'The quick brown fox jumps over the lazy dog and runs back home.'
    app = app_for('c', text)
    app._analyze_text()
    finish(app)
    assert app.analysis_results[0]['shift'] == 0
    assert 'not probabilities' in app.analysis_result.value
    monkeypatch.setattr('src.ui.gui.messagebox.showinfo', lambda *a, **kw: None)
    app._apply_suggested_key()
    assert app.caesar_key_entry.get() == '0'
    app._process_text()
    assert app.action_var.get() == 'd'
    assert app.result_text.value == text


@pytest.mark.parametrize('change', ['input', 'mode', 'cipher'])
def test_analysis_runs_off_ui_thread_and_discards_stale_results(change):
    app = app_for('c', 'Khoor')
    entered, release = Event(), Event()
    worker_threads = []

    def slow_analysis(_):
        worker_threads.append(get_ident())
        entered.set()
        assert release.wait(3)
        return [{'shift': 3, 'sample': 'Hello', 'confidence': 100}]

    app.cipher_service.analyze_caesar_encryption = slow_analysis
    try:
        app._analyze_text()
        assert entered.wait(2)
        assert app._analysis_running
        assert app.analyze_button.options['state'] == 'disabled'
        heartbeat = []
        app.root.after(0, lambda: heartbeat.append(True))
        app.root.step()
        app.root.step()
        assert heartbeat == [True], 'The UI scheduler was blocked by analysis'
        assert len(worker_threads) == 1
        assert worker_threads[0] != get_ident()
        if change == 'input':
            app.input_entry.set('new ciphertext')
        elif change == 'mode':
            app.input_mode_var.set('file')
        else:
            app.cipher_var.set('s')
        app._invalidate_analysis()
    finally:
        release.set()
    finish(app)
    assert app.analysis_results == []
    assert app.analysis_result.value == ''
    assert app.apply_button.options['state'] == 'disabled'
    assert app.analyze_button.options['state'] == ('disabled' if change == 'cipher' else 'normal')


def test_analysis_error_is_visible_and_allows_retry():
    app = app_for('c', 'Khoor')

    def fail(_):
        raise OSError('Could not read ciphertext')

    app.cipher_service.analyze_caesar_encryption = fail
    app._analyze_text()
    finish(app)
    assert app.selected_tab is app.results_frame
    assert 'Could not read ciphertext' in app.result_text.value
    assert app.analyze_button.options['state'] == 'normal'
    app.cipher_service = CipherService()
    app._analyze_text()
    finish(app)
    assert app.analysis_results


def test_changed_input_clears_completed_suggestions():
    app = app_for('c', 'Khoor')
    app._analyze_text()
    finish(app)
    assert app.analysis_results
    app.input_entry.set('different text')
    app._invalidate_analysis()
    assert not app.analysis_results
    assert app.apply_button.options['state'] == 'disabled'


@pytest.mark.parametrize('cipher,method', [
    ('p', 'analyze_polyalphabetic_encryption'), ('r', 'analyze_rail_fence_encryption'),
])
def test_file_analysis_does_not_merge_independent_lines(tmp_path, cipher, method):
    path = tmp_path / 'cipher.txt'
    longest = 'ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ'
    path.write_text('ABC\n' + longest + '\nXYZ\n', encoding='utf-8')
    app = app_for(cipher, str(path))
    app.input_mode_var.set('file')
    seen = []

    def analyze(text):
        seen.append(text)
        return []

    setattr(app.cipher_service, method, analyze)
    app._analyze_text()
    finish(app)
    assert seen == [longest]
    assert 'longest letter-bearing line' in app.analysis_result.value
