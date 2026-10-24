"""Packaging metadata and GUI/CLI entry points for CipherCraft."""
from setuptools import find_packages, setup

setup(
    name="ciphercraft",
    version="1.0.0",
    description="Educational classical ciphers and statistical cryptanalysis",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.3.1", "flake8>=6.0.0", "pyyaml>=6.0.1"],
        "build": ["pyinstaller>=6.0.0"],
    },
    entry_points={
        "console_scripts": ["cipher_tool=src.ui.cli:main"],
        "gui_scripts": ["cipher_gui=src.ui.gui:main"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Education",
    ],
)
