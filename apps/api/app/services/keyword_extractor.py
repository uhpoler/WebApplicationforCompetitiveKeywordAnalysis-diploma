"""Keyword extraction service using YAKE for extracting key phrases from ad text.

Key design decisions:
- Keyphrases are extracted PER-SEGMENT (headline, description, sitelinks)
  to avoid merging unrelated context across boundaries.
- Text is split into sentences before extraction to prevent cross-sentence phrases.
- Ad-specific cleaning removes URLs, ratings, OCR artifacts, and common ad noise.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

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
    """Extract key phrases from ad text using YAKE algorithm."""

    # ---------- Cleaning patterns ----------
    # URLs: http(s), www, or domain-like strings
    URL_PATTERN = re.compile(
        r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:/[^\s]*)?",
        re.IGNORECASE,
    )
    # Ratings like "4.1 (555)", phone numbers, standalone numbers
    NUMBER_PATTERN = re.compile(
        r"\b\d+\.?\d*\s*\([^)]*\)|\b\d{3,}[-.\s]?\d{3,}[-.\s]?\d{4}\b|\b\d+\.?\d*\b"
    )
    # Special characters (keep basic punctuation for sentence splitting)
    SYMBOL_PATTERN = re.compile(r"[^\w\s.,!?;:'\"-]", re.UNICODE)
    # Repeated characters (OCR artifacts like "aaaa")
    REPEATED_CHAR_PATTERN = re.compile(r"(.)\1{3,}")
    # Common OCR garbage words
    OCR_GARBAGE_PATTERN = re.compile(
        r"\b(gor|Saree|oes|bees|sa|ston|bs|eX|il)\b", re.IGNORECASE
    )
    # Common ad call-to-action phrases that aren't meaningful keyphrases
    CTA_PATTERN = re.compile(
        r"\b(try (?:it|them|now)|learn more|sign up|get started|click here|"
        r"buy now|shop now|order now|free trial|download now|start now|"
        r"view more|see more|find out|read more)\b",
        re.IGNORECASE,
    )
    # Sentence boundary pattern (split on . ! ? ; or significant punctuation)
    SENTENCE_SPLIT = re.compile(r"[.!?;]+\s+|\s*[~\-–—]\s+|\n+")

    def __init__(
        self,
        language: str = "en",
        max_ngram_size: int = 3,
        dedup_threshold: float = 0.7,
        num_keywords: int = 5,
    ):
        """
        Initialize the keyword extractor.

        Args:
            language: Language code for keyword extraction
            max_ngram_size: Maximum number of words in a keyphrase (1-5)
            dedup_threshold: Deduplication threshold (0-1, lower = stricter)
            num_keywords: Maximum number of keywords to extract per segment
        """
        self.language = language
        self.max_ngram_size = min(max(max_ngram_size, 1), 5)
        self.dedup_threshold = dedup_threshold
        self.num_keywords = min(max(num_keywords, 1), 5)
        self._extractor: yake.KeywordExtractor | None = None  # type: ignore[name-defined]

    def _get_extractor(self) -> Any:
        """Lazy-load the YAKE extractor."""
        if self._extractor is None and YAKE_AVAILABLE:
            self._extractor = yake.KeywordExtractor(  # type: ignore[union-attr]
                lan=self.language,
                n=self.max_ngram_size,
                dedupLim=self.dedup_threshold,
                dedupFunc="seqm",
                windowsSize=1,
                top=self.num_keywords * 2,  # extract more, filter later
            )
        return self._extractor

    # ---------- Text cleaning ----------

    def clean_text(self, text: str | None) -> str:
        """
        Clean text from URLs, numbers, symbols, and OCR artifacts.

        Preserves sentence-boundary punctuation so that later splitting works.
        """
        if not text:
            return ""

        cleaned = text

        # Remove URLs first (before other transformations)
        cleaned = self.URL_PATTERN.sub(" ", cleaned)

        # Remove ratings and numbers
        cleaned = self.NUMBER_PATTERN.sub(" ", cleaned)

        # Remove OCR garbage words
        cleaned = self.OCR_GARBAGE_PATTERN.sub(" ", cleaned)

        # Remove CTA phrases (they pollute keyphrases)
        cleaned = self.CTA_PATTERN.sub(" ", cleaned)

        # Remove special symbols (keep sentence-boundary punctuation)
        cleaned = self.SYMBOL_PATTERN.sub(" ", cleaned)

        # Remove repeated characters (OCR artifacts)
        cleaned = self.REPEATED_CHAR_PATTERN.sub(r"\1", cleaned)

        # Normalize whitespace
        cleaned = " ".join(cleaned.split())

        # Remove very short words (likely OCR artifacts), keep "a", "i"
        words = cleaned.split()
        words = [w for w in words if len(w) > 1 or w.lower() in ("a", "i")]
        cleaned = " ".join(words)

        return cleaned.strip()

    # ---------- Per-sentence extraction ----------

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences to avoid cross-boundary phrases."""
        sentences = self.SENTENCE_SPLIT.split(text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 5]

    def _extract_from_sentence(self, sentence: str) -> list[tuple[str, float]]:
        """Extract keyphrases from a single sentence using YAKE."""
        extractor = self._get_extractor()
        if not extractor:
            return []

        try:
            return extractor.extract_keywords(sentence)
        except Exception:
            return []

    def extract_keyphrases_from_segment(self, text: str | None) -> list[str]:
        """
        Extract keyphrases from a single text segment (headline OR description).

        Splits the segment into sentences and runs YAKE on each sentence
        independently, so keyphrases never cross sentence boundaries.
        """
        if not YAKE_AVAILABLE:
            return []

        cleaned = self.clean_text(text)
        if not cleaned or len(cleaned) < 5:
            return []

        # Split into sentences
        sentences = self._split_into_sentences(cleaned)
        if not sentences:
            # If no sentence boundaries, treat whole text as one sentence
            sentences = [cleaned]

        # Collect candidates from all sentences with their scores
        all_candidates: list[tuple[str, float]] = []
        for sentence in sentences:
            if len(sentence.split()) < 2:
                continue
            candidates = self._extract_from_sentence(sentence)
            all_candidates.extend(candidates)

        # Deduplicate, validate, and rank
        seen: set[str] = set()
        keyphrases: list[str] = []

        # Sort by score (lower = better in YAKE)
        all_candidates.sort(key=lambda x: x[1])

        for keyword, _score in all_candidates:
            keyphrase = keyword.strip().lower()

            # Validate word count (1-5 words)
            word_count = len(keyphrase.split())
            if not (1 <= word_count <= 5):
                continue

            # Skip if too short or is garbage
            if len(keyphrase) < 3 or self._is_garbage(keyphrase):
                continue

            # Skip near-duplicates: if any existing phrase fully contains this one
            # or this one fully contains an existing phrase
            is_duplicate = False
            for existing in seen:
                if existing in keyphrase or keyphrase in existing:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue

            seen.add(keyphrase)
            keyphrases.append(keyphrase)

        return keyphrases

    # ---------- Main extraction method ----------

    def extract_from_ad_text(
        self,
        headline: str | None,
        description: str | None,
        raw_text: str | None = None,
        sitelinks: list[str] | None = None,
    ) -> list[str]:
        """
        Extract keyphrases from ad text components.

        Each component is processed independently to prevent phrases that
        merge words from unrelated sections (e.g. headline + description).

        Args:
            headline: Ad headline text
            description: Ad description text
            raw_text: Raw extracted text (fallback only if headline & desc missing)
            sitelinks: List of sitelink texts

        Returns:
            List of unique keyphrases (1-5 total)
        """
        all_keyphrases: list[str] = []
        seen: set[str] = set()

        def _add_unique(phrases: list[str]) -> None:
            for p in phrases:
                lower_p = p.lower()
                # Check for containment duplicates across segments too
                is_dup = False
                for existing in seen:
                    if existing in lower_p or lower_p in existing:
                        is_dup = True
                        break
                if not is_dup:
                    seen.add(lower_p)
                    all_keyphrases.append(p)

        # 1. Extract from headline (highest priority)
        if headline:
            headline_phrases = self.extract_keyphrases_from_segment(headline)
            _add_unique(headline_phrases)

        # 2. Extract from description
        if description:
            desc_phrases = self.extract_keyphrases_from_segment(description)
            _add_unique(desc_phrases)

        # 3. Extract from sitelinks (often contain good keywords)
        if sitelinks:
            for sitelink in sitelinks:
                if sitelink and len(sitelink) >= 3:
                    # Sitelinks are already short phrases - use them directly
                    cleaned = self.clean_text(sitelink)
                    if cleaned and len(cleaned) >= 3 and not self._is_garbage(cleaned):
                        lower_cleaned = cleaned.lower()
                        is_dup = False
                        for existing in seen:
                            if existing in lower_cleaned or lower_cleaned in existing:
                                is_dup = True
                                break
                        if not is_dup:
                            seen.add(lower_cleaned)
                            all_keyphrases.append(lower_cleaned)

        # 4. Fallback to raw_text only if nothing else worked
        if not all_keyphrases and raw_text:
            raw_phrases = self.extract_keyphrases_from_segment(raw_text)
            _add_unique(raw_phrases)

        # Return top 5
        return all_keyphrases[: self.num_keywords]

    # ---------- Validation helpers ----------

    def _is_garbage(self, phrase: str) -> bool:
        """Check if a phrase is likely OCR garbage."""
        # Too many consonants in a row (likely OCR error)
        if re.search(r"[bcdfghjklmnpqrstvwxz]{4,}", phrase, re.IGNORECASE):
            return True

        # Mostly non-alphabetic characters
        alpha_count = sum(1 for c in phrase if c.isalpha())
        if len(phrase) > 0 and alpha_count < len(phrase) * 0.6:
            return True

        # Single word that is very short
        if len(phrase.split()) == 1 and len(phrase) < 3:
            return True

        return False


# Singleton instance for dependency injection
_extractor_instance: KeywordExtractor | None = None


def get_keyword_extractor() -> KeywordExtractor:
    """Get a keyword extractor instance."""
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = KeywordExtractor()
    return _extractor_instance
