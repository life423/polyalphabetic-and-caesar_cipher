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

        # Input text or file
        input_frame = ttk.Frame(self.io_frame)
        ttk.Label(
            input_frame,
            text="Input:", font=self.font_subheading
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
            text="Output:", font=self.font_subheading
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
        ttk.Checkbutton(
            self.io_frame,
            text="Delete input file after processing",
            variable=self.delete_input_var
        ).pack(anchor="w", padx=self.SPACING['md'], pady=self.SPACING['md'])
        
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
            text="AI Analysis",
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
            bg='white'  # White background for text area
        )
        self.result_text.pack(
            fill="both", expand=True,
            padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # ===== Analysis Frame =====
        self.analysis_frame = ttk.LabelFrame(
            self.root,
            text="AI Analysis Results",
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
            bg='white'  # White background for text area
        )
        self.analysis_result.pack(
            fill="both", expand=True,
            padx=self.SPACING['md'], pady=self.SPACING['md']
        )
        
        # Apply suggestion button
        self.apply_button = ttk.Button(
            self.analysis_frame,
            text="Apply Selected Key",
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