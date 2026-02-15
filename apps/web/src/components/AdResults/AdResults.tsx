import type { CombinedAdsSearchResponse } from '../../types/ads'
import { AdCard } from '../AdCard'
import { Tabs } from '../Tabs'
import { ClusterView } from '../ClusterView'
import './AdResults.css'

interface AdResultsProps {
  results: CombinedAdsSearchResponse
}

export function AdResults({ results }: AdResultsProps) {
  const cardsContent = (
    <>
      {results.ads.length === 0 ? (
        <p className="no-results">No ads found for the specified domain(s).</p>
      ) : (
        <div className="ads-grid">
          {results.ads.map((ad, index) => (
            <AdCard key={ad.creative_id || index} ad={ad} />
          ))}
        </div>
      )}
    </>
  )

  const clustersContent = results.clustering ? (
    <ClusterView clustering={results.clustering} />
  ) : (
    <p className="no-results">Clustering data not available.</p>
  )

  const tabs = [
    {
      id: 'cards',
      label: `Ad Cards (${results.ads_count})`,
      content: cardsContent,
    },
    {
      id: 'clusters',
      label: `Clusters (${results.clustering?.clusters.length || 0})`,
      content: clustersContent,
    },
  ]

  // Format domain list for display
  const domainsDisplay = results.domains.length > 3
    ? `${results.domains.slice(0, 3).join(', ')} +${results.domains.length - 3} more`
    : results.domains.join(', ')

  return (
    <section className="results-container">
      <header className="results-header">
        <h2>Results for: {domainsDisplay}</h2>
        {results.domains.length > 1 && (
          <span className="domains-count">{results.domains.length} domains</span>
        )}
      </header>

      <Tabs tabs={tabs} defaultTab="cards" />
    </section>
  )
}
