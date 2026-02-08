import type { AdItem } from '../../types/ads'
import { AdTextDisplay } from './AdTextDisplay'
import './AdCard.css'

interface AdCardProps {
  ad: AdItem
}

export function AdCard({ ad }: AdCardProps) {
  const formatDate = (dateStr: string) => dateStr.split(' ')[0]

  return (
    <article className="ad-card">
      <header className="ad-card-header">
        <span className="ad-title">{ad.title || 'Unknown Advertiser'}</span>
        {ad.verified && <span className="verified-badge">Verified</span>}
      </header>

      <AdTextDisplay textContent={ad.text_content} />

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
              {formatDate(ad.first_shown)} to {formatDate(ad.last_shown)}
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
            View in Transparency Center
          </a>
        )}
      </div>
    </article>
  )
}
