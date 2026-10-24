"""
Core Cipher Algorithms - Implements encryption/decryption algorithms.

This module contains the core implementations of various cipher algorithms
without any I/O operations or business logic.
"""

import string
import random
import math


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
        # Normalize shift to be between 0 and 25
        shift = shift % cls.ALPHABET_SIZE
        
        # Adjust shift for decryption (in opposite direction)
        effective_shift = shift if encrypt else -shift

        for char in text:
            if char in string.ascii_letters:
                # Determine the ASCII offset based on case
                offset = (cls.UPPERCASE_OFFSET if char.isupper()
                          else cls.LOWERCASE_OFFSET)

                # Apply the shift and ensure it wraps around the alphabet
                new_index = ((ord(char) - offset + effective_shift)
                             % cls.ALPHABET_SIZE)

                # Convert back to a character and add to result
                result += chr(new_index + offset)
            else:
                # Non-alphabetic characters remain unchanged
                result += char

        return result


class PolyalphabeticCipher:
    """Implements the Polyalphabetic (Vigenère) cipher algorithm."""

    # ASCII offset constants
    UPPERCASE_OFFSET = 65  # ASCII code for 'A'
    LOWERCASE_OFFSET = 97  # ASCII code for 'a'
    ALPHABET_SIZE = 26     # Number of letters in the English alphabet

    @classmethod
    def transform(cls, text, keyword, encrypt=True):
        """
        Apply the Polyalphabetic (Vigenère) cipher to the given text.

        Args:
            text (str): The text to encrypt or decrypt
            keyword (str): The keyword to use for the cipher
            encrypt (bool): True for encryption, False for decryption

        Returns:
            str: The encrypted or decrypted text
        """
        # Ensure keyword is not empty
        if not isinstance(keyword, str) or not keyword.isascii() or not keyword.isalpha():
            raise ValueError("Keyword must contain only ASCII letters")

        # Convert the keyword to lowercase and repeat it to match text length
        # Creates a key sequence that's as long as the input text
        keyword = (keyword * (len(text) // len(keyword) + 1)).lower()
        result = []
        key_idx = 0

        for char in text:
            if char in string.ascii_letters:
                # Get the current key character
                key_char = keyword[key_idx]
                key_idx = (key_idx + 1) % len(keyword)

                # Calculate the shift value (a=0, b=1, etc.)
                shift = ord(key_char) - cls.LOWERCASE_OFFSET

                # Adjust shift direction for decryption
                if not encrypt:
                    shift = -shift

                # Determine the ASCII offset based on case
                offset = (cls.UPPERCASE_OFFSET if char.isupper()
                          else cls.LOWERCASE_OFFSET)

                # Apply the shift and wrap around the alphabet
                shifted_index = ((ord(char) - offset + shift)
                                 % cls.ALPHABET_SIZE)

                # Convert back to a character and add to result
                result.append(chr(shifted_index + offset))
            else:
                # Non-alphabetic characters remain unchanged
                result.append(char)
                # Don't advance the key for non-alphabetic characters

        return ''.join(result)


class SubstitutionCipher:
    """Implements a full substitution cipher with custom alphabet mapping."""

    @classmethod
    def generate_key(cls, seed=None):
        """
        Generate a random substitution key or from a seed word.

        Args:
            seed (str, optional): Seed for random number generator

        Returns:
            str: Shuffled alphabet to use as encryption key
        """
        alphabet = list(string.ascii_lowercase)
        rng = random.Random(seed) if seed is not None else random.SystemRandom()
        rng.shuffle(alphabet)
        return ''.join(alphabet)

    @classmethod
    def transform(cls, text, key, encrypt=True):
        """
        Apply substitution cipher using the provided key.

        Args:
            text (str): The text to encrypt or decrypt
            key (str): The substitution key (shuffled alphabet)
            encrypt (bool): True for encryption, False for decryption

        Returns:
            str: The encrypted or decrypted text
        """
        if (not isinstance(key, str) or len(key) != 26
                or set(key.lower()) != set(string.ascii_lowercase)):
            raise ValueError("Substitution key must be a permutation of the 26 ASCII letters")

        # Create the mapping
        if encrypt:
            # For encryption: map standard alphabet to key
            char_map = {
                a: b for a, b in zip(string.ascii_lowercase, key.lower())
            }
            char_map.update({
                a: b for a, b in zip(string.ascii_uppercase, key.upper())
            })
        else:
            # For decryption: map key to standard alphabet
            char_map = {
                b: a for a, b in zip(string.ascii_lowercase, key.lower())
            }
            char_map.update({
                b: a for a, b in zip(string.ascii_uppercase, key.upper())
            })

        # Apply the substitution
        result = []
        for char in text:
            if char in string.ascii_letters:
                result.append(char_map.get(char, char))
            else:
                result.append(char)

        return ''.join(result)


class TranspositionCipher:
    """Columnar transposition using a keyword or zero-based column permutation."""

    @staticmethod
    def _column_order(key):
        if isinstance(key, str):
            if len(key) < 2 or not key.isascii() or not key.isalpha():
                raise ValueError("Transposition keyword must contain at least two ASCII letters")
            # Sort by letter, retaining the original order of duplicate letters.
            return sorted(range(len(key)), key=lambda index: (key[index].lower(), index))

        if not isinstance(key, (list, tuple)) or len(key) < 2:
            raise ValueError("Numeric key must be a permutation of at least two columns")
        if any(type(index) is not int for index in key) or sorted(key) != list(range(len(key))):
            raise ValueError("Numeric key must contain each column index from 0 to n-1 once")
        return list(key)

    @classmethod
    def transform(cls, text, key, encrypt=True):
        """Transform text; encryption removes whitespace and pads with X."""
        order = cls._column_order(key)
        width = len(order)

        if encrypt:
            plain = ''.join(text.split())
            padded = plain.ljust(((len(plain) + width - 1) // width) * width, 'X')
            return ''.join(padded[column::width] for column in order)

        if len(text) % width:
            raise ValueError("Ciphertext length must be a multiple of the key length")

        rows = len(text) // width
        columns = [''] * width
        for column in order:
            columns[column] = text[:rows]
            text = text[rows:]
        return ''.join(columns[column][row] for row in range(rows) for column in range(width))


class RailFenceCipher:
    """Zigzag rail-fence cipher with consistent encryption and decryption."""

    @staticmethod
    def _rails_for_positions(length, rails):
        row, direction = 0, 1
        positions = []
        for _ in range(length):
            positions.append(row)
            row += direction
            if row == 0 or row == rails - 1:
                direction *= -1
        return positions

    @classmethod
    def transform(cls, text, rails, encrypt=True):
        """Encrypt/decrypt using zigzag rail order; encryption removes whitespace."""
        if not isinstance(rails, int) or rails < 2:
            raise ValueError("Number of rails must be at least 2")

        if encrypt:
            text = ''.join(text.split())
        if len(text) <= 1 or rails >= len(text):
            return text

        positions = cls._rails_for_positions(len(text), rails)
        rail_indices = [
            index for rail in range(rails)
            for index, position in enumerate(positions) if position == rail
        ]

        if encrypt:
            return ''.join(text[index] for index in rail_indices)

        plaintext = [''] * len(text)
        for character, index in zip(text, rail_indices):
            plaintext[index] = character
        return ''.join(plaintext)


class AffineCipher:
    """Implements an affine cipher with mathematical transformation."""

    @classmethod
    def is_coprime(cls, a, b):
        """Check if two numbers are coprime (gcd is 1)."""
        return math.gcd(a, b) == 1

    @classmethod
    def mod_inverse(cls, a, m):
        """Find modular multiplicative inverse of a under modulo m."""
        g, x, y = cls._extended_gcd(a, m)
        if g != 1:
            msg = f"Modular inverse does not exist (gcd({a}, {m}) != 1)"
            raise ValueError(msg)
        else:
            return x % m

    @classmethod
    def _extended_gcd(cls, a, b):
        """Extended Euclidean Algorithm for finding GCD."""
        if a == 0:
            return b, 0, 1
        else:
            gcd, x1, y1 = cls._extended_gcd(b % a, a)
            x = y1 - (b // a) * x1
            y = x1
            return gcd, x, y

    @classmethod
    def transform(cls, text, key_pair, encrypt=True):
        """
        Apply affine cipher with key pair.

        The affine cipher uses the transformation:
        - Encryption: E(x) = (ax + b) mod m
        - Decryption: D(x) = a^-1 * (x - b) mod m

        Where:
        - a and b are the key components
        - m is the size of the alphabet (26)
        - a^-1 is the modular multiplicative inverse of a modulo m

        Args:
            text (str): The text to encrypt or decrypt
            key_pair (tuple): Pair of values (a, b) where:
                a: multiplicative factor (must be coprime to 26)
                b: additive shift
            encrypt (bool): True for encryption, False for decryption

        Returns:
            str: The encrypted or decrypted text
        """
        a, b = key_pair
        m = 26  # Size of alphabet

        # Validate that 'a' is coprime with 'm' (alphabet size)
        if not cls.is_coprime(a, m):
            raise ValueError(f"The value 'a' ({a}) must be coprime to 26")

        result = []

        # For decryption, find modular multiplicative inverse of 'a'
        if not encrypt:
            a_inv = cls.mod_inverse(a, m)

        for char in text:
            if char in string.ascii_letters:
                # Determine case and convert to 0-25 range
                is_upper = char.isupper()
                x = ord(char.lower()) - ord('a')

                # Apply transformation
                if encrypt:
                    # E(x) = (ax + b) mod m
                    y = (a * x + b) % m
                else:
                    # D(x) = a^-1 * (x - b) mod m
                    y = (a_inv * ((x - b) % m)) % m

                # Convert back to character
                new_char = chr(y + ord('a'))
                if is_upper:
                    new_char = new_char.upper()

                result.append(new_char)
            else:
                result.append(char)

        return ''.join(result)
