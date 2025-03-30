#!/usr/bin/env python3
"""
Build script for creating executable versions of the Cipher Tools application.
This script packages the application into a standalone executable using PyInstaller.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path


def main():
    """Main build function."""
    # Detect the operating system
    system = platform.system().lower()
    
    # Clean any previous build artifacts
    clean_build_directories()
    
    # Install required dependencies if needed
    install_dependencies()
    
    # Get build options based on the OS
    build_cmd = get_build_command(system)
    
    # Run the build
    print(f"Building executable with command: {' '.join(build_cmd)}")
    subprocess.run(build_cmd, check=True)
    
    # Copy additional files if needed
    # copy_additional_files(system)
    
    # Report success
    if system == "windows":
        exe_path = Path("dist") / "cipher_tool.exe"
    else:
        exe_path = Path("dist") / "cipher_tool"
    
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\nBuild completed successfully!")
        print(f"Executable: {exe_path.absolute()}")
        print(f"Size: {size_mb:.2f} MB")
    else:
        print("\nBuild may have completed but the expected executable was not found.")
        print(f"Expected path: {exe_path.absolute()}")
        print("Check the 'dist' directory for the generated executable.")


def clean_build_directories():
    """Clean previous build artifacts."""
    print("Cleaning previous build directories...")
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed {dir_name}/")


def install_dependencies():
    """Install required build dependencies."""
    print("Checking PyInstaller installation...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("Failed to install PyInstaller. Please install it manually.")
        sys.exit(1)


def get_build_command(system):
    """Get the PyInstaller command based on the operating system."""
    # Create a new spec file rather than using an old one that might
    # reference invalid paths after refactoring
    
    # Entry point is scripts/run_cipher_app.py
    entry_point = "scripts/run_cipher_app.py"
    
    # Common settings across all platforms
    base_settings = [
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "--onefile",  # Create single executable
        "--name", "cipher_tool",
        "--add-data", "requirements.txt:.",  # Include requirements file
        "--paths", ".",  # Look for modules in current directory
        "--hidden-import", "src.core.base",
        "--hidden-import", "src.core.ciphers",
        "--hidden-import", "src.services.file_service",
        "--hidden-import", "src.services.cipher_service",
        "--hidden-import", "src.ai.analyzer",
        "--hidden-import", "src.ui.cli",
        "--hidden-import", "src.ui.gui"
    ]
    
    # Platform-specific settings
    if system == "windows":
        if os.path.exists("icon.ico"):
            base_settings.extend(["--icon", "icon.ico"])
        base_settings.append("--windowed")  # No console window on Windows
        
    elif system == "darwin":  # macOS
        if os.path.exists("icon.icns"):
            base_settings.extend(["--icon", "icon.icns"])
        base_settings.append("--windowed")  # Create app bundle on macOS
    
    # Add the entry point last
    base_settings.append(entry_point)
    
    return base_settings


if __name__ == "__main__":
    main()
