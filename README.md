# Cipher Tools

A comprehensive toolkit for encryption and decryption using multiple cipher algorithms with AI-driven analysis capabilities.

## Features

- Multiple cipher implementations:
  - Caesar Cipher
  - Polyalphabetic (Vigenère) Cipher
  - Substitution Cipher
  - Transposition Cipher
  - Rail Fence Cipher
  - Affine Cipher

- AI-driven analysis tools:
  - Encryption key detection
  - Automated cryptanalysis for Caesar and Polyalphabetic ciphers
  - Letter frequency analysis
  - N-gram scoring
  - Known-plaintext analysis

- User interfaces:
  - Command-line interface
  - Graphical user interface
  - File-based operations

## Installation

### From Source

```bash
git clone https://github.com/yourusername/polyalphabetic-and-caesar_cipher.git
cd polyalphabetic-and-caesar_cipher
pip install -r requirements.txt
python setup.py install
```

### Using the Executables

Download the latest release package (`cipher_tools_windows.zip`) from the [Releases](https://github.com/yourusername/polyalphabetic-and-caesar_cipher/releases) page. The package includes:

- `cipher_tool.exe` - Command-line interface
- `cipher_gui.exe` - Graphical user interface
- `run_cipher_app.bat` - Unified launcher script

Simply extract the ZIP file and run either:
- `run_cipher_app.bat` for the unified launcher
- `cipher_gui.exe` to directly launch the GUI
- `cipher_tool.exe` for command-line usage

## Usage

### Using the New Unified Launcher (Recommended)

The easiest way to run the application is using the unified launcher:

#### Windows
Simply double-click the `scripts/run_cipher_app.bat` file or run:

```bash
python scripts/run_cipher_app.py
```

This will open a menu where you can choose between:
- Graphical User Interface
- Interactive Command Line Interface
- Advanced CLI (with arguments)
- Build Standalone Executable

### Traditional Command Line Interface

If you prefer the traditional command line approach:

```bash
# Encrypt a message using Caesar cipher
python src/ui/cli.py -c caesar -e -s 3 -t "Hello, World!"

# Decrypt a message using Polyalphabetic cipher
python src/ui/cli.py -c poly -d -k "KEY" -t "Rijvs, Uyvjn!"

# Analyze encrypted text to guess the key
python src/ui/cli.py -c caesar -a -t "Khoor, Zruog!"
```

### Direct GUI Launch

You can also launch the GUI directly:

```bash
python src/ui/gui.py
```

## Developer Guide

### Project Structure

The project has been reorganized into a more modular structure:

```
polyalphabetic-and-caesar_cipher/
├── scripts/                 # Scripts for running and building
│   ├── build_exe.py         # Build script for creating executables
│   ├── run_cipher_app.py    # Main launcher script
│   └── run_cipher_app.bat   # Windows batch launcher
├── src/                     # Source code
│   ├── ai/                  # AI and analysis modules
│   │   └── analyzer.py      # AI-driven text analysis
│   ├── core/                # Core cipher implementations
│   │   ├── base.py          # Base classes for ciphers
│   │   └── ciphers.py       # Cipher algorithm implementations
│   ├── services/            # Service layer
│   │   ├── cipher_service.py # Coordinates cipher operations
│   │   └── file_service.py   # File handling utilities
│   └── ui/                  # User interfaces
│       ├── cli.py           # Command-line interface
│       └── gui.py           # Graphical user interface
├── tests/                   # Test suite
├── requirements.txt         # Dependencies
└── setup.py                 # Installation script
```

### Running Tests

```bash
pytest tests/
```

### Building the Executable

```bash
python scripts/build_exe.py
```

This will create a standalone executable in the `dist/` directory.

### CI/CD Pipeline

This project uses GitHub Actions for continuous integration and delivery:

1. On every push or pull request to main/master branch:
   - Run linting checks with flake8
   - Execute test suite with pytest
   - Validate the codebase quality

2. On push to main/master branch:
   - Automatically builds both CLI and GUI executables
   - Packages executables and launcher into a zip file
   - Creates a new GitHub release with the version from setup.py
   - Uploads the package as a release asset
   - Makes the release available for download

The workflow configuration is defined in `.github/workflows/python-app.yml`.

## Cipher Implementations

### Caesar Cipher

A substitution cipher where each letter is shifted by a fixed number of positions.

```python
from src.core.ciphers import CaesarCipher

# Encrypt
encrypted = CaesarCipher.transform("Hello", 3, encrypt=True)  # "Khoor"

# Decrypt
decrypted = CaesarCipher.transform("Khoor", 3, encrypt=False)  # "Hello"
```

### Polyalphabetic Cipher

Uses a keyword to determine the shift for each letter in the plaintext.

```python
from src.core.ciphers import PolyalphabeticCipher

# Encrypt
encrypted = PolyalphabeticCipher.transform("Hello", "KEY", encrypt=True)

# Decrypt
decrypted = PolyalphabeticCipher.transform(encrypted, "KEY", encrypt=False)
```

### Substitution Cipher

Replaces each letter with another letter from a shuffled alphabet.

```python
from src.core.ciphers import SubstitutionCipher

# Generate a random key
key = SubstitutionCipher.generate_key()

# Encrypt
encrypted = SubstitutionCipher.transform("Hello", key, encrypt=True)

# Decrypt
decrypted = SubstitutionCipher.transform(encrypted, key, encrypt=False)
```

### Transposition Cipher

Rearranges the letters of the plaintext according to a key.

```python
from src.core.ciphers import TranspositionCipher

# Encrypt using a string key
encrypted = TranspositionCipher.transform("Hello World", "KEY", encrypt=True)

# Decrypt
decrypted = TranspositionCipher.transform(encrypted, "KEY", encrypt=False)
```

### Rail Fence Cipher

Writes the plaintext in a zigzag pattern across multiple rows and reads off by row.

```python
from src.core.ciphers import RailFenceCipher

# Encrypt with 3 rails
encrypted = RailFenceCipher.transform("Hello World", 3, encrypt=True)

# Decrypt
decrypted = RailFenceCipher.transform(encrypted, 3, encrypt=False)
```

### Affine Cipher

Uses a mathematical function to encrypt/decrypt text.

```python
from src.core.ciphers import AffineCipher

# Encrypt using key pair (a, b)
encrypted = AffineCipher.transform("Hello", (5, 8), encrypt=True)

# Decrypt
decrypted = AffineCipher.transform(encrypted, (5, 8), encrypt=False)
```

## AI Analysis

The AI analyzer can be used to detect encryption methods and guess keys:

```python
from src.ai.analyzer import CipherAnalyzer

# Analyze Caesar-encrypted text
results = CipherAnalyzer.analyze_caesar(encrypted_text)
for r in results:
    print(f"Shift: {r['shift']}, Confidence: {r['confidence']}%, Sample: {r['sample']}")

# Analyze Polyalphabetic-encrypted text
results = CipherAnalyzer.analyze_polyalphabetic(encrypted_text)
for r in results:
    print(f"Keyword: {r['keyword']}, Confidence: {r['confidence']}%, Sample: {r['sample']}")
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
