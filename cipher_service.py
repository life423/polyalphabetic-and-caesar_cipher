"""
Cipher Service Module - Coordinates cipher operations and file handling.

This module serves as a facade for the cipher operations, coordinating between
the core cipher algorithms and file handling services.
"""

from cipher_core import CaesarCipher, PolyalphabeticCipher
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
    
    def process_file_with_cipher(self, input_path, output_path, cipher_func, 
                                delete_input=False):
        """
        Process a file through the specified cipher function.
        
        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            cipher_func (callable): Cipher function to apply to file content
            delete_input (bool): Whether to delete the input file after processing
            
        Returns:
            str: A message indicating success or the error encountered
        """
        result = self.file_service.process_file(input_path, output_path, cipher_func)
        
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
    cipher_choice = input("Choose cipher (c=Caesar, p=Polyalphabetic): ")
    if cipher_choice.lower() not in {'c', 'p'}:
        print("Invalid choice. Please enter 'c' for Caesar or 'p' for Polyalphabetic.")
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
                shift = int(input("Enter shift value: "))
                if encrypt:
                    result = service.encrypt_caesar(text, shift)
                else:
                    result = service.decrypt_caesar(text, shift)
                print(f"Result: {result}")
            except ValueError:
                print("Error: Shift value must be an integer.")
                
        else:  # Polyalphabetic cipher
            keyword = input("Enter keyword: ")
            if not keyword:
                print("Error: Keyword cannot be empty.")
                return
                
            if encrypt:
                result = service.encrypt_polyalphabetic(text, keyword)
            else:
                result = service.decrypt_polyalphabetic(text, keyword)
            print(f"Result: {result}")
            
    else:  # File input
        input_file = input("Path to input file: ")
        output_file = input("Path to output file: ")
        delete_input = input("Delete input file after processing? (yes/no): ").lower() == 'yes'
        
        if not input_file or not output_file:
            print("Error: File paths cannot be empty.")
            return
            
        if cipher_choice.lower() == 'c':  # Caesar cipher
            try:
                shift = int(input("Enter shift value: "))
                
                if encrypt:
                    cipher_func = lambda x: service.encrypt_caesar(x, shift)
                else:
                    cipher_func = lambda x: service.decrypt_caesar(x, shift)
                    
                result = service.process_file_with_cipher(
                    input_file, output_file, cipher_func, delete_input
                )
                print(result)
            except ValueError:
                print("Error: Shift value must be an integer.")
                
        else:  # Polyalphabetic cipher
            keyword = input("Enter keyword: ")
            if not keyword:
                print("Error: Keyword cannot be empty.")
                return
                
            if encrypt:
                cipher_func = lambda x: service.encrypt_polyalphabetic(x, keyword)
            else:
                cipher_func = lambda x: service.decrypt_polyalphabetic(x, keyword)
                
            result = service.process_file_with_cipher(
                input_file, output_file, cipher_func, delete_input
            )
            print(result)


if __name__ == "__main__":
    main()
