"""
Cipher AI Helper - AI-driven analysis tools for cipher operations.

This module contains algorithms for analyzing encrypted text to guess encryption
keys and suggest possible plaintext interpretations.
"""

import string
from collections import Counter
import re

from src.core.ciphers import AffineCipher, RailFenceCipher


class CipherAnalyzer:
    """
    AI-driven analysis tools for various ciphers.
    
    This class implements various cryptanalysis techniques to guess encryption
    keys and suggest possible plaintext interpretations of encrypted messages.
    """
    
    # English letter frequency (from most common to least)
    ENGLISH_FREQ_MAP = {
        'e': 0.1202, 't': 0.0910, 'a': 0.0812, 'o': 0.0768, 'i': 0.0731,
        'n': 0.0695, 's': 0.0628, 'r': 0.0602, 'h': 0.0592, 'd': 0.0432,
        'l': 0.0398, 'u': 0.0288, 'c': 0.0271, 'm': 0.0261, 'f': 0.0230,
        'y': 0.0211, 'w': 0.0209, 'g': 0.0203, 'p': 0.0182, 'b': 0.0149,
        'v': 0.0111, 'k': 0.0069, 'x': 0.0017, 'q': 0.0011, 'j': 0.0010, 
        'z': 0.0007
    }
    
    # Common English bigrams (pairs of letters)
    ENGLISH_BIGRAMS = {
        'th': 0.0271, 'he': 0.0233, 'in': 0.0203, 'er': 0.0178, 'an': 0.0161,
        're': 0.0141, 'on': 0.0135, 'at': 0.0125, 'en': 0.0125, 'nd': 0.0124,
        'ti': 0.0120, 'es': 0.0118, 'or': 0.0112, 'te': 0.0107, 'of': 0.0099,
        'ed': 0.0098, 'is': 0.0097, 'it': 0.0096, 'al': 0.0095, 'ar': 0.0094,
        'st': 0.0094, 'to': 0.0091, 'nt': 0.0089, 'ng': 0.0088, 'se': 0.0088
    }
    
    # Common English words for plaintext validation
    COMMON_WORDS = [
        'the', 'be', 'to', 'of', 'and', 'in', 'that', 'have', 'it', 'for', 
        'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but',
        'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an',
        'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so',
        'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when',
        'make', 'can', 'like', 'time', 'know', 'just', 'people', 'year', 'take',
        'some', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only',
        'come', 'its', 'over', 'think', 'also', 'back', 'use', 'two', 'how',
        'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'any',
        'these', 'give', 'day', 'most', 'us'
    ]
    
    # Medium-length English words that are good indicators of plaintext
    INDICATOR_WORDS = [
        'because', 'between', 'country', 'different', 'important', 'through',
        'information', 'something', 'government', 'everything', 'together',
        'following', 'question', 'american', 'possible', 'understand',
        'business', 'actually', 'problems', 'remember', 'national', 'political'
    ]

    # Longest keyword the polyalphabetic analysis considers
    MAX_KEY_LENGTH = 20

    # How many likely key lengths (by index of coincidence) get full scoring
    KEY_LENGTH_CANDIDATES = 6

    # Largest rail count tried by the rail fence analysis
    MAX_RAILS = 20

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

        for shift in range(26):  # All possible shifts (0-25); 0 means the text is unchanged
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
            
            # Decrypt the ciphertext using this shift
            decrypted = cls._decrypt_caesar(ciphertext, shift)
            
            # Calculate word match score for additional confidence
            word_score = cls._calculate_word_score(decrypted)
            
            # Calculate bigram score
            bigram_score = cls._calculate_ngram_score(decrypted, 2) 
            
            # Combined score (lower is better)
            # Weight the different factors
            combined_score = (
                0.5 * chi_squared / (1 + word_score) + 
                0.5 * chi_squared / (1 + bigram_score)
            )
            
            results.append({
                'shift': shift,
                'score': combined_score,
                'confidence': 0,  # Will be calculated after sorting
                'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
            })

        return cls._rank_candidates(results)

    @classmethod
    def analyze_polyalphabetic(cls, ciphertext):
        """
        Analyze Polyalphabetic-encrypted text and suggest possible keywords and decryptions.

        Likely key lengths come from the index of coincidence. For each one, the keyword
        is recovered column by column. The strongest keyword is then refined one letter
        at a time, and all candidates are ranked on their full decryption.

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
            return [{
                'keyword': '?', 
                'confidence': 0, 
                'sample': 'Insufficient text for analysis'
            }]

        key_lengths = cls._estimate_key_lengths(letters_only, cls.MAX_KEY_LENGTH)
        key_lengths = sorted(key_lengths[:cls.KEY_LENGTH_CANDIDATES])

        keywords = [cls._recover_keyword(letters_only, key_length) for key_length in key_lengths]

        # Column-by-column recovery is noisy on short text, so polish the strongest candidate
        best = min(keywords, key=lambda keyword: cls._plaintext_score(
            cls._decrypt_polyalphabetic(ciphertext, keyword)
        ))
        keywords.append(cls._refine_keyword(ciphertext, best))

        # Different key lengths can decrypt to the same text (e.g. "ab" and "abab"); keep the first
        decryptions = {}
        for keyword in keywords:
            decrypted = cls._decrypt_polyalphabetic(ciphertext, keyword)
            decryptions.setdefault(decrypted, keyword)

        results = []
        for decrypted, keyword in decryptions.items():
            results.append({
                'keyword': keyword,
                'score': cls._plaintext_score(decrypted),
                'confidence': 0,  # Will be calculated after sorting
                'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
            })

        return cls._rank_candidates(results)

    @classmethod
    def analyze_affine(cls, ciphertext):
        """
        Analyze Affine-encrypted text by trying every valid key (a, b).

        There are only 312 valid keys, so each one is decrypted and ranked on how
        English the result looks.

        Args:
            ciphertext (str): The encrypted text to analyze

        Returns:
            list: List of dicts containing {a, b, score, sample} for top candidates
        """
        if not re.sub(r'[^a-zA-Z]', '', ciphertext or ''):
            return []

        results = []
        for a in range(1, 26):
            if not AffineCipher.is_coprime(a, 26):
                continue
            for b in range(26):
                decrypted = AffineCipher.transform(ciphertext, (a, b), encrypt=False)
                results.append({
                    'a': a,
                    'b': b,
                    'score': cls._plaintext_score(decrypted),
                    'confidence': 0,  # Will be calculated after sorting
                    'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
                })

        return cls._rank_candidates(results)

    @classmethod
    def analyze_rail_fence(cls, ciphertext):
        """
        Analyze Rail Fence-encrypted text by trying each rail count.

        Rail Fence encryption drops whitespace, so the text is stripped of it
        before each rail count is decrypted and ranked.

        Args:
            ciphertext (str): The encrypted text to analyze

        Returns:
            list: List of dicts containing {rails, score, sample} for top candidates
        """
        text = ''.join((ciphertext or '').split())

        results = []
        # A rail count of at least the text length leaves the text unchanged, so stop before that
        for rails in range(2, min(len(text), cls.MAX_RAILS + 1)):
            decrypted = RailFenceCipher.transform(text, rails, encrypt=False)
            results.append({
                'rails': rails,
                'score': cls._plaintext_score(decrypted),
                'confidence': 0,  # Will be calculated after sorting
                'sample': decrypted[:100] + ("..." if len(decrypted) > 100 else "")
            })

        return cls._rank_candidates(results)

    @classmethod
    def analyze_with_known_plaintext(cls, ciphertext, known_plaintext, cipher_type="caesar"):
        """
        Use known plaintext segment to determine the encryption key.
        
        Args:
            ciphertext (str): The encrypted text
            known_plaintext (str): The known plaintext segment
            cipher_type (str): Type of cipher ('caesar' or 'polyalphabetic')
            
        Returns:
            dict: Information about the determined key or error message
        """
        if not ciphertext or not known_plaintext:
            return {
                'success': False,
                'message': 'Both ciphertext and known plaintext are required'
            }
        
        # Preprocess to focus on alphabetic characters
        cipher_clean = re.sub(r'[^a-zA-Z]', '', ciphertext).lower()
        known_clean = re.sub(r'[^a-zA-Z]', '', known_plaintext).lower()
        
        if cipher_type.lower() == "caesar":
            # For Caesar, we need to find all potential matches of the known text
            potential_shifts = []
            
            for i in range(len(cipher_clean) - len(known_clean) + 1):
                segment = cipher_clean[i:i+len(known_clean)]
                # Try all 25 possible shifts
                for shift in range(1, 26):
                    decrypted = cls._decrypt_caesar(segment, shift)
                    if decrypted == known_clean:
                        potential_shifts.append(shift)
                        break
            
            if potential_shifts:
                if len(set(potential_shifts)) == 1:
                    # All matches suggest the same shift
                    shift = potential_shifts[0]
                    decrypted = cls._decrypt_caesar(ciphertext, shift)
                    return {
                        'success': True,
                        'key': shift,
                        'decrypted': decrypted
                    }
                else:
                    # Multiple potential shifts found
                    return {
                        'success': False,
                        'message': f'Multiple possible shifts found: {list(set(potential_shifts))}'
                    }
            else:
                return {
                    'success': False,
                    'message': 'Known plaintext segment not found in ciphertext'
                }
                
        elif cipher_type.lower() == "polyalphabetic":
            # For polyalphabetic, this is more complex and might need further implementation
            return {
                'success': False,
                'message': 'Known plaintext analysis for polyalphabetic cipher is not fully implemented'
            }
        
        else:
            return {
                'success': False,
                'message': f'Unsupported cipher type: {cipher_type}'
            }

    @staticmethod
    def _rank_candidates(results, limit=5):
        """
        Order candidates best-first and attach a relative confidence to each.

        Args:
            results (list): Dicts with a 'score' (lower is better) and 'confidence'
            limit (int): How many candidates to keep

        Returns:
            list: The best candidates, with 'confidence' filled in
        """
        ranked = sorted(results, key=lambda result: result['score'])[:limit]
        weights = [1 / max(result['score'], 1e-12) for result in ranked]
        total = sum(weights)
        for result, weight in zip(ranked, weights):
            result['confidence'] = round(weight / total * 100, 1)
        return ranked

    @classmethod
    def _recover_keyword(cls, letters, key_length):
        """
        Recover a keyword by solving each column as a Caesar cipher.

        Args:
            letters (str): Lowercase ciphertext letters only
            key_length (int): Keyword length, which sets the number of columns

        Returns:
            str: The recovered keyword, one letter per column
        """
        keyword = ''
        for offset in range(key_length):
            column = letters[offset::key_length]
            best_shift = min(range(26), key=lambda shift: cls._chi_squared(
                cls._decrypt_caesar(column, shift)
            ))
            keyword += chr(best_shift + ord('a'))
        return keyword

    @classmethod
    def _refine_keyword(cls, ciphertext, keyword, passes=3):
        """
        Improve a keyword one letter at a time, keeping any change that scores better.

        Args:
            ciphertext (str): The encrypted text
            keyword (str): The keyword to start from
            passes (int): Maximum number of sweeps over the keyword

        Returns:
            str: The refined keyword (equal to the input if nothing improved)
        """
        best = list(keyword)
        best_score = cls._plaintext_score(cls._decrypt_polyalphabetic(ciphertext, keyword))
        for _ in range(passes):
            improved = False
            for position in range(len(best)):
                for shift in range(26):
                    trial = best.copy()
                    trial[position] = chr(shift + ord('a'))
                    score = cls._plaintext_score(
                        cls._decrypt_polyalphabetic(ciphertext, ''.join(trial))
                    )
                    if score < best_score:
                        best, best_score, improved = trial, score, True
            if not improved:
                break
        return ''.join(best)

    @classmethod
    def _chi_squared(cls, letters):
        """
        Chi-squared distance between a text's letter frequencies and English.

        Args:
            letters (str): Lowercase letters only

        Returns:
            float: Lower means closer to English letter frequencies
        """
        if not letters:
            return float('inf')
        counts = Counter(letters)
        total = len(letters)
        return sum(
            (counts.get(letter, 0) / total - expected) ** 2 / expected
            for letter, expected in cls.ENGLISH_FREQ_MAP.items()
        )

    @classmethod
    def _plaintext_score(cls, text):
        """
        Score decrypted text for English-likeness. Lower is better.

        Evidence comes from common words, indicator words, and bigrams. Letter
        frequencies are not used here: on real prose they ranked wrong keys higher.

        Args:
            text (str): Decrypted text

        Returns:
            float: Score where lower means more English-like
        """
        text_lower = text.lower()
        indicator_score = sum(5 for word in cls.INDICATOR_WORDS if word in text_lower)
        evidence = (
            1 + cls._calculate_word_score(text)
            + cls._calculate_ngram_score(text, 2) + indicator_score
        )
        return 1 / evidence

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
    def _calculate_word_score(cls, text):
        """
        Calculate a score based on the presence of common English words.
        
        Args:
            text (str): The text to analyze
            
        Returns:
            float: Score indicating likelihood of being English text
        """
        text_lower = text.lower()
        word_score = 0
        
        # Check for common words
        for word in cls.COMMON_WORDS:
            word_count = len(re.findall(r'\b' + word + r'\b', text_lower))
            word_score += word_count
            
        # Higher weight for indicator words
        for word in cls.INDICATOR_WORDS:
            word_count = len(re.findall(r'\b' + word + r'\b', text_lower))
            word_score += word_count * 3
            
        return word_score
    
    @classmethod
    def _calculate_ngram_score(cls, text, n=2):
        """
        Calculate score based on n-gram frequencies compared to English.
        
        Args:
            text (str): The text to analyze
            n (int): Size of n-grams (2 for bigrams, 3 for trigrams)
            
        Returns:
            float: Score indicating likelihood of being English text
        """
        if n == 2:
            ngram_map = cls.ENGLISH_BIGRAMS
        else:
            # For now we only have bigrams defined
            return 0
            
        # Extract only alphabetic characters
        letters_only = re.sub(r'[^a-zA-Z]', '', text).lower()
        
        # Not enough text for analysis
        if len(letters_only) < n:
            return 0
            
        # Count n-grams in the text
        ngrams = [letters_only[i:i+n] for i in range(len(letters_only) - n + 1)]
        ngram_counts = Counter(ngrams)
        
        # Calculate score based on common n-grams
        score = 0
        for ngram, count in ngram_counts.items():
            if ngram in ngram_map:
                score += count * ngram_map[ngram] * 100  # Scale up for better weighting
                
        return score
    
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
