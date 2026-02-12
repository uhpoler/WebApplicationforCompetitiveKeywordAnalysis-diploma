import type { ClusteringData } from '../../types/ads'
import { ClusterCard } from './ClusterCard'
import './ClusterView.css'

interface ClusterViewProps {
  clustering: ClusteringData
}

export function ClusterView({ clustering }: ClusterViewProps) {
  const { clusters, unclustered, total_phrases, error } = clustering

  if (error) {
    return (
      <div className="cluster-view">
        <div className="cluster-error">
          <span className="error-icon">!</span>
          <div>
            <strong>Clustering unavailable</strong>
            <p>{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (total_phrases === 0) {
    return (
      <div className="cluster-view">
        <p className="no-clusters">No keyphrases to cluster.</p>
      </div>
    )
  }

  return (
    <div className="cluster-view">
      <div className="cluster-stats">
        <div className="stat">
          <span className="stat-value">{total_phrases}</span>
          <span className="stat-label">Total Phrases</span>
        </div>
        <div className="stat">
          <span className="stat-value">{clusters.length}</span>
          <span className="stat-label">Clusters</span>
        </div>
        <div className="stat">
          <span className="stat-value">{unclustered.length}</span>
          <span className="stat-label">Unclustered</span>
        </div>
      </div>

      {clusters.length > 0 && (
        <div className="clusters-grid">
          {clusters.map((cluster) => (
            <ClusterCard key={cluster.id} cluster={cluster} />
          ))}
        </div>
      )}

      {unclustered.length > 0 && (
        <div className="unclustered-section">
          <h3 className="section-title">Unclustered Phrases</h3>
          <div className="unclustered-phrases">
            {unclustered.map((phrase, index) => (
              <div key={index} className="unclustered-phrase">
                <span className="phrase-text">{phrase.phrase}</span>
                {phrase.ad_url && (
                  <a
                    href={phrase.ad_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="phrase-link"
                    title="View ad"
                  >
                    View Ad
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
