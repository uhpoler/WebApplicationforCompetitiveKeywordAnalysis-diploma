"""Keyword extraction service using YAKE for extracting key phrases from ad text."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

# Try to import yake, handle gracefully if not installed
try:
    import yake

    YAKE_AVAILABLE = True
except ImportError:
    YAKE_AVAILABLE = False
    yake = None  # type: ignore[assignment]

if TYPE_CHECKING:
    pass


class KeywordExtractor:
    """Extract key phrases from text using YAKE algorithm."""

    # Common OCR artifacts and garbage patterns to remove
    URL_PATTERN = re.compile(
        r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/[^\s]*)?",
        re.IGNORECASE,
    )
    # Match standalone numbers, ratings like "4.1 (555)", phone numbers
    NUMBER_PATTERN = re.compile(
        r"\b\d+\.?\d*\s*\([^)]*\)|\b\d{3,}[-.\s]?\d{3,}[-.\s]?\d{4}\b|\b\d+\.?\d*\b"
    )
    # Match special characters and symbols (keeping basic punctuation)
    SYMBOL_PATTERN = re.compile(r"[^\w\s.,!?'-]", re.UNICODE)
    # Match repeated characters (OCR artifacts)
    REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{3,}")
    # Match single characters surrounded by spaces (OCR noise)
    SINGLE_CHAR_PATTERN = re.compile(r"\s[a-zA-Z]\s")
    # Match common OCR garbage patterns
    OCR_GARBAGE_PATTERN = re.compile(
        r"\b(gor|Saree|oes|bees|sa|ston|bs|eX|il)\b", re.IGNORECASE
    )

    def __init__(
        self,
        language: str = "en",
        max_ngram_size: int = 3,
        dedup_threshold: float = 0.9,
        num_keywords: int = 5,
    ):
        """
        Initialize the keyword extractor.

        Args:
            language: Language code for keyword extraction
            max_ngram_size: Maximum number of words in a keyphrase (1-5)
            dedup_threshold: Deduplication threshold (0-1)
            num_keywords: Maximum number of keywords to extract (1-5)
        """
        self.language = language
        self.max_ngram_size = min(max(max_ngram_size, 1), 5)
        self.dedup_threshold = dedup_threshold
        self.num_keywords = min(max(num_keywords, 1), 5)

        if YAKE_AVAILABLE:
            self.extractor = yake.KeywordExtractor(  # type: ignore[union-attr]
                lan=language,
                n=self.max_ngram_size,
                dedupLim=dedup_threshold,
                dedupFunc="seqm",
                windowsSize=1,
                top=num_keywords,
            )
        else:
            self.extractor = None

    def clean_text(self, text: str | None) -> str:
        """
        Clean text from URLs, numbers, symbols, and OCR artifacts.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text suitable for keyword extraction
        """
        if not text:
            return ""

        cleaned = text

        # Remove URLs
        cleaned = self.URL_PATTERN.sub(" ", cleaned)

        # Remove numbers and ratings
        cleaned = self.NUMBER_PATTERN.sub(" ", cleaned)

        # Remove OCR garbage words
        cleaned = self.OCR_GARBAGE_PATTERN.sub(" ", cleaned)

        # Remove special symbols (keep basic punctuation)
        cleaned = self.SYMBOL_PATTERN.sub(" ", cleaned)

        # Remove repeated characters (OCR artifacts like "aaaa")
        cleaned = self.REPEATED_CHAR_PATTERN.sub(r"\1", cleaned)

        # Remove single standalone characters
        cleaned = self.SINGLE_CHAR_PATTERN.sub(" ", cleaned)

        # Normalize whitespace
        cleaned = " ".join(cleaned.split())

        # Remove very short words (likely OCR artifacts)
        words = cleaned.split()
        words = [w for w in words if len(w) > 1 or w.lower() in ("a", "i")]
        cleaned = " ".join(words)

        return cleaned.strip()

    def extract_keyphrases(self, text: str | None) -> list[str]:
        """
        Extract key phrases from text.

        Args:
            text: Text to extract keyphrases from

        Returns:
            List of keyphrases (1-5 phrases, each 1-5 words)
        """
        if not YAKE_AVAILABLE:
            return []

        # Clean the text first
        cleaned_text = self.clean_text(text)

        if not cleaned_text or len(cleaned_text) < 10:
            return []

        try:
            # Extract keywords using YAKE
            # YAKE returns tuples of (keyword, score) - lower score = more relevant
            keywords = self.extractor.extract_keywords(cleaned_text)  # type: ignore[union-attr]

            # Extract just the keyword strings
            keyphrases = []
            for keyword, _score in keywords:
                # Validate keyphrase: 1-5 words
                word_count = len(keyword.split())
                if 1 <= word_count <= 5:
                    # Clean up the keyphrase
                    keyphrase = keyword.strip().lower()
                    # Skip if too short or contains garbage
                    if len(keyphrase) >= 3 and not self._is_garbage(keyphrase):
                        keyphrases.append(keyphrase)

            # Return up to num_keywords unique keyphrases
            return keyphrases[: self.num_keywords]

        except Exception:
            return []

    def _is_garbage(self, phrase: str) -> bool:
        """Check if a phrase is likely OCR garbage."""
        # Check for too many consonants in a row (likely OCR error)
        consonant_pattern = re.compile(r"[bcdfghjklmnpqrstvwxz]{4,}", re.IGNORECASE)
        if consonant_pattern.search(phrase):
            return True

        # Check if mostly non-alphabetic
        alpha_count = sum(1 for c in phrase if c.isalpha())
        if alpha_count < len(phrase) * 0.7:
            return True

        return False

    def extract_from_ad_text(
        self,
        headline: str | None,
        description: str | None,
        raw_text: str | None = None,
    ) -> list[str]:
        """
        Extract keyphrases from ad text components.

        Combines headline, description, and raw_text for better extraction.

        Args:
            headline: Ad headline text
            description: Ad description text
            raw_text: Raw extracted text (fallback)

        Returns:
            List of keyphrases
        """
        # Combine available text
        text_parts = []
        if headline:
            text_parts.append(headline)
        if description:
            text_parts.append(description)
        if raw_text and not (headline or description):
            text_parts.append(raw_text)

        combined_text = " ".join(text_parts)

        return self.extract_keyphrases(combined_text)


# Singleton instance for dependency injection
_extractor_instance: KeywordExtractor | None = None


def get_keyword_extractor() -> KeywordExtractor:
    """Get a keyword extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = KeywordExtractor()
    return _extractor_instance
