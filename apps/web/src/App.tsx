import { useState } from 'react'
import { SearchForm, AdResults, ErrorMessage } from './components'
import { useLocations } from './hooks/useLocations'
import { useLanguages } from './hooks/useLanguages'
import { useAdsSearch } from './hooks/useAdsSearch'
import './App.css'

const DEFAULT_LOCATION = 2840 // United States
const DEFAULT_DEPTH = 10

function App() {
  // Form state
  const [domains, setDomains] = useState<string[]>([])
  const [depth, setDepth] = useState(DEFAULT_DEPTH)
  const [selectedLocation, setSelectedLocation] = useState(DEFAULT_LOCATION)
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null)

  // Data hooks
  const { locations, isLoading: locationsLoading } = useLocations()
  const { languages, isLoading: languagesLoading } = useLanguages()
  const { results, isLoading, error, search } = useAdsSearch()

  const handleSearch = () => {
    search({
      domains,
      depth,
      locationCode: selectedLocation,
      language: selectedLanguage,
    })
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>Google Ads Search</h1>
        <p className="subtitle">Find ads by domain using DataForSEO API</p>
      </header>

      <SearchForm
        domains={domains}
        depth={depth}
        selectedLocation={selectedLocation}
        selectedLanguage={selectedLanguage}
        locations={locations}
        languages={languages}
        locationsLoading={locationsLoading}
        languagesLoading={languagesLoading}
        isLoading={isLoading}
        onDomainsChange={setDomains}
        onDepthChange={setDepth}
        onLocationChange={setSelectedLocation}
        onLanguageChange={setSelectedLanguage}
        onSubmit={handleSearch}
      />

      {error && <ErrorMessage message={error} />}

      {results && <AdResults results={results} />}
    </div>
  )
}

export default App
