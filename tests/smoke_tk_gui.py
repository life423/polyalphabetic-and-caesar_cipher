"""Exercise real Tk widgets under a virtual display.

This supplements headless dispatch tests and the packaged CLI smoke test.
The macOS and Windows graphical windows still require interactive QA.
"""
import tkinter as tk

from tkinter import messagebox

from src.core.ciphers import AffineCipher, RailFenceCipher
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

        assert app.header_frame.cget("bg") == app.COLORS["primary"]
        assert app.title_label.cget("fg") == "#FFFFFF"
        assert app.output_entry.instate(["disabled"])

        app.input_entry.delete(0, tk.END)
        app.input_entry.insert(0, "Khoor, Zruog!")
        app.analyze_button.invoke()
        root.update()
        assert app.analysis_frame.winfo_ismapped(), "Analysis panel not visible"
        assert "Suggestion 1" in app.analysis_result.get("1.0", "end-1c")
        assert not app.apply_button.instate(["disabled"])

        # Affine and Rail Fence analysis: rank, show, and apply the top key
        messagebox.showinfo = lambda *args, **kwargs: None
        plaintext = ("When in the Course of human events it becomes necessary for one "
                     "people to dissolve the political bands which have connected them")

        app.cipher_var.set("a")
        app._update_key_section()
        app.input_entry.delete(0, tk.END)
        app.input_entry.insert(0, AffineCipher.transform(plaintext, (5, 8), encrypt=True))
        app.analyze_button.invoke()
        root.update()
        assert "a = 5, b = 8" in app.analysis_result.get("1.0", "end-1c"), "Affine analysis missed the key"
        app._apply_suggested_key()
        assert (app.affine_a_entry.get(), app.affine_b_entry.get()) == ("5", "8")

        app.cipher_var.set("r")
        app._update_key_section()
        app.input_entry.delete(0, tk.END)
        app.input_entry.insert(0, RailFenceCipher.transform(plaintext, 4, encrypt=True))
        app.analyze_button.invoke()
        root.update()
        assert "Rails = 4" in app.analysis_result.get("1.0", "end-1c"), "Rail Fence analysis missed the rails"
        app._apply_suggested_key()
        assert app.rail_key_entry.get() == "4"

        root.geometry("820x720")
        root.update()
        assert app.results_frame.winfo_height() > 20, "Results clipped on resize"
        print("Real Tk startup, palette, cipher actions, analysis, file modes and resizing passed")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
