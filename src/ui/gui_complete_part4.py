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
    
    def _display_result(self, result):
        """Display the result in the result text area."""
        self.result_text.delete('1.0', tk.END)  # Clear previous results
        self.result_text.insert(tk.END, result)

    def _display_error(self, error_message):
        """Display an error message in the result text area."""
        self.result_text.delete('1.0', tk.END)  # Clear previous results
        self.result_text.insert(tk.END, f"Error: {error_message}")