import { useState, useEffect } from 'react'
import type { Language } from '../types/ads'
import { fetchLanguages } from '../services/api'

interface UseLanguagesResult {
  languages: Language[]
  isLoading: boolean
  error: string | null
}

/**
 * Hook to fetch and manage available languages.
 */
export function useLanguages(): UseLanguagesResult {
  const [languages, setLanguages] = useState<Language[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadLanguages = async () => {
      try {
        const data = await fetchLanguages()
        setLanguages(data.languages)
      } catch (err) {
        console.error('Failed to load languages:', err)
        setError(err instanceof Error ? err.message : 'Failed to load languages')
      } finally {
        setIsLoading(false)
      }
    }

    loadLanguages()
  }, [])

  return { languages, isLoading, error }
}
