"""
Test script for the AI-driven cipher analysis functionality.

This script demonstrates how the cipher analyzer works by encrypting some
sample text and then using the analyzer to attempt to recover the key.
"""

from cipher_core import CaesarCipher, PolyalphabeticCipher
from cipher_ai import CipherAnalyzer


def test_caesar_analyzer():
    """Test the Caesar cipher analyzer with known plaintext."""
    print("\n=== Testing Caesar Cipher Analysis ===")
    
    # Original text (a famous quote)
    plaintext = """To be, or not to be, that is the question:
    Whether 'tis nobler in the mind to suffer
    The slings and arrows of outrageous fortune,
    Or to take arms against a sea of troubles
    And by opposing end them."""
    
    # Encrypt with a known shift
    actual_shift = 7
    print(f"Original shift: {actual_shift}")
    
    ciphertext = CaesarCipher.transform(plaintext, actual_shift, encrypt=True)
    print(f"\nEncrypted text:\n{ciphertext[:100]}...\n")
    
    # Analyze the ciphertext
    print("Analyzing ciphertext...")
    results = CipherAnalyzer.analyze_caesar(ciphertext)
    
    # Display results
    print("\nTop 5 predictions:")
    for i, result in enumerate(results):
        print(
            f"{i+1}. Shift = {result['shift']} "
            f"(Confidence: {result['confidence']}%)"
        )
        print(f"   Sample: {result['sample'][:50]}...\n")
    
    # Check if our analysis found the correct shift
    shifts = [r['shift'] for r in results]
    if actual_shift in shifts:
        position = shifts.index(actual_shift) + 1
        print(
            f"SUCCESS! Correct shift ({actual_shift}) found at position "
            f"{position}"
        )
    else:
        print(
            f"Analysis did not find the correct shift ({actual_shift}) "
            f"in top 5 results."
        )


def test_polyalphabetic_analyzer():
    """Test the Polyalphabetic cipher analyzer with known plaintext."""
    print("\n=== Testing Polyalphabetic Cipher Analysis ===")
    
    # Original text
    plaintext = """When in the Course of human events, it becomes necessary for one 
    people to dissolve the political bands which have connected them with another, 
    and to assume among the powers of the earth, the separate and equal station to 
    which the Laws of Nature and of Nature's God entitle them, a decent respect to 
    the opinions of mankind requires that they should declare the causes which impel 
    them to the separation."""
    
    # Encrypt with a known keyword
    actual_keyword = "liberty"
    print(f"Original keyword: '{actual_keyword}'")
    
    ciphertext = PolyalphabeticCipher.transform(
        plaintext, actual_keyword, encrypt=True
    )
    print(f"\nEncrypted text:\n{ciphertext[:100]}...\n")
    
    # Analyze the ciphertext
    print("Analyzing ciphertext...")
    results = CipherAnalyzer.analyze_polyalphabetic(ciphertext)
    
    # Display results
    print("\nTop predictions:")
    for i, result in enumerate(results):
        print(
            f"{i+1}. Keyword = '{result['keyword']}' "
            f"(Confidence: {result['confidence']}%)"
        )
        print(f"   Sample: {result['sample'][:50]}...\n")
    
    # Check if our analysis found the correct keyword or a functionally equivalent one
    found = False
    for i, result in enumerate(results):
        # Check if decryption with this keyword produces readable text
        decrypted = PolyalphabeticCipher.transform(
            ciphertext, result['keyword'], encrypt=False
        )
        if (actual_keyword == result['keyword'] or 
                plaintext[:20].lower() in decrypted[:30].lower()):
            found = True
            print(
                f"SUCCESS! Working keyword found at position {i+1}: "
                f"'{result['keyword']}'"
            )
            break
    
    if not found:
        print(
            "Analysis did not find the correct keyword or equivalent "
            "in top results."
        )


if __name__ == "__main__":
    print("Testing the AI-driven cipher analysis functionality")
    test_caesar_analyzer()
    test_polyalphabetic_analyzer()
