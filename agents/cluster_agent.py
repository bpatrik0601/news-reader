from typing import List
import re

from models.article import Article


class ClusterAgent:
    """
    Token-based clustering agent for news articles.

    Uses Jaccard similarity on normalized tokens
    instead of character-based sequence matching.
    """

    def __init__(self, similarity_threshold: float = 0.55, verbose: bool = False):
        self.similarity_threshold = similarity_threshold
        self.verbose = verbose

    def cluster(self, articles: List[Article]) -> List[List[Article]]:
        if self.verbose:
            print("[ClusterAgent] Starting clustering")
            print(f"[ClusterAgent] Similarity threshold: {self.similarity_threshold}")

        clusters: List[List[Article]] = []

        for article in articles:
            added_to_cluster = False
            article_repr = self._representation(article)

            for cluster in clusters:
                cluster_repr = self._representation(cluster[0])
                similarity = self._jaccard_similarity(article_repr, cluster_repr)

                if self.verbose:
                    print("[ClusterAgent] Compare:")
                    print(f"  - '{article.title}'")
                    print(f"  - '{cluster[0].title}'")
                    print(f"  → similarity={similarity:.2f}")

                if similarity >= self.similarity_threshold:
                    cluster.append(article)
                    added_to_cluster = True
                    if self.verbose:
                        print("[ClusterAgent] → Added to existing cluster")
                    break

            if not added_to_cluster:
                clusters.append([article])
                if self.verbose:
                    print("[ClusterAgent] → New cluster created")

        if self.verbose: 
            print(f"[ClusterAgent] Clustering finished | clusters={len(clusters)}")
        return clusters

    # --------------------------------------------------
    # INTERNALS
    # --------------------------------------------------

    def _representation(self, article: Article) -> set[str]:
        """
        Normalized token set based on title + short content prefix.
        """
        text = f"{article.title} {article.content[:300]}"
        tokens = self._tokenize(text)
        return tokens

    def _tokenize(self, text: str) -> set[str]:
        """
        Lowercase, remove punctuation, split to tokens.
        """
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        return set(tokens)

    def _jaccard_similarity(self, a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)