"""Language detection service for ad text."""

from __future__ import annotations

# Try to import langdetect
try:
    from langdetect import detect, LangDetectException

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    detect = None  # type: ignore[assignment]
    LangDetectException = Exception  # type: ignore[misc, assignment]


# Common language codes and their names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ar": "Arabic",
    "tr": "Turkish",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "cs": "Czech",
    "uk": "Ukrainian",
    "el": "Greek",
    "he": "Hebrew",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "hi": "Hindi",
    "bn": "Bengali",
    "ro": "Romanian",
    "hu": "Hungarian",
    "sk": "Slovak",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sl": "Slovenian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
}


class LanguageDetector:
    """Detect language of text using langdetect."""

    def detect_language(self, text: str | None) -> str | None:
        """
        Detect the language of the given text.

        Args:
            text: Text to detect language for

        Returns:
            ISO 639-1 language code (e.g., 'en', 'es', 'fr') or None if detection fails
        """
        if not LANGDETECT_AVAILABLE:
            return None

        if not text or len(text.strip()) < 10:
            return None

        try:
            lang = detect(text)  # type: ignore[misc]
            return lang
        except LangDetectException:
            return None
        except Exception:
            return None

    def is_language(self, text: str | None, language_code: str) -> bool:
        """
        Check if text is in the specified language.

        Args:
            text: Text to check
            language_code: ISO 639-1 language code to match

        Returns:
            True if text is in the specified language
        """
        detected = self.detect_language(text)
        if detected is None:
            return False

        # Handle Chinese variants
        if language_code.startswith("zh"):
            return detected.startswith("zh")

        return detected.lower() == language_code.lower()

    @staticmethod
    def get_supported_languages() -> list[dict[str, str]]:
        """
        Get list of supported languages.

        Returns:
            List of dicts with 'code' and 'name' keys
        """
        return [
            {"code": code, "name": name}
            for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
        ]


# Singleton instance
_detector_instance: LanguageDetector | None = None


def get_language_detector() -> LanguageDetector:
    """Get a language detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance
