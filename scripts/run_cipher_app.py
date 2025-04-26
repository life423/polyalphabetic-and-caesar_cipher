#!/usr/bin/env python3
"""
Unified Launcher for Cipher Tools Application

This script provides an easy way to run the Cipher Tools application,
offering quick access to both the GUI and command-line interfaces.
"""

import importlib
import os
import platform
import subprocess
import sys

import pkg_resources


def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []
    
    # Core dependencies check
    required_modules = {
        "tkinter": "Usually included with Python installation",
        "pytest": "For running tests",
        "yaml": "For configuration and tests",
    }
    
    for module_name, description in required_modules.items():
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing_deps.append(f"{module_name} ({description})")
    
    # Check package versions from requirements.txt if it exists
    try:
        with open("requirements.txt", "r") as f:
            requirements = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
        
        # Create a dict of installed distributions
        installed = {pkg.key: pkg for pkg in pkg_resources.working_set}
        
        for req in requirements:
            # Skip non-package lines
            if "==" not in req:
                continue
                
            # Parse package name and version
            pkg_name, version = req.split("==")
            pkg_name = pkg_name.lower()
            
            if pkg_name not in installed:
                missing_deps.append(f"{pkg_name} ({version})")
    except Exception as e:
        print(f"Warning: Could not check package versions - {e}")
    
    # Report and return results
    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f" - {dep}")
        print("\nPlease install required dependencies using:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def clear_screen():
    """Clear the terminal screen based on operating system."""
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def print_header():
    """Print the application header."""
    clear_screen()
    print("=" * 60)
    print("                    CIPHER TOOLS APP")
    print("=" * 60)
    print("A comprehensive toolkit for encryption and decryption")
    print("with multiple cipher algorithms and AI-driven analysis.")
    print("=" * 60)
    print()


def launch_gui():
    """Launch the graphical user interface."""
    print("Launching GUI application...")
    try:
        # Direct import and use of tkinter to avoid potential import issues
        import tkinter as tk

        from src.ui.gui import CipherGUI, main

        # Try running the GUI's main function
        main()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        print("\nAlternative method: Launching GUI directly...")
        
        try:
            # If main() fails, try launching directly
            root = tk.Tk()
            # Create application instance and run
            CipherGUI(root)
            root.mainloop()
        except Exception as e2:
            print(f"Error with alternative launch method: {e2}")
            input("Press Enter to return to the main menu...")
            show_main_menu()


def launch_cli():
    """Launch command-line interface with interactive mode."""
    print("Launching command-line interface...")
    try:
        from src.services.cipher_service import CipherService
        
        service = CipherService()
        
        print("\nWelcome to Cipher Tools CLI")
        print("=" * 40)
        
        # Get encryption or decryption choice
        choice = input("Choose operation (e=encrypt, d=decrypt, a=analyze): ")
        if choice.lower() not in {'e', 'd', 'a'}:
            print("Invalid choice. Please enter 'e', 'd', or 'a'.")
            input("Press Enter to return to the main menu...")
            show_main_menu()
            return
        
        # Handle analysis option
        if choice.lower() == 'a':
            analyze_text(service)
            return
            
        encrypt = choice.lower() == 'e'
        
        # Get cipher type choice
        print("\nAvailable ciphers:")
        print("c - Caesar")
        print("p - Polyalphabetic (Vigenère)")
        print("s - Substitution")
        print("t - Transposition")
        print("r - Rail Fence")
        print("a - Affine")
        
        cipher_choice = input("\nChoose cipher type: ")
        if cipher_choice.lower() not in {'c', 'p', 's', 't', 'r', 'a'}:
            print("Invalid choice. Please select a valid cipher type.")
            input("Press Enter to return to the main menu...")
            show_main_menu()
            return
        
        # Get input text
        text = input("\nEnter text to process: ")
        
        # Process based on cipher type
        if cipher_choice.lower() == 'c':  # Caesar cipher
            try:
                shift = int(input("Enter shift value (1-25): "))
                if encrypt:
                    result = service.encrypt_caesar(text, shift)
                else:
                    result = service.decrypt_caesar(text, shift)
                print(f"\nResult: {result}")
            except ValueError:
                print("Error: Shift value must be an integer.")
                
        elif cipher_choice.lower() == 'p':  # Polyalphabetic cipher
            keyword = input("Enter keyword: ")
            if not keyword:
                print("Error: Keyword cannot be empty.")
                input("Press Enter to return to the main menu...")
                show_main_menu()
                return
                
            if encrypt:
                result = service.encrypt_polyalphabetic(text, keyword)
            else:
                result = service.decrypt_polyalphabetic(text, keyword)
            print(f"\nResult: {result}")
            
        elif cipher_choice.lower() == 's':  # Substitution cipher
            if encrypt:
                prompt = "Generate random key? (yes/no): "
                use_random = input(prompt).lower() == 'yes'
                if use_random:
                    prompt = "Enter seed (optional, press Enter to skip): "
                    seed = input(prompt) or None
                    key = service.generate_substitution_key(seed)
                    print(f"Generated key: {key}")
                else:
                    key = input("Enter 26-character substitution key: ")
                    if len(key) != 26:
                        print("Error: Key must be exactly 26 "
                              "characters long.")
                        input("Press Enter to return to the main menu...")
                        show_main_menu()
                        return
                result = service.encrypt_substitution(text, key)
            else:
                key = input("Enter 26-character substitution key: ")
                if len(key) != 26:
                    print("Error: Key must be exactly 26 "
                          "characters long.")
                    input("Press Enter to return to the main menu...")
                    show_main_menu()
                    return
                result = service.decrypt_substitution(text, key)
            print(f"\nResult: {result}")
            
        elif cipher_choice.lower() == 't':  # Transposition cipher
            prompt = "Enter transposition key: "
            prompt += "(word or comma-separated numbers): "
            key = input(prompt)
            if ',' in key:
                # Handle numeric key format
                try:
                    key = [int(k.strip()) for k in key.split(',')]
                except ValueError:
                    print("Error: Numeric key must contain only integers.")
                    input("Press Enter to return to the main menu...")
                    show_main_menu()
                    return
            
            if encrypt:
                result = service.encrypt_transposition(text, key)
            else:
                result = service.decrypt_transposition(text, key)
            print(f"\nResult: {result}")
            
        elif cipher_choice.lower() == 'r':  # Rail Fence cipher
            try:
                rails = int(input("Enter number of rails (2 or more): "))
                if rails < 2:
                    print("Error: Number of rails must be at least 2.")
                    input("Press Enter to return to the main menu...")
                    show_main_menu()
                    return
                
                if encrypt:
                    result = service.encrypt_rail_fence(text, rails)
                else:
                    result = service.decrypt_rail_fence(text, rails)
                print(f"\nResult: {result}")
            except ValueError:
                print("Error: Number of rails must be an integer.")
                
        elif cipher_choice.lower() == 'a':  # Affine cipher
            try:
                a = int(input("Enter 'a' value (must be coprime to 26): "))
                b = int(input("Enter 'b' value: "))
                
                if encrypt:
                    result = service.encrypt_affine(text, (a, b))
                else:
                    result = service.decrypt_affine(text, (a, b))
                print(f"\nResult: {result}")
            except ValueError as e:
                print(f"Error: {e}")
                
        input("\nPress Enter to return to the main menu...")
        show_main_menu()
            
    except Exception as e:
        print(f"Error in CLI mode: {e}")
        input("Press Enter to return to the main menu...")
        show_main_menu()


def analyze_text(service):
    """Analyze encrypted text using AI tools."""
    print("\nAI-Driven Cipher Analysis")
    print("=" * 40)
    
    text = input("Enter encrypted text to analyze: ")
    if not text:
        print("Error: Text cannot be empty.")
        input("Press Enter to return to the main menu...")
        show_main_menu()
        return
        
    print("\nSelect cipher type to analyze:")
    print("1 - Caesar cipher")
    print("2 - Polyalphabetic cipher")
    print("3 - Try both")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == '1' or choice == '3':
        print("\nAnalyzing with Caesar cipher techniques...")
        results = service.analyze_caesar_encryption(text)
        
        print("\nResults for Caesar cipher analysis:")
        print("-" * 40)
        for i, result in enumerate(results):
            print(f"Suggestion {i+1}: Shift = {result['shift']} "
                  f"(Confidence: {result['confidence']}%)")
            print(f"Sample: {result['sample']}\n")
            
    if choice == '2' or choice == '3':
        print("\nAnalyzing with Polyalphabetic cipher techniques...")
        results = service.analyze_polyalphabetic_encryption(text)
        
        print("\nResults for Polyalphabetic cipher analysis:")
        print("-" * 40)
        for i, result in enumerate(results):
            print(f"Suggestion {i+1}: Keyword = '{result['keyword']}' "
                  f"(Confidence: {result['confidence']}%)")
            print(f"Sample: {result['sample']}\n")
    
    if choice not in ['1', '2', '3']:
        print("Invalid choice.")
    
    input("\nPress Enter to return to the main menu...")
    show_main_menu()


def run_advanced_cli():
    """Run the original command-line interface with arguments."""
    print("Running advanced command-line interface...")
    print("(Use --help for available options)")
    
    args = input("Enter command line arguments: ")
    cmd = [sys.executable, "src/ui/cli.py"] + args.split()
    
    try:
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error: {e}")
    
    input("\nPress Enter to return to the main menu...")
    show_main_menu()


def build_executable():
    """Build a standalone executable."""
    print("Building standalone executable...")
    
    try:
        # Import from scripts directory
        from scripts.build_exe import main as build_main
        build_main()
    except ImportError:
        try:
            subprocess.run([sys.executable, "scripts/build_exe.py"])
        except Exception as e:
            print(f"Error during build: {e}")
    
    input("\nPress Enter to return to the main menu...")
    show_main_menu()


def show_help():
    """Display help information."""
    print("\nCipher Tools Help")
    print("=" * 40)
    print("\nThis application provides tools for encrypting and")
    print("decrypting text using various cipher algorithms, as well as")
    print("AI-driven analysis capabilities.")
    print("\nSupported cipher algorithms:")
    print("  - Caesar Cipher: Simple substitution cipher with a shift value")
    print("  - Polyalphabetic Cipher: Uses a keyword to determine")
    print("    varying shifts")
    print("  - Substitution Cipher: Replaces letters according to a key")
    print("  - Transposition Cipher: Rearranges letters based on a key")
    print("  - Rail Fence Cipher: Arranges text in zigzag pattern")
    print("  - Affine Cipher: Uses mathematical function")
    print("    (ax + b) mod 26")
    print("\nThe GUI provides a more user-friendly interface with")
    print("additional options such as file input/output and detailed")
    print("analysis results.")
    print("\nFor developers:")
    print("  - Source code available for customization")
    print("  - Can be extended with additional cipher implementations")
    print("  - AI analysis tools can be enhanced for better accuracy")
    
    input("\nPress Enter to return to the main menu...")
    show_main_menu()


def show_main_menu():
    """Display the main menu and process user choice."""
    while True:
        print_header()
        print("Please select an option:")
        print("1. Launch Graphical User Interface")
        print("2. Run Interactive Command Line Interface")
        print("3. Run Advanced CLI (with arguments)")
        print("4. Build Standalone Executable")
        print("5. Help")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-5): ")
        
        if choice == '1':
            launch_gui()
        elif choice == '2':
            launch_cli()
        elif choice == '3':
            run_advanced_cli()
        elif choice == '4':
            build_executable()
        elif choice == '5':
            show_help()
        elif choice == '0':
            print("\nExiting Cipher Tools App. Goodbye!")
            sys.exit(0)
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")


def main():
    """Main function to start the launcher."""
    if check_dependencies():
        show_main_menu()
    else:
        input("\nPress Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
