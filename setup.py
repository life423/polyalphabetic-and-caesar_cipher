from setuptools import setup, find_packages

setup(
    name="cipher_tools",
    version="1.0.0",
    description="A comprehensive cipher encryption/decryption tool with AI analysis",
    author="Cipher Team",
    packages=find_packages(),
    install_requires=[],
    extras_require={"dev": ["pytest>=7.3.1", "flake8>=6.0.0", "pyyaml>=6.0.1"],
                    "build": ["pyinstaller>=6.0.0"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "cipher_tool=src.ui.cli:main",
        ],
        "gui_scripts": [
            "cipher_gui=src.ui.gui:main",
        ],
    },
)
