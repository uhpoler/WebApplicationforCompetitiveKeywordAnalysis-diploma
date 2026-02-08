import type { AdsSearchResponse } from '../../types/ads'
import { AdCard } from '../AdCard'
import './AdResults.css'

interface AdResultsProps {
  results: AdsSearchResponse
}

export function AdResults({ results }: AdResultsProps) {
  return (
    <section className="results-container">
      <header className="results-header">
        <h2>Results for: {results.domain}</h2>
        <span className="ads-count">{results.ads_count} ads found</span>
      </header>

      {results.ads.length === 0 ? (
        <p className="no-results">No ads found for this domain.</p>
      ) : (
        <div className="ads-grid">
          {results.ads.map((ad, index) => (
            <AdCard key={ad.creative_id || index} ad={ad} />
          ))}
        </div>
      )}
    </section>
  )
}
