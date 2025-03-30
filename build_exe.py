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
    
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\nBuild completed successfully!")
    print(f"Executable: {exe_path.absolute()}")
    print(f"Size: {size_mb:.2f} MB")


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
    # Base command using the spec file
    base_cmd = [sys.executable, "-m", "PyInstaller", "cipher_tool.spec"]
    
    # For Windows: Add icon if available
    if system == "windows":
        if os.path.exists("icon.ico"):
            return base_cmd
        else:
            print("Note: icon.ico not found. Building without custom icon.")
            return [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "cipher_tool.py"]
    
    # For macOS: Add app bundle settings if needed
    elif system == "darwin":
        if os.path.exists("icon.icns"):
            return base_cmd
        else:
            print("Note: icon.icns not found. Building without custom icon.")
            return [sys.executable, "-m", "PyInstaller", "--onefile", "--windowed", "cipher_tool.py"]
    
    # For Linux: Standard build
    else:
        return [sys.executable, "-m", "PyInstaller", "--onefile", "cipher_tool.py"]


if __name__ == "__main__":
    main()
