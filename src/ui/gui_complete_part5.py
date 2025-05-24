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
                    is_encrypt, key, input_text, output_file, 
                    is_file_input, delete_input
                )
            elif cipher_type == 'p':  # Polyalphabetic cipher
                key = self.poly_key_entry.get()
                if not key:
                    self._display_error("Please enter a keyword.")
                    return
                self._process_polyalphabetic_cipher(
                    is_encrypt, key, input_text, output_file, 
                    is_file_input, delete_input
                )
            elif cipher_type == 's':  # Substitution cipher
                key = self.sub_key_entry.get()
                if not key or len(key) != 26:
                    self._display_error("Substitution key must be exactly 26 characters long.")
                    return
                self._process_substitution_cipher(
                    is_encrypt, key, input_text, output_file, 
                    is_file_input, delete_input
                )
            elif cipher_type == 't':  # Transposition cipher
                key = self.trans_key_entry.get()
                if not key:
                    self._display_error("Please enter a transposition key.")
                    return
                self._process_transposition_cipher(
                    is_encrypt, key, input_text, output_file, 
                    is_file_input, delete_input
                )
            elif cipher_type == 'r':  # Rail Fence cipher
                key = self.rail_key_entry.get()
                if not key:
                    self._display_error("Please enter the number of rails.")
                    return
                self._process_rail_fence_cipher(
                    is_encrypt, key, input_text, output_file, 
                    is_file_input, delete_input
                )
            elif cipher_type == 'a':  # Affine cipher
                a_value = self.affine_a_entry.get()
                b_value = self.affine_b_entry.get()
                if not a_value or not b_value:
                    self._display_error("Please enter both 'a' and 'b' values.")
                    return
                self._process_affine_cipher(
                    is_encrypt, (a_value, b_value), input_text, output_file, 
                    is_file_input, delete_input
                )
        except Exception as e:
            self._display_error(str(e))
    
    def _process_caesar_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
        """
        Process text using the Caesar cipher.
        
        Args:
            is_encrypt (bool): True for encryption, False for decryption
            key (str): The shift value as a string
            input_text (str): The text to process or path to input file
            output_file (str): Path to output file (if file output is desired)
            is_file_input (bool): True if input is a file path, False if direct text
            delete_input (bool): Whether to delete input file after processing
        """
        try:
            # Convert shift to integer
            shift = int(key)
            
            # Validate shift value
            if shift < 1 or shift > 25:
                self._display_error("Shift value must be between 1 and 25.")
                return
                
            if is_file_input:
                # Process file
                if not output_file:
                    self._display_error("Please specify an output file.")
                    return
                    
                # Create a cipher function to pass to the file processor
                def cipher_func(content):
                    if is_encrypt:
                        return self.cipher_service.encrypt_caesar(content, shift)
                    else:
                        return self.cipher_service.decrypt_caesar(content, shift)
                
                # Process the file
                result = self.cipher_service.process_file_with_cipher(
                    input_text, output_file, cipher_func, delete_input
                )
                self._display_result(result)
            else:
                # Process direct text input
                if is_encrypt:
                    result = self.cipher_service.encrypt_caesar(input_text, shift)
                else:
                    result = self.cipher_service.decrypt_caesar(input_text, shift)
                self._display_result(result)
                
        except ValueError:
            self._display_error("Invalid shift value. Please enter a number between 1 and 25.")