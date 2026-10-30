# CipherCraft

**Educational classical-cipher toolkit** with a Tkinter desktop GUI, interactive
CLI, file processing, and heuristic ciphertext analysis. Classical ciphers are
not secure for protecting sensitive information.

## Supported ciphers

- Caesar (shift)
- Vigenère / polyalphabetic (keyword)
- Monoalphabetic substitution (26-letter permutation)
- Columnar transposition (keyword or zero-based column indices)
- Rail Fence (rail count)
- Affine (coprime multiplier and shift)

For columnar transposition and Rail Fence, encryption removes whitespace.
Columnar transposition pads with `X` to a whole column; decrypting cannot
reliably tell padding from a real trailing `X`. Fixes made in the modernization
branch change outputs compared with the old faulty transposition and Rail
Fence implementations. **Previously encrypted messages may need legacy
decoding.** Preserve old ciphertext and keys until compatibility is resolved.

The analyzer suggests keys for Caesar, Vigenère, Affine (all 312 valid keys),
and Rail Fence (2–20 rails). Vigenère analysis needs at least 20 ASCII letters
and considers keywords up to 20 letters. The “AI” label means classical statistical techniques:
it does **not** call an LLM or remote AI API. Results are estimates, not
guaranteed successful decryptions. Relative scores compare the displayed guesses;
they are not probabilities of correct decryption. GUI analysis runs in the
background, and changing the input or cipher discards obsolete suggestions.

## Run from source

Requires Python 3.10+; the GUI additionally requires Tkinter:

```bash
git clone https://github.com/life423/polyalphabetic-and-caesar_cipher.git
cd polyalphabetic-and-caesar_cipher
python3 run.py                # desktop GUI
python3 run.py --cli          # interactive CLI
python3 -m src.ui.cli        # same interactive CLI
```

On Windows, use `python` instead of `python3` where appropriate.
On macOS, some Homebrew/pyenv Python installations require a matching
`python-tk@X.Y` package before the GUI will start. A headless or missing-Tk
environment can use `--cli` without Tkinter.

For editable installation and optional developer dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest tests/ -q
```

## CLI workflow

The CLI is **interactive**, not a flag-based batch CLI. It prompts for:

1. Encryption (`e`) or decryption (`d`).
2. Cipher (`c`, `p`, `s`, `t`, `r`, `a`).
3. Text (`1`) or file (`2`) input.
4. Text or file paths, then the cipher key.

Example (`python3 run.py --cli`):

```text
Choose operation (e=encrypt, d=decrypt): e
Choose cipher type: c
Input source: (1=text, 2=file): 1
Enter text: Hello, World!
Enter shift value (0-25; 0 leaves text unchanged): 3
Result: Khoor, Zruog!
```

**File safety:** Source files are never bulk-deleted at startup. Explicit
“delete input file after processing” is still available for file operations;
leave that option off unless you want the source removed. Input and output
must not refer to the same file, including through symlinks or hard links.
Output is written to a temporary file beside the destination and replaces the
destination only after all transforms and writes succeed. Source deletion
requires explicit successful completion; failures keep the source.

Files are UTF-8 and processed one line at a time, including resetting Vigenère
keywords at line boundaries. Line endings are preserved outside the cipher
transform so Rail Fence and columnar-transposition ciphertext lines stay
independent and can be decrypted again. Columnar padding applies to each line.
Old multiline transposition files whose ciphertext boundaries were already lost
cannot be repaired automatically; preserve their original files and keys.
Vigenère and Rail Fence file analysis uses the longest letter-bearing line,
since combining independently encrypted lines would give incorrect key suggestions.

## Python API

```python
from src.services.cipher_service import CipherService

service = CipherService()
encrypted = service.encrypt_caesar("Hello, World!", 3)
assert service.decrypt_caesar(encrypted, 3) == "Hello, World!"

suggestions = service.analyze_caesar_encryption(encrypted)
```

## Structure

```text
run.py                       source GUI/CLI launcher
gui.py                       minimal GUI packaging entry point
src/core/ciphers.py          classical cipher algorithms
src/ai/analyzer.py           statistical analyzer
src/services/cipher_service.py  application services
src/services/file_service.py    file handling
src/ui/cli.py                interactive CLI
src/ui/gui.py                Tkinter GUI
tests/                       regression and integration tests
.github/workflows/python-app.yml  tests and builds
```

Application entry points installed via packaging are `cipher_tool` (CLI) and
`cipher_gui` (GUI). `gui.py` remains as the PyInstaller GUI stub; older
multi-stage launchers and unused framework classes have been removed.

## CI/CD and downloads

Pull requests test against Python 3.10, 3.12, and 3.13 on Linux, Windows,
and macOS, then package Windows and macOS desktop executables. CI launches
the packaged CLI to verify a known cipher result. When a version changes and a commit lands on main, GitHub Actions publishes
a new release with permanent Windows and macOS download links:

- [Actions](https://github.com/life423/polyalphabetic-and-caesar_cipher/actions)
- [Latest release](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest)
- [Windows app — CipherCraft.exe](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest/download/CipherCraft.exe)
- [macOS ZIP](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest/download/ciphercraft-macos.zip)
- [Optional Windows ZIP with CLI](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest/download/ciphercraft-windows.zip)

**Windows:** Download `CipherCraft.exe` and double-click it to open the app.
No ZIP extraction, Python installation, or command prompt is needed. The
optional ZIP includes the command-line version as well.

Generated `dist/` binaries are intentionally **not kept in Git**.
CI checks actual Tk widget startup, operations and layout under a virtual
Linux display, along with packaged CLI smoke tests on Windows and macOS.
Interactive QA on actual Windows and macOS desktops is still recommended.
The macOS build is not Apple notarized; users may need to approve it under
System Settings → Privacy & Security after the first launch attempt.

## Security note

These are historical, educational ciphers, **not modern encryption**.
Do not use them for passwords, secrets, personal data, or confidential files.
