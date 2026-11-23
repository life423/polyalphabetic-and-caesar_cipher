"""Key search with our own locally trained next-character language model."""
from src.ai.analyzer import CipherAnalyzer
from src.ai.language_model import language_score
from src.core.ciphers import CaesarCipher


class NeuralCipherAnalyzer(CipherAnalyzer):
    """Reuse existing searches while learning which plaintext candidates to prefer."""

    _plaintext_score = staticmethod(language_score)

    @classmethod
    def analyze_caesar(cls, ciphertext):
        if not any(c.isascii() and c.isalpha() for c in (ciphertext or '')):
            return []
        results = []
        for shift in range(26):
            decrypted = CaesarCipher.transform(ciphertext, shift, False)
            results.append({'shift': shift, 'score': language_score(decrypted), 'confidence': 0,
                            'sample': decrypted[:100] + ('...' if len(decrypted) > 100 else '')})
        return cls._rank_candidates(results)
