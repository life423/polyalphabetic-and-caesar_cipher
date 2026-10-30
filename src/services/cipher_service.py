"""
Cipher Service Module - Coordinates cipher operations and file handling.

This module serves as a facade for the cipher operations, coordinating between
the core cipher algorithms and file handling services.
"""

from src.core.ciphers import (
    CaesarCipher, PolyalphabeticCipher, SubstitutionCipher,
    TranspositionCipher, RailFenceCipher, AffineCipher
)
from src.services.file_service import FileService
from src.ai.analyzer import CipherAnalyzer


class CipherService:
    """
    Coordinates cipher operations and file handling.
    
    This class acts as a service layer, providing a simplified interface
    for performing cipher operations while abstracting away the details
    of the underlying implementations.
    """
    
    def __init__(self):
        """Initialize the CipherService with required dependencies."""
        self.file_service = FileService()
    
    # Caesar Cipher Methods
    def encrypt_caesar(self, text, shift):
        """
        Encrypt text using the Caesar cipher.
        
        Args:
            text (str): The text to encrypt
            shift (int): The number of positions to shift characters
            
        Returns:
            str: The encrypted text
        """
        return CaesarCipher.transform(text, shift, encrypt=True)
    
    def decrypt_caesar(self, text, shift):
        """
        Decrypt text using the Caesar cipher.
        
        Args:
            text (str): The text to decrypt
            shift (int): The shift value used for encryption
            
        Returns:
            str: The decrypted text
        """
        return CaesarCipher.transform(text, shift, encrypt=False)
    
    # Polyalphabetic Cipher Methods
    def encrypt_polyalphabetic(self, text, keyword):
        """
        Encrypt text using the Polyalphabetic cipher.
        
        Args:
            text (str): The text to encrypt
            keyword (str): The keyword to use for encryption
            
        Returns:
            str: The encrypted text
        """
        return PolyalphabeticCipher.transform(text, keyword, encrypt=True)
    
    def decrypt_polyalphabetic(self, text, keyword):
        """
        Decrypt text using the Polyalphabetic cipher.
        
        Args:
            text (str): The text to decrypt
            keyword (str): The keyword used for encryption
            
        Returns:
            str: The decrypted text
        """
        return PolyalphabeticCipher.transform(text, keyword, encrypt=False)
    
    # Substitution Cipher Methods
    def generate_substitution_key(self, seed=None):
        """
        Generate a substitution cipher key.
        
        Args:
            seed (str, optional): Seed for the random generator
            
        Returns:
            str: Generated substitution key
        """
        return SubstitutionCipher.generate_key(seed)
    
    def encrypt_substitution(self, text, key):
        """
        Encrypt text using the Substitution cipher.
        
        Args:
            text (str): The text to encrypt
            key (str): The substitution key (shuffled alphabet)
            
        Returns:
            str: The encrypted text
        """
        return SubstitutionCipher.transform(text, key, encrypt=True)
    
    def decrypt_substitution(self, text, key):
        """
        Decrypt text using the Substitution cipher.
        
        Args:
            text (str): The text to decrypt
            key (str): The substitution key used for encryption
            
        Returns:
            str: The decrypted text
        """
        return SubstitutionCipher.transform(text, key, encrypt=False)
    
    # Transposition Cipher Methods
    def encrypt_transposition(self, text, key):
        """
        Encrypt text using the Transposition cipher.
        
        Args:
            text (str): The text to encrypt
            key (str or list): Keyword or numeric key for column ordering
            
        Returns:
            str: The encrypted text
        """
        return TranspositionCipher.transform(text, key, encrypt=True)
    
    def decrypt_transposition(self, text, key):
        """
        Decrypt text using the Transposition cipher.
        
        Args:
            text (str): The text to decrypt
            key (str or list): Keyword or numeric key used for encryption
            
        Returns:
            str: The decrypted text
        """
        return TranspositionCipher.transform(text, key, encrypt=False)
    
    # Rail Fence Cipher Methods
    def encrypt_rail_fence(self, text, rails):
        """
        Encrypt text using the Rail Fence cipher.
        
        Args:
            text (str): The text to encrypt
            rails (int): Number of rails to use
            
        Returns:
            str: The encrypted text
        """
        return RailFenceCipher.transform(text, rails, encrypt=True)
    
    def decrypt_rail_fence(self, text, rails):
        """
        Decrypt text using the Rail Fence cipher.
        
        Args:
            text (str): The text to decrypt
            rails (int): Number of rails used for encryption
            
        Returns:
            str: The decrypted text
        """
        return RailFenceCipher.transform(text, rails, encrypt=False)
    
    # Affine Cipher Methods
    def encrypt_affine(self, text, key_pair):
        """
        Encrypt text using the Affine cipher.
        
        Args:
            text (str): The text to encrypt
            key_pair (tuple): Pair of values (a, b) for the affine function
            
        Returns:
            str: The encrypted text
        """
        return AffineCipher.transform(text, key_pair, encrypt=True)
    
    def decrypt_affine(self, text, key_pair):
        """
        Decrypt text using the Affine cipher.
        
        Args:
            text (str): The text to decrypt
            key_pair (tuple): Pair of values (a, b) used for encryption
            
        Returns:
            str: The decrypted text
        """
        return AffineCipher.transform(text, key_pair, encrypt=False)
    
    # File Operations
    def process_file_with_cipher(
            self, input_path, output_path, cipher_func, delete_input=False
    ):
        """
        Process a file through the specified cipher function.
        
        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            cipher_func (callable): Cipher function to apply to file content
            delete_input (bool): Whether to delete input file after processing
            
        Returns:
            str: A message indicating success or the error encountered
        """
        result = self.file_service.process_file_result(
            input_path, output_path, cipher_func
        )
        
        if delete_input and result.success:
            if not self.file_service.delete_file_after_processing(input_path):
                return result.message + " Warning: The source file could not be deleted."
        
        return result.message
    
    # Analysis Methods
    def analyze_caesar_encryption(self, ciphertext):
        """
        Analyze Caesar-encrypted text to guess the shift key.
        
        Args:
            ciphertext (str): The encrypted text to analyze
            
        Returns:
            list: List of potential shift values with confidence scores
        """
        return CipherAnalyzer.analyze_caesar(ciphertext)
    
    def analyze_polyalphabetic_encryption(self, ciphertext):
        """
        Analyze Polyalphabetic-encrypted text to guess possible keywords.
        
        Args:
            ciphertext (str): The encrypted text to analyze
            
        Returns:
            list: List of potential keywords with confidence scores
        """
        return CipherAnalyzer.analyze_polyalphabetic(ciphertext)

    def analyze_affine_encryption(self, ciphertext):
        """
        Analyze Affine-encrypted text by trying every valid key.

        Args:
            ciphertext (str): The encrypted text to analyze

        Returns:
            list: List of candidate (a, b) keys with confidence scores
        """
        return CipherAnalyzer.analyze_affine(ciphertext)

    def analyze_rail_fence_encryption(self, ciphertext):
        """
        Analyze Rail Fence-encrypted text by trying each rail count.

        Args:
            ciphertext (str): The encrypted text to analyze

        Returns:
            list: List of candidate rail counts with confidence scores
        """
        return CipherAnalyzer.analyze_rail_fence(ciphertext)
