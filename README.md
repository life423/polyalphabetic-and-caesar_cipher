# 🚀 Polyalphabetic and Caesar Cipher Toolbox

Hey there! 👋 Welcome to a little corner of the internet where cryptography meets Python in a dance of letters and numbers.

## 🧠 The Journey

This project has been a wild ride. From humble beginnings with a basic understanding of Python and cryptography, it evolved to comprehensively cover Polyalphabetic and Caesar Ciphers. It's been a journey of discovery, learning, and lots of coffee. Recently, the challenge has been creating a Graphical User Interface (GUI) with Python's Tkinter libraries.

## 📚 The Learning Curve

Learning has felt like climbing a mountain with a laptop and a dream. It started with understanding the basics of Polyalphabetic and Caesar Ciphers, then implementing these ciphers in Python! The most recent twist in this journey has been integrating a GUI, making the toolbox even more versatile and user-friendly.

## 🛠️ Building the Toolbox

Building this toolbox was akin to assembling a puzzle, one piece at a time. It began with creating the basic functions for the ciphers, making the code as readable as a children's book, and then developing the ability to encrypt .txt files - all in Python! Now, the process includes adding a GUI with Tkinter to make the cipher toolbox accessible to all.

## 🔄 The Iterative Dance

This project danced to the rhythm of iterative development. Review, improve, repeat. Version control has been the dance partner, gracefully tracking the evolution of the code over time.

## 🌱 The Evolution

From a seed of an idea to a fully grown toolbox, the growth has been dramatic. There's been a deep dive into Python, cryptography, and heaps of problem-solving. The continuous enhancements to this toolbox are a testament to the journey taken and the skills acquired along the way. This toolbox isn't just about cryptography or programming. It's about a sustained effort to learn, grow, and improve.

## 👥 Get In Touch

If you're impressed with the toolbox and think we could create something incredible together, feel free to drop me a line. The journey continues, and I'm always eager to work on interesting projects with great people. The toolbox awaits! Geronimo!

That's all for now. Keep exploring!

# 💻 Running the Program

## Prerequisites
- Python 3 (latest version recommended)

## Instructions

### Running from the source code
1. Clone or download this GitHub repository to your local system.
2. Open the terminal or command line interface.
3. Navigate to the directory of the downloaded repository.
4. If you wish to run the source code directly, you can execute the python script by running the following command:
    ```bash
    python3 cipher_tool.py
    ```
    or
    ```bash
    python3 cipher_gui.py
    ```
    Remember to replace "cipher_tool.py" or "cipher_gui.py" with the script you want to run.

### Running the Executable
For convenience, we have also provided pre-compiled executable versions for Windows and MacOS. These can be run without needing a Python environment on your system.
1. Go to the Releases page of the toolbox repository.
2. Download the appropriate `.exe` (for Windows) or `.app` (for MacOS) file.
3. You do not need to install anything. Simply double click the downloaded file to run the toolbox.

### Building the Executable Yourself
If you have Python and PyInstaller set up, you can build an executable version of the toolbox yourself:
1. Install PyInstaller: `pip install pyinstaller`.
2. From the root project directory, run the following commands to create a standalone executable:

    For the command line tool:
    ```bash
    pyinstaller --onefile cipher_tool.py
    ```
    For the GUI:
    ```bash
    pyinstaller --noconsole --onefile cipher_gui.py
    ```
    The executable (`.exe` or `.app`) will be created in the `dist` subdirectory.
