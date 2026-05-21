from datetime import datetime
from typing import Any

from agents.source_agent import SourceAgent
from agents.relevance_agent import RelevanceAgent
from agents.cluster_agent import ClusterAgent
from agents.cluster_merge_agent import ClusterMergeAgent
from agents.summary_agent import SummaryAgent
from agents.ollama_client import OllamaClient

from utils.snapshot import save_snapshot

import time
from utils.demo_logger import DemoLogger

from models.article import Article


class NewsPipeline:
    def __init__(self, demo: bool = False):
        llm_client = OllamaClient()

        self.demo = demo
        self.logger = DemoLogger(demo)

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
        self.logger.step("1. lépés", "Hírek gyűjtése az interneten --> cikkek lekérése a forrásokból.")
        
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

        time.sleep(1)  # Szünet a lépések között, hogy jobban látszódjon a demo során

        # --------------------------------------------------
        # 2. RELEVANCE
        # --------------------------------------------------
        self.logger.step("2. lépés", f"Relevancia-szűrés --> releváns cikkek kiválasztása a témához : {topic}.")
        
        relevant_articles: list[Article] = []

        print("\n[Pipeline] Starting relevance filtering")

        for idx, article in enumerate(articles, start=1):
            print(f"\n[Pipeline] Relevance check {idx}/{len(articles)}")
            print(f"[Pipeline] Title: {article.title}")

            text = article.title + "\n\n" + article.content[:500]
            decision = self.relevance_agent.is_relevant(text, topic)

            if decision:
                print("[Pipeline] → Accepted as relevant")
                self.logger.decision("Ez a cikk relevánsnak tűnik a témához, ezért belevesszük a további feldolgozásba.")
                relevant_articles.append(article)
            else:
                print("[Pipeline] → Rejected as not relevant")
                self.logger.decision("Ez a cikk nem tűnik elég relevánsnak a témához, ezért kihagyjuk.")

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

        time.sleep(1)

        # --------------------------------------------------
        # 3. CLUSTERING
        # --------------------------------------------------
        self.logger.step("3. lépés", "Klaszterezés --> hasonló hírek csoportositása.")
        print("\n[Pipeline] Starting clustering")

        initial_clusters: list[list[Article]] = self.cluster_agent.cluster(
            relevant_articles
        )

        print(f"\n[Pipeline] Initial clusters | count={len(initial_clusters)}")
        for idx, cluster in enumerate(initial_clusters, start=1):
            print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")
            self.logger.info(f"{len(cluster)} cikk tartozik ebbe a csoportba.")
            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["initial"] = [
            [a.title for a in cluster]
            for cluster in initial_clusters
        ]

        # --------------------------------------------------
        # 3b. CLUSTER MERGE
        # --------------------------------------------------
        self.logger.step("3b. lépés", "\'Mördzsölés\' --> csoportok osszevonása, ha ugyanarról szólnak.")
        print("\n[Pipeline] Starting cluster merge")

        clusters: list[list[Article]]
        merge_performed: bool

        clusters, merge_performed = self.cluster_merge_agent.merge(
            initial_clusters, topic
        )

        snapshot["clusters"]["merge_performed"] = merge_performed

        if merge_performed:
            print("Az AI összevont néhány hasonló témájú cikkcsoportot.")
            self.logger.decision("Az AI összevont néhány hasonló témájú cikkcsoportot.")
        else:
            print("Nem talált olyan csoportokat, amiket össze kellett volna vonni.")
            self.logger.decision("Nem talált olyan csoportokat, amiket össze kellett volna vonni.")


        for idx, cluster in enumerate(clusters, start=1):
            print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")
            self.logger.info(f"{len(clusters)} végleges témakört azonosított az AI.")
            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["merged"] = [
            [a.title for a in cluster]
            for cluster in clusters
        ]

        time.sleep(1)

        # --------------------------------------------------
        # 4. SUMMARY
        # --------------------------------------------------
        self.logger.step("4. lépés", "Összefoglaló készítése --> releváns cikkek rövid összefoglalása.")

        print("\n[Pipeline] Generating summaries")

        summaries: list[str] = []

        for idx, cluster in enumerate(clusters, start=1):
            print(f"\n[Pipeline] Summary for cluster {idx}")

            summary = self.summary_agent.summarize(cluster, topic)
            summaries.append(summary)

            print(summary)

            snapshot["summaries"].append({
                "cluster_index": idx,
                "summary": summary,
            })

        # ==================================================
        # PIPELINE VÉGE – SNAPSHOT MENTÉS (FIXEN BENNE VAN)
        # ==================================================
        save_snapshot(snapshot)

        return summaries