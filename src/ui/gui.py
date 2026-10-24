"""
Complete GUI implementation for CipherCraft.

This file contains the complete implementation of the GUI class with all methods.
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, font, messagebox
from src.services.cipher_service import CipherService


class CipherGUI:
    """
    A GUI application for encryption and decryption using multiple cipher algorithms.

    This class is responsible only for UI interactions and delegates
    all cipher operations to the CipherService.
    """

    # Modern color palette
    COLORS = {
        'primary': '#2D3E50',      # Dark blue-gray
        'secondary': '#1ABC9C',    # Teal
        'accent': '#3498DB',       # Blue
        'danger': '#E74C3C',       # Red
        'warning': '#F39C12',      # Orange
        'success': '#2ECC71',      # Green
        'light': '#ECF0F1',        # Light gray
        'dark': '#2C3E50',         # Dark blue-gray
        'text': '#34495E',         # Dark gray-blue
        'bg': '#F5F7FA'            # Light background
    }

    # Spacing scale (in pixels)
    SPACING = {
        'xs': 2,
        'sm': 5,
        'md': 10,
        'lg': 20,
        'xl': 30
    }

    def __init__(self, root):
        """
        Initialize the GUI components.

        Args:
            root: The Tkinter root window
        """
        self.root = root
        self.root.title("CipherCraft")
        self.root.configure(bg=self.COLORS['bg'])
        
        # Set minimum window size
        self.root.minsize(800, 650)
        
        # Initialize the service layer
        self.cipher_service = CipherService()
        
        # Setup custom fonts
        self._setup_fonts()
        
        # Create custom styles for ttk widgets
        self._create_styles()
        
        # Create and configure the UI components
        self._create_widgets()
        self._layout_widgets()
    
    def _setup_fonts(self):
        """Setup custom fonts for the application."""
        # Store fonts as instance variables for later use
        self.font_heading = font.Font(
            family='Arial', size=18, weight='bold')
        self.font_subheading = font.Font(
            family='Arial', size=12, weight='bold')
        self.font_body = font.Font(
            family='Arial', size=10)
        self.font_small = font.Font(
            family='Arial', size=9)
        self.font_button = font.Font(
            family='Arial', size=10, weight='bold')
        self.font_code = font.Font(
            family='Courier New', size=10)
    
    def _create_styles(self):
        """Create custom ttk styles for widgets."""
        style = ttk.Style()
        
        # Configure the overall theme
        style.theme_use('clam')  # Use a modern-looking base theme
        
        # Configure TLabel
        style.configure(
            'TLabel',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TFrame
        style.configure(
            'TFrame',
            background=self.COLORS['bg']
        )
        
        # Configure TLabelframe
        style.configure(
            'TLabelframe',
            background=self.COLORS['bg'],
            foreground=self.COLORS['primary'],
            font=self.font_subheading
        )
        style.configure(
            'TLabelframe.Label',
            background=self.COLORS['bg'],
            foreground=self.COLORS['primary'],
            font=self.font_subheading
        )
        
        # Configure TButton
        style.configure(
            'TButton',
            background=self.COLORS['primary'],
            foreground=self.COLORS['light'],
            font=self.font_button,
            padding=(self.SPACING['md'], self.SPACING['sm'])
        )
        
        # Special button styles
        style.configure(
            'Primary.TButton',
            background=self.COLORS['primary'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Success.TButton',
            background=self.COLORS['success'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Accent.TButton',
            background=self.COLORS['accent'],
            foreground='white',
            font=self.font_button
        )
        
        style.configure(
            'Warning.TButton',
            background=self.COLORS['warning'],
            foreground='white',
            font=self.font_button
        )
        
        # Configure TRadiobutton
        style.configure(
            'TRadiobutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TCheckbutton
        style.configure(
            'TCheckbutton',
            background=self.COLORS['bg'],
            foreground=self.COLORS['text'],
            font=self.font_body
        )
        
        # Configure TEntry
        style.configure(
            'TEntry',
            fieldbackground='white',
            foreground=self.COLORS['text'],
            font=self.font_body,
            padding=self.SPACING['sm']
        )
    def _create_widgets(self):
        """Create all the widgets for the application."""
        # Title
        self.title_label = tk.Label(
            self.root,
            text="CipherCraft",
            font=self.font_heading,
            bg=self.COLORS['bg'],
            fg=self.COLORS['primary']
        )
        
        self.subtitle_label = tk.Label(
            self.root,
            text="Classical Ciphers & Cryptanalysis",
            font=self.font_subheading,
            bg=self.COLORS['bg'],
            fg=self.COLORS['secondary']
        )

        # ===== Settings Frame =====
        self.settings_frame = ttk.LabelFrame(
            self.root,
            text="Cipher Settings",
            padding=self.SPACING['md']
        )

        # Cipher selection
        self.cipher_var = tk.StringVar(value="c")  # Default to Caesar
        cipher_selection = ttk.Frame(self.settings_frame)
        ttk.Label(
            cipher_selection,
            text="Cipher Type:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        
        cipher_types_frame = ttk.Frame(cipher_selection)
        # Row 1 of cipher types
        ttk.Radiobutton(
            cipher_types_frame,
            text="Caesar",
            variable=self.cipher_var,
            value="c",
            command=self._update_key_section
        ).grid(
            row=0, column=0, sticky="w", 
            padx=(0, self.SPACING['md']), pady=self.SPACING['sm']
        )
        ttk.Radiobutton(
            cipher_types_frame,
            text="Polyalphabetic",
            variable=self.cipher_var,
            value="p",
            command=self._update_key_section
        ).grid(
            row=0, column=1, sticky="w",
            padx=(0, self.SPACING['md']), pady=self.SPACING['sm']
        )
        ttk.Radiobutton(
            cipher_types_frame,
            text="Substitution",
            variable=self.cipher_var,
            value="s",
            command=self._update_key_section
        ).grid(row=0, column=2, sticky="w", pady=self.SPACING['sm'])
        
        # Row 2 of cipher types
        ttk.Radiobutton(
            cipher_types_frame,
            text="Transposition",
            variable=self.cipher_var,
            value="t",
            command=self._update_key_section
        ).grid(
            row=1, column=0, sticky="w",
            padx=(0, self.SPACING['md']), pady=self.SPACING['sm']
        )
        ttk.Radiobutton(
            cipher_types_frame,
            text="Rail Fence",
            variable=self.cipher_var,
            value="r",
            command=self._update_key_section
        ).grid(
            row=1, column=1, sticky="w",
            padx=(0, self.SPACING['md']), pady=self.SPACING['sm']
        )
        ttk.Radiobutton(
            cipher_types_frame,
            text="Affine",
            variable=self.cipher_var,
            value="a",
            command=self._update_key_section
        ).grid(row=1, column=2, sticky="w", pady=self.SPACING['sm'])
        
        cipher_types_frame.pack(side="left")
        cipher_selection.pack(
            fill="x", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Operation selection
        self.action_var = tk.StringVar(value="e")  # 'e' for encrypt, 'd' for decrypt
        operation_selection = ttk.Frame(self.settings_frame)
        ttk.Label(
            operation_selection,
            text="Operation:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        
        operation_buttons_frame = ttk.Frame(operation_selection)
        ttk.Radiobutton(
            operation_buttons_frame,
            text="Encrypt",
            variable=self.action_var,
            value="e"
        ).pack(side="left", padx=(0, self.SPACING['lg']))
        ttk.Radiobutton(
            operation_buttons_frame,
            text="Decrypt",
            variable=self.action_var,
            value="d"
        ).pack(side="left")
        operation_buttons_frame.pack(side="left")
        operation_selection.pack(
            fill="x", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Key section frame - will hold different key inputs based on cipher type
        self.key_section_frame = ttk.Frame(self.settings_frame)
        
        # Create different key input frames for each cipher type
        # We'll show/hide them based on the selected cipher
        
        # 1. Caesar cipher key input (shift)
        self.caesar_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.caesar_key_frame,
            text="Shift Value:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.caesar_key_entry = ttk.Entry(
            self.caesar_key_frame, width=10, font=self.font_body
        )
        self.caesar_key_entry.pack(side="left")
        ttk.Label(
            self.caesar_key_frame,
            text="(1-25)", font=self.font_small
        ).pack(side="left", padx=(self.SPACING['sm'], 0))
        
        # 2. Polyalphabetic cipher key input (keyword)
        self.poly_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.poly_key_frame,
            text="Keyword:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.poly_key_entry = ttk.Entry(
            self.poly_key_frame, width=30, font=self.font_body
        )
        self.poly_key_entry.pack(side="left", fill="x", expand=True)
        
        # 3. Substitution cipher key input (26 chars)
        self.sub_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.sub_key_frame,
            text="Key:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.sub_key_entry = ttk.Entry(
            self.sub_key_frame, width=30, font=self.font_body
        )
        self.sub_key_entry.pack(side="left", fill="x", expand=True)
        self.sub_gen_key_button = ttk.Button(
            self.sub_key_frame,
            text="Generate Key",
            style="Accent.TButton",
            command=self._generate_substitution_key
        )
        self.sub_gen_key_button.pack(side="left", padx=(self.SPACING['md'], 0))
        
        # 4. Transposition cipher key input
        self.trans_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.trans_key_frame,
            text="Key:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.trans_key_entry = ttk.Entry(
            self.trans_key_frame, width=30, font=self.font_body
        )
        self.trans_key_entry.pack(side="left", fill="x", expand=True)
        
        # 5. Rail Fence cipher key input
        self.rail_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.rail_key_frame,
            text="Rails:",
            font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.rail_key_entry = ttk.Entry(
            self.rail_key_frame, width=10, font=self.font_body
        )
        self.rail_key_entry.pack(side="left")
        ttk.Label(
            self.rail_key_frame,
            text="(2 or more)", font=self.font_small
        ).pack(side="left", padx=(self.SPACING['sm'], 0))
        
        # 6. Affine cipher key input
        self.affine_key_frame = ttk.Frame(self.key_section_frame)
        ttk.Label(
            self.affine_key_frame,
            text="a value:", font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.affine_a_entry = ttk.Entry(
            self.affine_key_frame, width=5, font=self.font_body
        )
        self.affine_a_entry.pack(side="left")
        ttk.Label(
            self.affine_key_frame,
            text="b value:", font=self.font_subheading
        ).pack(
            side="left", padx=(self.SPACING['md'], self.SPACING['md'])
        )
        self.affine_b_entry = ttk.Entry(
            self.affine_key_frame, width=5, font=self.font_body
        )
        self.affine_b_entry.pack(side="left")
        ttk.Label(
            self.affine_key_frame,
            text="(a must be coprime to 26)", font=self.font_small
        ).pack(side="left", padx=(self.SPACING['sm'], 0))
        # Add all frames to the key section (only one will be visible at a time)
        self.key_section_frame.pack(
            fill="x", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Help text container - will be updated based on the selected cipher
        self.help_text_var = tk.StringVar()
        
        # Initialize with Caesar cipher key frame visible
        self._update_key_section()
        self.help_text_label = ttk.Label(
            self.settings_frame,
            textvariable=self.help_text_var,
            font=self.font_small,
            wraplength=700,  # Wrap text if it's too long
            foreground=self.COLORS['text']
        )
        self.help_text_label.pack(
            padx=self.SPACING['md'], pady=(0, self.SPACING['md']), anchor="w"
        )

        # ===== Input/Output Frame =====
        self.io_frame = ttk.LabelFrame(
            self.root,
            text="Input/Output",
            padding=self.SPACING['md']
        )

        # Explicit input mode avoids interpreting ordinary text as a filename.
        self.input_mode_var = tk.StringVar(value="text")
        mode_frame = ttk.Frame(self.io_frame)
        ttk.Label(mode_frame, text="Input Mode:", font=self.font_subheading).pack(
            side="left", padx=(0, self.SPACING['md'])
        )
        ttk.Radiobutton(
            mode_frame, text="Text", value="text", variable=self.input_mode_var,
            command=self._update_input_mode,
        ).pack(side="left", padx=(0, self.SPACING['lg']))
        ttk.Radiobutton(
            mode_frame, text="File", value="file", variable=self.input_mode_var,
            command=self._update_input_mode,
        ).pack(side="left")
        mode_frame.pack(fill="x", padx=self.SPACING['md'], pady=self.SPACING['sm'])

        # Input text or file
        input_frame = ttk.Frame(self.io_frame)
        ttk.Label(
            input_frame,
            text="Text / File Path:", font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.input_entry = ttk.Entry(input_frame, font=self.font_body)
        self.input_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, self.SPACING['md'])
        )
        self.input_file_button = ttk.Button(
            input_frame,
            text="Select File...",
            style="Accent.TButton",
            command=self._select_input_file
        )
        self.input_file_button.pack(side="left")
        input_frame.pack(
            fill="x", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Output file
        output_frame = ttk.Frame(self.io_frame)
        ttk.Label(
            output_frame,
            text="Output File:", font=self.font_subheading
        ).pack(side="left", padx=(0, self.SPACING['md']))
        self.output_entry = ttk.Entry(output_frame, font=self.font_body)
        self.output_entry.pack(
            side="left", fill="x", expand=True,
            padx=(0, self.SPACING['md'])
        )
        self.output_file_button = ttk.Button(
            output_frame,
            text="Select File...",
            style="Accent.TButton",
            command=self._select_output_file
        )
        self.output_file_button.pack(side="left")
        output_frame.pack(
            fill="x", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Delete input file option
        self.delete_input_var = tk.BooleanVar(value=False)
        self.delete_input_checkbox = ttk.Checkbutton(
            self.io_frame,
            text="Delete source file after processing",
            variable=self.delete_input_var
        )
        self.delete_input_checkbox.pack(
            anchor="w", padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        self._update_input_mode()
        
        # ===== Buttons Frame =====
        self.buttons_frame = ttk.Frame(self.root)

        # Process button
        self.process_button = ttk.Button(
            self.buttons_frame,
            text="Process",
            style="Success.TButton",
            command=self._process_text
        )

        # Analyze button
        self.analyze_button = ttk.Button(
            self.buttons_frame,
            text="Analyze Cipher",
            style="Primary.TButton",
            command=self._analyze_text
        )

        # ===== Results Frame =====
        self.results_frame = ttk.LabelFrame(
            self.root,
            text="Results",
            padding=self.SPACING['md']
        )
        
        # Results area
        self.result_text = scrolledtext.ScrolledText(
            self.results_frame,
            height=10,
            width=60,
            wrap=tk.WORD,
            font=self.font_code,
            bd=2,  # Add subtle border
            relief=tk.GROOVE,
            bg='white',  # White background for text area
            fg=self.COLORS['text'],  # Explicit text color: system default turns white in macOS Dark Mode
            insertbackground=self.COLORS['text']  # Visible cursor on the white background
        )
        self.result_text.pack(
            fill="both", expand=True,
            padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # ===== Analysis Frame =====
        self.analysis_frame = ttk.LabelFrame(
            self.root,
            text="Statistical Key Suggestions",
            padding=self.SPACING['md']
        )

        # Analysis results
        self.analysis_result = scrolledtext.ScrolledText(
            self.analysis_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            font=self.font_code,
            bd=2,  # Add subtle border
            relief=tk.GROOVE,
            bg='white',  # White background for text area
            fg=self.COLORS['text'],  # Explicit text color: system default turns white in macOS Dark Mode
            insertbackground=self.COLORS['text']  # Visible cursor on the white background
        )
        self.analysis_result.pack(
            fill="both", expand=True,
            padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Apply suggestion button
        self.apply_button = ttk.Button(
            self.analysis_frame,
            text="Apply Best Guess",
            style="Warning.TButton",
            command=self._apply_suggested_key,
            state=tk.DISABLED
        )
        self.apply_button.pack(pady=self.SPACING['md'])

        # Store analysis results for later use
        self.analysis_results = []
        self.selected_suggestion = None
    
    def _layout_widgets(self):
        """Arrange all widgets in the UI."""
        # Add some padding around all widgets
        for child in self.root.winfo_children():
            child.grid_configure(padx=self.SPACING['md'], pady=self.SPACING['md'])
            
        # Configure the grid
        self.root.grid_columnconfigure(0, weight=1)
        
        # Title at the top
        self.title_label.grid(
            row=0, column=0, pady=(self.SPACING['lg'], 0), sticky="ew"
        )
        self.subtitle_label.grid(
            row=1, column=0, pady=(0, self.SPACING['md']), sticky="ew"
        )
        
        # Settings frame
        self.settings_frame.grid(
            row=2, column=0, sticky="ew",
            padx=self.SPACING['lg'], pady=self.SPACING['md']
        )
        
        # Input/Output frame
        self.io_frame.grid(
            row=3, column=0, sticky="ew",
            padx=self.SPACING['lg'], pady=self.SPACING['md']
        )
        
        # Buttons frame
        self.buttons_frame.grid(row=4, column=0, pady=self.SPACING['md'])
        self.process_button.pack(
            side="left", padx=(0, self.SPACING['md']), pady=self.SPACING['sm']
        )
        self.analyze_button.pack(side="left", pady=self.SPACING['sm'])
        
        # Results frame
        self.results_frame.grid(
            row=5, column=0, sticky="nsew",
            padx=self.SPACING['lg'], pady=self.SPACING['md']
        )
        
        # Analysis frame - initially hidden
        self.analysis_frame.grid(
            row=6, column=0, sticky="nsew",
            padx=self.SPACING['lg'], pady=self.SPACING['md']
        )
        self.analysis_frame.grid_remove()  # Hide initially
        
        # Make the results area expandable
        self.root.grid_rowconfigure(5, weight=1)
    def _update_input_mode(self):
        """Keep file-only controls inactive when working with typed text."""
        is_file = self.input_mode_var.get() == "file"
        self.delete_input_checkbox.configure(
            state=tk.NORMAL if is_file else tk.DISABLED
        )
        if not is_file:
            self.delete_input_var.set(False)

    def _select_input_file(self):
        """Open file dialog, then explicitly switch to file mode."""
        filename = filedialog.askopenfilename()
        if filename:
            self.input_mode_var.set("file")
            self._update_input_mode()
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)

    def _select_output_file(self):
        """Open file dialog to select an output file."""
        filename = filedialog.asksaveasfilename()
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def _update_key_section(self):
        """Update cipher-specific controls and invalidate obsolete analysis results."""
        if hasattr(self, "analysis_results"):
            self.analysis_results = []
            self.selected_suggestion = None
            self.apply_button.configure(state=tk.DISABLED)
        if hasattr(self, "analyze_button"):
            self.analyze_button.configure(
                state=tk.NORMAL if self.cipher_var.get() in ("c", "p") else tk.DISABLED
            )
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
                "Caesar cipher shifts each letter in the plaintext by a fixed "
                "number of positions in the alphabet. Enter a shift value "
                "between 1 and 25."
            )
        elif cipher_type == 'p':  # Polyalphabetic
            self.poly_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Polyalphabetic (Vigenère) cipher uses a keyword to determine "
                "different shift values for each letter. Enter a keyword "
                "without spaces."
            )
        elif cipher_type == 's':  # Substitution
            self.sub_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Substitution cipher replaces each letter with another letter "
                "according to a fixed mapping. Enter a 26-character key, or use "
                "the 'Generate Key' button to create a random one."
            )
        elif cipher_type == 't':  # Transposition
            self.trans_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Transposition cipher rearranges the letters of the plaintext "
                "according to a key. Enter a word or comma-separated numbers "
                "(e.g., '2,0,1,3' or 'KEY')."
            )
        elif cipher_type == 'r':  # Rail Fence
            self.rail_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Rail Fence cipher writes the message in a zig-zag pattern "
                "across a number of rows (rails), then reads off each row. "
                "Enter the number of rails (2 or more)."
            )
        elif cipher_type == 'a':  # Affine
            self.affine_key_frame.pack(fill="x")
            self.help_text_var.set(
                "Affine cipher uses the formula (ax + b) mod 26 for encryption, "
                "where x is the position of each letter. Value 'a' must be "
                "coprime to 26 (typically 1, 3, 5, 7, 9, 11, 15, 17, 19, 21, "
                "23, or 25)."
            )
    
    def _generate_substitution_key(self):
        """Generate a random substitution key and insert it into the entry field."""
        # Use the service to generate a random key
        key = self.cipher_service.generate_substitution_key()
        
        # Clear the entry and insert the new key
        self.sub_key_entry.delete(0, tk.END)
        self.sub_key_entry.insert(0, key)

    def _display_result(self, result):
        """Display the result in the result text area."""
        self.result_text.delete('1.0', tk.END)  # Clear previous results
        self.result_text.insert(tk.END, result)

    def _display_error(self, error_message):
        """Display an error message in the result text area."""
        self.result_text.delete('1.0', tk.END)  # Clear previous results
        self.result_text.insert(tk.END, f"Error: {error_message}")
    def _process_text(self):
        """Validate UI state and dispatch every cipher through one shared path."""
        self.result_text.delete('1.0', tk.END)
        code = self.cipher_var.get()
        encrypt = self.action_var.get() == 'e'
        source = self.input_entry.get()
        output_file = self.output_entry.get()
        delete_input = self.delete_input_var.get()

        if not source:
            self._display_error("Please enter text or select a file for input.")
            return

        try:
            if code == 'c':
                key = int(self.caesar_key_entry.get())
                if not 1 <= key <= 25:
                    raise ValueError("Shift value must be between 1 and 25.")
                algorithm = "caesar"
            elif code == 'p':
                key = self.poly_key_entry.get()
                if not key:
                    raise ValueError("Please enter a keyword.")
                algorithm = "polyalphabetic"
            elif code == 's':
                key = self.sub_key_entry.get()
                if len(key) != 26:
                    raise ValueError("Substitution key must be exactly 26 characters long.")
                algorithm = "substitution"
            elif code == 't':
                key = self.trans_key_entry.get()
                if not key:
                    raise ValueError("Please enter a transposition key.")
                if ',' in key:
                    try:
                        key = [int(part.strip()) for part in key.split(',')]
                    except ValueError as exc:
                        raise ValueError("Numeric key must contain only integers.") from exc
                algorithm = "transposition"
            elif code == 'r':
                key = int(self.rail_key_entry.get())
                if key < 2:
                    raise ValueError("Number of rails must be at least 2.")
                algorithm = "rail_fence"
            elif code == 'a':
                key = (int(self.affine_a_entry.get()), int(self.affine_b_entry.get()))
                algorithm = "affine"
            else:
                raise ValueError("Select a supported cipher.")

            action = "encrypt" if encrypt else "decrypt"
            transform = getattr(self.cipher_service, f"{action}_{algorithm}")
            if self.input_mode_var.get() == "file":
                if not os.path.isfile(source):
                    raise ValueError("Input file not found. Select an existing file.")
                if not output_file:
                    raise ValueError("Please specify an output file.")
                if delete_input and not messagebox.askyesno(
                    "Delete source file?",
                    "The original source file will be permanently deleted after "
                    "a successful operation. Continue?",
                    parent=self.root,
                ):
                    return
                result = self.cipher_service.process_file_with_cipher(
                    source, output_file, lambda content: transform(content, key), delete_input
                )
            else:
                result = transform(source, key)
            self._display_result(result)
        except (ValueError, TypeError, OSError) as exc:
            self._display_error(str(exc))

    def _analyze_text(self):
        """
        Analyze encrypted text using AI-driven techniques.
        
        This method attempts to determine the encryption method and key
        used to encrypt the provided text.
        """
        # Get the input text
        input_text = self.input_entry.get()
        
        if not input_text:
            self._display_error("Please enter text to analyze.")
            return
            
        # Only treat a path as a file when the user explicitly selected File mode.
        if self.input_mode_var.get() == "file":
            try:
                with open(input_text, 'r', encoding='utf-8') as file:
                    text = file.read()
            except Exception as e:
                self._display_error(f"Could not read file: {e}")
                return
        else:
            text = input_text
        
        # Get the selected cipher type and invalidate stale suggestions first.
        cipher_type = self.cipher_var.get()
        self.analysis_results = []
        self.selected_suggestion = None
        self.apply_button.configure(state=tk.DISABLED)
        
        # Show the analysis frame
        self.analysis_frame.grid()
        self.analysis_result.delete('1.0', tk.END)
        
        # Perform analysis based on cipher type
        if cipher_type == 'c':  # Caesar cipher
            self.analysis_result.insert(tk.END, "Ranking Caesar keys using statistical analysis...\n\n")
            results = self.cipher_service.analyze_caesar_encryption(text)
            
            if not results:
                self.analysis_result.insert(tk.END, "No results found. Try a different cipher type.")
                return
                
            # Store results for later use
            self.analysis_results = results
            
            # Display results
            for i, result in enumerate(results):
                self.analysis_result.insert(
                    tk.END, 
                    f"Suggestion {i+1}: Shift = {result['shift']} "
                    f"(Confidence: {result['confidence']}%)\n"
                )
                self.analysis_result.insert(tk.END, f"Sample: {result['sample']}\n\n")
                
            # Enable the apply button
            self.apply_button.config(state=tk.NORMAL)
        elif cipher_type == 'p':  # Polyalphabetic cipher
            self.analysis_result.insert(tk.END, "Ranking Vigenère keys using statistical analysis...\n\n")
            results = self.cipher_service.analyze_polyalphabetic_encryption(text)
            
            if not results:
                self.analysis_result.insert(tk.END, "No results found. Try a different cipher type.")
                return
                
            # Store results for later use
            self.analysis_results = results
            
            # Display results
            for i, result in enumerate(results):
                self.analysis_result.insert(
                    tk.END, 
                    f"Suggestion {i+1}: Keyword = '{result['keyword']}' "
                    f"(Confidence: {result['confidence']}%)\n"
                )
                self.analysis_result.insert(tk.END, f"Sample: {result['sample']}\n\n")
                
            # Enable the apply button
            self.apply_button.config(state=tk.NORMAL)
            
        else:
            self.analysis_result.insert(
                tk.END, 
                f"AI analysis is currently only available for Caesar and "
                f"Polyalphabetic ciphers.\n\n"
                f"Please select one of these cipher types and try again."
            )

    def _apply_suggested_key(self):
        """
        Apply the selected key from the analysis results.
        
        This method takes the first (highest confidence) result from the
        analysis and applies it to the appropriate key field.
        """
        if not self.analysis_results:
            return
            
        # Get the selected cipher type
        cipher_type = self.cipher_var.get()
        
        # Get the highest confidence result
        result = self.analysis_results[0]
        
        if cipher_type == 'c':  # Caesar cipher
            # Set the shift value
            self.caesar_key_entry.delete(0, tk.END)
            self.caesar_key_entry.insert(0, str(result['shift']))
            
        elif cipher_type == 'p':  # Polyalphabetic cipher
            # Set the keyword
            self.poly_key_entry.delete(0, tk.END)
            self.poly_key_entry.insert(0, result['keyword'])
            
        # Set action to decrypt
        self.action_var.set('d')
        
        # Show a message
        messagebox.showinfo(
            "Key Applied", 
            "The highest-ranked key has been applied. Click 'Process' to decrypt."
        )


def main():
    """Main function to start the GUI application."""
    root = tk.Tk()
    app = CipherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
