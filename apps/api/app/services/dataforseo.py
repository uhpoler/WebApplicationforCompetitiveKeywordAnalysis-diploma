"""DataForSEO API client service for retrieving Google Ads data."""

import base64
from urllib.parse import urlparse

import httpx

from app.core.config import settings


class DataForSEOError(Exception):
    """Custom exception for DataForSEO API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DataForSEOClient:
    """Client for interacting with the DataForSEO V3 API."""

    BASE_URL = "https://api.dataforseo.com"
    ADS_SEARCH_LIVE_ENDPOINT = "/v3/serp/google/ads_search/live/advanced"
    ADS_SEARCH_LOCATIONS_ENDPOINT = "/v3/serp/google/ads_search/locations"

    def __init__(self, login: str | None = None, password: str | None = None):
        self.login = login or settings.dataforseo_login
        self.password = password or settings.dataforseo_password

        if not self.login or not self.password:
            raise DataForSEOError(
                "DataForSEO credentials not configured. "
                "Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD environment variables."
            )

    def _get_auth_header(self) -> str:
        """Generate Base64-encoded authorization header."""
        credentials = f"{self.login}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """
        Normalize a domain URL to a clean domain name.

        Examples:
            - "https://theliven.com/" -> "theliven.com"
            - "http://example.com/page" -> "example.com"
            - "example.com" -> "example.com"
        """
        domain = domain.strip()

        # Add scheme if not present for proper parsing
        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"

        parsed = urlparse(domain)
        hostname = parsed.netloc or parsed.path.split("/")[0]

        # Remove www. prefix if present
        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname.lower()

    async def get_domain_ads(
        self,
        domain: str,
        location_code: int = 2840,  # United States
        platform: str = "google_search",
        ad_format: str = "text",
        depth: int = 100,
    ) -> list[dict]:
        """
        Retrieve Google ads for a specific domain.

        Args:
            domain: The domain to search ads for (e.g., "theliven.com")
            location_code: Location code (default: 2840 for United States)
            platform: Advertising platform (default: "google_search")
            ad_format: Ad format filter - "text", "image", "video", or "all"
            depth: Number of results to retrieve (default: 100, max: 120)

        Returns:
            List of ad items from the API response.

        Raises:
            DataForSEOError: If the API request fails.
        """
        normalized_domain = self._normalize_domain(domain)

        request_data = [
            {
                "target": normalized_domain,
                "location_code": location_code,
                "platform": platform,
                "format": ad_format,
                "depth": min(depth, 120),  # API max is 120
            }
        ]

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}{self.ADS_SEARCH_LIVE_ENDPOINT}",
                json=request_data,
                headers=headers,
            )

            if response.status_code != 200:
                raise DataForSEOError(
                    f"HTTP error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()

            # Check API-level status
            if data.get("status_code") != 20000:
                raise DataForSEOError(
                    f"API error: {data.get('status_message', 'Unknown error')}",
                    status_code=data.get("status_code"),
                )

            # Extract items from the response
            tasks = data.get("tasks", [])
            if not tasks:
                return []

            task = tasks[0]
            if task.get("status_code") != 20000:
                raise DataForSEOError(
                    f"Task error: {task.get('status_message', 'Unknown error')}",
                    status_code=task.get("status_code"),
                )

            results = task.get("result", [])
            if not results:
                return []

            return results[0].get("items", [])

    async def get_domain_ad_texts(
        self,
        domain: str,
        location_code: int = 2840,
        platform: str = "google_search",
        depth: int = 100,
    ) -> list[str]:
        """
        Retrieve text ad content for a specific domain.

        This method filters for text-format ads and extracts readable text
        from the ad titles and preview URLs.

        Args:
            domain: The domain to search ads for.
            location_code: Location code (default: 2840 for United States).
            platform: Advertising platform (default: "google_search").
            depth: Number of results to retrieve (default: 100).

        Returns:
            List of ad text strings.
        """
        items = await self.get_domain_ads(
            domain=domain,
            location_code=location_code,
            platform=platform,
            ad_format="text",
            depth=depth,
        )

        ad_texts: list[str] = []

        for item in items:
            if item.get("type") != "ads_search":
                continue

            # Only process text format ads
            if item.get("format") != "text":
                continue

            # Build a text representation of the ad
            ad_parts: list[str] = []

            title = item.get("title")
            if title:
                ad_parts.append(f"Advertiser: {title}")

            advertiser_id = item.get("advertiser_id")
            if advertiser_id:
                ad_parts.append(f"ID: {advertiser_id}")

            creative_id = item.get("creative_id")
            if creative_id:
                ad_parts.append(f"Creative: {creative_id}")

            url = item.get("url")
            if url:
                ad_parts.append(f"URL: {url}")

            first_shown = item.get("first_shown")
            last_shown = item.get("last_shown")
            if first_shown and last_shown:
                ad_parts.append(f"Active: {first_shown} to {last_shown}")

            verified = item.get("verified")
            if verified is not None:
                ad_parts.append(f"Verified: {'Yes' if verified else 'No'}")

            if ad_parts:
                ad_texts.append(" | ".join(ad_parts))

        return ad_texts


    async def get_available_locations(self) -> list[dict]:
        """
        Retrieve available locations for Google Ads Search.

        Returns:
            List of location objects with location_code, location_name, and country_iso_code.

        Raises:
            DataForSEOError: If the API request fails.
        """
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}{self.ADS_SEARCH_LOCATIONS_ENDPOINT}",
                headers=headers,
            )

            if response.status_code != 200:
                raise DataForSEOError(
                    f"HTTP error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

            data = response.json()

            if data.get("status_code") != 20000:
                raise DataForSEOError(
                    f"API error: {data.get('status_message', 'Unknown error')}",
                    status_code=data.get("status_code"),
                )

            tasks = data.get("tasks", [])
            if not tasks:
                return []

            task = tasks[0]
            if task.get("status_code") != 20000:
                raise DataForSEOError(
                    f"Task error: {task.get('status_message', 'Unknown error')}",
                    status_code=task.get("status_code"),
                )

            locations = task.get("result", [])
            
            # Filter to only return country-level locations (not states/cities)
            countries = [
                loc for loc in locations
                if loc.get("location_type") == "Country"
            ]
            
            # Sort by location name
            countries.sort(key=lambda x: x.get("location_name", ""))
            
            return countries


# Singleton instance for dependency injection
def get_dataforseo_client() -> DataForSEOClient:
    """Get a DataForSEO client instance."""
    return DataForSEOClient()
