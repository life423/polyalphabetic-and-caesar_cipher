"""Exercise real Tk widgets under a virtual display.

This supplements headless dispatch tests and the packaged CLI smoke test.
The macOS and Windows graphical windows still require interactive QA.
"""
import tkinter as tk

from src.ui.gui import CipherGUI


def main():
    root = tk.Tk()
    try:
        app = CipherGUI(root)
        root.update()
        assert root.winfo_viewable(), "GUI window did not become visible"
        assert root.winfo_height() >= 650
        assert app.results_frame.winfo_ismapped(), "Results panel not displayed"
        assert app.delete_input_checkbox.instate(["disabled"])

        app.input_entry.insert(0, "Hello")
        app.caesar_key_entry.insert(0, "3")
        app.process_button.invoke()
        root.update_idletasks()
        assert app.result_text.get("1.0", "end-1c") == "Khoor", "Process button is broken"

        app.input_mode_var.set("file")
        app._update_input_mode()
        assert not app.delete_input_checkbox.instate(["disabled"])
        app.input_mode_var.set("text")
        app._update_input_mode()
        assert app.delete_input_checkbox.instate(["disabled"])

        app.analysis_results = [{"shift": 3, "sample": "Hello", "confidence": 90}]
        app.apply_button.configure(state=tk.NORMAL)
        app.cipher_var.set("s")
        app._update_key_section()
        assert not app.analysis_results, "Old suggestions survived cipher change"
        assert app.apply_button.instate(["disabled"])
        assert app.analyze_button.instate(["disabled"])
        app.cipher_var.set("c")
        app._update_key_section()
        assert not app.analyze_button.instate(["disabled"])

        root.geometry("820x720")
        root.update()
        assert app.results_frame.winfo_height() > 20, "Results clipped on resize"
        print("Real Tk GUI startup, input mode, buttons, analysis state, and resizing passed")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
