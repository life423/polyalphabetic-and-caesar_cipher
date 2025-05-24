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