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
    A GUI application for encryption and decryption using multiple cipher algorithms.

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
            text="Comprehensive Cipher Tool",
            font=('Helvetica', 16, 'bold')
        )

        # ===== Settings Frame =====
        self.settings_frame = ttk.LabelFrame(self.root, text="Cipher Settings")

        # Cipher selection
        self.cipher_var = tk.StringVar(value="c")  # Default to Caesar
        cipher_selection = ttk.Frame(self.settings_frame)
        ttk.Label(
            cipher_selection, text="Cipher type:"
        ).pack(side="left", padx=(0, 10))
        
        cipher_types_frame = ttk.Frame(cipher_selection)
        # Row 1 of cipher types
        ttk.Radiobutton(
            cipher_types_frame,
            text="Caesar",
            variable=self.cipher_var,
            value="c",
            command=self._update_key_section
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Radiobutton(
            cipher_types_frame,
            text="Polyalphabetic",
            variable=self.cipher_var,
            value="p",
            command=self._update_key_section
        ).grid(row=0, column=1, sticky="w", padx=(0, 10))
        ttk.Radiobutton(
            cipher_types_frame,
            text="Substitution",
            variable=self.cipher_var,
            value="s",
            command=self._update_key_section
        ).grid(row=0, column=2, sticky="w")
        
        # Row 2 of cipher types
        ttk.Radiobutton(
            cipher_types_frame,
            text="Transposition",
            variable=self.cipher_var,
            value="t",
            command=self._update_key_section
        ).grid(row=1, column=0, sticky="w", padx=(0, 10))
        ttk.Radiobutton(
            cipher_types_frame,
            text="Rail Fence",
            variable=self.cipher_var,
            value="r",
            command=self._update_key_section
        ).grid(row=1, column=1, sticky="w", padx=(0, 10))
        ttk.Radiobutton(
            cipher_types_frame,
            text="Affine",
            variable=self.cipher_var,
            value="a",
            command=self._update_key_section
        ).grid(row=1, column=2, sticky="w")
        
        cipher_types_frame.pack(side="left")
        cipher_selection.pack(fill="x", padx=10, pady=5)
        
        # Operation selection
        self.action_var = tk.StringVar(value="e")  # 'e' for encrypt, 'd' for decrypt
        operation_selection = ttk.Frame(self.settings_frame)
        ttk.Label(
            operation_selection, text="Operation:"
        ).pack(side="left", padx=(0, 10))
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
        
        # Key/shift input section - will be updated dynamically based on cipher type
        self.key_section_frame = ttk.Frame(self.settings_frame)
        
        # Create different key input frames for each cipher type
        # We'll show/hide them based on the selected cipher
        
        # 1. Caesar cipher key input (shift)
        self.caesar_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.caesar_key_frame,
            text="Shift value:"
        ).pack(side="left", padx=(0, 10))
        self.caesar_key_entry = ttk.Entry(self.caesar_key_frame, width=10)
        self.caesar_key_entry.pack(side="left")
        ttk.Label(
            self.caesar_key_frame,
            text="(1-25)"
        ).pack(side="left", padx=(5, 0))
        
        # 2. Polyalphabetic cipher key input (keyword)
        self.poly_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.poly_key_frame,
            text="Keyword:"
        ).pack(side="left", padx=(0, 10))
        self.poly_key_entry = ttk.Entry(self.poly_key_frame, width=30)
        self.poly_key_entry.pack(side="left", fill="x", expand=True)
        
        # 3. Substitution cipher key input (26 chars)
        self.sub_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.sub_key_frame,
            text="Key:"
        ).pack(side="left", padx=(0, 10))
        self.sub_key_entry = ttk.Entry(self.sub_key_frame, width=30)
        self.sub_key_entry.pack(side="left", fill="x", expand=True)
        self.sub_gen_key_button = ttk.Button(
            self.sub_key_frame,
            text="Generate Key",
            command=self._generate_substitution_key
        )
        self.sub_gen_key_button.pack(side="left", padx=(10, 0))
        
        # 4. Transposition cipher key input
        self.trans_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.trans_key_frame,
            text="Key:"
        ).pack(side="left", padx=(0, 10))
        self.trans_key_entry = ttk.Entry(self.trans_key_frame, width=30)
        self.trans_key_entry.pack(side="left", fill="x", expand=True)
        
        # 5. Rail Fence cipher key input
        self.rail_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.rail_key_frame,
            text="Rails:"
        ).pack(side="left", padx=(0, 10))
        self.rail_key_entry = ttk.Entry(self.rail_key_frame, width=10)
        self.rail_key_entry.pack(side="left")
        ttk.Label(
            self.rail_key_frame,
            text="(2 or more)"
        ).pack(side="left", padx=(5, 0))
        
        # 6. Affine cipher key input
        self.affine_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.affine_key_frame,
            text="a value:"
        ).pack(side="left", padx=(0, 10))
        self.affine_a_entry = ttk.Entry(self.affine_key_frame, width=5)
        self.affine_a_entry.pack(side="left")
        ttk.Label(
            self.affine_key_frame,
            text="b value:"
        ).pack(side="left", padx=(10, 10))
        self.affine_b_entry = ttk.Entry(self.affine_key_frame, width=5)
        self.affine_b_entry.pack(side="left")
        ttk.Label(
            self.affine_key_frame,
            text="(a must be coprime to 26)"
        ).pack(side="left", padx=(5, 0))
        
        # Add all frames to the key section (only one will be visible at a time)
        self.key_section_frame.pack(fill="x", padx=10, pady=5)
        
        # Help text container - will be updated based on the selected cipher
        self.help_text_var = tk.StringVar()
        
        # Initialize with Caesar cipher key frame visible
        self._update_key_section()
        self.help_text_label = ttk.Label(
            self.settings_frame,
            textvariable=self.help_text_var,
            font=('Helvetica', 8),
            wraplength=500  # Wrap text if it's too long
        )
        self.help_text_label.pack(padx=10, pady=(0, 5), anchor="w")

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

        # Process button - using standard tk buttons for better color support
        self.process_button = tk.Button(
            self.buttons_frame,
            text="Process",
            command=self._process_text,
            bg="#4CAF50",  # Green background
            fg="white",    # White text
            padx=20,
            pady=5,
            font=('Helvetica', 10, 'bold')
        )

        # Analyze button
        self.analyze_button = tk.Button(
            self.buttons_frame,
            text="AI Analysis",
            command=self._analyze_text,
            bg="#3F51B5",  # Blue background
            fg="white",    # White text
            padx=20,
            pady=5,
            font=('Helvetica', 10, 'bold')
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
        self.analysis_frame = ttk.LabelFrame(
            self.root, text="AI Analysis Results")

        # Analysis results
        self.analysis_result = scrolledtext.ScrolledText(
            self.analysis_frame,
            height=8,
            width=60,
            wrap=tk.WORD
        )
        self.analysis_result.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Apply suggestion button - matching style with other buttons
        self.apply_button = tk.Button(
            self.analysis_frame,
            text="Apply Selected Key",
            command=self._apply_suggested_key,
            bg="#FF9800",  # Orange background
            fg="white",    # White text
            padx=10,
            pady=3,
            font=('Helvetica', 10, 'bold'),
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

    def _update_key_section(self):
        """Update the key section based on the selected cipher type."""
        # Hide all key frames first
        for frame in [
            self.caesar_key_frame, 
            self.poly_key_frame,
            self.sub_key_frame,
            self.trans_key_frame,
            self.rail_key_frame,
            self.affine_key_frame
        ]:
            frame.pack_forget()
        
        # Show the appropriate key frame based on selected cipher type
        cipher_type = self.cipher_var.get()
        
        if cipher_type == 'c':  # Caesar
            self.caesar_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Caesar cipher shifts each letter in the plaintext by a fixed number of positions in the alphabet. " +
                "Enter a shift value between 1 and 25."
            )
        elif cipher_type == 'p':  # Polyalphabetic
            self.poly_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Polyalphabetic (Vigenère) cipher uses a keyword to determine different shift values for each letter. " +
                "Enter a keyword without spaces."
            )
        elif cipher_type == 's':  # Substitution
            self.sub_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Substitution cipher replaces each letter with another letter according to a fixed mapping. " +
                "Enter a 26-character key, or use the 'Generate Key' button to create a random one."
            )
        elif cipher_type == 't':  # Transposition
            self.trans_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Transposition cipher rearranges the letters of the plaintext according to a key. " +
                "Enter a word or comma-separated numbers (e.g., '2,0,1,3' or 'KEY')."
            )
        elif cipher_type == 'r':  # Rail Fence
            self.rail_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Rail Fence cipher writes the message in a zig-zag pattern across a number of rows (rails), " +
                "then reads off each row. Enter the number of rails (2 or more)."
            )
        elif cipher_type == 'a':  # Affine
            self.affine_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Affine cipher uses the formula (ax + b) mod 26 for encryption, where x is the position of each letter. " +
                "Value 'a' must be coprime to 26 (typically 1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, or 25)."
            )
    
    def _generate_substitution_key(self):
        """Generate a random substitution key and insert it into the entry field."""
        # Use the service to generate a random key
        key = self.cipher_service.generate_substitution_key()
        
        # Clear the entry and insert the new key
        self.sub_key_entry.delete(0, tk.END)
        self.sub_key_entry.insert(0, key)

    def _get_current_key(self):
        """Get the key from the appropriate entry field based on the selected cipher type."""
        cipher_type = self.cipher_var.get()
        
        if cipher_type == 'c':  # Caesar
            return self.caesar_key_entry.get()
        elif cipher_type == 'p':  # Polyalphabetic
            return self.poly_key_entry.get()
        elif cipher_type == 's':  # Substitution
            return self.sub_key_entry.get()
        elif cipher_type == 't':  # Transposition
            return self.trans_key_entry.get()
        elif cipher_type == 'r':  # Rail Fence
            return self.rail_key_entry.get()
        elif cipher_type == 'a':  # Affine
            a_value = self.affine_a_entry.get()
            b_value = self.affine_b_entry.get()
            return (a_value, b_value)  # Return as tuple for Affine cipher
    
    def _process_text(self):
        """
        Process the text/file based on the selected cipher and options.

        This method gathers all user inputs from the UI, validates them,
        and then delegates the actual processing to appropriate service methods.
        """
        # Clear previous results
        self.result_text.delete('1.0', tk.END)
        
        # Get user inputs
        cipher_type = self.cipher_var.get()
        is_encrypt = self.action_var.get() == 'e'  # True for encrypt, False for decrypt
        input_text = self.input_entry.get()
        output_file = self.output_entry.get()
        delete_input = self.delete_input_var.get()
        
        # Validate input text
        if not input_text:
            self._display_error("Please enter text or select a file for input.")
            return
        
        # Determine if using file or direct text input
        is_file_input = os.path.isfile(input_text)
        
        try:
            # Process with appropriate cipher based on user selections
            if cipher_type == 'c':  # Caesar cipher
                key = self.caesar_key_entry.get()
                if not key:
                    self._display_error("Please enter a shift value.")
                    return
                self._process_caesar_cipher(
                    is_encrypt, key, input_text, output_file, is_file_input, delete_input
                )
            elif cipher_type == 'p':  # Polyalphabetic cipher
                key = self.poly_key_entry.get()
                if not key:
                    self._display_error("Please enter a keyword.")
                    return
                self._process_polyalphabetic_cipher(
                    is_encrypt, key, input_text, output_file, is_file_input, delete_input
                )
            elif cipher_type == 's':  # Substitution cipher
                key = self.sub_key_entry.get()
                if not key or len(key) != 26:
                    self._display_error("Please enter a 26-character substitution key.")
                    return
                self._process_substitution_cipher(
                    is_encrypt, key, input_text, output_file, is_file_input, delete_input
                )
            elif cipher_type == 't':  # Transposition cipher
                key = self.trans_key_entry.get()
                if not key:
                    self._display_error("Please enter a transposition key.")
                    return
                self._process_transposition_cipher(
                    is_encrypt, key, input_text, output_file, is_file_input, delete_input
                )
            elif cipher_type == 'r':  # Rail Fence cipher
                key = self.rail_key_entry.get()
                if not key:
                    self._display_error("Please enter the number of rails.")
                    return
                self._process_rail_fence_cipher(
                    is_encrypt, key, input_text, output_file, is_file_input, delete_input
                )
            elif cipher_type == 'a':  # Affine cipher
                a_value = self.affine_a_entry.get()
                b_value = self.affine_b_entry.get()
                if not a_value or not b_value:
                    self._display_error("Please enter both 'a' and 'b' values.")
                    return
                self._process_affine_cipher(
                    is_encrypt, a_value, b_value, input_text, output_file, is_file_input, delete_input
                )
                
        except Exception as e:
            self._display_error(str(e))
    
    def _process_caesar_cipher(
            self, is_encrypt, shift_str, input_text,
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
                def cipher_func(x):
                    return self.cipher_service.encrypt_caesar(x, shift)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_caesar(x, shift)
                
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
    
    def _process_polyalphabetic_cipher(
            self, is_encrypt, keyword, input_text,
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
                def cipher_func(x):
                    return self.cipher_service.encrypt_polyalphabetic(x, keyword)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_polyalphabetic(x, keyword)
                
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
                result = self.cipher_service.encrypt_polyalphabetic(
                    input_text, keyword)
            else:
                result = self.cipher_service.decrypt_polyalphabetic(
                    input_text, keyword)
                
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
            cipher_type = self.cipher_var.get()  # 'c' for Caesar, 'p' for Poly
            
            if cipher_type == 'c':
                # Analyze with Caesar cipher
                results = self.cipher_service.analyze_caesar_encryption(ciphertext)
                self.analysis_results = results
                
                # Display results
                self.analysis_result.insert(
                    tk.END, "=== Caesar Cipher Analysis ===\n\n")
                
                for i, result in enumerate(results):
                    confidence = result['confidence']
                    shift = result['shift']
                    sample = result['sample']
                    
                    suggestion = f"Suggestion {i+1}: Shift = {shift} "
                    suggestion += f"(Confidence: {confidence}%)\n"
                    self.analysis_result.insert(tk.END, suggestion)
                    self.analysis_result.insert(
                        tk.END, f"Sample: {sample}\n\n")
                
                # Enable the apply button if we have results
                if results:
                    self.apply_button.config(state=tk.NORMAL)
                    # Select the first one by default
                    self.selected_suggestion = results[0]
                    
            else:
                # Analyze with Polyalphabetic cipher
                results = self.cipher_service.analyze_polyalphabetic_encryption(
                    ciphertext)
                self.analysis_results = results
                
                # Display results
                self.analysis_result.insert(
                    tk.END, "=== Polyalphabetic Cipher Analysis ===\n\n")
                
                for i, result in enumerate(results):
                    confidence = result['confidence']
                    keyword = result['keyword']
                    sample = result['sample']
                    
                    suggestion = f"Suggestion {i+1}: Keyword = '{keyword}' "
                    suggestion += f"(Confidence: {confidence}%)\n"
                    self.analysis_result.insert(tk.END, suggestion)
                    self.analysis_result.insert(
                        tk.END, f"Sample: {sample}\n\n")
                
                # Enable the apply button if we have results
                if results and '?' not in results[0]['keyword']:
                    self.apply_button.config(state=tk.NORMAL)
                    # Select the first one by default
                    self.selected_suggestion = results[0]
        
        except Exception as e:
            self._display_error(f"Analysis error: {e}")
    
    def _process_substitution_cipher(
            self, is_encrypt, key, input_text,
            output_file, is_file_input, delete_input):
        """
        Process text or file using the Substitution cipher.

        Args:
            is_encrypt (bool): True for encryption, False for decryption
            key (str): 26-character substitution key
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        if len(key) != 26:
            self._display_error("Substitution key must be 26 characters long.")
            return
            
        if is_file_input and output_file:
            # Process file with Substitution cipher
            if is_encrypt:
                def cipher_func(x):
                    return self.cipher_service.encrypt_substitution(x, key)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_substitution(x, key)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Substitution cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_substitution(input_text, key)
            else:
                result = self.cipher_service.decrypt_substitution(input_text, key)
                
            self._display_result(result)
    
    def _process_transposition_cipher(
            self, is_encrypt, key, input_text,
            output_file, is_file_input, delete_input):
        """
        Process text or file using the Transposition cipher.

        Args:
            is_encrypt (bool): True for encryption, False for decryption
            key (str): String key or comma-separated numbers
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        # Convert numeric key if needed
        if ',' in key:
            try:
                key = [int(k.strip()) for k in key.split(',')]
            except ValueError:
                self._display_error("Invalid numeric key format. Use comma-separated integers.")
                return
        
        if is_file_input and output_file:
            # Process file with Transposition cipher
            if is_encrypt:
                def cipher_func(x):
                    return self.cipher_service.encrypt_transposition(x, key)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_transposition(x, key)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Transposition cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_transposition(input_text, key)
            else:
                result = self.cipher_service.decrypt_transposition(input_text, key)
                
            self._display_result(result)
    
    def _process_rail_fence_cipher(
            self, is_encrypt, rails_str, input_text,
            output_file, is_file_input, delete_input):
        """
        Process text or file using the Rail Fence cipher.

        Args:
            is_encrypt (bool): True for encryption, False for decryption
            rails_str (str): Number of rails as string (will be converted to int)
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        try:
            rails = int(rails_str)
            if rails < 2:
                self._display_error("Number of rails must be at least 2.")
                return
        except ValueError:
            self._display_error("Number of rails must be an integer.")
            return
            
        if is_file_input and output_file:
            # Process file with Rail Fence cipher
            if is_encrypt:
                def cipher_func(x):
                    return self.cipher_service.encrypt_rail_fence(x, rails)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_rail_fence(x, rails)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Rail Fence cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_rail_fence(input_text, rails)
            else:
                result = self.cipher_service.decrypt_rail_fence(input_text, rails)
                
            self._display_result(result)
    
    def _process_affine_cipher(
            self, is_encrypt, a_str, b_str, input_text,
            output_file, is_file_input, delete_input):
        """
        Process text or file using the Affine cipher.

        Args:
            is_encrypt (bool): True for encryption, False for decryption
            a_str (str): 'a' value as string (will be converted to int)
            b_str (str): 'b' value as string (will be converted to int)
            input_text (str): Text to process or path to input file
            output_file (str): Path to output file (if processing file)
            is_file_input (bool): True if input is a file, False for direct text
            delete_input (bool): Whether to delete input file after processing
        """
        try:
            a = int(a_str)
            b = int(b_str)
            key_pair = (a, b)
        except ValueError:
            self._display_error("Both 'a' and 'b' values must be integers.")
            return
            
        if is_file_input and output_file:
            # Process file with Affine cipher
            if is_encrypt:
                def cipher_func(x):
                    return self.cipher_service.encrypt_affine(x, key_pair)
            else:
                def cipher_func(x):
                    return self.cipher_service.decrypt_affine(x, key_pair)
                
            result = self.cipher_service.process_file_with_cipher(
                input_text,
                output_file,
                cipher_func,
                delete_input
            )
            self._display_result(result)
        else:
            # Process text with Affine cipher
            if is_encrypt:
                result = self.cipher_service.encrypt_affine(input_text, key_pair)
            else:
                result = self.cipher_service.decrypt_affine(input_text, key_pair)
                
            self._display_result(result)
    
    def _apply_suggested_key(self):
        """Apply the selected key suggestion to the appropriate key field."""
        if not self.selected_suggestion:
            return
            
        # Get the current cipher type
        cipher_type = self.cipher_var.get()
        
        if cipher_type == 'c':
            # For Caesar cipher, insert the shift value
            self.caesar_key_entry.delete(0, tk.END)
            self.caesar_key_entry.insert(0, str(self.selected_suggestion['shift']))
        elif cipher_type == 'p':
            # For Polyalphabetic cipher, insert the keyword
            self.poly_key_entry.delete(0, tk.END)
            self.poly_key_entry.insert(0, self.selected_suggestion['keyword'])
        
        # Set focus to the process button
        self.process_button.focus_set()


def main():
    """Run the Cipher GUI application."""
    root = tk.Tk()
    app = CipherGUI(root)  # Variable kept to avoid linting warning
    root.mainloop()


if __name__ == "__main__":
    main()
