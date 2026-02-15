import type {
  AdsSearchParams,
  CombinedAdsSearchResponse,
  LanguagesResponse,
  LocationsResponse,
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
 * Search for ads across multiple domains with unified clustering.
 * 
 * All domains are processed together on the backend, and ALL keyphrases
 * from ALL domains are clustered as one unit.
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

  // Build query params
  const queryParams = new URLSearchParams()
  if (language) {
    queryParams.set('language', language)
  }
  const queryString = queryParams.toString()
  const url = `${API_BASE_URL}/ads/domains/with-text${queryString ? `?${queryString}` : ''}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      domains: domains.map((d) => d.trim()),
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
