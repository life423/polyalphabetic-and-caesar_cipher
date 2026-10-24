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

The analyzer performs statistical scoring and key suggestions for Caesar and
Vigenère ciphertext. The “AI” label means classical statistical techniques:
it does **not** call an LLM or remote AI API. Results are estimates, not
guaranteed successful decryptions.

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
Enter shift value (1-25): 3
Result: Khoor, Zruog!
```

**File safety:** Source files are never bulk-deleted at startup. Explicit
“delete input file after processing” is still available for file operations;
leave that option off unless you want the source removed. Input and output
must not resolve to the same path. The transform finishes before writing an
output file, to avoid destroying existing output on invalid cipher keys.
File processing preserves the historical behavior of processing each line
independently, including resetting Vigenère keywords at line boundaries.

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
- [macOS ZIP](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest/download/ciphercraft-macos.zip)
- [Windows ZIP](https://github.com/life423/polyalphabetic-and-caesar_cipher/releases/latest/download/ciphercraft-windows.zip)

Generated `dist/` binaries are intentionally **not kept in Git**.
CI checks actual Tk widget startup, operations and layout under a virtual
Linux display, along with packaged CLI smoke tests on Windows and macOS.
Interactive QA on actual Windows and macOS desktops is still recommended.
The macOS build is not Apple notarized; users may need to approve it under
System Settings → Privacy & Security after the first launch attempt.

## Security note

These are historical, educational ciphers, **not modern encryption**.
Do not use them for passwords, secrets, personal data, or confidential files.
