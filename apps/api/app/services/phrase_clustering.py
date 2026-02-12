"""Phrase clustering service using sentence-transformers and HDBSCAN."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# Try to import required libraries
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore[misc, assignment]

try:
    from sklearn.cluster import HDBSCAN

    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    HDBSCAN = None  # type: ignore[misc, assignment]

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore[assignment]


@dataclass
class PhraseInfo:
    """Information about a keyphrase and its source ad."""

    phrase: str
    ad_title: str | None
    ad_url: str | None
    creative_id: str | None


@dataclass
class Cluster:
    """A cluster of related keyphrases."""

    id: int
    name: str
    phrases: list[PhraseInfo] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.phrases)


@dataclass
class ClusteringResult:
    """Result of phrase clustering."""

    clusters: list[Cluster]
    unclustered: list[PhraseInfo]
    total_phrases: int
    error: str | None = None


class PhraseClusterer:
    """Cluster keyphrases using sentence embeddings and HDBSCAN."""

    # Use a lightweight but effective model
    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self, min_cluster_size: int = 2, min_samples: int = 1):
        """
        Initialize the phrase clusterer.

        Args:
            min_cluster_size: Minimum number of phrases to form a cluster
            min_samples: HDBSCAN min_samples parameter
        """
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self._model: SentenceTransformer | None = None  # type: ignore[valid-type]

    def _get_model(self) -> SentenceTransformer | None:  # type: ignore[valid-type]
        """Lazy load the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return None

        if self._model is None:
            self._model = SentenceTransformer(self.MODEL_NAME)  # type: ignore[misc]

        return self._model

    def _generate_cluster_name(self, phrases: list[str]) -> str:
        """
        Generate a descriptive name for a cluster based on its phrases.

        Uses the most common words across all phrases in the cluster.
        """
        # Collect all words from phrases
        all_words: list[str] = []
        for phrase in phrases:
            words = phrase.lower().split()
            all_words.extend(words)

        # Count word frequencies
        word_counts = Counter(all_words)

        # Filter out very common/short words
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "shall", "can", "need", "dare", "ought", "used", "it", "its", "this", "that", "these", "those", "i", "you", "he", "she", "we", "they", "what", "which", "who", "whom", "whose", "where", "when", "why", "how", "all", "each", "every", "both", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "just", "your", "our"}

        filtered_words = [
            (word, count)
            for word, count in word_counts.most_common(10)
            if word not in stopwords and len(word) > 2
        ]

        if not filtered_words:
            # Fallback to most common phrase
            phrase_counts = Counter(phrases)
            most_common = phrase_counts.most_common(1)
            if most_common:
                return most_common[0][0].title()
            return "Miscellaneous"

        # Take top 2-3 most common meaningful words
        top_words = [word for word, _ in filtered_words[:3]]
        return " ".join(top_words).title()

    def cluster_phrases(self, phrase_infos: list[PhraseInfo]) -> ClusteringResult:
        """
        Cluster a list of phrases using sentence embeddings and HDBSCAN.

        Args:
            phrase_infos: List of PhraseInfo objects containing phrases and metadata

        Returns:
            ClusteringResult with clusters and unclustered phrases
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error="sentence-transformers not installed",
            )

        if not HDBSCAN_AVAILABLE:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error="hdbscan not installed",
            )

        if not NUMPY_AVAILABLE:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error="numpy not installed",
            )

        if len(phrase_infos) < 2:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
            )

        try:
            model = self._get_model()
            if model is None:
                return ClusteringResult(
                    clusters=[],
                    unclustered=phrase_infos,
                    total_phrases=len(phrase_infos),
                    error="Failed to load sentence transformer model",
                )

            # Extract unique phrases for embedding
            phrases = [info.phrase for info in phrase_infos]

            # Generate embeddings
            embeddings = model.encode(phrases, show_progress_bar=False)

            # Determine min_cluster_size based on data size
            adaptive_min_cluster_size = max(2, min(self.min_cluster_size, len(phrases) // 3))

            # Cluster using sklearn's built-in HDBSCAN
            clusterer = HDBSCAN(  # type: ignore[misc]
                min_cluster_size=adaptive_min_cluster_size,
                min_samples=self.min_samples,
                metric="euclidean",
                cluster_selection_method="eom",
            )
            cluster_labels = clusterer.fit_predict(embeddings)

            # Group phrases by cluster
            cluster_dict: dict[int, list[PhraseInfo]] = {}
            unclustered: list[PhraseInfo] = []

            for phrase_info, label in zip(phrase_infos, cluster_labels):
                if label == -1:
                    unclustered.append(phrase_info)
                else:
                    if label not in cluster_dict:
                        cluster_dict[label] = []
                    cluster_dict[label].append(phrase_info)

            # Build cluster objects with generated names
            clusters: list[Cluster] = []
            for cluster_id, cluster_phrases in cluster_dict.items():
                phrase_texts = [p.phrase for p in cluster_phrases]
                cluster_name = self._generate_cluster_name(phrase_texts)

                clusters.append(
                    Cluster(
                        id=cluster_id,
                        name=cluster_name,
                        phrases=cluster_phrases,
                    )
                )

            # Sort clusters by size (largest first)
            clusters.sort(key=lambda c: c.size, reverse=True)

            return ClusteringResult(
                clusters=clusters,
                unclustered=unclustered,
                total_phrases=len(phrase_infos),
            )

        except Exception as e:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error=f"Clustering failed: {str(e)}",
            )


# Singleton instance
_clusterer_instance: PhraseClusterer | None = None


def get_phrase_clusterer() -> PhraseClusterer:
    """Get a phrase clusterer instance."""
    global _clusterer_instance
    if _clusterer_instance is None:
        _clusterer_instance = PhraseClusterer()
    return _clusterer_instance
