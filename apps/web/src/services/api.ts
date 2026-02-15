import type { AdsSearchParams, AdsSearchResponse, LanguagesResponse, LocationsResponse } from '../types/ads'

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
 * Search for ads by domain with text extraction.
 */
export async function searchAds(params: AdsSearchParams): Promise<AdsSearchResponse> {
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
