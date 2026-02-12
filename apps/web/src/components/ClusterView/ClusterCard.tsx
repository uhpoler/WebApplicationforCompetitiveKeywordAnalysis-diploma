import { useState } from 'react'
import type { Cluster } from '../../types/ads'

interface ClusterCardProps {
  cluster: Cluster
}

export function ClusterCard({ cluster }: ClusterCardProps) {
  const [expanded, setExpanded] = useState(false)

  // Generate a color based on cluster id for visual distinction
  const hue = (cluster.id * 137) % 360
  const borderColor = `hsl(${hue}, 70%, 50%)`
  const bgColor = `hsl(${hue}, 70%, 95%)`
  const tagBgColor = `hsl(${hue}, 60%, 90%)`
  const tagBorderColor = `hsl(${hue}, 60%, 70%)`

  const displayPhrases = expanded ? cluster.phrases : cluster.phrases.slice(0, 5)
  const hasMore = cluster.phrases.length > 5

  return (
    <div
      className="cluster-card"
      style={{ borderLeftColor: borderColor }}
    >
      <div className="cluster-header" style={{ backgroundColor: bgColor }}>
        <div className="cluster-name-row">
          <h4 className="cluster-name">{cluster.name}</h4>
          <span className="cluster-count" style={{ backgroundColor: borderColor }}>
            {cluster.size}
          </span>
        </div>
      </div>

      <div className="cluster-phrases">
        {displayPhrases.map((phraseInfo, index) => (
          <div key={index} className="phrase-item">
            <span
              className="phrase-tag"
              style={{
                backgroundColor: tagBgColor,
                borderColor: tagBorderColor,
              }}
            >
              {phraseInfo.phrase}
            </span>
            {phraseInfo.ad_url && (
              <a
                href={phraseInfo.ad_url}
                target="_blank"
                rel="noopener noreferrer"
                className="phrase-ad-link"
                title={`View ad: ${phraseInfo.ad_title || 'Unknown'}`}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </a>
            )}
          </div>
        ))}
      </div>

      {hasMore && (
        <button
          className="show-more-btn"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? 'Show less' : `Show ${cluster.phrases.length - 5} more`}
        </button>
      )}
    </div>
  )
}
