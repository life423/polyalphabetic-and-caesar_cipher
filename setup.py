from setuptools import setup, find_packages

setup(
    name="cipher_tools",
    version="1.0.0",
    description="A comprehensive cipher encryption/decryption tool with AI analysis",
    author="Cipher Team",
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
            "cipher_tool=cipher_tool:main",
        ],
        "gui_scripts": [
            "cipher_gui=cipher_gui:main",
        ],
    },
)
