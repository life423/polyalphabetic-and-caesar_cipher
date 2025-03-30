"""
Cipher Service Module - Coordinates cipher operations and file handling.

This module serves as a facade for the cipher operations, coordinating between
the core cipher algorithms and file handling services.
"""

from cipher_core import (
    CaesarCipher, PolyalphabeticCipher, SubstitutionCipher,
    TranspositionCipher, RailFenceCipher, AffineCipher
)
from file_service import FileService
from cipher_ai import CipherAnalyzer


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
        result = self.file_service.process_file(
            input_path, output_path, cipher_func
        )
        
        if delete_input and "Successfully" in result:
            self.file_service.delete_file_after_processing(input_path)
        
        return result
    
    def clean_txt_files(self, directory="."):
        """
        Delete all .txt files in the specified directory.
        
        Args:
            directory (str): Directory to search for .txt files
            
        Returns:
            list: Names of files that were deleted
        """
        return self.file_service.clean_txt_files(directory)
    
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


# For backward compatibility with scripts that might directly import CipherService
def main():
    """
    Command-line interface for the cipher tool.
    Run this function when the script is executed directly.
    """
    service = CipherService()
    
    print("Welcome to the Cipher Tool CLI")
    print("==============================")
    
    # Ask if user wants to clean up .txt files
    cleanup_confirm = input("Clean .txt files before proceeding? (yes/no): ")
    if cleanup_confirm.lower() == 'yes':
        deleted_files = service.clean_txt_files()
        if deleted_files:
            print(f"Deleted files: {', '.join(deleted_files)}")
        else:
            print("No .txt files found to delete.")

    # Get encryption or decryption choice
    choice = input("Choose operation (e=encrypt, d=decrypt): ")
    if choice.lower() not in {'e', 'd'}:
        print("Invalid choice. Please enter 'e' for encryption or 'd' for decryption.")
        return
    
    encrypt = choice.lower() == 'e'
    
    # Get cipher type choice
    print("\nAvailable ciphers:")
    print("c - Caesar")
    print("p - Polyalphabetic (Vigenère)")
    print("s - Substitution")
    print("t - Transposition")
    print("r - Rail Fence")
    print("a - Affine")
    
    cipher_choice = input("\nChoose cipher type: ")
    if cipher_choice.lower() not in {'c', 'p', 's', 't', 'r', 'a'}:
        print("Invalid choice. Please select a valid cipher type.")
        return
    
    # Get input source (text or file)
    source = input("Input source: (1=text, 2=file): ")
    if source not in {'1', '2'}:
        print("Invalid choice. Please enter '1' for text input or '2' for file input.")
        return
    
    # Process based on user choices
    if source == '1':  # Direct text input
        text = input("Enter text: ")
        
        if cipher_choice.lower() == 'c':  # Caesar cipher
            try:
                shift = int(input("Enter shift value (1-25): "))
                if encrypt:
                    result = service.encrypt_caesar(text, shift)
                else:
                    result = service.decrypt_caesar(text, shift)
                print(f"Result: {result}")
            except ValueError:
                print("Error: Shift value must be an integer.")
                
        elif cipher_choice.lower() == 'p':  # Polyalphabetic cipher
            keyword = input("Enter keyword: ")
            if not keyword:
                print("Error: Keyword cannot be empty.")
                return
                
            if encrypt:
                result = service.encrypt_polyalphabetic(text, keyword)
            else:
                result = service.decrypt_polyalphabetic(text, keyword)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 's':  # Substitution cipher
            if encrypt:
                use_random = input("Generate random key? (yes/no): ").lower() == 'yes'
                if use_random:
                    seed_prompt = "Enter seed (optional, press Enter to skip): "
                    seed = input(seed_prompt) or None
                    key = service.generate_substitution_key(seed)
                    print(f"Generated key: {key}")
                else:
                    key = input("Enter 26-character substitution key: ")
                    if len(key) != 26:
                        print("Error: Key must be exactly 26 characters long.")
                        return
                result = service.encrypt_substitution(text, key)
            else:
                key = input("Enter 26-character substitution key: ")
                if len(key) != 26:
                    print("Error: Key must be exactly 26 characters long.")
                    return
                result = service.decrypt_substitution(text, key)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 't':  # Transposition cipher
            key_prompt = "Enter transposition key (word or comma-separated numbers): "
            key = input(key_prompt)
            if ',' in key:
                # Handle numeric key format
                try:
                    key = [int(k.strip()) for k in key.split(',')]
                except ValueError:
                    print("Error: Numeric key must contain only integers.")
                    return
            
            if encrypt:
                result = service.encrypt_transposition(text, key)
            else:
                result = service.decrypt_transposition(text, key)
            print(f"Result: {result}")
            
        elif cipher_choice.lower() == 'r':  # Rail Fence cipher
            try:
                rails = int(input("Enter number of rails (2 or more): "))
                if rails < 2:
                    print("Error: Number of rails must be at least 2.")
                    return
                
                if encrypt:
                    result = service.encrypt_rail_fence(text, rails)
                else:
                    result = service.decrypt_rail_fence(text, rails)
                print(f"Result: {result}")
            except ValueError:
                print("Error: Number of rails must be an integer.")
                
        elif cipher_choice.lower() == 'a':  # Affine cipher
            try:
                a = int(input("Enter 'a' value (must be coprime to 26): "))
                b = int(input("Enter 'b' value: "))
                
                if encrypt:
                    result = service.encrypt_affine(text, (a, b))
                else:
                    result = service.decrypt_affine(text, (a, b))
                print(f"Result: {result}")
            except ValueError as e:
                print(f"Error: {e}")
            
    else:  # File input
        input_file = input("Path to input file: ")
        output_file = input("Path to output file: ")
        delete_prompt = "Delete input file after processing? (yes/no): "
        delete_input = input(delete_prompt).lower() == 'yes'
        
        if not input_file or not output_file:
            print("Error: File paths cannot be empty.")
            return
        
        try:
            if cipher_choice.lower() == 'c':  # Caesar cipher
                shift = int(input("Enter shift value (1-25): "))
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_caesar(content, shift)
                    else:
                        return service.decrypt_caesar(content, shift)
                
            elif cipher_choice.lower() == 'p':  # Polyalphabetic cipher
                keyword = input("Enter keyword: ")
                if not keyword:
                    print("Error: Keyword cannot be empty.")
                    return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_polyalphabetic(content, keyword)
                    else:
                        return service.decrypt_polyalphabetic(content, keyword)
                
            elif cipher_choice.lower() == 's':  # Substitution cipher
                if encrypt:
                    random_prompt = "Generate random key? (yes/no): "
                    use_random = input(random_prompt).lower() == 'yes'
                    if use_random:
                        seed_prompt = "Enter seed (optional, press Enter to skip): "
                        seed = input(seed_prompt) or None
                        key = service.generate_substitution_key(seed)
                        print(f"Generated key: {key}")
                    else:
                        key = input("Enter 26-character substitution key: ")
                        if len(key) != 26:
                            print("Error: Key must be exactly 26 characters long.")
                            return
                else:
                    key = input("Enter 26-character substitution key: ")
                    if len(key) != 26:
                        print("Error: Key must be exactly 26 characters long.")
                        return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_substitution(content, key)
                    else:
                        return service.decrypt_substitution(content, key)
                
            elif cipher_choice.lower() == 't':  # Transposition cipher
                key_prompt = "Enter transposition key (word or comma-separated numbers): "
                key = input(key_prompt)
                if ',' in key:
                    # Handle numeric key format
                    try:
                        key = [int(k.strip()) for k in key.split(',')]
                    except ValueError:
                        print("Error: Numeric key must contain only integers.")
                        return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_transposition(content, key)
                    else:
                        return service.decrypt_transposition(content, key)
                
            elif cipher_choice.lower() == 'r':  # Rail Fence cipher
                rails = int(input("Enter number of rails (2 or more): "))
                if rails < 2:
                    print("Error: Number of rails must be at least 2.")
                    return
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_rail_fence(content, rails)
                    else:
                        return service.decrypt_rail_fence(content, rails)
                
            elif cipher_choice.lower() == 'a':  # Affine cipher
                a = int(input("Enter 'a' value (must be coprime to 26): "))
                b = int(input("Enter 'b' value: "))
                
                def cipher_func(content):
                    if encrypt:
                        return service.encrypt_affine(content, (a, b))
                    else:
                        return service.decrypt_affine(content, (a, b))
            
            # Process the file with the selected cipher
            result = service.process_file_with_cipher(
                input_file, output_file, cipher_func, delete_input
            )
            print(result)
            
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
