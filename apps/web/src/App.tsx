import { useState } from 'react'
import { SearchForm, AdResults, ErrorMessage } from './components'
import { useLocations } from './hooks/useLocations'
import { useAdsSearch } from './hooks/useAdsSearch'
import './App.css'

const DEFAULT_LOCATION = 2840 // United States
const DEFAULT_DEPTH = 50
const DEFAULT_MAX_SCRAPE = 5

function App() {
  // Form state
  const [domain, setDomain] = useState('')
  const [depth, setDepth] = useState(DEFAULT_DEPTH)
  const [maxScrape, setMaxScrape] = useState(DEFAULT_MAX_SCRAPE)
  const [selectedLocation, setSelectedLocation] = useState(DEFAULT_LOCATION)

  // Data hooks
  const { locations, isLoading: locationsLoading } = useLocations()
  const { results, isLoading, error, search } = useAdsSearch()

  const handleSearch = () => {
    search({
      domain,
      depth,
      locationCode: selectedLocation,
      maxScrape,
    })
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>Google Ads Search</h1>
        <p className="subtitle">Find ads by domain using DataForSEO API</p>
      </header>

      <SearchForm
        domain={domain}
        depth={depth}
        maxScrape={maxScrape}
        selectedLocation={selectedLocation}
        locations={locations}
        locationsLoading={locationsLoading}
        isLoading={isLoading}
        onDomainChange={setDomain}
        onDepthChange={setDepth}
        onMaxScrapeChange={setMaxScrape}
        onLocationChange={setSelectedLocation}
        onSubmit={handleSearch}
      />

      {error && <ErrorMessage message={error} />}

      {results && <AdResults results={results} />}
    </div>
  )
}

export default App
