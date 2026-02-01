"""Service for extracting ad text from preview images using OCR."""

from __future__ import annotations

import asyncio
import io
import re
from dataclasses import dataclass
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


@dataclass
class AdTextContent:
    """Extracted ad text content."""

    headline: str | None = None
    description: str | None = None
    raw_text: str | None = None
    error: str | None = None


class AdTextScraper:
    """
    Extracts ad text from preview images using OCR (Tesseract).

    Uses color-based segmentation to extract:
    - Blue text = Headlines/Links
    - Gray text = Description
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
            AdTextContent with extracted headline and description.
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

            # Extract text using color-based segmentation
            headline, description = self._extract_text_by_color(image)

            content.headline = headline
            content.description = description
            content.raw_text = (
                f"{headline or ''}\n{description or ''}".strip() or None
            )

            return content

        except httpx.HTTPError as e:
            content.error = f"Failed to download image: {str(e)}"
            return content
        except Exception as e:
            content.error = f"OCR extraction failed: {str(e)}"
            return content

    def _extract_text_by_color(
        self, image: Any
    ) -> tuple[str | None, str | None]:
        """
        Extract headline and description based on text color.

        Google Ads use specific colors:
        - Blue text (~RGB 26, 13, 171) = Headline/Links
        - Gray text (~RGB 95, 99, 104) = Description

        Returns:
            Tuple of (headline, description)
        """
        img_array = np.array(image)  # type: ignore[union-attr]

        # Create masks for blue and gray text
        blue_mask = self._create_blue_mask(img_array)
        gray_mask = self._create_gray_mask(img_array)

        # Create images with only the colored text visible (white background)
        blue_image = self._apply_mask(image, blue_mask)
        gray_image = self._apply_mask(image, gray_mask)

        # OCR each masked image
        custom_config = r"--oem 3 --psm 6"

        headline_raw = pytesseract.image_to_string(  # type: ignore[union-attr]
            blue_image, config=custom_config
        )
        headline = self._clean_ocr_text(headline_raw)

        description_raw = pytesseract.image_to_string(  # type: ignore[union-attr]
            gray_image, config=custom_config
        )
        description = self._clean_ocr_text(description_raw)

        # Filter out noise - text should be substantial
        if headline and len(headline) < 10:
            headline = None
        if description and len(description) < 10:
            description = None

        return headline, description

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

    def _clean_ocr_text(self, text: str) -> str | None:
        """Clean up OCR-extracted text."""
        if not text:
            return None

        # Remove excessive whitespace and OCR artifacts
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[|\\]", "", text)

        # Join lines into single text
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        result = " ".join(lines).strip()

        return result if result else None

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
