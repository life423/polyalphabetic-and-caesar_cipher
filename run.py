#!/usr/bin/env python3
"""
Unified Launcher for CipherCraft - Cryptography Toolkit

A single, simple entry point for the CipherCraft application.
Provides access to both the GUI and command-line interfaces.
"""

import sys
import tkinter as tk
from src.ui.gui import CipherGUI
from src.services.cipher_service import CipherService


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
        _ = CipherService()  # Initialize but don't need the reference
        print("\nWelcome to CipherCraft CLI")
        print("=" * 40)
        
        _ = input("Choose operation (e=encrypt, d=decrypt, a=analyze): ")
        # Rest of CLI functionality would go here
        # For simplicity, just exit for now
        print("Please run 'python -m src.ui.cli' for full CLI functionality")


if __name__ == "__main__":
    main()
