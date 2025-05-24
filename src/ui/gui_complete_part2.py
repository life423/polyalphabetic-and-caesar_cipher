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
            text="Advanced Encryption/Decryption Tool",
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