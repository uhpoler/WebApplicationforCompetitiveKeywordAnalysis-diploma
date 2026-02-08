import type { AdTextContent } from '../../types/ads'

interface AdTextDisplayProps {
  textContent: AdTextContent | null
}

export function AdTextDisplay({ textContent }: AdTextDisplayProps) {
  if (!textContent) {
    return (
      <div className="ad-text-content">
        <div className="text-empty">No text content available</div>
      </div>
    )
  }

  if (textContent.error) {
    return (
      <div className="ad-text-content">
        <div className="text-error">
          <span className="error-icon">!</span>
          {textContent.error}
        </div>
      </div>
    )
  }

  const hasStructuredContent = textContent.headline || textContent.description
  const hasRawText = textContent.raw_text
  const hasNoContent = !hasStructuredContent && !hasRawText

  return (
    <div className="ad-text-content">
      {textContent.headline && (
        <div className="text-headline">{textContent.headline}</div>
      )}

      {textContent.description && (
        <div className="text-description">{textContent.description}</div>
      )}

      {!hasStructuredContent && hasRawText && (
        <div className="text-raw">
          <strong>Extracted Text:</strong>
          <p>{textContent.raw_text}</p>
        </div>
      )}

      {hasNoContent && (
        <div className="text-empty">No text content extracted</div>
      )}
    </div>
  )
}
