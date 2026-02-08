"""API endpoints for Google Ads search functionality."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.ads import (
    AdItem,
    AdItemWithText,
    AdTextContent,
    DomainAdsDetailedResponse,
    DomainAdsRequest,
    DomainAdsResponse,
    DomainAdsWithTextResponse,
    Location,
    LocationsResponse,
    PreviewImage,
)
from app.services.ad_scraper import AdTextScraper, get_ad_scraper
from app.services.dataforseo import (
    DataForSEOClient,
    DataForSEOError,
    get_dataforseo_client,
)

router = APIRouter(prefix="/ads", tags=["ads"])


@router.get(
    "/locations",
    response_model=LocationsResponse,
    summary="Get available locations/countries",
    description="Retrieve list of available countries for filtering ads.",
    responses={
        200: {"description": "Successfully retrieved locations"},
        500: {"description": "DataForSEO API error"},
    },
)
async def get_locations(
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
) -> LocationsResponse:
    """
    Get available locations (countries) for filtering Google Ads.

    Returns a list of countries with their location codes that can be used
    in the location_code parameter when searching for ads.
    """
    try:
        locations_data = await client.get_available_locations()

        locations = [
            Location(
                location_code=loc.get("location_code", 0),
                location_name=loc.get("location_name", "Unknown"),
                country_iso_code=loc.get("country_iso_code", ""),
            )
            for loc in locations_data
            if loc.get("location_code") is not None and loc.get("location_name") is not None
        ]

        return LocationsResponse(locations=locations)

    except DataForSEOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DataForSEO API error: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.post(
    "/domain",
    response_model=DomainAdsResponse,
    summary="Get ad texts for a domain",
    description="Retrieve Google Ads text content for a specific domain. "
    "Returns an array of formatted ad text strings.",
    responses={
        200: {"description": "Successfully retrieved ads"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "DataForSEO API error or server error"},
    },
)
async def get_domain_ads(
    request: DomainAdsRequest,
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
) -> DomainAdsResponse:
    """
    Fetch Google Ads for a specific domain.

    This endpoint queries the DataForSEO Google Ads Search API to find
    text advertisements associated with the provided domain.

    - **domain**: The domain URL (e.g., "https://theliven.com/" or "theliven.com")
    - **location_code**: Geographic location code (default: 2840 for United States)
    - **platform**: Ad platform filter (default: "google_search")
    - **depth**: Maximum number of results (default: 100, max: 120)

    Returns a list of formatted ad text strings containing advertiser info,
    creative IDs, URLs, and activity dates.
    """
    try:
        ad_texts = await client.get_domain_ad_texts(
            domain=request.domain,
            location_code=request.location_code,
            platform=request.platform,
            depth=request.depth,
        )

        normalized_domain = DataForSEOClient._normalize_domain(request.domain)

        return DomainAdsResponse(
            domain=normalized_domain,
            ads_count=len(ad_texts),
            ads=ad_texts,
        )

    except DataForSEOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DataForSEO API error: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.post(
    "/domain/detailed",
    response_model=DomainAdsDetailedResponse,
    summary="Get detailed ad data for a domain",
    description="Retrieve full Google Ads data for a domain including all metadata.",
    responses={
        200: {"description": "Successfully retrieved detailed ads"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "DataForSEO API error or server error"},
    },
)
async def get_domain_ads_detailed(
    request: DomainAdsRequest,
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
) -> DomainAdsDetailedResponse:
    """
    Fetch detailed Google Ads data for a specific domain.

    This endpoint returns the full ad item data including all metadata
    from the DataForSEO API.
    """
    try:
        items = await client.get_domain_ads(
            domain=request.domain,
            location_code=request.location_code,
            platform=request.platform,
            ad_format="text",  # Only get text format ads
            depth=request.depth,
        )

        normalized_domain = DataForSEOClient._normalize_domain(request.domain)

        ads = []
        for item in items:
            if item.get("type") != "ads_search":
                continue

            # Parse preview_image if available
            preview_image_data = item.get("preview_image")
            preview_image = None
            if preview_image_data and isinstance(preview_image_data, dict):
                preview_image = PreviewImage(
                    url=preview_image_data.get("url"),
                    width=preview_image_data.get("width"),
                    height=preview_image_data.get("height"),
                )

            ads.append(
                AdItem(
                    type=item.get("type", "ads_search"),
                    rank_group=item.get("rank_group"),
                    rank_absolute=item.get("rank_absolute"),
                    advertiser_id=item.get("advertiser_id"),
                    creative_id=item.get("creative_id"),
                    title=item.get("title"),
                    url=item.get("url"),
                    verified=item.get("verified"),
                    format=item.get("format"),
                    preview_image=preview_image,
                    first_shown=item.get("first_shown"),
                    last_shown=item.get("last_shown"),
                )
            )

        return DomainAdsDetailedResponse(
            domain=normalized_domain,
            ads_count=len(ads),
            ads=ads,
        )

    except DataForSEOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DataForSEO API error: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.get(
    "/domain/{domain}",
    response_model=DomainAdsResponse,
    summary="Get ad texts for a domain (GET)",
    description="Simple GET endpoint to retrieve Google Ads for a domain.",
    responses={
        200: {"description": "Successfully retrieved ads"},
        500: {"description": "DataForSEO API error or server error"},
    },
)
async def get_domain_ads_simple(
    domain: str,
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
    location_code: Annotated[
        int,
        Query(description="Location code (default: 2840 for US)", ge=1),
    ] = 2840,
    depth: Annotated[
        int,
        Query(description="Max results (default: 100)", ge=1, le=120),
    ] = 100,
) -> DomainAdsResponse:
    """
    Simple GET endpoint to fetch Google Ads for a domain.

    Example: GET /api/ads/domain/theliven.com?depth=50
    """
    try:
        ad_texts = await client.get_domain_ad_texts(
            domain=domain,
            location_code=location_code,
            platform="google_search",
            depth=depth,
        )

        normalized_domain = DataForSEOClient._normalize_domain(domain)

        return DomainAdsResponse(
            domain=normalized_domain,
            ads_count=len(ad_texts),
            ads=ad_texts,
        )

    except DataForSEOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DataForSEO API error: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        ) from e


@router.post(
    "/domain/with-text",
    response_model=DomainAdsWithTextResponse,
    summary="Get ads with scraped text content",
    description="Retrieve Google Ads with actual text content scraped from Google Ads Transparency Center. "
    "This endpoint is slower as it scrapes each ad page individually.",
    responses={
        200: {"description": "Successfully retrieved ads with text"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "API or scraping error"},
    },
)
async def get_domain_ads_with_text(
    request: DomainAdsRequest,
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
    scraper: Annotated[AdTextScraper, Depends(get_ad_scraper)],
    max_scrape: Annotated[
        int,
        Query(description="Max ads to scrape text from (default: 5)", ge=1),
    ] = 5,
) -> DomainAdsWithTextResponse:
    """
    Fetch Google Ads with text extracted via OCR from preview images.

    This endpoint:
    1. Fetches ad metadata from DataForSEO (including preview image URLs)
    2. Downloads the preview images
    3. Extracts text from images using OCR (Tesseract)

    - **domain**: The domain URL to search
    - **max_scrape**: Maximum number of ads to extract text from (default: 5, max: 20)
    """
    try:
        # First, get ads from DataForSEO (all formats to get preview images)
        items = await client.get_domain_ads(
            domain=request.domain,
            location_code=request.location_code,
            platform=request.platform,
            ad_format="text",  # Only get text format ads
            depth=request.depth,
        )

        normalized_domain = DataForSEOClient._normalize_domain(request.domain)

        # Filter to only ads_search type items with preview images
        ads_items = [
            item for item in items
            if item.get("type") == "ads_search" and item.get("preview_image")
        ]

        # Limit to max_scrape for performance
        items_to_scrape = ads_items[:max_scrape]

        # Extract text from preview images using OCR
        scraped_items = await scraper.scrape_multiple_ads(
            items_to_scrape,
            max_concurrent=5,  # OCR is fast, can run more concurrently
        )

        # Build response
        ads = []
        for item in scraped_items:
            # Parse preview_image if available
            preview_image_data = item.get("preview_image")
            preview_image = None
            if preview_image_data and isinstance(preview_image_data, dict):
                preview_image = PreviewImage(
                    url=preview_image_data.get("url"),
                    width=preview_image_data.get("width"),
                    height=preview_image_data.get("height"),
                )

            # Parse text_content if available
            text_content_data = item.get("text_content")
            text_content = None
            if text_content_data and isinstance(text_content_data, dict):
                text_content = AdTextContent(
                    headline=text_content_data.get("headline"),
                    description=text_content_data.get("description"),
                    # display_url=text_content_data.get("display_url"),
                    # sitelinks=text_content_data.get("sitelinks", []),
                    raw_text=text_content_data.get("raw_text"),
                    error=text_content_data.get("error"),
                )

            ads.append(
                AdItemWithText(
                    type=item.get("type", "ads_search"),
                    rank_group=item.get("rank_group"),
                    rank_absolute=item.get("rank_absolute"),
                    advertiser_id=item.get("advertiser_id"),
                    creative_id=item.get("creative_id"),
                    title=item.get("title"),
                    url=item.get("url"),
                    verified=item.get("verified"),
                    format=item.get("format"),
                    preview_image=preview_image,
                    first_shown=item.get("first_shown"),
                    last_shown=item.get("last_shown"),
                    text_content=text_content,
                )
            )

        return DomainAdsWithTextResponse(
            domain=normalized_domain,
            ads_count=len(ads),
            ads=ads,
        )

    except DataForSEOError as e:
        raise HTTPException(
            status_code=500,
            detail=f"DataForSEO API error: {e.message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}",
        ) from e
