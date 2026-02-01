"""Pydantic schemas for ads-related endpoints."""

from pydantic import BaseModel, Field, field_validator


class DomainAdsRequest(BaseModel):
    """Request schema for fetching domain ads."""

    domain: str = Field(
        ...,
        description="Domain URL to search ads for (e.g., 'https://theliven.com/' or 'theliven.com')",
        min_length=1,
        examples=["https://theliven.com/", "example.com"],
    )
    location_code: int = Field(
        default=2840,
        description="Location code for the search (default: 2840 for United States)",
        ge=1,
    )
    platform: str = Field(
        default="google_search",
        description="Advertising platform to search",
    )
    depth: int = Field(
        default=100,
        description="Number of results to retrieve (max: 120)",
        ge=1,
        le=120,
    )

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Validate and clean the domain input."""
        v = v.strip()
        if not v:
            raise ValueError("Domain cannot be empty")
        return v

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """Validate platform value."""
        allowed_platforms = {
            "all",
            "google_play",
            "google_maps",
            "google_search",
            "google_shopping",
            "youtube",
        }
        if v.lower() not in allowed_platforms:
            raise ValueError(f"Platform must be one of: {', '.join(sorted(allowed_platforms))}")
        return v.lower()


class DomainAdsResponse(BaseModel):
    """Response schema for domain ads endpoint."""

    domain: str = Field(description="The normalized domain that was searched")
    ads_count: int = Field(description="Number of ads found")
    ads: list[str] = Field(description="List of ad text strings")


class PreviewImage(BaseModel):
    """Schema for ad preview image."""

    url: str | None = Field(default=None, description="URL to the preview image")
    width: int | None = Field(default=None, description="Image width in pixels")
    height: int | None = Field(default=None, description="Image height in pixels")


class AdItem(BaseModel):
    """Schema for a single ad item with full details."""

    type: str = Field(description="Type of the item (ads_search)")
    rank_group: int | None = Field(default=None, description="Rank within the group")
    rank_absolute: int | None = Field(default=None, description="Absolute rank in SERP")
    advertiser_id: str | None = Field(default=None, description="Advertiser ID")
    creative_id: str | None = Field(default=None, description="Creative/ad ID")
    title: str | None = Field(default=None, description="Advertiser name/title")
    url: str | None = Field(default=None, description="URL to the ad in transparency center")
    verified: bool | None = Field(default=None, description="Whether advertiser is verified")
    format: str | None = Field(default=None, description="Ad format (text, image, video)")
    preview_image: PreviewImage | None = Field(default=None, description="Preview image of the ad creative")
    first_shown: str | None = Field(default=None, description="When ad was first shown")
    last_shown: str | None = Field(default=None, description="When ad was last shown")


class DomainAdsDetailedResponse(BaseModel):
    """Response schema for domain ads with full item details."""

    domain: str = Field(description="The normalized domain that was searched")
    ads_count: int = Field(description="Number of ads found")
    ads: list[AdItem] = Field(description="List of ad items with full details")


class AdTextContent(BaseModel):
    """Schema for scraped ad text content (extracted via color-based OCR)."""

    headline: str | None = Field(default=None, description="Ad headline (blue text)")
    description: str | None = Field(default=None, description="Ad description (gray text)")
    raw_text: str | None = Field(default=None, description="Raw extracted text from the ad")
    error: str | None = Field(default=None, description="Error message if extraction failed")


class AdItemWithText(BaseModel):
    """Schema for ad item with scraped text content."""

    type: str = Field(description="Type of the item (ads_search)")
    rank_group: int | None = Field(default=None, description="Rank within the group")
    rank_absolute: int | None = Field(default=None, description="Absolute rank in SERP")
    advertiser_id: str | None = Field(default=None, description="Advertiser ID")
    creative_id: str | None = Field(default=None, description="Creative/ad ID")
    title: str | None = Field(default=None, description="Advertiser name/title")
    url: str | None = Field(default=None, description="URL to the ad in transparency center")
    verified: bool | None = Field(default=None, description="Whether advertiser is verified")
    format: str | None = Field(default=None, description="Ad format (text, image, video)")
    preview_image: PreviewImage | None = Field(default=None, description="Preview image of the ad creative")
    first_shown: str | None = Field(default=None, description="When ad was first shown")
    last_shown: str | None = Field(default=None, description="When ad was last shown")
    text_content: AdTextContent | None = Field(default=None, description="Scraped text content from the ad")


class DomainAdsWithTextResponse(BaseModel):
    """Response schema for domain ads with scraped text content."""

    domain: str = Field(description="The normalized domain that was searched")
    ads_count: int = Field(description="Number of ads found")
    ads: list[AdItemWithText] = Field(description="List of ad items with text content")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(description="Error message")
    status_code: int | None = Field(default=None, description="DataForSEO API status code if applicable")


class Location(BaseModel):
    """Schema for a location/country."""

    location_code: int = Field(description="Unique location code for API calls")
    location_name: str = Field(description="Human-readable location name")
    country_iso_code: str = Field(description="ISO country code (e.g., 'US', 'GB')")


class LocationsResponse(BaseModel):
    """Response schema for locations endpoint."""

    locations: list[Location] = Field(description="List of available locations/countries")
