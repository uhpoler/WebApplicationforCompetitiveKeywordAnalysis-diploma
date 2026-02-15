import { useState } from 'react'
import type { Location, Language } from '../../types/ads'
import { DomainTagInput } from '../DomainTagInput'
import './SearchForm.css'

interface SearchFormProps {
  domains: string[]
  depth: number
  selectedLocation: number
  selectedLanguage: string | null
  locations: Location[]
  languages: Language[]
  locationsLoading: boolean
  languagesLoading: boolean
  isLoading: boolean
  onDomainsChange: (domains: string[]) => void
  onDepthChange: (value: number) => void
  onLocationChange: (value: number) => void
  onLanguageChange: (value: string | null) => void
  onSubmit: () => void
}

export function SearchForm({
  domains,
  depth,
  selectedLocation,
  selectedLanguage,
  locations,
  languages,
  locationsLoading,
  languagesLoading,
  isLoading,
  onDomainsChange,
  onDepthChange,
  onLocationChange,
  onLanguageChange,
  onSubmit,
}: SearchFormProps) {
  // Local state for the input value to fix UX issue with number inputs
  const [depthInput, setDepthInput] = useState(String(depth))

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit()
  }

  const handleDepthChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value

    // Allow empty input for better UX while typing
    setDepthInput(value)

    // Only update the actual value if it's a valid number
    if (value !== '') {
      const numValue = parseInt(value, 10)
      if (!isNaN(numValue) && numValue >= 1 && numValue <= 120) {
        onDepthChange(numValue)
      }
    }
  }

  const handleDepthBlur = () => {
    // On blur, ensure we have a valid value
    const numValue = parseInt(depthInput, 10)
    if (isNaN(numValue) || numValue < 1) {
      setDepthInput('1')
      onDepthChange(1)
    } else if (numValue > 120) {
      setDepthInput('120')
      onDepthChange(120)
    } else {
      setDepthInput(String(numValue))
      onDepthChange(numValue)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="search-form">
      <div className="form-row form-row-domains">
        <div className="input-group input-group-domains">
          <label htmlFor="domains">Domains</label>
          <DomainTagInput
            domains={domains}
            onChange={onDomainsChange}
            placeholder="Type domain and press Enter..."
            disabled={isLoading}
          />
        </div>
      </div>

      <div className="form-row">
        <div className="input-group">
          <label htmlFor="country">Country *</label>
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

        <div className="input-group">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            value={selectedLanguage || ''}
            onChange={(e) => onLanguageChange(e.target.value || null)}
            className="language-select"
            disabled={languagesLoading}
          >
            <option value="">All languages</option>
            {!languagesLoading &&
              languages.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
          </select>
        </div>

        <div className="input-group input-group-small">
          <label htmlFor="depth">Ads per domain</label>
          <input
            id="depth"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            value={depthInput}
            onChange={handleDepthChange}
            onBlur={handleDepthBlur}
            className="depth-input"
            placeholder="1-120"
          />
        </div>
      </div>

      <button type="submit" disabled={isLoading || domains.length === 0} className="search-button">
        {isLoading ? 'Searching...' : `Search Ads${domains.length > 0 ? ` (${domains.length} domain${domains.length > 1 ? 's' : ''})` : ''}`}
      </button>
    </form>
  )
}
