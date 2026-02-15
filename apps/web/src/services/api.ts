import type {
  AdsSearchParams,
  AdsSearchResponse,
  CombinedAdsSearchResponse,
  LanguagesResponse,
  LocationsResponse,
  SingleDomainSearchParams,
} from '../types/ads'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/** Custom error class for API errors */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Fetch available locations/countries for filtering ads.
 */
export async function fetchLocations(): Promise<LocationsResponse> {
  const response = await fetch(`${API_BASE_URL}/ads/locations`)

  if (!response.ok) {
    throw new ApiError(`Failed to load locations: ${response.status}`, response.status)
  }

  return response.json()
}

/**
 * Fetch available languages for filtering ads.
 */
export async function fetchLanguages(): Promise<LanguagesResponse> {
  const response = await fetch(`${API_BASE_URL}/ads/languages`)

  if (!response.ok) {
    throw new ApiError(`Failed to load languages: ${response.status}`, response.status)
  }

  return response.json()
}

/**
 * Search for ads by a single domain with text extraction.
 */
export async function searchSingleDomain(params: SingleDomainSearchParams): Promise<AdsSearchResponse> {
  const { domain, depth, locationCode, language } = params

  // Build query params
  const queryParams = new URLSearchParams()
  if (language) {
    queryParams.set('language', language)
  }
  const queryString = queryParams.toString()
  const url = `${API_BASE_URL}/ads/domain/with-text${queryString ? `?${queryString}` : ''}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      domain: domain.trim(),
      depth,
      location_code: locationCode,
      platform: 'google_search',
    }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new ApiError(
      errorData.detail || `HTTP error: ${response.status}`,
      response.status
    )
  }

  return response.json()
}

/**
 * Search for ads across multiple domains in parallel.
 * Results are combined: ads are merged, and clustering is performed
 * on the combined set of keyphrases.
 */
export async function searchAds(params: AdsSearchParams): Promise<CombinedAdsSearchResponse> {
  const { domains, depth, locationCode, language } = params

  if (domains.length === 0) {
    return {
      domains: [],
      ads_count: 0,
      ads: [],
      clustering: null,
    }
  }

  // Search all domains in parallel
  const searchPromises = domains.map((domain) =>
    searchSingleDomain({ domain, depth, locationCode, language })
      .catch((error) => {
        // Return a partial result with error info instead of failing entirely
        console.error(`Failed to search domain ${domain}:`, error)
        return null
      })
  )

  const results = await Promise.all(searchPromises)

  // Filter out failed requests and combine results
  const successfulResults = results.filter((r): r is AdsSearchResponse => r !== null)

  if (successfulResults.length === 0) {
    throw new ApiError('All domain searches failed')
  }

  // Combine ads from all domains
  const allAds = successfulResults.flatMap((r) => r.ads)

  // Combine clustering data - merge all phrases and re-cluster on client
  // For simplicity, we'll combine clusters and unclustered from all results
  const combinedClustering = combineClusteringData(successfulResults)

  return {
    domains: successfulResults.map((r) => r.domain),
    ads_count: allAds.length,
    ads: allAds,
    clustering: combinedClustering,
  }
}

/**
 * Combine clustering data from multiple search results.
 * Since the backend clusters per-domain, we need to merge them client-side.
 * This creates a simple combined view - for better clustering across domains,
 * we rely on the backend to re-cluster all phrases together.
 */
function combineClusteringData(
  results: AdsSearchResponse[]
): CombinedAdsSearchResponse['clustering'] {
  const allClusters: CombinedAdsSearchResponse['clustering'] = {
    clusters: [],
    unclustered: [],
    total_phrases: 0,
    error: null,
  }

  let clusterIdOffset = 0

  for (const result of results) {
    if (!result.clustering) continue

    // Add clusters with adjusted IDs to avoid conflicts
    for (const cluster of result.clustering.clusters) {
      allClusters.clusters.push({
        ...cluster,
        id: cluster.id + clusterIdOffset,
      })
    }
    clusterIdOffset += result.clustering.clusters.length

    // Add unclustered phrases
    allClusters.unclustered.push(...result.clustering.unclustered)
    allClusters.total_phrases += result.clustering.total_phrases
  }

  // Sort combined clusters by size
  allClusters.clusters.sort((a, b) => b.size - a.size)

  // Re-assign sequential IDs
  allClusters.clusters.forEach((cluster, idx) => {
    cluster.id = idx
  })

  return allClusters
}
