"""
Core Cipher Algorithms - Implements the fundamental encryption/decryption algorithms.

This module contains the core implementations of various cipher algorithms 
without any I/O operations or business logic.
"""

class CaesarCipher:
    """Implements the Caesar cipher encryption and decryption algorithm."""
    
    # ASCII offset constants
    UPPERCASE_OFFSET = 65  # ASCII code for 'A'
    LOWERCASE_OFFSET = 97  # ASCII code for 'a'
    ALPHABET_SIZE = 26     # Number of letters in the English alphabet
    
    @classmethod
    def transform(cls, text, shift, encrypt=True):
        """
        Apply the Caesar cipher to the given text.
        
        Args:
            text (str): The text to encrypt or decrypt
            shift (int): The number of positions to shift characters
            encrypt (bool): True for encryption, False for decryption
            
        Returns:
            str: The encrypted or decrypted text
        """
        result = ''
        
        # Adjust shift for decryption (in opposite direction)
        effective_shift = shift if encrypt else -shift
        
        for char in text:
            if char.isalpha():
                # Determine the ASCII offset based on case
                offset = cls.UPPERCASE_OFFSET if char.isupper() else cls.LOWERCASE_OFFSET
                
                # Apply the shift and ensure it wraps around the alphabet
                new_index = (ord(char) - offset + effective_shift) % cls.ALPHABET_SIZE
                
                # Convert back to a character and add to result
                result += chr(new_index + offset)
            else:
                # Non-alphabetic characters remain unchanged
                result += char
                
        return result


class PolyalphabeticCipher:
    """Implements the Polyalphabetic (Vigenère) cipher encryption and decryption algorithm."""
    
    # ASCII offset constants
    UPPERCASE_OFFSET = 65  # ASCII code for 'A'
    LOWERCASE_OFFSET = 97  # ASCII code for 'a'
    ALPHABET_SIZE = 26     # Number of letters in the English alphabet
    
    @classmethod
    def transform(cls, text, keyword, encrypt=True):
        """
        Apply the Polyalphabetic (Vigenère) cipher to the given text using the provided keyword.
        
        Args:
            text (str): The text to encrypt or decrypt
            keyword (str): The keyword to use for the cipher
            encrypt (bool): True for encryption, False for decryption
            
        Returns:
            str: The encrypted or decrypted text
        """
        # Ensure keyword is not empty
        if not keyword:
            raise ValueError("Keyword cannot be empty")
            
        # Convert the keyword to lowercase and repeat it to match the length of the text
        # This creates a key sequence that's as long as the input text
        keyword = (keyword * (len(text) // len(keyword) + 1)).lower()
        result = []
        key_idx = 0
        
        for char in text:
            if char.isalpha():
                # Get the current key character
                key_char = keyword[key_idx]
                key_idx = (key_idx + 1) % len(keyword)
                
                # Calculate the shift value from the key character (a=0, b=1, etc.)
                shift = ord(key_char) - cls.LOWERCASE_OFFSET
                
                # Adjust shift direction for decryption
                if not encrypt:
                    shift = -shift
                
                # Determine the ASCII offset based on case
                offset = cls.UPPERCASE_OFFSET if char.isupper() else cls.LOWERCASE_OFFSET
                
                # Apply the shift and wrap around the alphabet
                shifted_index = (ord(char) - offset + shift) % cls.ALPHABET_SIZE
                
                # Convert back to a character and add to result
                result.append(chr(shifted_index + offset))
            else:
                # Non-alphabetic characters remain unchanged
                result.append(char)
                # Don't advance the key for non-alphabetic characters
        
        return ''.join(result)
