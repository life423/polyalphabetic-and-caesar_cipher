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