#!/usr/bin/env python3
"""
Simple launcher for CipherCraft GUI application.
Just run this file to start the graphical interface.
"""

if __name__ == "__main__":
    try:
        # Import and run the GUI main function
        from src.ui.gui import main
        main()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        input("Press Enter to exit...")
