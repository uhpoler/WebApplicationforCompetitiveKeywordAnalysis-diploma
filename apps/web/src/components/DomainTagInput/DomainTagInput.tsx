import { useState, useRef, type KeyboardEvent } from 'react'
import './DomainTagInput.css'

interface DomainTagInputProps {
  domains: string[]
  onChange: (domains: string[]) => void
  placeholder?: string
  disabled?: boolean
}

/**
 * Tag-style input for entering multiple domains.
 * Domains are added when pressing Enter or comma.
 * Tags can be removed by clicking the X button.
 */
export function DomainTagInput({
  domains,
  onChange,
  placeholder = 'e.g., example.com',
  disabled = false,
}: DomainTagInputProps) {
  const [inputValue, setInputValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const normalizeDomain = (value: string): string => {
    let domain = value.trim().toLowerCase()
    // Remove protocol if present
    domain = domain.replace(/^https?:\/\//, '')
    // Remove trailing slash
    domain = domain.replace(/\/$/, '')
    // Remove www. prefix for consistency
    domain = domain.replace(/^www\./, '')
    return domain
  }

  const addDomain = (value: string) => {
    const normalized = normalizeDomain(value)
    if (normalized && !domains.includes(normalized)) {
      onChange([...domains, normalized])
    }
    setInputValue('')
  }

  const removeDomain = (domainToRemove: string) => {
    onChange(domains.filter((d) => d !== domainToRemove))
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      if (inputValue.trim()) {
        addDomain(inputValue)
      }
    } else if (e.key === 'Backspace' && inputValue === '' && domains.length > 0) {
      // Remove last domain when backspace is pressed on empty input
      removeDomain(domains[domains.length - 1])
    }
  }

  const handleBlur = () => {
    // Add domain on blur if there's text in the input
    if (inputValue.trim()) {
      addDomain(inputValue)
    }
  }

  const handleContainerClick = () => {
    inputRef.current?.focus()
  }

  return (
    <div
      className={`domain-tag-input-container ${disabled ? 'disabled' : ''}`}
      onClick={handleContainerClick}
    >
      <div className="domain-tags">
        {domains.map((domain) => (
          <span key={domain} className="domain-tag">
            {domain}
            {!disabled && (
              <button
                type="button"
                className="domain-tag-remove"
                onClick={(e) => {
                  e.stopPropagation()
                  removeDomain(domain)
                }}
                aria-label={`Remove ${domain}`}
              >
                ×
              </button>
            )}
          </span>
        ))}
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder={domains.length === 0 ? placeholder : ''}
          className="domain-tag-input"
          disabled={disabled}
        />
      </div>
    </div>
  )
}
