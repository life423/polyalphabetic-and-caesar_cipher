"""
File Service Module - Handles file operations for the cipher application.

This module encapsulates all file I/O operations needed by the cipher
application, providing a clean separation between file handling and cipher ops.
"""

import os
from dataclasses import dataclass
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class FileProcessResult:
    """Separate the operation's status from filenames and user-facing text."""

    success: bool
    message: str


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
        return FileService.process_file_result(
            input_path, output_path, transform_function
        ).message

    @staticmethod
    def process_file_result(input_path, output_path, transform_function):
        """Transform independent lines, retaining separators, then atomically publish."""
        temporary_path = None
        try:
            source = Path(input_path).resolve()
            destination = Path(output_path).resolve()
            if source == destination or (destination.exists() and source.samefile(destination)):
                return FileProcessResult(False, "Error: Input and output files must be different.")
            # Keep line boundaries outside the transform: transposition ciphers
            # discard whitespace, and must not merge independently encrypted lines.
            with source.open('r', encoding='utf-8', newline='') as input_file:
                with NamedTemporaryFile(
                    mode='w', encoding='utf-8', newline='',
                    dir=destination.parent, prefix='.ciphercraft-', delete=False,
                ) as output_file:
                    temporary_path = Path(output_file.name)
                    for line in input_file:
                        body = line.rstrip('\r\n')
                        separator = line[len(body):]
                        output_file.write(transform_function(body))
                        output_file.write(separator)
                    output_file.flush()
                    os.fsync(output_file.fileno())
            os.replace(temporary_path, destination)
            return FileProcessResult(True, f"Successfully processed {input_path} to {output_path}")
        except Exception as e:
            return FileProcessResult(False, f"Error: Couldn't process the file due to {e}")
        finally:
            if temporary_path is not None:
                # A cleanup problem must not mask the actual operation result.
                with suppress(OSError):
                    temporary_path.unlink(missing_ok=True)
    
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
