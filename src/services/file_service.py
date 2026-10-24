"""
File Service Module - Handles file operations for the cipher application.

This module encapsulates all file I/O operations needed by the cipher
application, providing a clean separation between file handling and cipher ops.
"""

import os
from pathlib import Path


class FileService:
    """Handles file operations for the cipher application."""
    
    @staticmethod
    def process_file(input_path, output_path, transform_function):
        """
        Process a file through the specified transformation function.
        
        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            transform_function (callable): Function to apply to each line
            
        Returns:
            str: A message indicating success or the error encountered
        """
        try:
            source = Path(input_path).resolve()
            destination = Path(output_path).resolve()
            if source == destination:
                return "Error: Input and output files must be different."
            # Preserve legacy line-by-line cipher processing (including keyword
            # resets per line), without risking an existing destination on error.
            with source.open('r', encoding='utf-8') as input_file:
                result = ''.join(transform_function(line) for line in input_file)
            with destination.open('w', encoding='utf-8') as output_file:
                output_file.write(result)
            
            return f"Successfully processed {input_path} to {output_path}"
        except FileNotFoundError:
            return f"Error: The file {input_path} does not exist."
        except Exception as e:
            return f"Error: Couldn't process the file due to {str(e)}"
    
    @staticmethod
    def delete_file_after_processing(file_path):
        """
        Delete a file after it has been processed.
        
        Args:
            file_path (str): Path to the file to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            os.remove(file_path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def file_exists(file_path):
        """
        Check if a file exists.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if the file exists, False otherwise
        """
        return os.path.isfile(file_path)
