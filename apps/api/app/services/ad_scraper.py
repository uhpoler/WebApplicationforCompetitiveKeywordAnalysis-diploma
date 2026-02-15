"""Service for extracting ad text from preview images using OCR."""

from __future__ import annotations

import asyncio
import io
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

# Type checking imports
if TYPE_CHECKING:
    import numpy as np
    from numpy import ndarray
    from PIL.Image import Image as PILImage

# Try to import pytesseract, PIL, and numpy, but don't fail if not available
try:
    import numpy as np
    import pytesseract
    from PIL import Image

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    Image = None
    np = None


# Regex to detect URLs in OCR text
URL_PATTERN = re.compile(
    r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:/[^\s]*)?",
    re.IGNORECASE,
)

# Pattern to detect "Sponsored" / "Sponsorisé" / "Ad" labels
SPONSORED_PATTERN = re.compile(
    r"\b(Sponsored|Sponsoris[eé]|Ad|Anzeige|Annonce|Patrocinado)\b",
    re.IGNORECASE,
)


@dataclass
class TextBlock:
    """A block of text extracted from OCR with spatial info."""

    text: str
    x: int
    y: int
    width: int
    height: int
    confidence: float


@dataclass
class AdTextContent:
    """Extracted ad text content."""

    headline: str | None = None
    description: str | None = None
    sitelinks: list[str] = field(default_factory=list)
    raw_text: str | None = None
    error: str | None = None


class AdTextScraper:
    """
    Extracts ad text from preview images using OCR (Tesseract).

    Uses color-based segmentation combined with spatial analysis to extract:
    - Blue text at top = Headline
    - Blue text at bottom (after gap) = Sitelinks (separated by · or similar)
    - Gray text (excluding URLs) = Description
    """

    def __init__(self) -> None:
        self._tesseract_checked = False
        self._tesseract_available = False
        self._tesseract_error: str | None = None

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available (lazy check)."""
        if self._tesseract_checked:
            return self._tesseract_available

        self._tesseract_checked = True

        if not TESSERACT_AVAILABLE:
            self._tesseract_error = (
                "Required libraries not installed. "
                "Run: pip install pytesseract Pillow numpy"
            )
            return False

        try:
            pytesseract.get_tesseract_version()  # type: ignore[union-attr]
            self._tesseract_available = True
            return True
        except pytesseract.TesseractNotFoundError:  # type: ignore[union-attr]
            self._tesseract_error = (
                "Tesseract OCR is not installed. "
                "Install it with: brew install tesseract (macOS) or "
                "apt-get install tesseract-ocr (Linux)"
            )
            return False
        except Exception as e:
            self._tesseract_error = f"Tesseract check failed: {str(e)}"
            return False

    async def extract_text_from_image_url(
        self,
        image_url: str,
        timeout: float = 30.0,
    ) -> AdTextContent:
        """
        Download an image and extract text using OCR with color segmentation.

        Args:
            image_url: URL of the preview image.
            timeout: HTTP request timeout in seconds.

        Returns:
            AdTextContent with extracted headline, description, and sitelinks.
        """
        content = AdTextContent()

        if not self._check_tesseract():
            content.error = self._tesseract_error
            return content

        if not image_url:
            content.error = "No image URL provided"
            return content

        try:
            # Download the image
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content

            # Open image with PIL
            image = Image.open(io.BytesIO(image_data))  # type: ignore[union-attr]

            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Extract structured text using spatial + color analysis
            self._extract_structured_text(image, content)

            # Build raw_text from structured parts
            parts = []
            if content.headline:
                parts.append(content.headline)
            if content.description:
                parts.append(content.description)
            if content.sitelinks:
                parts.append(" · ".join(content.sitelinks))
            content.raw_text = "\n".join(parts).strip() or None

            return content

        except httpx.HTTPError as e:
            content.error = f"Failed to download image: {str(e)}"
            return content
        except Exception as e:
            content.error = f"OCR extraction failed: {str(e)}"
            return content

    def _extract_structured_text(self, image: Any, content: AdTextContent) -> None:
        """
        Extract headline, description, and sitelinks using spatial OCR on
        color-segmented images.

        Uses pytesseract.image_to_data() to get bounding boxes, then groups
        text lines by their vertical position to separate headline from sitelinks.
        """
        img_array = np.array(image)  # type: ignore[union-attr]

        # Create color masks
        blue_mask = self._create_blue_mask(img_array)
        gray_mask = self._create_gray_mask(img_array)

        # Create masked images
        blue_image = self._apply_mask(image, blue_mask)
        gray_image = self._apply_mask(image, gray_mask)

        # --- Process blue text (headline + sitelinks) with spatial data ---
        blue_lines = self._get_text_lines(blue_image)
        if blue_lines:
            headline_lines, sitelink_lines = self._split_headline_sitelinks(blue_lines)

            headline_text = " ".join(headline_lines).strip()
            headline_text = self._clean_line(headline_text)
            if headline_text and len(headline_text) >= 10:
                content.headline = headline_text

            # Parse sitelinks (usually separated by · or on separate lines)
            if sitelink_lines:
                raw_sitelinks = " ".join(sitelink_lines).strip()
                content.sitelinks = self._parse_sitelinks(raw_sitelinks)

        # --- Process gray text (description) with URL filtering ---
        gray_lines = self._get_text_lines(gray_image)
        if gray_lines:
            # Filter out URL lines and sponsored labels
            desc_lines = []
            for line_text in gray_lines:
                cleaned = line_text.strip()
                if not cleaned:
                    continue
                # Skip lines that are primarily URLs
                without_urls = URL_PATTERN.sub("", cleaned).strip()
                if len(without_urls) < 5:
                    continue
                # Skip sponsored labels
                if SPONSORED_PATTERN.fullmatch(cleaned.strip()):
                    continue
                # Remove any remaining inline URLs
                without_urls = URL_PATTERN.sub("", cleaned).strip()
                desc_lines.append(without_urls)

            description = " ".join(desc_lines).strip()
            description = self._clean_line(description)
            if description and len(description) >= 10:
                content.description = description

    def _get_text_lines(self, masked_image: Any) -> list[str]:
        """
        Run OCR on a masked image and return text grouped by line.

        Uses image_to_data to get bounding boxes and groups words by
        their line number.
        """
        custom_config = r"--oem 3 --psm 6"
        data = pytesseract.image_to_data(  # type: ignore[union-attr]
            masked_image, config=custom_config, output_type=pytesseract.Output.DICT  # type: ignore[union-attr]
        )

        # Group words by (block_num, par_num, line_num) to preserve line structure
        line_groups: dict[tuple[int, int, int], list[tuple[int, str]]] = {}

        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])
            if not text or conf < 30:
                continue

            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            x = data["left"][i]
            if key not in line_groups:
                line_groups[key] = []
            line_groups[key].append((x, text))

        # Sort words within each line by x-coordinate, then sort lines by key
        lines: list[str] = []
        for key in sorted(line_groups.keys()):
            words = line_groups[key]
            words.sort(key=lambda w: w[0])
            line_text = " ".join(w[1] for w in words)
            if line_text.strip():
                lines.append(line_text.strip())

        return lines

    def _split_headline_sitelinks(
        self, blue_lines: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Split blue text lines into headline lines and sitelink lines.

        Sitelinks are identified by:
        - Lines containing · (middle dot separator)
        - Short lines after a gap from the main headline text
        """
        if not blue_lines:
            return [], []

        if len(blue_lines) == 1:
            # Check if the single line contains sitelink separators
            line = blue_lines[0]
            if "·" in line or " - " not in line and "·" in line:
                # Try splitting: part before · might be headline
                parts = [p.strip() for p in line.split("·")]
                if len(parts) >= 2 and len(parts[0]) > 15:
                    return [parts[0]], parts[1:]
            return blue_lines, []

        # For multiple lines, look for sitelink indicators
        headline_lines: list[str] = []
        sitelink_lines: list[str] = []
        found_sitelinks = False

        for line in blue_lines:
            # Sitelink indicators: contains ·, or is a very short line after headline
            has_separator = "·" in line
            is_short_after_headline = (
                len(headline_lines) >= 1
                and len(line) < 30
                and not found_sitelinks
            )

            if has_separator:
                found_sitelinks = True
                sitelink_lines.append(line)
            elif found_sitelinks:
                sitelink_lines.append(line)
            elif is_short_after_headline and self._looks_like_sitelink(line):
                found_sitelinks = True
                sitelink_lines.append(line)
            else:
                headline_lines.append(line)

        return headline_lines, sitelink_lines

    def _looks_like_sitelink(self, text: str) -> bool:
        """Check if text looks like a sitelink (short, capitalized phrase)."""
        words = text.split()
        # Sitelinks are typically 1-4 words, capitalized
        if 1 <= len(words) <= 5 and len(text) < 40:
            return True
        return False

    def _parse_sitelinks(self, text: str) -> list[str]:
        """Parse sitelink text into individual links."""
        if not text:
            return []

        # Split by common separators
        parts = re.split(r"\s*[·•|]\s*", text)
        sitelinks = []
        for part in parts:
            cleaned = part.strip()
            if cleaned and len(cleaned) >= 3:
                # Remove any trailing/leading punctuation
                cleaned = cleaned.strip(".,;:-")
                if cleaned:
                    sitelinks.append(cleaned)

        return sitelinks

    def _create_blue_mask(self, img_array: Any) -> Any:
        """
        Create a mask for blue text (Google's link/headline blue).

        Detects pixels where blue channel is dominant.
        """
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

        # Blue text: B > R and B > G, with B being reasonably high
        blue_dominant = (b > r + 30) & (b > g + 30) & (b > 80)

        # Also catch the specific Google blue
        google_blue = (b > 120) & (r < 100) & (g < 100)

        return blue_dominant | google_blue

    def _create_gray_mask(self, img_array: Any) -> Any:
        """
        Create a mask for gray text (description text).

        Gray text has similar R, G, B values in the mid-range.
        Excludes green-ish text (URLs in Google Ads are slightly green-tinted).
        """
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]

        # Calculate the difference between channels
        r_int, g_int, b_int = r.astype(int), g.astype(int), b.astype(int)
        max_diff = np.maximum(  # type: ignore[union-attr]
            np.maximum(np.abs(r_int - g_int), np.abs(g_int - b_int)),  # type: ignore[union-attr]
            np.abs(r_int - b_int),  # type: ignore[union-attr]
        )

        # Gray: channels are similar (diff < 30) and in mid-range
        is_gray = max_diff < 30

        # Mid-range intensity (not too bright, not too dark)
        avg_intensity = (r_int + g_int + b_int) / 3
        is_mid_range = (avg_intensity > 50) & (avg_intensity < 180)

        return is_gray & is_mid_range

    def _apply_mask(self, image: Any, mask: Any) -> Any:
        """Apply a mask to an image - keep masked pixels, make rest white."""
        img_array = np.array(image)  # type: ignore[union-attr]

        # Create white background
        result = np.ones_like(img_array) * 255  # type: ignore[union-attr]

        # Copy pixels where mask is True
        result[mask] = img_array[mask]

        return Image.fromarray(result.astype(np.uint8))  # type: ignore[union-attr]

    def _clean_line(self, text: str) -> str | None:
        """Clean up a line of OCR-extracted text."""
        if not text:
            return None

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove common OCR artifacts
        text = re.sub(r"[|\\{}\[\]]", "", text)
        text = text.strip()

        return text if text else None

    async def extract_text_from_ad_item(self, ad_item: dict[str, Any]) -> dict[str, Any]:
        """
        Extract text from an ad item's preview image.

        Args:
            ad_item: Ad item dict with preview_image data.

        Returns:
            Ad item with added text_content field.
        """
        preview_image = ad_item.get("preview_image")

        if not preview_image:
            ad_item["text_content"] = AdTextContent(
                error="No preview image available"
            ).__dict__
            return ad_item

        image_url = preview_image.get("url") if isinstance(preview_image, dict) else None

        if not image_url:
            ad_item["text_content"] = AdTextContent(
                error="No image URL in preview_image"
            ).__dict__
            return ad_item

        text_content = await self.extract_text_from_image_url(image_url)
        ad_item["text_content"] = {
            "headline": text_content.headline,
            "description": text_content.description,
            "sitelinks": text_content.sitelinks,
            "raw_text": text_content.raw_text,
            "error": text_content.error,
        }

        return ad_item

    async def scrape_multiple_ads(
        self,
        ad_items: list[dict[str, Any]],
        max_concurrent: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Extract text from multiple ad items using OCR.

        Args:
            ad_items: List of ad items with preview_image data.
            max_concurrent: Maximum concurrent OCR operations.

        Returns:
            List of ad items with added text_content.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def extract_with_limit(ad_item: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self.extract_text_from_ad_item(ad_item)

        tasks = [extract_with_limit(ad) for ad in ad_items]
        results = await asyncio.gather(*tasks)
        return list(results)


# Singleton instance
_scraper_instance: AdTextScraper | None = None


def get_ad_scraper() -> AdTextScraper:
    """Get the ad scraper instance."""
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = AdTextScraper()
    return _scraper_instance
