"""API endpoints for Google Ads search functionality."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.ads import (
    AdItemWithText,
    AdTextContent,
    Cluster,
    ClusteringData,
    DomainAdsRequest,
    DomainAdsWithTextResponse,
    Location,
    LocationsResponse,
    PhraseInfo,
    PreviewImage,
)
from app.services.ad_scraper import AdTextScraper, get_ad_scraper
from app.services.dataforseo import (
    DataForSEOClient,
    DataForSEOError,
    get_dataforseo_client,
)
from app.services.keyword_extractor import KeywordExtractor, get_keyword_extractor
from app.services.phrase_clustering import (
    PhraseClusterer,
    PhraseInfo as ClusterPhraseInfo,
    get_phrase_clusterer,
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
    "/domain/with-text",
    response_model=DomainAdsWithTextResponse,
    summary="Get ads with extracted text content and keyphrase clusters",
    description="Retrieve Google Ads with text content extracted via OCR, keyphrases, and clustering.",
    responses={
        200: {"description": "Successfully retrieved ads with text and clusters"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "API or OCR error"},
    },
)
async def get_domain_ads_with_text(
    request: DomainAdsRequest,
    client: Annotated[DataForSEOClient, Depends(get_dataforseo_client)],
    scraper: Annotated[AdTextScraper, Depends(get_ad_scraper)],
    keyword_extractor: Annotated[KeywordExtractor, Depends(get_keyword_extractor)],
    clusterer: Annotated[PhraseClusterer, Depends(get_phrase_clusterer)],
    max_scrape: Annotated[
        int,
        Query(description="Max ads to extract text from (default: 5)", ge=1),
    ] = 5,
) -> DomainAdsWithTextResponse:
    """
    Fetch Google Ads with text extracted via OCR from preview images.

    This endpoint:
    1. Fetches ad metadata from DataForSEO (including preview image URLs)
    2. Downloads the preview images
    3. Extracts headline and description using color-based OCR
    4. Extracts keyphrases using YAKE
    5. Clusters keyphrases using sentence embeddings + HDBSCAN

    - **domain**: The domain URL to search
    - **location_code**: Geographic location code (default: 2840 for US)
    - **depth**: Maximum number of results to fetch from DataForSEO
    - **max_scrape**: Maximum number of ads to extract text from
    """
    try:
        # Get ads from DataForSEO
        items = await client.get_domain_ads(
            domain=request.domain,
            location_code=request.location_code,
            platform=request.platform,
            ad_format="text",
            depth=request.depth,
        )

        normalized_domain = DataForSEOClient._normalize_domain(request.domain)

        # Filter to ads_search type items with preview images
        ads_items = [
            item for item in items
            if item.get("type") == "ads_search" and item.get("preview_image")
        ]

        # Limit to max_scrape for performance
        items_to_scrape = ads_items[:max_scrape]

        # Extract text from preview images using OCR
        scraped_items = await scraper.scrape_multiple_ads(
            items_to_scrape,
            max_concurrent=5,
        )

        # Build response and collect phrases for clustering
        ads: list[AdItemWithText] = []
        all_phrase_infos: list[ClusterPhraseInfo] = []

        for item in scraped_items:
            # Parse preview_image
            preview_image_data = item.get("preview_image")
            preview_image = None
            if preview_image_data and isinstance(preview_image_data, dict):
                preview_image = PreviewImage(
                    url=preview_image_data.get("url"),
                    width=preview_image_data.get("width"),
                    height=preview_image_data.get("height"),
                )

            # Parse text_content and extract keyphrases
            text_content_data = item.get("text_content")
            text_content = None
            keyphrases: list[str] = []

            if text_content_data and isinstance(text_content_data, dict):
                headline = text_content_data.get("headline")
                description = text_content_data.get("description")
                raw_text = text_content_data.get("raw_text")

                # Extract keyphrases from the ad text
                keyphrases = keyword_extractor.extract_from_ad_text(
                    headline=headline,
                    description=description,
                    raw_text=raw_text,
                )

                text_content = AdTextContent(
                    headline=headline,
                    description=description,
                    raw_text=raw_text,
                    keyphrases=keyphrases,
                    error=text_content_data.get("error"),
                )

            # Collect phrase info for clustering
            ad_title = item.get("title")
            ad_url = item.get("url")
            creative_id = item.get("creative_id")

            for phrase in keyphrases:
                all_phrase_infos.append(
                    ClusterPhraseInfo(
                        phrase=phrase,
                        ad_title=ad_title,
                        ad_url=ad_url,
                        creative_id=creative_id,
                    )
                )

            ads.append(
                AdItemWithText(
                    type=item.get("type", "ads_search"),
                    rank_group=item.get("rank_group"),
                    rank_absolute=item.get("rank_absolute"),
                    advertiser_id=item.get("advertiser_id"),
                    creative_id=creative_id,
                    title=ad_title,
                    url=ad_url,
                    verified=item.get("verified"),
                    format=item.get("format"),
                    preview_image=preview_image,
                    first_shown=item.get("first_shown"),
                    last_shown=item.get("last_shown"),
                    text_content=text_content,
                )
            )

        # Cluster the keyphrases
        clustering_result = clusterer.cluster_phrases(all_phrase_infos)

        # Convert to response schema
        clusters = [
            Cluster(
                id=c.id,
                name=c.name,
                size=c.size,
                phrases=[
                    PhraseInfo(
                        phrase=p.phrase,
                        ad_title=p.ad_title,
                        ad_url=p.ad_url,
                        creative_id=p.creative_id,
                    )
                    for p in c.phrases
                ],
            )
            for c in clustering_result.clusters
        ]

        unclustered = [
            PhraseInfo(
                phrase=p.phrase,
                ad_title=p.ad_title,
                ad_url=p.ad_url,
                creative_id=p.creative_id,
            )
            for p in clustering_result.unclustered
        ]

        clustering_data = ClusteringData(
            clusters=clusters,
            unclustered=unclustered,
            total_phrases=clustering_result.total_phrases,
            error=clustering_result.error,
        )

        return DomainAdsWithTextResponse(
            domain=normalized_domain,
            ads_count=len(ads),
            ads=ads,
            clustering=clustering_data,
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
