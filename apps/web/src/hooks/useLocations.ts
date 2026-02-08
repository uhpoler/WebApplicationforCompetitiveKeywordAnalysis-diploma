import { useState, useEffect } from 'react'
import type { Location } from '../types/ads'
import { fetchLocations } from '../services/api'

interface UseLocationsResult {
  locations: Location[]
  isLoading: boolean
  error: string | null
}

/**
 * Hook to fetch and manage available locations.
 */
export function useLocations(): UseLocationsResult {
  const [locations, setLocations] = useState<Location[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadLocations = async () => {
      try {
        const data = await fetchLocations()
        setLocations(data.locations)
      } catch (err) {
        console.error('Failed to load locations:', err)
        setError(err instanceof Error ? err.message : 'Failed to load locations')
      } finally {
        setIsLoading(false)
      }
    }

    loadLocations()
  }, [])

  return { locations, isLoading, error }
}
