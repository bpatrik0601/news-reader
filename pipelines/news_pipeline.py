from datetime import datetime
from importlib.resources.readers import remove_duplicates
from typing import Any

from agents.source_agent import SourceAgent
from agents.relevance_agent import RelevanceAgent
from agents.cluster_agent import ClusterAgent
from agents.cluster_merge_agent import ClusterMergeAgent
from agents.summary_agent import SummaryAgent
from agents.ollama_client import OllamaClient

from utils.snapshot import save_snapshot
from models.article import Article


class NewsPipeline:
    def __init__(self):
        llm_client = OllamaClient()

        self.source_agent = SourceAgent()
        self.relevance_agent = RelevanceAgent(llm_client)
        self.cluster_agent = ClusterAgent(similarity_threshold=0.55)
        self.cluster_merge_agent = ClusterMergeAgent(llm_client)
        self.summary_agent = SummaryAgent(llm_client)

    def run(self, config: dict, topic: str) -> list[str]:
        # ==================================================
        # PIPELINE ELEJE – SNAPSHOT TELJES, FIX SÉMA
        # ==================================================
        run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        snapshot: dict[str, Any] = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "models": {
                "llm": self.relevance_agent.llm.model_id(),
            },
            "articles": {
                "fetched": [],
                "relevant": [],
            },
            "clusters": {
                "initial": [],
                "merged": [],
            },
            "summaries": [],
        }

        print(f"\n[Pipeline] Starting run {run_id}")
        print(f"[Pipeline] Topic: {topic}")

        # --------------------------------------------------
        # 1. FETCH
        # --------------------------------------------------
        articles: list[Article] = self.source_agent.fetch(
            sources=config["sources"],
            max_per_source=config["fetch"]["max_articles_per_source"],
            max_total=config["fetch"]["max_total_articles"],
            lookback_hours=config["fetch"]["lookback_hours"],
        )

        print("\n[Pipeline] Fetched articles:")
        for idx, article in enumerate(articles, start=1):
            print(f"  {idx}. [{article.source}] {article.title}")

        snapshot["articles"]["fetched"] = [
            {
                "id": f"{a.source}-{i}",
                "source": a.source,
                "title": a.title,
                "published_at": a.published_at,
                "content": a.content[:2000],
            }
            for i, a in enumerate(articles)
        ]

        # --------------------------------------------------
        # 2. RELEVANCE
        # --------------------------------------------------
        relevant_articles: list[Article] = []

        print("\n[Pipeline] Starting relevance filtering")

        for idx, article in enumerate(articles, start=1):
            print(f"\n[Pipeline] Relevance check {idx}/{len(articles)}")
            print(f"[Pipeline] Title: {article.title}")

            text = article.title + "\n\n" + article.content[:500]
            decision = self.relevance_agent.is_relevant(text, topic)

            if decision:
                print("[Pipeline] → Accepted as relevant")
                relevant_articles.append(article)
            else:
                print("[Pipeline] → Rejected as not relevant")

        print(
            f"\n[Pipeline] Relevance filtering finished | "
            f"relevant_articles={len(relevant_articles)}"
        )

        snapshot["articles"]["relevant"] = [
            {
                "source": a.source,
                "title": a.title,
            }
            for a in relevant_articles
        ]

        # --------------------------------------------------
        # 3. CLUSTERING
        # --------------------------------------------------
        print("\n[Pipeline] Starting clustering")

        initial_clusters: list[list[Article]] = self.cluster_agent.cluster(
            relevant_articles
        )

        print(f"\n[Pipeline] Initial clusters | count={len(initial_clusters)}")
        for idx, cluster in enumerate(initial_clusters, start=1):
            print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")
            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["initial"] = [
            [a.title for a in cluster]
            for cluster in initial_clusters
        ]

        # --------------------------------------------------
        # 3b. CLUSTER MERGE
        # --------------------------------------------------
        print("\n[Pipeline] Starting cluster merge")

        clusters: list[list[Article]] = self.cluster_merge_agent.merge(
            initial_clusters, topic
        )

        snapshot["clusters"]["merge_performed"] = clusters != initial_clusters

        if snapshot["clusters"]["merge_performed"]:
            print("[Pipeline] Cluster merge resulted in changes.")
            print(f"\n[Pipeline] Clusters after merge | count={len(clusters)}")
        else:
            print("[Pipeline] No cluster merges performed.")

        for idx, cluster in enumerate(clusters, start=1):
            print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")
            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["merged"] = [
            [a.title for a in cluster]
            for cluster in clusters
        ]


        # --------------------------------------------------
        # 4. SUMMARY
        # --------------------------------------------------
        print("\n[Pipeline] Generating summaries")

        summaries: list[str] = []

        for idx, cluster in enumerate(clusters, start=1):

            print("\n" + "=" * 60)
            print(f"📰 {idx}. témakör")
            print("=" * 60)

            # 📄 CIKKEK LISTÁZÁSA (riport jellegű)
            for article in cluster:
                preview = article.content[:300] if article.content else ""

                print(f"\n📌 Cím: {article.title}")
                print(f"📡 Forrás: {article.source}")

                if hasattr(article, "published_at"):
                    print(f"🕒 Időpont: {article.published_at}")

                print(f"📄 Rövid kivonat: {preview}...")

            # 🧠 AI összefoglaló
            print("\n🧠 AI összefoglaló:")

            summary = self.summary_agent.summarize(cluster, topic)

            # ✅ deduplikálás
            lines = [l.strip() for l in summary.split("\n") if l.strip()]
            lines = remove_duplicates(lines)
            clean_summary = "\n".join(lines)

            print(clean_summary)

            summaries.append(clean_summary)

            snapshot["summaries"].append({
                "cluster_index": idx,
                "summary": clean_summary,
            })

        # ==================================================
        # PIPELINE VÉGE – SNAPSHOT MENTÉS (FIXEN BENNE VAN)
        # ==================================================
        save_snapshot(snapshot)

        return summaries