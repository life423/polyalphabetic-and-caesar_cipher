"""
File Service Module - Handles file operations for the cipher application.

This module encapsulates all file I/O operations needed by the cipher application,
providing a clean separation between file handling and cipher operations.
"""

import os


class FileService:
    """Handles file operations for the cipher application."""
    
    @staticmethod
    def process_file(input_path, output_path, transform_function):
        """
        Process a file through the specified transformation function.
        
        Args:
            input_path (str): Path to the input file
            output_path (str): Path to the output file
            transform_function (callable): Function to apply to each line of the file
            
        Returns:
            str: A message indicating success or the error encountered
        """
        try:
            with open(input_path, 'r') as input_file, open(output_path, 'w') as output_file:
                for line in input_file:
                    output_file.write(transform_function(line))
            
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
    def clean_txt_files(directory="."):
        """
        Delete all .txt files in the specified directory.
        
        Args:
            directory (str): Directory to search for .txt files
            
        Returns:
            list: Names of files that were deleted
        """
        files_in_dir = os.listdir(directory)
        txt_files = [file for file in files_in_dir if file.endswith(".txt")]
        
        deleted_files = []
        for file in txt_files:
            file_path = os.path.join(directory, file)
            try:
                os.remove(file_path)
                deleted_files.append(file)
            except Exception:
                pass  # Skip files that couldn't be deleted
            
        return deleted_files
    
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
