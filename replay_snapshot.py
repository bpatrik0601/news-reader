import json
import sys
from pathlib import Path

from pipelines.news_pipeline import NewsPipeline
from models.article import Article


def load_snapshot(snapshot_path: Path) -> dict:
    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
    return json.loads(snapshot_path.read_text(encoding="utf-8"))


def build_articles_from_snapshot(snapshot: dict) -> list[Article]:
    """
    Recreate Article objects from snapshot data.
    """
    articles = []

    for item in snapshot["articles"]["fetched"]:
        article = Article(
            source=item["source"],
            title=item["title"],
            content=item["content"],
            published_at=item.get("published_at"),
            url=""  # replaynél irreleváns
        )
        articles.append(article)

    return articles


def run_replay(snapshot_path: Path):
    print(f"[Replay] Loading snapshot: {snapshot_path.name}")

    snapshot = load_snapshot(snapshot_path)
    topic = snapshot["topic"]

    print(f"[Replay] Topic: {topic}")
    print(f"[Replay] Original model: {snapshot['models']['llm']}")

    # --------------------------------------------------
    # Pipeline újraindítása
    # --------------------------------------------------
    pipeline = NewsPipeline()

    # --------------------------------------------------
    # Articles visszaépítése (RSS NÉLKÜL)
    # --------------------------------------------------
    articles = build_articles_from_snapshot(snapshot)

    print(f"[Replay] Articles loaded: {len(articles)}")

    # --------------------------------------------------
    # RELEVANCE
    # --------------------------------------------------
    print("\n[Replay] Starting relevance filtering")

    relevant_articles = []

    for idx, article in enumerate(articles, start=1):
        print(f"\n[Replay] Relevance check {idx}/{len(articles)}")
        print(f"[Replay] Title: {article.title}")

        text = article.title + "\n\n" + article.content[:500]
        decision = pipeline.relevance_agent.is_relevant(text, topic)

        if decision:
            print("[Replay] → Accepted as relevant")
            relevant_articles.append(article)
        else:
            print("[Replay] → Rejected as not relevant")

    print(
        f"\n[Replay] Relevance filtering finished | "
        f"relevant_articles={len(relevant_articles)}"
    )

    # --------------------------------------------------
    # CLUSTERING
    # --------------------------------------------------
    initial_clusters = pipeline.cluster_agent.cluster(relevant_articles)

    print(f"[Replay] Initial clusters: {len(initial_clusters)}")

    # --------------------------------------------------
    # CLUSTER MERGE
    # --------------------------------------------------
    clusters = pipeline.cluster_merge_agent.merge(initial_clusters, topic)

    print(f"[Replay] Clusters after merge: {len(clusters)}")

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    print("[Replay] Generating summaries")

    summaries = []

    for idx, cluster in enumerate(clusters):
        print(f"\n[Replay] Summary for cluster {idx}")
        summary = pipeline.summary_agent.summarize(cluster, topic)
        summaries.append(summary)
        print(summary)

    print("\n[Replay] Finished replay")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python replay_snapshot.py path/to/snapshot.json")
        sys.exit(1)

    snapshot_file = Path(sys.argv[1])
    run_replay(snapshot_file)