"""
Additional methods for the CipherGUI class.

This file contains implementations of the missing methods in the GUI class.
These methods will be integrated into the main gui.py file.
"""

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

def _process_polyalphabetic_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """
    Process text using the Polyalphabetic cipher.
    
    Args:
        is_encrypt (bool): True for encryption, False for decryption
        key (str): The keyword
        input_text (str): The text to process or path to input file
        output_file (str): Path to output file (if file output is desired)
        is_file_input (bool): True if input is a file path, False if direct text
        delete_input (bool): Whether to delete input file after processing
    """
    try:
        # Validate keyword
        if not key:
            self._display_error("Please enter a keyword.")
            return
            
        if is_file_input:
            # Process file
            if not output_file:
                self._display_error("Please specify an output file.")
                return
                
            # Create a cipher function to pass to the file processor
            def cipher_func(content):
                if is_encrypt:
                    return self.cipher_service.encrypt_polyalphabetic(content, key)
                else:
                    return self.cipher_service.decrypt_polyalphabetic(content, key)
            
            # Process the file
            result = self.cipher_service.process_file_with_cipher(
                input_text, output_file, cipher_func, delete_input
            )
            self._display_result(result)
        else:
            # Process direct text input
            if is_encrypt:
                result = self.cipher_service.encrypt_polyalphabetic(input_text, key)
            else:
                result = self.cipher_service.decrypt_polyalphabetic(input_text, key)
            self._display_result(result)
            
    except ValueError as e:
        self._display_error(str(e))

def _process_substitution_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """
    Process text using the Substitution cipher.
    
    Args:
        is_encrypt (bool): True for encryption, False for decryption
        key (str): The substitution key (26 characters)
        input_text (str): The text to process or path to input file
        output_file (str): Path to output file (if file output is desired)
        is_file_input (bool): True if input is a file path, False if direct text
        delete_input (bool): Whether to delete input file after processing
    """
    try:
        # Validate key
        if not key or len(key) != 26:
            self._display_error("Substitution key must be exactly 26 characters long.")
            return
            
        if is_file_input:
            # Process file
            if not output_file:
                self._display_error("Please specify an output file.")
                return
                
            # Create a cipher function to pass to the file processor
            def cipher_func(content):
                if is_encrypt:
                    return self.cipher_service.encrypt_substitution(content, key)
                else:
                    return self.cipher_service.decrypt_substitution(content, key)
            
            # Process the file
            result = self.cipher_service.process_file_with_cipher(
                input_text, output_file, cipher_func, delete_input
            )
            self._display_result(result)
        else:
            # Process direct text input
            if is_encrypt:
                result = self.cipher_service.encrypt_substitution(input_text, key)
            else:
                result = self.cipher_service.decrypt_substitution(input_text, key)
            self._display_result(result)
            
    except ValueError as e:
        self._display_error(str(e))

def _process_transposition_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """
    Process text using the Transposition cipher.
    
    Args:
        is_encrypt (bool): True for encryption, False for decryption
        key (str): The transposition key (word or comma-separated numbers)
        input_text (str): The text to process or path to input file
        output_file (str): Path to output file (if file output is desired)
        is_file_input (bool): True if input is a file path, False if direct text
        delete_input (bool): Whether to delete input file after processing
    """
    try:
        # Validate key
        if not key:
            self._display_error("Please enter a transposition key.")
            return
            
        # Convert key to numeric format if it contains commas
        if ',' in key:
            try:
                key = [int(k.strip()) for k in key.split(',')]
            except ValueError:
                self._display_error("Numeric key must contain only integers.")
                return
            
        if is_file_input:
            # Process file
            if not output_file:
                self._display_error("Please specify an output file.")
                return
                
            # Create a cipher function to pass to the file processor
            def cipher_func(content):
                if is_encrypt:
                    return self.cipher_service.encrypt_transposition(content, key)
                else:
                    return self.cipher_service.decrypt_transposition(content, key)
            
            # Process the file
            result = self.cipher_service.process_file_with_cipher(
                input_text, output_file, cipher_func, delete_input
            )
            self._display_result(result)
        else:
            # Process direct text input
            if is_encrypt:
                result = self.cipher_service.encrypt_transposition(input_text, key)
            else:
                result = self.cipher_service.decrypt_transposition(input_text, key)
            self._display_result(result)
            
    except ValueError as e:
        self._display_error(str(e))

def _process_rail_fence_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """
    Process text using the Rail Fence cipher.
    
    Args:
        is_encrypt (bool): True for encryption, False for decryption
        key (str): The number of rails as a string
        input_text (str): The text to process or path to input file
        output_file (str): Path to output file (if file output is desired)
        is_file_input (bool): True if input is a file path, False if direct text
        delete_input (bool): Whether to delete input file after processing
    """
    try:
        # Convert rails to integer
        rails = int(key)
        
        # Validate rails value
        if rails < 2:
            self._display_error("Number of rails must be at least 2.")
            return
            
        if is_file_input:
            # Process file
            if not output_file:
                self._display_error("Please specify an output file.")
                return
                
            # Create a cipher function to pass to the file processor
            def cipher_func(content):
                if is_encrypt:
                    return self.cipher_service.encrypt_rail_fence(content, rails)
                else:
                    return self.cipher_service.decrypt_rail_fence(content, rails)
            
            # Process the file
            result = self.cipher_service.process_file_with_cipher(
                input_text, output_file, cipher_func, delete_input
            )
            self._display_result(result)
        else:
            # Process direct text input
            if is_encrypt:
                result = self.cipher_service.encrypt_rail_fence(input_text, rails)
            else:
                result = self.cipher_service.decrypt_rail_fence(input_text, rails)
            self._display_result(result)
            
    except ValueError:
        self._display_error("Invalid rail value. Please enter a number greater than or equal to 2.")

def _process_affine_cipher(self, is_encrypt, key, input_text, output_file, is_file_input, delete_input):
    """
    Process text using the Affine cipher.
    
    Args:
        is_encrypt (bool): True for encryption, False for decryption
        key (tuple): The (a, b) values as strings
        input_text (str): The text to process or path to input file
        output_file (str): Path to output file (if file output is desired)
        is_file_input (bool): True if input is a file path, False if direct text
        delete_input (bool): Whether to delete input file after processing
    """
    try:
        # Convert a and b to integers
        a_value, b_value = key
        a = int(a_value)
        b = int(b_value)
        
        # Key pair for Affine cipher
        key_pair = (a, b)
            
        if is_file_input:
            # Process file
            if not output_file:
                self._display_error("Please specify an output file.")
                return
                
            # Create a cipher function to pass to the file processor
            def cipher_func(content):
                if is_encrypt:
                    return self.cipher_service.encrypt_affine(content, key_pair)
                else:
                    return self.cipher_service.decrypt_affine(content, key_pair)
            
            # Process the file
            result = self.cipher_service.process_file_with_cipher(
                input_text, output_file, cipher_func, delete_input
            )
            self._display_result(result)
        else:
            # Process direct text input
            if is_encrypt:
                result = self.cipher_service.encrypt_affine(input_text, key_pair)
            else:
                result = self.cipher_service.decrypt_affine(input_text, key_pair)
            self._display_result(result)
            
    except ValueError as e:
        self._display_error(str(e))

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
        
    # Check if input is a file
    if os.path.isfile(input_text):
        try:
            with open(input_text, 'r') as file:
                text = file.read()
        except Exception as e:
            self._display_error(f"Could not read file: {e}")
            return
    else:
        text = input_text
    
    # Get the selected cipher type
    cipher_type = self.cipher_var.get()
    
    # Show the analysis frame
    self.analysis_frame.grid()
    self.analysis_result.delete('1.0', tk.END)
    
    # Perform analysis based on cipher type
    if cipher_type == 'c':  # Caesar cipher
        self.analysis_result.insert(tk.END, "Analyzing with Caesar cipher techniques...\n\n")
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
        self.analysis_result.insert(tk.END, "Analyzing with Polyalphabetic cipher techniques...\n\n")
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
        "The suggested key has been applied. Click 'Process' to decrypt."
    )