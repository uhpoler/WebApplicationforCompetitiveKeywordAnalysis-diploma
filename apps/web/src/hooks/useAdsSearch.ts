import { useState, useCallback } from 'react'
import type { AdsSearchParams, AdsSearchResponse } from '../types/ads'
import { searchAds } from '../services/api'

interface UseAdsSearchResult {
  results: AdsSearchResponse | null
  isLoading: boolean
  error: string | null
  search: (params: AdsSearchParams) => Promise<void>
  clearResults: () => void
}

/**
 * Hook to manage ads search state and operations.
 */
export function useAdsSearch(): UseAdsSearchResult {
  const [results, setResults] = useState<AdsSearchResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const search = useCallback(async (params: AdsSearchParams) => {
    if (!params.domain.trim()) {
      setError('Please enter a domain')
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
