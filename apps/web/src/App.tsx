import { useState, useEffect } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

interface Location {
  location_code: number
  location_name: string
  country_iso_code: string
}

interface LocationsResponse {
  locations: Location[]
}

interface PreviewImage {
  url: string | null
  width: number | null
  height: number | null
}

interface AdTextContent {
  headline: string | null
  description: string | null
  raw_text: string | null
  error: string | null
}

interface AdItem {
  type: string
  rank_group: number | null
  rank_absolute: number | null
  advertiser_id: string | null
  creative_id: string | null
  title: string | null
  url: string | null
  verified: boolean | null
  format: string | null
  preview_image: PreviewImage | null
  first_shown: string | null
  last_shown: string | null
}

interface AdItemWithText extends AdItem {
  text_content: AdTextContent | null
}

interface DomainAdsResponse {
  domain: string
  ads_count: number
  ads: string[]
}

interface DomainAdsDetailedResponse {
  domain: string
  ads_count: number
  ads: AdItem[]
}

interface DomainAdsWithTextResponse {
  domain: string
  ads_count: number
  ads: AdItemWithText[]
}

function App() {
  const [domain, setDomain] = useState('')
  const [depth, setDepth] = useState(50)
  const [maxScrape, setMaxScrape] = useState(5)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [simpleResults, setSimpleResults] = useState<DomainAdsResponse | null>(null)
  const [detailedResults, setDetailedResults] = useState<DomainAdsDetailedResponse | null>(null)
  const [textResults, setTextResults] = useState<DomainAdsWithTextResponse | null>(null)
  const [viewMode, setViewMode] = useState<'simple' | 'detailed' | 'with-text'>('with-text')
  
  // Location/Country filter
  const [locations, setLocations] = useState<Location[]>([])
  const [selectedLocation, setSelectedLocation] = useState<number>(2840) // Default: United States
  const [locationsLoading, setLocationsLoading] = useState(true)

  // Fetch available locations on mount
  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/ads/locations`)
        if (response.ok) {
          const data: LocationsResponse = await response.json()
          setLocations(data.locations)
        }
      } catch (err) {
        console.error('Failed to load locations:', err)
      } finally {
        setLocationsLoading(false)
      }
    }
    fetchLocations()
  }, [])
  

  const fetchAds = async () => {
    if (!domain.trim()) {
      setError('Please enter a domain')
      return
    }

    setLoading(true)
    setError(null)
    setSimpleResults(null)
    setDetailedResults(null)
    setTextResults(null)

    try {
      let endpoint: string
      let queryParams = ''

      if (viewMode === 'simple') {
        endpoint = '/ads/domain'
      } else if (viewMode === 'detailed') {
        endpoint = '/ads/domain/detailed'
      } else {
        endpoint = '/ads/domain/with-text'
        queryParams = `?max_scrape=${maxScrape}`
      }

      const response = await fetch(`${API_BASE_URL}${endpoint}${queryParams}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          domain: domain.trim(),
          depth,
          location_code: selectedLocation,
          platform: 'google_search',
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error: ${response.status}`)
      }

      const data = await response.json()

      if (viewMode === 'simple') {
        setSimpleResults(data as DomainAdsResponse)
      } else if (viewMode === 'detailed') {
        setDetailedResults(data as DomainAdsDetailedResponse)
      } else {
        setTextResults(data as DomainAdsWithTextResponse)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchAds()
  }

  return (
    <div className="app-container">
      <header className="header">
        <h1>Google Ads Search</h1>
        <p className="subtitle">Find ads by domain using DataForSEO API</p>
      </header>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="form-row">
          <div className="input-group">
            <label htmlFor="domain">Domain</label>
            <input
              id="domain"
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="e.g., theliven.com"
              className="domain-input"
            />
          </div>

          <div className="input-group">
            <label htmlFor="country">Country</label>
            <select
              id="country"
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(Number(e.target.value))}
              className="country-select"
              disabled={locationsLoading}
            >
              {locationsLoading ? (
                <option>Loading...</option>
              ) : (
                locations.map((loc) => (
                  <option key={loc.location_code} value={loc.location_code}>
                    {loc.location_name} ({loc.country_iso_code})
                  </option>
                ))
              )}
            </select>
          </div>

          <div className="input-group input-group-small">
            <label htmlFor="depth">Results</label>
            <input
              id="depth"
              type="number"
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              min={1}
              max={120}
              className="depth-input"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="view-mode-toggle">
            <label>
              <input
                type="radio"
                name="viewMode"
                value="with-text"
                checked={viewMode === 'with-text'}
                onChange={() => setViewMode('with-text')}
              />
              With Text (scraped ad content)
            </label>
            <label>
              <input
                type="radio"
                name="viewMode"
                value="detailed"
                checked={viewMode === 'detailed'}
                onChange={() => setViewMode('detailed')}
              />
              Detailed (metadata + preview)
            </label>
            <label>
              <input
                type="radio"
                name="viewMode"
                value="simple"
                checked={viewMode === 'simple'}
                onChange={() => setViewMode('simple')}
              />
              Simple (text array)
            </label>
          </div>
        </div>

        {viewMode === 'with-text' && (
          <div className="form-row">
            <div className="input-group input-group-small">
              <label htmlFor="maxScrape">Max to scrape</label>
              <input
                id="maxScrape"
                type="number"
                value={maxScrape}
                onChange={(e) => setMaxScrape(Number(e.target.value))}
                min={1}
                max={20}
                className="depth-input"
              />
            </div>
            <p className="hint-text">
              Scraping is slow (~5-10s per ad). Limit results for faster response.
            </p>
          </div>
        )}

        <button type="submit" disabled={loading} className="search-button">
          {loading ? 'Searching...' : 'Search Ads'}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {simpleResults && (
        <div className="results-container">
          <div className="results-header">
            <h2>Results for: {simpleResults.domain}</h2>
            <span className="ads-count">{simpleResults.ads_count} ads found</span>
          </div>

          {simpleResults.ads.length === 0 ? (
            <p className="no-results">No ads found for this domain.</p>
          ) : (
            <ul className="ads-list">
              {simpleResults.ads.map((ad, index) => (
                <li key={index} className="ad-item-simple">
                  {ad}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {detailedResults && (
        <div className="results-container">
          <div className="results-header">
            <h2>Results for: {detailedResults.domain}</h2>
            <span className="ads-count">{detailedResults.ads_count} ads found</span>
          </div>

          {detailedResults.ads.length === 0 ? (
            <p className="no-results">No ads found for this domain.</p>
          ) : (
            <div className="ads-grid">
              {detailedResults.ads.map((ad, index) => (
                <div key={index} className="ad-card">
                  <div className="ad-card-header">
                    <span className="ad-title">{ad.title || 'Unknown Advertiser'}</span>
                    {ad.verified && <span className="verified-badge">✓ Verified</span>}
                  </div>

                  {/* Preview Image - Shows actual ad content */}
                  {ad.preview_image?.url && (
                    <div className="ad-preview-container">
                      <img
                        src={ad.preview_image.url}
                        alt={`Ad preview for ${ad.title || 'advertiser'}`}
                        className="ad-preview-image"
                        loading="lazy"
                      />
                    </div>
                  )}

                  <div className="ad-card-body">
                    <div className="ad-field">
                      <span className="field-label">Format:</span>
                      <span className="field-value">{ad.format || 'N/A'}</span>
                    </div>

                    <div className="ad-field">
                      <span className="field-label">Advertiser ID:</span>
                      <span className="field-value mono">{ad.advertiser_id || 'N/A'}</span>
                    </div>

                    <div className="ad-field">
                      <span className="field-label">Creative ID:</span>
                      <span className="field-value mono">{ad.creative_id || 'N/A'}</span>
                    </div>

                    {ad.first_shown && (
                      <div className="ad-field">
                        <span className="field-label">First Shown:</span>
                        <span className="field-value">{ad.first_shown}</span>
                      </div>
                    )}

                    {ad.last_shown && (
                      <div className="ad-field">
                        <span className="field-label">Last Shown:</span>
                        <span className="field-value">{ad.last_shown}</span>
                      </div>
                    )}

                    {ad.url && (
                      <a
                        href={ad.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ad-link"
                      >
                        View in Ads Transparency Center →
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {textResults && (
        <div className="results-container">
          <div className="results-header">
            <h2>Results for: {textResults.domain}</h2>
            <span className="ads-count">{textResults.ads_count} ads found</span>
          </div>

          {textResults.ads.length === 0 ? (
            <p className="no-results">No ads found for this domain.</p>
          ) : (
            <div className="ads-grid">
              {textResults.ads.map((ad, index) => (
                <div key={index} className="ad-card ad-card-with-text">
                  <div className="ad-card-header">
                    <span className="ad-title">{ad.title || 'Unknown Advertiser'}</span>
                    {ad.verified && <span className="verified-badge">✓ Verified</span>}
                  </div>

                  {/* Scraped Text Content */}
                  <div className="ad-text-content">
                    {ad.text_content?.error ? (
                      <div className="text-error">
                        <span className="error-icon">⚠️</span>
                        {ad.text_content.error}
                      </div>
                    ) : (
                      <>
                        {ad.text_content?.headline && (
                          <div className="text-headline">
                            {ad.text_content.headline}
                          </div>
                        )}
                        {ad.text_content?.description && (
                          <div className="text-description">
                            {ad.text_content.description}
                          </div>
                        )}
                        {ad.text_content?.raw_text && !ad.text_content?.headline && !ad.text_content?.description && (
                          <div className="text-raw">
                            <strong>Extracted Text:</strong>
                            <p>{ad.text_content.raw_text}</p>
                          </div>
                        )}
                        {!ad.text_content?.headline && !ad.text_content?.description && !ad.text_content?.raw_text && (
                          <div className="text-empty">No text content extracted</div>
                        )}
                      </>
                    )}
                  </div>

                  {/* Preview Image fallback */}
                  {ad.preview_image?.url && (
                    <details className="preview-details">
                      <summary>Show preview image</summary>
                      <div className="ad-preview-container">
                        <img
                          src={ad.preview_image.url}
                          alt={`Ad preview for ${ad.title || 'advertiser'}`}
                          className="ad-preview-image"
                          loading="lazy"
                        />
                      </div>
                    </details>
                  )}

                  <div className="ad-card-body">
                    <div className="ad-field">
                      <span className="field-label">Creative ID:</span>
                      <span className="field-value mono">{ad.creative_id || 'N/A'}</span>
                    </div>

                    {ad.first_shown && ad.last_shown && (
                      <div className="ad-field">
                        <span className="field-label">Active:</span>
                        <span className="field-value">
                          {ad.first_shown.split(' ')[0]} to {ad.last_shown.split(' ')[0]}
                        </span>
                      </div>
                    )}

                    {ad.url && (
                      <a
                        href={ad.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ad-link"
                      >
                        View in Transparency Center →
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
