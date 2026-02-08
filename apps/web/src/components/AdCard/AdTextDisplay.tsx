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
  const hasKeyphrases = textContent.keyphrases && textContent.keyphrases.length > 0

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

      {hasKeyphrases && (
        <div className="keyphrases-container">
          <span className="keyphrases-label">Key phrases:</span>
          <div className="keyphrases-list">
            {textContent.keyphrases.map((phrase, index) => (
              <span key={index} className="keyphrase-tag">
                {phrase}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
