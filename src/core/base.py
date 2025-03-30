"""
Base Cipher Module - Provides abstract base classes for all cipher
implementations.

This module defines a common interface for all cipher types, promoting
consistent behavior and making it easier to extend with new cipher
implementations.
"""

from abc import ABC, abstractmethod


class BaseCipher(ABC):
    """
    Abstract base class for all cipher implementations.
    
    This class defines the common interface that all cipher implementations
    should follow. It ensures consistency across different cipher types
    and simplifies the addition of new cipher algorithms.
    """
    
    @classmethod
    @abstractmethod
    def transform(cls, text, key, encrypt=True):
        """
        Transform text using the cipher algorithm.
        
        Args:
            text (str): The text to encrypt or decrypt
            key: The key for the cipher (type depends on the cipher)
            encrypt (bool): True for encryption, False for decryption
            
        Returns:
            str: The transformed text
        
        This method must be implemented by all concrete cipher classes.
        """
        pass
    
    @classmethod
    def validate_key(cls, key):
        """
        Validate that the key is appropriate for this cipher type.
        
        Args:
            key: The key to validate
            
        Returns:
            bool: True if the key is valid, False otherwise
            
        This method can be overridden by concrete cipher classes to
        provide specific validation logic. By default, it returns True.
        """
        return True
    
    @classmethod
    def get_key_type(cls):
        """
        Get the expected type of key for this cipher.
        
        Returns:
            type or str: Description of the expected key type
            
        This method can be overridden by concrete cipher classes to
        provide specific information about the expected key format.
        """
        return "Unspecified"


class SubstitutionBaseCipher(BaseCipher):
    """
    Base class for substitution-based ciphers.
    
    This class provides common functionality for ciphers that use
    character substitution.
    """
    
    @classmethod
    def transform_char(cls, char, key, encrypt=True):
        """
        Transform a single character using the substitution rule.
        
        Args:
            char (str): Single character to transform
            key: The key for the transformation
            encrypt (bool): True for encryption, False for decryption
            
        Returns:
            str: Transformed character
            
        This method can be overridden by concrete cipher classes to
        provide specific character transformation logic.
        """
        return char


class TranspositionBaseCipher(BaseCipher):
    """
    Base class for transposition-based ciphers.
    
    This class provides common functionality for ciphers that use
    character rearrangement.
    """
    
    @classmethod
    def prepare_text(cls, text):
        """
        Prepare text for transposition.
        
        Args:
            text (str): The text to prepare
            
        Returns:
            str: Prepared text
            
        This method can be overridden by concrete cipher classes to
        provide specific text preparation logic.
        """
        return text


class MathematicalCipher(BaseCipher):
    """
    Base class for mathematically-based ciphers.
    
    This class provides common functionality for ciphers that use
    mathematical operations.
    """
    
    @classmethod
    def validate_key(cls, key):
        """
        Validate that the key is mathematically valid.
        
        Args:
            key: The key to validate
            
        Returns:
            bool: True if the key is valid, False otherwise
        """
        return True
