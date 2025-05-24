# CipherCraft Refactoring Guide

This guide provides step-by-step instructions for refactoring the CipherCraft codebase to address the issues identified in the audit.

## 1. Fix Incomplete GUI Implementation

The GUI implementation in `src/ui/gui.py` is incomplete. The file is truncated at the `_process_text` method where it's handling the polyalphabetic cipher case.

### Step 1.1: Complete the `_process_text` method

```python
def _process_text(self):
    """
    Process the text/file based on the selected cipher and options.

    This method gathers all user inputs from the UI, validates them,
    and then delegates the actual processing to appropriate service methods.
    """
    # Clear previous results
    self.result_text.delete('1.0', tk.END)
    
    # Get user inputs
    cipher_type = self.cipher_var.get()
    is_encrypt = self.action_var.get() == 'e'  # True for encrypt, False for decrypt
    input_text = self.input_entry.get()
    output_file = self.output_entry.get()
    delete_input = self.delete_input_var.get()
    
    # Validate input text
    if not input_text:
        self._display_error("Please enter text or select a file for input.")
        return
    
    # Determine if using file or direct text input
    is_file_input = os.path.isfile(input_text)
    
    try:
        # Process with appropriate cipher based on user selections
        if cipher_type == 'c':  # Caesar cipher
            key = self.caesar_key_entry.get()
            if not key:
                self._display_error("Please enter a shift value.")
                return
            self._process_caesar_cipher(
                is_encrypt, key, input_text, output_file, 
                is_file_input, delete_input
            )
        elif cipher_type == 'p':  # Polyalphabetic cipher
            key = self.poly_key_entry.get()
            if not key:
                self._display_error("Please enter a keyword.")
                return
            self._process_polyalphabetic_cipher(
                is_encrypt, key, input_text, output_file, 
                is_file_input, delete_input
            )
        elif cipher_type == 's':  # Substitution cipher
            key = self.sub_key_entry.get()
            if not key or len(key) != 26:
                self._display_error("Substitution key must be exactly 26 characters long.")
                return
            self._process_substitution_cipher(
                is_encrypt, key, input_text, output_file, 
                is_file_input, delete_input
            )
        elif cipher_type == 't':  # Transposition cipher
            key = self.trans_key_entry.get()
            if not key:
                self._display_error("Please enter a transposition key.")
                return
            self._process_transposition_cipher(
                is_encrypt, key, input_text, output_file, 
                is_file_input, delete_input
            )
        elif cipher_type == 'r':  # Rail Fence cipher
            key = self.rail_key_entry.get()
            if not key:
                self._display_error("Please enter the number of rails.")
                return
            self._process_rail_fence_cipher(
                is_encrypt, key, input_text, output_file, 
                is_file_input, delete_input
            )
        elif cipher_type == 'a':  # Affine cipher
            a_value = self.affine_a_entry.get()
            b_value = self.affine_b_entry.get()
            if not a_value or not b_value:
                self._display_error("Please enter both 'a' and 'b' values.")
                return
            self._process_affine_cipher(
                is_encrypt, (a_value, b_value), input_text, output_file, 
                is_file_input, delete_input
            )
    except Exception as e:
        self._display_error(str(e))
```

### Step 1.2: Add the missing processing methods

Add the following methods to the `CipherGUI` class:

1. `_process_caesar_cipher`
2. `_process_polyalphabetic_cipher`
3. `_process_substitution_cipher`
4. `_process_transposition_cipher`
5. `_process_rail_fence_cipher`
6. `_process_affine_cipher`
7. `_analyze_text`
8. `_apply_suggested_key`

Each method should follow the same pattern:
- Validate inputs
- Process file or direct text input
- Display results or errors

## 2. Consolidate Entry Points

### Step 2.1: Update `run.py` to be the main entry point

Ensure `run.py` can handle both GUI and CLI modes:

```python
#!/usr/bin/env python3
"""
CipherCraft - Advanced Cryptography Toolkit

A single, simple entry point for the CipherCraft application.
Provides access to both the GUI and command-line interfaces.
"""

import sys
import tkinter as tk
from src.ui.gui import CipherGUI

def main():
    """Main function to start the application."""
    # Print welcome message
    print("=" * 60)
    print("                    CIPHERCRAFT")
    print("=" * 60)
    print("A comprehensive toolkit for encryption and decryption")
    print("with multiple cipher algorithms and AI-driven analysis.")
    print("=" * 60)
    print()
    
    # Check for command-line arguments - if present, run CLI mode
    if len(sys.argv) > 1:
        # Import CLI functionality
        from src.ui.cli import main as cli_main
        cli_main()
        return
    
    # If no arguments, start the GUI
    print("Starting CipherCraft GUI...")
    try:
        # Initialize the GUI
        root = tk.Tk()
        _ = CipherGUI(root)  # Initialize but don't need the reference
        root.mainloop()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        print("Falling back to interactive CLI mode...")
        
        # If GUI fails, offer CLI mode as a fallback
        from src.services.cipher_service import CipherService
        _ = CipherService()  # Initialize but don't need the reference
        print("\nWelcome to CipherCraft CLI")
        print("=" * 40)
        
        from src.ui.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
```

### Step 2.2: Update batch files

Update all batch files to use `run.py` as the entry point:

```batch
@echo off
title CipherCraft
echo ================================================
echo             STARTING CIPHERCRAFT 
echo ================================================
echo.

:: Set working directory to where the batch file is located
cd /d "%~dp0"

:: Try to find Python - check multiple possible commands
set PYTHON_CMD=none
set PYTHON_FOUND=false

:: Try py launcher first (preferred on Windows)
py --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=py
    set PYTHON_FOUND=true
    goto :run_app
)

:: Try python command
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python
    set PYTHON_FOUND=true
    goto :run_app
)

:: Try python3 command
python3 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PYTHON_CMD=python3
    set PYTHON_FOUND=true
    goto :run_app
)

:: No Python found
echo Error: Python is not installed or not in the PATH.
echo.
echo Please install Python 3.7 or later from https://www.python.org/downloads/
echo After installing, ensure Python is added to your PATH.
echo.
pause
exit /b 1

:run_app
:: Run the Python launcher script
%PYTHON_CMD% run.py %*

:: If there was an error, pause so the user can see the message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error occurred. Exit code: %ERRORLEVEL%
    echo.
    pause > nul
)
```

### Step 2.3: Remove redundant entry points

Delete or mark as deprecated:
- `gui.py`
- `cipher_launcher.py`

## 3. Standardize Naming

### Step 3.1: Update all references to "Cipher Tools" to "CipherCraft"

Search for "Cipher Tools" in the codebase and replace with "CipherCraft":

- Update window titles
- Update welcome messages
- Update documentation
- Update file names and comments

### Step 3.2: Update package name in `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="ciphercraft",
    version="1.0.0",
    description="A comprehensive cipher encryption/decryption tool with AI analysis",
    author="CipherCraft Team",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.3.1",
        "flake8>=6.0.0",
        "pyinstaller>=5.9.0",
        "pyyaml>=6.0.1",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "ciphercraft=src.ui.cli:main",
        ],
        "gui_scripts": [
            "ciphercraft_gui=src.ui.gui:main",
        ],
    },
)
```

## 4. Fix Backward Compatibility Issues

### Step 4.1: Remove redundant backward compatibility methods in `src/ui/cli.py`

Replace the `CipherCLI` class with direct usage of `CipherService`:

```python
"""
CipherCraft - Command Line Interface module.

This module provides a command-line interface for encryption and decryption
operations, making use of the service layer to handle business logic.
"""

from src.services.cipher_service import CipherService

def main():
    """
    Command-line interface for CipherCraft.
    Run this function when the script is executed directly.
    """
    service = CipherService()
    
    print("Welcome to CipherCraft CLI")
    print("==============================")
    
    # Ask if user wants to clean up .txt files
    cleanup_confirm = input("Clean .txt files before proceeding? (yes/no): ")
    if cleanup_confirm.lower() == 'yes':
        deleted_files = service.clean_txt_files()
        if deleted_files:
            print(f"Deleted files: {', '.join(deleted_files)}")
        else:
            print("No .txt files found to delete.")

    # Get encryption or decryption choice
    choice = input("Choose operation (e=encrypt, d=decrypt): ")
    if choice.lower() not in {'e', 'd'}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")
        return
    
    encrypt = choice.lower() == 'e'
    
    # Continue with the rest of the CLI implementation...
```

## 5. Improve Error Handling

### Step 5.1: Add proper exception handling in all user-facing methods

Example for the GUI:

```python
def _process_caesar_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """Process text using the Caesar cipher."""
    try:
        # Convert shift to integer
        shift = int(key)
        
        # Validate shift value
        if shift < 1 or shift > 25:
            self._display_error("Shift value must be between 1 and 25.")
            return
            
        # Process text or file
        # ...
    except ValueError:
        self._display_error("Invalid shift value. Please enter a number between 1 and 25.")
    except FileNotFoundError:
        self._display_error(f"File not found: {input_text}")
    except PermissionError:
        self._display_error(f"Permission denied when accessing file: {input_text}")
    except Exception as e:
        self._display_error(f"An unexpected error occurred: {str(e)}")
```

## 6. Enhance Documentation

### Step 6.1: Update docstrings to be more comprehensive

Example:

```python
def encrypt_caesar(self, text, shift):
    """
    Encrypt text using the Caesar cipher.
    
    The Caesar cipher is a substitution cipher where each letter in the plaintext
    is shifted a certain number of places down the alphabet. For example, with a
    shift of 1, 'A' would be replaced by 'B', 'B' would become 'C', and so on.
    
    Args:
        text (str): The plaintext to encrypt
        shift (int): The number of positions to shift characters (1-25)
            
    Returns:
        str: The encrypted text
        
    Raises:
        ValueError: If shift is not an integer or is outside the valid range
        
    Example:
        >>> service = CipherService()
        >>> service.encrypt_caesar("Hello", 3)
        'Khoor'
    """
    return CaesarCipher.transform(text, shift, encrypt=True)
```

### Step 6.2: Add a user guide

Create a `docs/user_guide.md` file with comprehensive usage instructions.

## 7. Refactor Redundant Code

### Step 7.1: Use inheritance and composition more effectively

Example:

```python
class BaseCipherProcessor:
    """Base class for cipher processing in the GUI."""
    
    def __init__(self, cipher_service):
        self.cipher_service = cipher_service
        
    def process_file(self, input_path, output_path, cipher_func, delete_input=False):
        """Process a file through the specified cipher function."""
        return self.cipher_service.process_file_with_cipher(
            input_path, output_path, cipher_func, delete_input
        )
        
    def validate_file_paths(self, input_path, output_path):
        """Validate input and output file paths."""
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        if not output_path:
            raise ValueError("Output file path cannot be empty")
```

## 8. Improve Test Coverage

### Step 8.1: Add tests for edge cases

Example:

```python
def test_caesar_cipher_edge_cases(self):
    """Test edge cases for Caesar cipher."""
    # Test with empty string
    self.assertEqual(CaesarCipher.transform("", 5, encrypt=True), "")
    
    # Test with non-alphabetic characters
    self.assertEqual(CaesarCipher.transform("123!@#", 5, encrypt=True), "123!@#")
    
    # Test with very large shift value (should wrap around)
    self.assertEqual(
        CaesarCipher.transform("abc", 27, encrypt=True),
        CaesarCipher.transform("abc", 1, encrypt=True)
    )
    
    # Test with negative shift value
    self.assertEqual(
        CaesarCipher.transform("abc", -1, encrypt=True),
        CaesarCipher.transform("abc", 25, encrypt=True)
    )
```

### Step 8.2: Add integration tests

Example:

```python
def test_end_to_end_caesar(self):
    """Test end-to-end Caesar cipher encryption and decryption with file I/O."""
    # Create a temporary file with test content
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_in:
        temp_in.write("Hello, World!")
        input_path = temp_in.name
    
    # Create a temporary file for output
    with tempfile.NamedTemporaryFile(delete=False) as temp_out:
        output_path = temp_out.name
    
    try:
        # Initialize the service
        service = CipherService()
        
        # Define the cipher function
        def encrypt_func(content):
            return service.encrypt_caesar(content, 3)
        
        # Process the file
        service.process_file_with_cipher(input_path, output_path, encrypt_func)
        
        # Read the output file
        with open(output_path, 'r') as f:
            encrypted = f.read()
        
        # Verify the encryption
        self.assertEqual(encrypted, "Khoor, Zruog!")
        
        # Now decrypt back
        def decrypt_func(content):
            return service.decrypt_caesar(content, 3)
        
        # Create another temporary file for the decrypted output
        with tempfile.NamedTemporaryFile(delete=False) as temp_decrypted:
            decrypted_path = temp_decrypted.name
        
        # Process the encrypted file
        service.process_file_with_cipher(output_path, decrypted_path, decrypt_func)
        
        # Read the decrypted file
        with open(decrypted_path, 'r') as f:
            decrypted = f.read()
        
        # Verify the decryption
        self.assertEqual(decrypted, "Hello, World!")
        
    finally:
        # Clean up temporary files
        for path in [input_path, output_path, decrypted_path]:
            if os.path.exists(path):
                os.unlink(path)
```

## Conclusion

By following this refactoring guide, you'll address the major issues identified in the codebase audit and significantly improve the quality and maintainability of the CipherCraft application.