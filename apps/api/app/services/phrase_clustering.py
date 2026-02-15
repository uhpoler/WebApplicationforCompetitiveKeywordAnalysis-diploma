"""Phrase clustering service using sentence-transformers and Agglomerative Clustering.

Clusters keyphrases into broad topic groups (e.g. all "anger"-related phrases
into one "Anger" cluster) using cosine distance between sentence embeddings.

Key design decisions:
- Uses AgglomerativeClustering with cosine distance threshold instead of HDBSCAN.
  HDBSCAN's density-based approach tends to over-split into many small clusters
  (e.g. "anger quiz" vs "control anger" vs "anger test"). Agglomerative clustering
  with average linkage merges all semantically related phrases into one topic.
- Cluster names are simplified to 1-2 core topic words.
- A post-merge step combines clusters that share a dominant keyword.
"""

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
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics.pairwise import cosine_distances
    from sklearn.preprocessing import normalize

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    AgglomerativeClustering = None  # type: ignore[misc, assignment]
    cosine_distances = None  # type: ignore[assignment]
    normalize = None  # type: ignore[assignment]

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore[assignment]


# Common English stopwords + ad-specific noise words
STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "must", "shall", "can", "need", "dare", "ought", "used",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "what", "which", "who", "whom", "whose", "where", "when",
    "why", "how", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "your", "our", "my", "his", "her", "their",
    "its", "from", "up", "out", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "about", "above", "below", "between",
    # Ad-specific noise
    "free", "best", "top", "new", "get", "try", "now", "find", "learn",
    "start", "online", "today", "help", "take", "see", "also", "many",
    "make", "know", "like", "way",
})


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
    """Cluster keyphrases using sentence embeddings and Agglomerative Clustering."""

    # Lightweight but effective model
    MODEL_NAME = "all-MiniLM-L6-v2"

    # Cosine distance threshold: phrases with distance below this are clustered.
    # 0.55 means phrases need ~45% cosine similarity to group together.
    # This is intentionally broad to merge topic-level clusters.
    DISTANCE_THRESHOLD = 0.55

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None  # type: ignore[valid-type]

    def _get_model(self) -> SentenceTransformer | None:  # type: ignore[valid-type]
        """Lazy load the sentence transformer model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return None

        if self._model is None:
            self._model = SentenceTransformer(self.MODEL_NAME)  # type: ignore[misc]

        return self._model

    # ---------- Cluster naming ----------

    def _extract_topic_words(self, phrases: list[str]) -> list[str]:
        """
        Extract the core topic words from a set of phrases.

        Returns 1-2 meaningful words that best represent the cluster topic.
        """
        # Collect all words
        all_words: list[str] = []
        for phrase in phrases:
            words = phrase.lower().split()
            all_words.extend(words)

        word_counts = Counter(all_words)

        # Filter out stopwords and short words
        meaningful = [
            (word, count)
            for word, count in word_counts.most_common(20)
            if word not in STOPWORDS and len(word) > 2
        ]

        if not meaningful:
            # Fallback: most common phrase
            phrase_counts = Counter(phrases)
            most_common = phrase_counts.most_common(1)
            if most_common:
                return [most_common[0][0]]
            return ["misc"]

        # Strategy: pick the single most frequent word.
        # If a second word is also very frequent (>60% of top word count)
        # and is not a substring/superstring of the first, include it too.
        top_word, top_count = meaningful[0]
        result = [top_word]

        if len(meaningful) > 1:
            second_word, second_count = meaningful[1]
            # Include second word only if it's frequent enough and distinct
            if (
                second_count >= top_count * 0.6
                and second_word not in top_word
                and top_word not in second_word
            ):
                result.append(second_word)

        return result

    def _generate_cluster_name(self, phrases: list[str]) -> str:
        """Generate a short, topic-level name for a cluster (1-2 words)."""
        topic_words = self._extract_topic_words(phrases)
        return " ".join(topic_words).title()

    # ---------- Post-clustering merge ----------

    def _merge_clusters_by_keyword(
        self, clusters: dict[int, list[PhraseInfo]]
    ) -> dict[int, list[PhraseInfo]]:
        """
        Merge clusters that share the same dominant keyword.

        For example, if cluster A has phrases about "anger quiz" and
        cluster B has phrases about "anger management", both have "anger"
        as the dominant word, so they should be merged.
        """
        # Find dominant keyword for each cluster
        cluster_keywords: dict[int, str] = {}
        for cid, phrase_infos in clusters.items():
            phrases = [p.phrase for p in phrase_infos]
            topic_words = self._extract_topic_words(phrases)
            cluster_keywords[cid] = topic_words[0] if topic_words else ""

        # Group cluster IDs by their dominant keyword
        keyword_groups: dict[str, list[int]] = {}
        for cid, keyword in cluster_keywords.items():
            if keyword:
                if keyword not in keyword_groups:
                    keyword_groups[keyword] = []
                keyword_groups[keyword].append(cid)

        # Merge clusters with the same dominant keyword
        merged: dict[int, list[PhraseInfo]] = {}
        next_id = 0
        seen_cids: set[int] = set()

        for keyword, cids in keyword_groups.items():
            if len(cids) > 1:
                # Merge all clusters with this keyword
                merged_phrases: list[PhraseInfo] = []
                for cid in cids:
                    merged_phrases.extend(clusters[cid])
                    seen_cids.add(cid)
                merged[next_id] = merged_phrases
                next_id += 1
            else:
                cid = cids[0]
                seen_cids.add(cid)
                merged[next_id] = clusters[cid]
                next_id += 1

        # Add any clusters we missed (shouldn't happen, but safety net)
        for cid, phrase_infos in clusters.items():
            if cid not in seen_cids:
                merged[next_id] = phrase_infos
                next_id += 1

        return merged

    # ---------- Main clustering ----------

    def cluster_phrases(self, phrase_infos: list[PhraseInfo]) -> ClusteringResult:
        """
        Cluster a list of phrases using sentence embeddings and
        Agglomerative Clustering with cosine distance.

        Args:
            phrase_infos: List of PhraseInfo objects containing phrases and metadata

        Returns:
            ClusteringResult with broad topic-level clusters
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error="sentence-transformers not installed",
            )

        if not SKLEARN_AVAILABLE:
            return ClusteringResult(
                clusters=[],
                unclustered=phrase_infos,
                total_phrases=len(phrase_infos),
                error="scikit-learn not installed",
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

            phrases = [info.phrase for info in phrase_infos]

            # Generate embeddings and normalize for cosine distance
            embeddings = model.encode(phrases, show_progress_bar=False)
            embeddings_normalized = normalize(embeddings)  # type: ignore[arg-type]

            # Compute pairwise cosine distances
            dist_matrix = cosine_distances(embeddings_normalized)  # type: ignore[arg-type]

            # Agglomerative Clustering with distance threshold
            # - metric='precomputed': we supply the distance matrix
            # - linkage='average': merge clusters based on average distance
            #   (more stable than 'single' which chains, or 'complete' which
            #    is too strict)
            # - distance_threshold: controls cluster granularity
            clusterer = AgglomerativeClustering(  # type: ignore[misc]
                n_clusters=None,
                distance_threshold=self.DISTANCE_THRESHOLD,
                metric="precomputed",
                linkage="average",
            )
            labels = clusterer.fit_predict(dist_matrix)

            # Group phrases by cluster label
            cluster_dict: dict[int, list[PhraseInfo]] = {}
            unclustered: list[PhraseInfo] = []

            for phrase_info, label in zip(phrase_infos, labels):
                label_int = int(label)
                if label_int not in cluster_dict:
                    cluster_dict[label_int] = []
                cluster_dict[label_int].append(phrase_info)

            # Move singleton clusters to unclustered
            singletons = [
                cid for cid, members in cluster_dict.items() if len(members) == 1
            ]
            for cid in singletons:
                unclustered.extend(cluster_dict.pop(cid))

            # Post-merge: combine clusters sharing the same dominant keyword
            if cluster_dict:
                cluster_dict = self._merge_clusters_by_keyword(cluster_dict)

            # Build final cluster objects
            clusters: list[Cluster] = []
            for cluster_id, cluster_phrases_list in cluster_dict.items():
                phrase_texts = [p.phrase for p in cluster_phrases_list]
                cluster_name = self._generate_cluster_name(phrase_texts)

                clusters.append(
                    Cluster(
                        id=cluster_id,
                        name=cluster_name,
                        phrases=cluster_phrases_list,
                    )
                )

            # Sort clusters by size (largest first)
            clusters.sort(key=lambda c: c.size, reverse=True)

            # Re-assign sequential IDs after sorting
            for idx, cluster in enumerate(clusters):
                cluster.id = idx

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
