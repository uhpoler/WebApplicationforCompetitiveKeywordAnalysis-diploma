import type { Location } from '../../types/ads'
import './SearchForm.css'

interface SearchFormProps {
  domain: string
  depth: number
  maxScrape: number
  selectedLocation: number
  locations: Location[]
  locationsLoading: boolean
  isLoading: boolean
  onDomainChange: (value: string) => void
  onDepthChange: (value: number) => void
  onMaxScrapeChange: (value: number) => void
  onLocationChange: (value: number) => void
  onSubmit: () => void
}

export function SearchForm({
  domain,
  depth,
  maxScrape,
  selectedLocation,
  locations,
  locationsLoading,
  isLoading,
  onDomainChange,
  onDepthChange,
  onMaxScrapeChange,
  onLocationChange,
  onSubmit,
}: SearchFormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-row">
        <div className="input-group">
          <label htmlFor="domain">Domain</label>
          <input
            id="domain"
            type="text"
            value={domain}
            onChange={(e) => onDomainChange(e.target.value)}
            placeholder="e.g., theliven.com"
            className="domain-input"
          />
        </div>

        <div className="input-group">
          <label htmlFor="country">Country</label>
          <select
            id="country"
            value={selectedLocation}
            onChange={(e) => onLocationChange(Number(e.target.value))}
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
            onChange={(e) => onDepthChange(Number(e.target.value))}
            min={1}
            max={120}
            className="depth-input"
          />
        </div>

        <div className="input-group input-group-small">
          <label htmlFor="maxScrape">Max OCR</label>
          <input
            id="maxScrape"
            type="number"
            value={maxScrape}
            onChange={(e) => onMaxScrapeChange(Number(e.target.value))}
            min={1}
            className="depth-input"
          />
        </div>
      </div>

      <button type="submit" disabled={isLoading} className="search-button">
        {isLoading ? 'Searching...' : 'Search Ads'}
      </button>
    </form>
  )
}
