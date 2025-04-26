#!/usr/bin/env python3
"""
CipherCraft Launcher - Main entry point for the application.

This is a unified launcher for CipherCraft that ensures proper
Python module resolution regardless of the working directory.
"""

import os
import sys
import platform

def main():
    """Ensure proper module resolution and launch the application."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the script directory to Python path to ensure imports work
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        
    # Print welcome message
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
        
    print("=" * 60)
    print("                 CIPHERCRAFT LAUNCHER")
    print("=" * 60)
    print("Starting application...")
    print("=" * 60)
    print()
    
    try:
        # Import and run the main launcher script
        from scripts.run_cipher_app import main as run_app
        run_app()
    except ImportError as e:
        print(f"Error: Could not import the application module: {e}")
        print("\nPlease make sure:")
        print("1. You are running this script from the project directory")
        print("2. All required dependencies are installed")
        print("\nTry running: pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
