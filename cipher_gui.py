"""
GUI Frontend for Cipher Tool - A Tkinter application for encryption/decryption.

This module provides a graphical interface for cipher operations,
allowing users to perform encryption and decryption through
a user-friendly interface while keeping all business logic separate.
"""

import os
import tkinter as tk
from tkinter import filedialog
from cipher_service import CipherService


class CipherGUI:
    """
    A GUI application for encryption and decryption using Caesar and
    Polyalphabetic ciphers.
    
    This class is responsible only for UI interactions and delegates
    all cipher operations to the CipherService.
    """
    
    def __init__(self, root):
        """
        Initialize the GUI components.
        
        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("Cipher Tool")
        
        # Initialize the service layer
        self.cipher_service = CipherService()
        
        # Create and configure the UI components
        self._create_widgets()
        self._layout_widgets()
    
    def _create_widgets(self):
        """Create all the widgets for the application."""
        # Title
        self.title_label = tk.Label(
            self.root, 
            text="Welcome to the Caesar and Polyalphabetic Cipher Tool!", 
            font=('Helvetica', 16, 'bold')
        )
        
        # Cipher selection
        self.cipher_label = tk.Label(
            self.root, 
            text="Select cipher type:"
        )
        self.cipher_var = tk.StringVar(value="c")  # 'c' for Caesar, 'p' for Polyalphabetic
        self.cipher_frame = tk.Frame(self.root)
        self.caesar_radio = tk.Radiobutton(
            self.cipher_frame, 
            text="Caesar", 
            variable=self.cipher_var, 
            value="c"
        )
        self.poly_radio = tk.Radiobutton(
            self.cipher_frame, 
            text="Polyalphabetic", 
            variable=self.cipher_var, 
            value="p"
        )
        
        # Operation selection
        self.action_label = tk.Label(
            self.root, 
            text="Select operation:"
        )
        self.action_var = tk.StringVar(value="e")  # 'e' for encrypt, 'd' for decrypt
        self.action_frame = tk.Frame(self.root)
        self.encrypt_radio = tk.Radiobutton(
            self.action_frame, 
            text="Encrypt", 
            variable=self.action_var, 
            value="e"
        )
        self.decrypt_radio = tk.Radiobutton(
            self.action_frame, 
            text="Decrypt", 
            variable=self.action_var, 
            value="d"
        )
        
        # Key/shift input
        self.key_label = tk.Label(
            self.root, 
            text="Enter keyword (for Polyalphabetic) or shift value (for Caesar):"
        )
        self.key_entry = tk.Entry(self.root, width=30)
        
        # Input text or file
        self.input_label = tk.Label(
            self.root, 
            text="Enter text or select file to process:"
        )
        self.input_entry = tk.Entry(self.root, width=50)
        self.input_file_button = tk.Button(
            self.root, 
            text="Select input file...", 
            command=self._select_input_file
        )
        
        # Output file (optional)
        self.output_label = tk.Label(
            self.root, 
            text="Select output file (optional):"
        )
        self.output_entry = tk.Entry(self.root, width=50)
        self.output_file_button = tk.Button(
            self.root, 
            text="Select output file...", 
            command=self._select_output_file
        )
        
        # Delete input file option
        self.delete_input_var = tk.BooleanVar(value=False)
        self.delete_input_checkbox = tk.Checkbutton(
            self.root,
            text="Delete input file after processing",
            variable=self.delete_input_var
        )
        
        # Results area
        self.result_label = tk.Label(self.root, text="Result:")
        self.result_text = tk.Text(self.root, height=10, width=50)
        
        # Process button
        self.process_button = tk.Button(
            self.root, 
            text="Process", 
            command=self._process_text,
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=5
        )
    
    def _layout_widgets(self):
        """Arrange all widgets in the UI."""
        # Title
        self.title_label.pack(pady=10)
        
        # Cipher type
        self.cipher_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.cipher_frame.pack(fill="x", padx=20)
        self.caesar_radio.pack(side="left", padx=(0, 10))
        self.poly_radio.pack(side="left")
        
        # Operation
        self.action_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.action_frame.pack(fill="x", padx=20)
        self.encrypt_radio.pack(side="left", padx=(0, 10))
        self.decrypt_radio.pack(side="left")
        
        # Key/shift
        self.key_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.key_entry.pack(fill="x", padx=20, pady=(0, 10))
        
        # Input
        self.input_label.pack(anchor="w", padx=10, pady=(10, 0))
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_file_button.pack(side="right", padx=(10, 0))
        
        # Output
        self.output_label.pack(anchor="w", padx=10, pady=(10, 0))
        output_frame = tk.Frame(self.root)
        output_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.output_entry.pack(side="left", fill="x", expand=True)
        self.output_file_button.pack(side="right", padx=(10, 0))
        
        # Delete input option
        self.delete_input_checkbox.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Result
        self.result_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.result_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Process button
        self.process_button.pack(pady=20)
    
    def _select_input_file(self):
        """Open file dialog to select an input file."""
        filename = filedialog.askopenfilename()
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
    
    def _select_output_file(self):
        """Open file dialog to select an output file."""
        filename = filedialog.asksaveasfilename()
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
    
    def _process_text(self):
        """
        Process the text/file based on the selected cipher and options.
        
        This method gathers all user inputs from the UI, validates them,
        and then delegates the actual processing to appropriate service methods.
        """
        # Clear previous results
        self.result_text.delete('1.0', tk.END)
        
        # Get user inputs
        cipher_type = self.cipher_var.get()  # 'c' for Caesar, 'p' for Polyalphabetic
        is_encrypt = self.action_var.get() == 'e'  # True for encrypt, False for decrypt
        key_or_shift = self.key_entry.get()
        input_text = self.input_entry.get()
        output_file = self.output_entry.get()
        delete_input = self.delete_input_var.get()
        
        # Validate inputs
        if not (cipher_type and key_or_shift and input_text):
            self._display_error("Please fill in all required fields.")
            return
        
        # Determine if using file or direct text input
        is_file_input = os.path.isfile(input_text)
        
        try:
            # Process with appropriate cipher based on user selections
            if cipher_type == 'c':  # Caesar cipher
                self._process_caesar_cipher(
                    is_encrypt, 
                    key_or_shift, 
                    input_text, 
                    output_file, 
                    is_file_input, 
                    delete_input
                )
            else:  # Polyalphabetic cipher
                self._process_polyalphabetic_cipher(
                    is_encrypt, 
                    key_or_shift, 
                    input_text, 
                    output_file, 
                    is_file_input, 
                    delete_input
                )
                
        except Exception as e:
            self._display_error(str(e))
    
    def _process_caesar_cipher(self, is_encrypt, shift_str, input_text, 
                              output_file, is_file_input, delete_input):
        """
        Process text or file using the Caesar cipher.
        
        Args:
            is_encrypt (bool): True for encryption, False for decryption
            shift_str (str): Shift value as string (will be converted to int)
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        try:
            shift = int(shift_str)
        except ValueError:
            self._display_error("Shift value must be an integer for Caesar cipher.")
            return
        
        if is_file_input and output_file:
            # Process file with Caesar cipher
            if is_encrypt:
                cipher_func = lambda x: self.cipher_service.encrypt_caesar(x, shift)
            else:
                cipher_func = lambda x: self.cipher_service.decrypt_caesar(x, shift)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Caesar cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_caesar(input_text, shift)
            else:
                result = self.cipher_service.decrypt_caesar(input_text, shift)
                
            self._display_result(result)
    
    def _process_polyalphabetic_cipher(self, is_encrypt, keyword, input_text, 
                                      output_file, is_file_input, delete_input):
        """
        Process text or file using the Polyalphabetic cipher.
        
        Args:
            is_encrypt (bool): True for encryption, False for decryption
            keyword (str): Keyword for the cipher
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        if not keyword:
            self._display_error("Keyword cannot be empty for Polyalphabetic cipher.")
            return
            
        if is_file_input and output_file:
            # Process file with Polyalphabetic cipher
            if is_encrypt:
                cipher_func = lambda x: self.cipher_service.encrypt_polyalphabetic(x, keyword)
            else:
                cipher_func = lambda x: self.cipher_service.decrypt_polyalphabetic(x, keyword)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Polyalphabetic cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_polyalphabetic(input_text, keyword)
            else:
                result = self.cipher_service.decrypt_polyalphabetic(input_text, keyword)
                
            self._display_result(result)
    
    def _display_result(self, result):
        """Display the result in the result text area."""
        self.result_text.insert(tk.END, result)
    
    def _display_error(self, error_message):
        """Display an error message in the result text area."""
        self.result_text.insert(tk.END, f"Error: {error_message}")


def main():
    """Run the Cipher GUI application."""
    root = tk.Tk()
    app = CipherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
