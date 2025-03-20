"""
Cipher AI Helper - AI-driven analysis tools for cipher operations.

This module contains algorithms for analyzing encrypted text to guess encryption
keys and suggest possible plaintext interpretations.
"""

import string
from collections import Counter
import re
import math


class CipherAnalyzer:
    """
    AI-driven analysis tools for Caesar and Polyalphabetic ciphers.
    
    This class implements various cryptanalysis techniques to guess encryption
    keys and suggest possible plaintext interpretations of encrypted messages.
    """
    
    # English letter frequency (from most common to least)
    ENGLISH_FREQ_MAP = {
        'e': 0.1202, 't': 0.0910, 'a': 0.0812, 'o': 0.0768, 'i': 0.0731,
        'n': 0.0695, 's': 0.0628, 'r': 0.0602, 'h': 0.0592, 'd': 0.0432,
        'l': 0.0398, 'u': 0.0288, 'c': 0.0271, 'm': 0.0261, 'f': 0.0230,
        'y': 0.0211, 'w': 0.0209, 'g': 0.0203, 'p': 0.0182, 'b': 0.0149,
        'v': 0.0111, 'k': 0.0069, 'x': 0.0017, 'q': 0.0011, 'j': 0.0010, 'z': 0.0007
    }
    
    # Common English words for plaintext validation
    COMMON_WORDS = [
        'the', 'be', 'to', 'of', 'and', 'in', 'that', 'have', 'it', 'for', 
        'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but',
        'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an',
        'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so',
        'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when'
    ]
    
    @classmethod
    def analyze_caesar(cls, ciphertext):
        """
        Analyze Caesar-encrypted text and return likely keys with sample decryptions.
        
        Args:
            ciphertext (str): The encrypted text to analyze
            
        Returns:
            list: List of dicts containing {shift, score, sample} for top candidates
        """
        if not ciphertext:
            return []
            
        # Filter alphabetic characters for analysis
        letters_only = re.sub(r'[^a-zA-Z]', '', ciphertext).lower()
        if not letters_only:
            return []
            
        # Calculate letter frequency in ciphertext
        letter_count = Counter(letters_only)
        total_letters = len(letters_only)
        
        # Generate all possible shifts and calculate chi-squared statistic for each
        results = []
        
        for shift in range(1, 26):  # All possible shifts (1-25)
            shifted_freq = {}
            
            # Calculate what the letter frequencies would be after applying this shift
            for char, count in letter_count.items():
                shifted_char = chr(((ord(char) - ord('a') - shift) % 26) + ord('a'))
                shifted_freq[shifted_char] = shifted_freq.get(shifted_char, 0) + count
            
            # Calculate chi-squared statistic (goodness of fit to English)
            chi_squared = 0
            for char in string.ascii_lowercase:
                observed = shifted_freq.get(char, 0) / total_letters if total_letters > 0 else 0
                expected = cls.ENGLISH_FREQ_MAP.get(char, 0)
                chi_squared += ((observed - expected) ** 2) / expected if expected > 0 else 0
            
            # Calculate word match score for additional confidence
            decrypted = cls._decrypt_caesar(ciphertext, shift)
            word_score = cls._calculate_common_word_score(decrypted)
            
            # Combined score (lower is better)
            combined_score = chi_squared / (1 + word_score)
            
            results.append({
                'shift': shift,
                'score': combined_score,
                'confidence': 0,  # Will be calculated after sorting
                'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
            })
        
        # Sort results by score (lower is better)
        results.sort(key=lambda x: x['score'])
        
        # Keep only top 5 results
        top_results = results[:5]
        
        # Calculate confidence percentages
        total_score = sum(1/r['score'] for r in top_results) if top_results else 1
        for result in top_results:
            result['confidence'] = round((1/result['score']) / total_score * 100, 1)
            
        return top_results
    
    @classmethod
    def analyze_polyalphabetic(cls, ciphertext):
        """
        Analyze Polyalphabetic-encrypted text and suggest possible keywords and decryptions.
        
        Args:
            ciphertext (str): The encrypted text to analyze
            
        Returns:
            list: List of dicts containing {keyword, score, sample} for top candidates
        """
        if not ciphertext:
            return []
            
        # Filter alphabetic characters for analysis
        letters_only = re.sub(r'[^a-zA-Z]', '', ciphertext).lower()
        if len(letters_only) < 20:  # Need sufficient text for analysis
            return [{'keyword': '?', 'confidence': 0, 'sample': 'Insufficient text for analysis'}]
            
        # Estimate possible key lengths using index of coincidence
        key_lengths = cls._estimate_key_lengths(letters_only)
        
        if not key_lengths:
            return [{'keyword': '?', 'confidence': 0, 'sample': 'Unable to determine key length'}]
            
        results = []
        
        # For each potential key length, try to determine the key
        for key_length in key_lengths[:3]:  # Consider top 3 key lengths
            # Split ciphertext into columns based on key length
            columns = [''] * key_length
            for i, char in enumerate(letters_only):
                columns[i % key_length] += char
                
            # For each column, perform Caesar analysis
            potential_key = ''
            column_scores = []
            
            for column in columns:
                column_result = cls.analyze_caesar(column)
                if column_result:
                    best_shift = column_result[0]['shift']
                    key_char = chr(((best_shift) % 26) + ord('a'))
                    potential_key += key_char
                    column_scores.append(column_result[0]['score'])
                else:
                    potential_key += '?'
                    column_scores.append(float('inf'))
            
            # Skip if we couldn't determine the key
            if '?' in potential_key:
                continue
                
            # Decrypt with the potential key
            decrypted = cls._decrypt_polyalphabetic(ciphertext, potential_key)
            
            # Calculate a score based on column scores and common word presence
            avg_column_score = sum(column_scores) / len(column_scores) if column_scores else float('inf')
            word_score = cls._calculate_common_word_score(decrypted)
            
            # Combined score (lower is better)
            combined_score = avg_column_score / (1 + word_score)
            
            results.append({
                'keyword': potential_key,
                'score': combined_score,
                'confidence': 0,  # Will be calculated after sorting
                'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
            })
        
        # If no key was found, return a fallback message
        if not results:
            return [{'keyword': '?', 'confidence': 0, 'sample': 'Unable to determine keyword'}]
            
        # Sort results by score (lower is better)
        results.sort(key=lambda x: x['score'])
        
        # Keep only top 5 results
        top_results = results[:5]
        
        # Calculate confidence percentages
        total_score = sum(1/r['score'] for r in top_results) if top_results else 1
        for result in top_results:
            result['confidence'] = round((1/result['score']) / total_score * 100, 1)
            
        return top_results
    
    @classmethod
    def _decrypt_caesar(cls, text, shift):
        """Decrypt text using Caesar cipher with the given shift."""
        result = ''
        for char in text:
            if char.isalpha():
                ascii_offset = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - ascii_offset - shift) % 26
                result += chr(shifted + ascii_offset)
            else:
                result += char
        return result
    
    @classmethod
    def _decrypt_polyalphabetic(cls, text, keyword):
        """Decrypt text using Polyalphabetic cipher with the given keyword."""
        result = ''
        key_idx = 0
        keyword = keyword.lower()
        
        for char in text:
            if char.isalpha():
                # Get the shift value from the keyword
                key_char = keyword[key_idx % len(keyword)]
                shift = ord(key_char) - ord('a')
                
                # Apply the reverse shift
                ascii_offset = ord('A') if char.isupper() else ord('a')
                shifted = (ord(char) - ascii_offset - shift) % 26
                result += chr(shifted + ascii_offset)
                
                # Move to the next key character
                key_idx += 1
            else:
                result += char
                
        return result
    
    @classmethod
    def _calculate_common_word_score(cls, text):
        """Calculate a score based on the presence of common English words."""
        text_lower = text.lower()
        word_score = 0
        
        for word in cls.COMMON_WORDS:
            word_count = len(re.findall(r'\b' + word + r'\b', text_lower))
            word_score += word_count
            
        return word_score
    
    @classmethod
    def _estimate_key_lengths(cls, text, max_length=10):
        """
        Estimate potential key lengths using index of coincidence.
        
        Args:
            text (str): The ciphertext to analyze
            max_length (int): Maximum key length to consider
            
        Returns:
            list: Potential key lengths sorted by likelihood (most likely first)
        """
        ic_scores = []
        
        # Try different key lengths
        for length in range(1, min(max_length + 1, len(text) // 2)):
            total_ic = 0
            
            # Calculate IC for each column
            for i in range(length):
                # Extract column
                column = text[i::length]
                
                # Skip if column is too short
                if len(column) < 2:
                    continue
                    
                # Count frequencies
                freqs = Counter(column)
                
                # Calculate index of coincidence
                n = len(column)
                ic = 0
                for count in freqs.values():
                    ic += count * (count - 1)
                
                ic = ic / (n * (n - 1)) if n > 1 else 0
                total_ic += ic
                
            # Average IC across all columns
            avg_ic = total_ic / length
            
            # English text typically has IC around 0.067
            # Random text has IC around 0.038
            ic_scores.append((length, abs(avg_ic - 0.067)))
        
        # Sort by proximity to English IC value (smaller difference is better)
        ic_scores.sort(key=lambda x: x[1])
        
        # Return just the lengths, sorted by likelihood
        return [length for length, _ in ic_scores]
