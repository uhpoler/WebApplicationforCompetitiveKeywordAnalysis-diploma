import { useState, useCallback } from 'react'
import type { AdsSearchParams, CombinedAdsSearchResponse } from '../types/ads'
import { searchAds } from '../services/api'

interface UseAdsSearchResult {
  results: CombinedAdsSearchResponse | null
  isLoading: boolean
  error: string | null
  search: (params: AdsSearchParams) => Promise<void>
  clearResults: () => void
}

/**
 * Hook to manage ads search state and operations.
 * Supports searching multiple domains in parallel.
 */
export function useAdsSearch(): UseAdsSearchResult {
  const [results, setResults] = useState<CombinedAdsSearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (params: AdsSearchParams) => {
    if (params.domains.length === 0) {
      setError('Please enter at least one domain')
      return
    }

    setIsLoading(true)
    setError(null)
    setResults(null)

    try {
      const data = await searchAds(params)
      setResults(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const clearResults = useCallback(() => {
    setResults(null)
    setError(null)
  }, [])

  return { results, isLoading, error, search, clearResults }
}
