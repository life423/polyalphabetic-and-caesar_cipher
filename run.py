#!/usr/bin/env python3
"""CipherCraft source launcher.

Use 'python run.py' for the desktop GUI, or 'python run.py --cli' for
the interactive command-line mode. Tk is only required for the GUI.
"""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(description="CipherCraft classical cipher toolkit")
    parser.add_argument("--cli", action="store_true", help="run the interactive command-line interface")
    args = parser.parse_args(argv)

    if args.cli:
        from src.ui.cli import main as cli_main
        return cli_main()

    try:
        import tkinter as tk
        root = tk.Tk()
    except Exception as exc:
        # A headless system can still use CipherCraft's interactive CLI.
        print(f"GUI is unavailable ({exc}); starting the CLI instead.")
        from src.ui.cli import main as cli_main
        return cli_main()

    from src.ui.gui import CipherGUI
    CipherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
