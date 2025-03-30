"""
Cipher Tool - Command Line Interface module.

This module provides a command-line interface for encryption and decryption
operations, making use of the service layer to handle business logic.
"""

from src.services.cipher_service import CipherService


class CipherCLI(CipherService):
    """Maintains backward compatibility with the original CipherService class."""

    def caesar_cipher(self, text, shift, encrypt=True):
        """
        Apply the Caesar cipher to the given text.

        This is a backward compatibility method.

        Args:
            text (str): The text to encrypt or decrypt
            shift (int): The number of positions to shift letters
            encrypt (bool): True for encryption, False for decryption

        Returns:
            str: The encrypted or decrypted text
        """
        if encrypt:
            return self.encrypt_caesar(text, shift)
        else:
            return self.decrypt_caesar(text, shift)

    def poly_alphabetic_cipher(self, text, keyword, encrypt=True):
        """
        Apply the Polyalphabetic cipher to the given text.

        This is a backward compatibility method.

        Args:
            text (str): The text to encrypt or decrypt
            keyword (str): The keyword to use for the cipher
            encrypt (bool): True for encryption, False for decryption

        Returns:
            str: The encrypted or decrypted text
        """
        if encrypt:
            return self.encrypt_polyalphabetic(text, keyword)
        else:
            return self.decrypt_polyalphabetic(text, keyword)

    def process_file(self, input_path, output_path, cipher_function):
        """
        Process a file through the specified cipher function.

        This is a backward compatibility method.

        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            cipher_function (callable): Function to apply to each line

        Returns:
            str: A message indicating success or the error encountered
        """
        return self.process_file_with_cipher(
            input_path, output_path, cipher_function, True)


# Maintain the original main function for backward compatibility
def main():
    """
    Command-line interface for the cipher tool.
    Run this function when the script is executed directly.
    """
    from src.services.cipher_service import main as service_main
    service_main()


if __name__ == "__main__":
    main()
