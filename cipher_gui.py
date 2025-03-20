"""
GUI Frontend for Cipher Tool - A Tkinter application for encryption/decryption.

This module provides a graphical interface for cipher operations,
allowing users to perform encryption and decryption through
a user-friendly interface while keeping all business logic separate.
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
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
            text="Caesar and Polyalphabetic Cipher Tool", 
            font=('Helvetica', 16, 'bold')
        )
        
        # ===== Settings Frame =====
        self.settings_frame = ttk.LabelFrame(self.root, text="Cipher Settings")
        
        # Cipher selection
        self.cipher_var = tk.StringVar(value="c")  # 'c' for Caesar, 'p' for Polyalphabetic
        cipher_selection = ttk.Frame(self.settings_frame)
        ttk.Label(cipher_selection, text="Cipher type:").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(
            cipher_selection, 
            text="Caesar", 
            variable=self.cipher_var, 
            value="c"
        ).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(
            cipher_selection, 
            text="Polyalphabetic", 
            variable=self.cipher_var, 
            value="p"
        ).pack(side="left")
        cipher_selection.pack(fill="x", padx=10, pady=5)
        
        # Operation selection
        self.action_var = tk.StringVar(value="e")  # 'e' for encrypt, 'd' for decrypt
        operation_selection = ttk.Frame(self.settings_frame)
        ttk.Label(operation_selection, text="Operation:").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(
            operation_selection, 
            text="Encrypt", 
            variable=self.action_var, 
            value="e"
        ).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(
            operation_selection, 
            text="Decrypt", 
            variable=self.action_var, 
            value="d"
        ).pack(side="left")
        operation_selection.pack(fill="x", padx=10, pady=5)
        
        # Key/shift input
        key_frame = ttk.Frame(self.settings_frame)
        ttk.Label(
            key_frame, 
            text="Key:"
        ).pack(side="left", padx=(0, 10))
        self.key_entry = ttk.Entry(key_frame, width=30)
        self.key_entry.pack(side="left", fill="x", expand=True)
        key_frame.pack(fill="x", padx=10, pady=5)
        
        # Key help text
        ttk.Label(
            self.settings_frame,
            text="For Caesar cipher, enter a number. For Polyalphabetic cipher, enter a keyword.",
            font=('Helvetica', 8)
        ).pack(padx=10, pady=(0, 5), anchor="w")
        
        # ===== Input/Output Frame =====
        self.io_frame = ttk.LabelFrame(self.root, text="Input/Output")
        
        # Input text or file
        input_frame = ttk.Frame(self.io_frame)
        ttk.Label(
            input_frame, 
            text="Input:"
        ).pack(side="left", padx=(0, 10))
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_file_button = ttk.Button(
            input_frame, 
            text="Select File...", 
            command=self._select_input_file
        )
        self.input_file_button.pack(side="left")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        # Output file
        output_frame = ttk.Frame(self.io_frame)
        ttk.Label(
            output_frame, 
            text="Output:"
        ).pack(side="left", padx=(0, 10))
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.output_file_button = ttk.Button(
            output_frame, 
            text="Select File...", 
            command=self._select_output_file
        )
        self.output_file_button.pack(side="left")
        output_frame.pack(fill="x", padx=10, pady=5)
        
        # Delete input file option
        self.delete_input_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.io_frame,
            text="Delete input file after processing",
            variable=self.delete_input_var
        ).pack(anchor="w", padx=10, pady=5)
        
        # ===== Buttons Frame =====
        self.buttons_frame = ttk.Frame(self.root)
        
        # Process button
        self.process_button = ttk.Button(
            self.buttons_frame, 
            text="Process", 
            command=self._process_text,
            style="Green.TButton"
        )
        
        # Analyze button
        self.analyze_button = ttk.Button(
            self.buttons_frame, 
            text="AI Analysis", 
            command=self._analyze_text,
            style="Blue.TButton"
        )
        
        # ===== Results Frame =====
        self.results_frame = ttk.LabelFrame(self.root, text="Results")
        
        # Results area
        self.result_text = scrolledtext.ScrolledText(
            self.results_frame, 
            height=10, 
            width=60, 
            wrap=tk.WORD
        )
        self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== Analysis Frame =====
        self.analysis_frame = ttk.LabelFrame(self.root, text="AI Analysis Results")
        
        # Analysis results
        self.analysis_result = scrolledtext.ScrolledText(
            self.analysis_frame, 
            height=8, 
            width=60, 
            wrap=tk.WORD
        )
        self.analysis_result.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Apply suggestion button
        self.apply_button = ttk.Button(
            self.analysis_frame,
            text="Apply Selected Key",
            command=self._apply_suggested_key,
            state=tk.DISABLED
        )
        self.apply_button.pack(pady=5)
        
        # Store analysis results for later use
        self.analysis_results = []
        self.selected_suggestion = None
        
        # Create custom button styles
        self._create_styles()
    
    def _create_styles(self):
        """Create custom ttk styles for buttons."""
        style = ttk.Style()
        
        # Green "Process" button
        style.configure(
            "Green.TButton",
            background="#4CAF50",
            foreground="white",
            padding=(20, 5)
        )
        
        # Blue "AI Analysis" button
        style.configure(
            "Blue.TButton",
            background="#3F51B5",
            foreground="white",
            padding=(20, 5)
        )
    
    def _layout_widgets(self):
        """Arrange all widgets in the UI."""
        # Add some padding around all widgets
        for child in self.root.winfo_children():
            child.grid_configure(padx=5, pady=5)
            
        # Configure the grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Title at the top
        self.title_label.grid(row=0, column=0, pady=10, sticky="ew")
        
        # Settings frame
        self.settings_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Input/Output frame
        self.io_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Buttons frame
        self.buttons_frame.grid(row=3, column=0, pady=10)
        self.process_button.pack(side="left", padx=(0, 10))
        self.analyze_button.pack(side="left")
        
        # Results frame
        self.results_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        
        # Analysis frame - initially hidden
        self.analysis_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
        self.analysis_frame.grid_remove()  # Hide initially
        
        # Make the results area expandable
        self.root.grid_rowconfigure(4, weight=1)
    
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
    
    def _analyze_text(self):
        """
        Analyze encrypted text to guess the key using AI-driven methods.
        
        This method analyzes the input text and suggests possible keys
        based on statistical analysis and language patterns.
        """
        # Clear previous analysis results
        self.analysis_result.delete('1.0', tk.END)
        self.analysis_results = []
        self.selected_suggestion = None
        self.apply_button.config(state=tk.DISABLED)
        
        # Get input text
        input_text = self.input_entry.get()
        if not input_text:
            self._display_error("Please enter text to analyze.")
            return
            
        # Read from file if path is provided
        if os.path.isfile(input_text):
            try:
                with open(input_text, 'r', encoding='utf-8') as file:
                    ciphertext = file.read()
            except Exception as e:
                self._display_error(f"Failed to read file: {e}")
                return
        else:
            ciphertext = input_text
            
        # Check if we have enough text to analyze
        if len(ciphertext.strip()) < 10:
            self._display_error("Text is too short for meaningful analysis.")
            return
            
        # Set the operation to decrypt
        self.action_var.set('d')
            
        # Show the analysis frame
        self.analysis_frame.grid()  # Show the previously hidden frame
        
        try:
            # Perform analysis based on cipher type
            cipher_type = self.cipher_var.get()  # 'c' for Caesar, 'p' for Polyalphabetic
            
            if cipher_type == 'c':
                # Analyze with Caesar cipher
                results = self.cipher_service.analyze_caesar_encryption(ciphertext)
                self.analysis_results = results
                
                # Display results
                self.analysis_result.insert(tk.END, "=== Caesar Cipher Analysis ===\n\n")
                
                for i, result in enumerate(results):
                    confidence = result['confidence']
                    shift = result['shift']
                    sample = result['sample']
                    
                    self.analysis_result.insert(
                        tk.END, 
                        f"Suggestion {i+1}: Shift = {shift} "
                        f"(Confidence: {confidence}%)\n"
                    )
                    self.analysis_result.insert(tk.END, f"Sample: {sample}\n\n")
                
                # Enable the apply button if we have results
                if results:
                    self.apply_button.config(state=tk.NORMAL)
                    self.selected_suggestion = results[0]  # Select the first one by default
                    
            else:
                # Analyze with Polyalphabetic cipher
                results = self.cipher_service.analyze_polyalphabetic_encryption(ciphertext)
                self.analysis_results = results
                
                # Display results
                self.analysis_result.insert(tk.END, "=== Polyalphabetic Cipher Analysis ===\n\n")
                
                for i, result in enumerate(results):
                    confidence = result['confidence']
                    keyword = result['keyword']
                    sample = result['sample']
                    
                    self.analysis_result.insert(
                        tk.END, 
                        f"Suggestion {i+1}: Keyword = '{keyword}' "
                        f"(Confidence: {confidence}%)\n"
                    )
                    self.analysis_result.insert(tk.END, f"Sample: {sample}\n\n")
                
                # Enable the apply button if we have results
                if results and '?' not in results[0]['keyword']:
                    self.apply_button.config(state=tk.NORMAL)
                    self.selected_suggestion = results[0]  # Select the first one by default
        
        except Exception as e:
            self._display_error(f"Analysis error: {e}")
    
    def _apply_suggested_key(self):
        """Apply the selected key suggestion to the key field."""
        if not self.selected_suggestion:
            return
            
        # Clear the key entry
        self.key_entry.delete(0, tk.END)
        
        # Insert the suggested key based on cipher type
        cipher_type = self.cipher_var.get()
        
        if cipher_type == 'c':
            # For Caesar cipher, insert the shift value
            self.key_entry.insert(0, str(self.selected_suggestion['shift']))
        else:
            # For Polyalphabetic cipher, insert the keyword
            self.key_entry.insert(0, self.selected_suggestion['keyword'])
        
        # Set focus to the process button
        self.process_button.focus_set()


def main():
    """Run the Cipher GUI application."""
    root = tk.Tk()
    app = CipherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
