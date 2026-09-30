# CipherCraft: Advanced Cryptography Toolkit

[![Build Status](https://github.com/yourusername/ciphercraft/workflows/Python%20Application/badge.svg)](https://github.com/yourusername/ciphercraft/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🔐 Overview

CipherCraft is a comprehensive cryptography toolkit that demonstrates advanced cipher implementation and cryptanalysis techniques. This project combines classical cryptographic algorithms with modern software engineering practices and AI-driven analysis capabilities.

![CipherCraft GUI](https://via.placeholder.com/800x450?text=CipherCraft+GUI+Screenshot)

## ✨ Key Features

### Multiple Cipher Implementations

- **Caesar Cipher**: Shift-based substitution with customizable offset
- **Polyalphabetic (Vigenère) Cipher**: Keyword-based shifting for enhanced security
- **Substitution Cipher**: Full alphabet substitution with random key generation
- **Transposition Cipher**: Column-based scrambling using keyword or numeric ordering
- **Rail Fence Cipher**: Zigzag pattern encryption with variable rail count
- **Affine Cipher**: Mathematical transformation using modular arithmetic

### AI-Driven Cryptanalysis

- **Automated Key Detection**: Statistical analysis to determine encryption methods
- **Frequency Analysis**: Letter distribution examination against language patterns
- **N-gram Scoring**: Analysis of character sequences for linguistic fingerprints
- **Known-Plaintext Analysis**: Decipher keys when portions of plaintext are known
- **Confidence Scoring**: Probabilistic ranking of decryption attempts

### Multiple User Interfaces

- **Graphical User Interface (GUI)**: Intuitive Tkinter-based application with:
  - Real-time analysis visualization
  - Cipher selection and configuration
  - File input/output capabilities
  - Key generation tools
  - Automated cryptanalysis results

- **Command Line Interface (CLI)**: Feature-rich terminal interface supporting:
  - Batch processing operations
  - Pipeline integration
  - Scriptable encryption/decryption
  - Direct text or file input/output

### Advanced Software Architecture

- **Clean Architecture**: Separation of concerns with core, service, and UI layers
- **Factory Method Pattern**: For cipher algorithm instantiation
- **Strategy Pattern**: Dynamic cipher algorithm selection
- **Facade Pattern**: Simplified service layer interface
- **Command Pattern**: For operation execution

## 🔧 Installation

### From Source

CipherCraft only needs the Python standard library plus **Tkinter** for the GUI. The packages in `requirements.txt` (pytest, flake8, pyinstaller, pyyaml) are for testing and building executables.

#### macOS prerequisite: a Python with Tk

Homebrew and pyenv builds of Python don't include Tkinter by default. If you see `ModuleNotFoundError: No module named '_tkinter'`, install the Tk add-on that matches your Python version:

```bash
python3 --version                  # e.g. Python 3.14.x
brew install python-tk@3.14        # match your major.minor version
python3 -c "import tkinter; print(tkinter.TkVersion)"   # should print 8.6 or 9.0
```

Avoid Apple's `/usr/bin/python3` for the GUI: it ships a deprecated Tk 8.5 that renders poorly on current macOS.

#### Setup

```bash
# Clone the repository
git clone https://github.com/life423/polyalphabetic-and-caesar_cipher.git
cd polyalphabetic-and-caesar_cipher

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dev/test/build tools (not needed just to run the app)
pip install -r requirements.txt
```

### Using Prebuilt Executables

Download the latest release package from the [Releases](https://github.com/yourusername/ciphercraft/releases) page:

- `cipher_tool.exe` - Unified application executable (includes both CLI and GUI)

## 📚 Usage Examples

### Starting the Application (Recommended)

```bash
# From the repo root, with the virtual environment active
python run.py        # launches the GUI
```

Without an active venv, use `python3` on macOS/Linux. On Windows you can also double-click `launch_gui.bat`.

If the window doesn't appear, look for the `Error starting GUI: ...` line in the terminal. It names the real cause (usually missing Tk; see Installation).

### Command Line Interface

The CLI is an interactive menu, not a flag-based tool. Start it either way (any argument to `run.py` switches it into CLI mode):

```bash
python -m src.ui.cli
python run.py --cli
```

It prompts for, in order:

1. **Clean .txt files?** **Warning:** `yes` deletes *every* `.txt` file in the current directory, including `requirements.txt` if you're in the repo root. Answer `no` unless you mean it.
2. **Operation:** `e` encrypt, `d` decrypt
3. **Cipher:** `c` Caesar, `p` Polyalphabetic (Vigenère), `s` Substitution, `t` Transposition, `r` Rail Fence, `a` Affine
4. **Input source:** `1` typed text, `2` file (then input/output paths, and whether to delete the input afterward)
5. **Key:** shift, keyword, 26-letter key, rail count, or affine `a`/`b`, depending on the cipher

Example session:

```text
Clean .txt files before proceeding? (yes/no): no
Choose operation (e=encrypt, d=decrypt): e
Choose cipher type: c
Input source: (1=text, 2=file): 1
Enter text: Hello, World!
Enter shift value (1-25): 3
Result: Khoor, Zruog!
```

### Python API

```python
from src.services.cipher_service import CipherService

# Initialize the service
cipher_service = CipherService()

# Caesar cipher
encrypted = cipher_service.encrypt_caesar("Hello, World!", 3)
decrypted = cipher_service.decrypt_caesar(encrypted, 3)

# Polyalphabetic cipher
encrypted = cipher_service.encrypt_polyalphabetic("Hello, World!", "KEY")
decrypted = cipher_service.decrypt_polyalphabetic(encrypted, "KEY")

# AI analysis
results = cipher_service.analyze_caesar_encryption("Khoor, Zruog!")
for result in results:
    print(f"Shift: {result['shift']}, Confidence: {result['confidence']}%")
```

## 🏛️ Architecture

CipherCraft follows a modular, layered architecture that separates concerns and provides clear boundaries between components:

```
ciphercraft/
├── src/
│   ├── core/         # Core cipher implementations
│   │   ├── base.py   # Abstract base classes
│   │   └── ciphers.py # Cipher algorithm implementations
│   ├── services/     # Business logic and coordination
│   │   ├── cipher_service.py # Service façade for operations
│   │   └── file_service.py   # File handling utilities
│   ├── ai/           # AI and analysis capabilities  
│   │   └── analyzer.py # Statistical analysis tools
│   └── ui/           # User interfaces
│       ├── cli.py    # Command-line interface
│       └── gui.py    # Graphical user interface
├── scripts/          # Utility scripts
├── tests/            # Comprehensive test suite
└── docs/             # Documentation
```

### Design Patterns

- **Service Layer Pattern**: Isolates business logic from UI and core implementations
- **Repository Pattern**: For file handling abstraction
- **Strategy Pattern**: For interchangeable cipher algorithms
- **Factory Method**: For cipher instantiation
- **Command Pattern**: For encapsulating operations

## 🧪 Testing and Quality Assurance

CipherCraft includes a comprehensive test suite using pytest, with:

- Unit tests for all cipher implementations
- Integration tests for service layer
- End-to-end tests for file operations
- Property-based testing for cryptographic properties

The CI/CD pipeline (GitHub Actions) ensures code quality by:
- Running automated tests on each push
- Enforcing code style with flake8
- Building executables for release
- Generating documentation

## 🔍 Implementation Details

### Caesar Cipher

```python
# Encryption
encrypted = CaesarCipher.transform("Hello", 3, encrypt=True)  # "Khoor"

# Decryption
decrypted = CaesarCipher.transform("Khoor", 3, encrypt=False)  # "Hello"
```

The Caesar cipher implementation handles proper wrapping of the alphabet and preserves case and non-alphabetic characters.

### AI Analysis Example

```python
# The analyzer uses sophisticated frequency analysis and language patterns
results = CipherAnalyzer.analyze_caesar(encrypted_text)

# Results include confidence scores and sample decryptions
for r in results:
    print(f"Shift: {r['shift']}, Confidence: {r['confidence']}%")
    print(f"Sample: {r['sample']}")
```

The AI analyzer uses:
- Letter frequency distribution compared to expected language patterns
- Chi-squared statistical analysis for goodness of fit
- N-gram analysis for language detection
- Word pattern matching against common word dictionaries

## 🌟 Applications and Use Cases

- **Educational Tool**: Learning cryptography principles and implementation
- **Security Training**: Demonstrating strengths and weaknesses of classical ciphers
- **CTF Competitions**: Cryptography challenge development and solving
- **Message Security**: Basic encryption for non-critical communication
- **Data Obfuscation**: Simple protection of configuration data

## 🛡️ Security Considerations

While CipherCraft implements classical ciphers with high-quality code, it's important to note:

- Classical ciphers are not suitable for modern security requirements
- These implementations are primarily for educational and demonstration purposes
- For production security needs, use established cryptographic libraries like:
  - OpenSSL
  - libsodium
  - Python's cryptography package

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*CipherCraft: Blend of classical cryptography with modern software engineering*
