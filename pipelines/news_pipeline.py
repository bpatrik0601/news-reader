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


def remove_duplicates(lines: list[str]) -> list[str]:
    seen = set()
    result = []
    for l in lines:
        if l not in seen:
            result.append(l)
            seen.add(l)
    return result

report_output: list[str] = []
def log_and_collect(text: str):
    print(text)
    report_output.append(text)

def export_report(report_output):
    full_output = "\n".join(report_output)
    with open("report_output.txt", "w", encoding="utf-8") as f:
        f.write(full_output)

def export_report_md(report_output):
    full_output = "\n".join(report_output)

    with open("report_output.md", "w", encoding="utf-8") as f:
        f.write(full_output)


class NewsPipeline:
    def __init__(self, demo: bool = False, level: int = 2):
        llm_client = OllamaClient()

        self.demo = demo
        self.level = level
        self.logger = DemoLogger(demo)

        self.source_agent = SourceAgent()
        self.relevance_agent = RelevanceAgent(llm_client, debug=not self.demo)
        self.cluster_agent = ClusterAgent(similarity_threshold=0.55, verbose=not self.demo)
        self.cluster_merge_agent = ClusterMergeAgent(llm_client, demo=self.demo)
        self.summary_agent = SummaryAgent(llm_client, demo=self.demo)

    def run(self, config: dict, topic: str) -> list[str]:
        # ==================================================
        # PIPELINE ELEJE – SNAPSHOT TELJES, FIX SÉMA
        # ==================================================
        report_output.clear()  # Clear previous output
        
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

        if not self.demo:
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
        if not self.demo:
            print(f"[Pipeline] Fetched {len(articles)} articles")
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

        # time.sleep(1)  # Szünet a lépések között, ha esetleg szimuláltabb kell, hogy legyen a demo során

        # --------------------------------------------------
        # 2. RELEVANCE
        # --------------------------------------------------
        self.logger.step("2. lépés", f"Relevancia-szűrés --> releváns cikkek kiválasztása a témához: {topic}.")
        
        if self.demo and isinstance(topic, list):
            self.logger.info(f"Figyelt kulcsszavak: {', '.join(topic)}")
        
        relevant_articles: list[Article] = []

        if not self.demo:
            print("\n[Pipeline] Starting relevance filtering")
        elif self.demo:
            print("\n[Demo] Most az AI eldönti, mely cikkek relevánsak.")

        for idx, article in enumerate(articles, start=1):
            if not self.demo:
                print(f"\n[Pipeline] Relevance check {idx}/{len(articles)}")
                print(f"[Pipeline] Title: {article.title}")

            text = article.title + "\n\n" + article.content[:500]
            
            if self.demo: # DEMO CONTEXT
                print("\n" + "-" * 50)
                print(f"[Demo] Vizsgált cikk: {idx}/{len(articles)}")
                print(f"{article.title}")

            if isinstance(topic, list):
                decision = any(
                    self.relevance_agent.is_relevant(text, t)
                    for t in topic
                )
            else:
                decision = self.relevance_agent.is_relevant(text, topic)            
            
            
            if decision:
                if not self.demo:
                    print("[Pipeline] → Accepted as relevant")
                self.logger.decision("Ez a cikk relevánsnak tűnik a témához, ezért belevesszük a további feldolgozásba.")
                relevant_articles.append(article)
            else:
                if not self.demo:
                    print("[Pipeline] → Rejected as not relevant")
                    self.logger.decision("Ez a cikk nem tűnik elég relevánsnak a témához, ezért kihagyjuk.")

        if not self.demo:
            print(
                f"\n[Pipeline] Relevance filtering finished | "
                f"relevant_articles={len(relevant_articles)}"
            )
        elif self.demo:
            self.logger.info(f"\nA témához releváns cikkek kiválasztva. Az AI összesen {len(relevant_articles)} releváns cikket talált a témában.")

        snapshot["articles"]["relevant"] = [
            {
                "source": a.source,
                "title": a.title,
            }
            for a in relevant_articles
        ]
        # Fallback, ha nincs releváns cikk, hogy a pipeline ne omoljon össze, hanem szépen leálljon és mentse a snapshotot a demo kedvéért
        if not relevant_articles:
            if not self.demo:
                print("\n[Pipeline] Nincs releváns cikk a témában.")
            self.logger.info("Az AI nem találtott releváns cikket ehhez a témához.")
            
            if self.demo:    
                print("\n[Demo] Fallback aktiválva: néhány további cikket mégis használunk bemutatási célból.")
                self.logger.info("Demo módban fallback aktiválva.")
                
                relevant_articles = articles[:3]  # csak demo kedvéért, hogy legyen mit mutatni

                # snapshot-ba is érdemes menteni
                snapshot["articles"]["relevant"] = [
                    {
                        "source": a.source,
                        "title": a.title,
                    }
                    for a in relevant_articles
                ]
            else:
                save_snapshot(snapshot)
                return []
        
        # LEVEL 1 – egyszerű mód
        if self.level == 1:
            self.logger.info("Egyszerű mód: csak releváns hírek összefoglalása")

            if not relevant_articles:
                print("Nincs releváns cikk.")
                return []

            summary = self.summary_agent.summarize(relevant_articles, topic)

            print("\nÖsszefoglaló:")
            print(summary)

            snapshot["summaries"].append({
                "cluster_index": 1,
                "summary": summary,
            })

            save_snapshot(snapshot)

            return [summary]

        # time.sleep(1)

        # --------------------------------------------------
        # 3. CLUSTERING
        # --------------------------------------------------
        self.logger.step("3. lépés", "Klaszterezés --> hasonló hírek csoportositása.")
        if not self.demo:
            print("\n[Pipeline] Starting clustering")
        elif self.demo:
            print("\n[Demo] A hasonló cikkek csoportosítása történik.")

        initial_clusters: list[list[Article]] = self.cluster_agent.cluster(
            relevant_articles
        )
        
        if not self.demo:
            print(f"\n[Pipeline] Initial clusters | count={len(initial_clusters)}")
        if self.demo:
            self.logger.info(f"\nAz AI a releváns cikkeket hasonlóság alapján csoportosította, hogy az egyes témaköröket elkülönítse egymástól. Ez segít abban, hogy a későbbi lépésekben fókuszáltabb elemzést és összefoglalást készíthessünk az egyes témakörökről.")

        for idx, cluster in enumerate(initial_clusters, start=1):
            if not self.demo:
                print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")
            self.logger.info(f"{len(cluster)} cikk tartozik ebbe a csoportba.")
            
            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["initial"] = [
            [a.title for a in cluster]
            for cluster in initial_clusters
        ]
        if not initial_clusters:
            if not self.demo:
                print("\n[Pipeline] Nem sikerült csoportosítani a cikkeket.")
            self.logger.info("Nem volt elegendő adat a klaszterezéshez.")

            save_snapshot(snapshot)
            return []

        # --------------------------------------------------
        # 3b. CLUSTER MERGE
        # --------------------------------------------------
        self.logger.step("3b. lépés", "Összevonás --> csoportok összevonása, ha ugyanarról szólnak (azonos események felismerése).")
        if not self.demo:
            print("\n[Pipeline] Starting cluster merge")

        clusters: list[list[Article]]
        merge_performed: bool

        # LEVEL 2 → nincs merge
        if self.level == 2:
            self.logger.info("Merge kihagyva – közepes mód")

            clusters = initial_clusters
            merge_performed = False

        # LEVEL 3 → teljes pipeline
        elif self.level == 3:
            clusters, merge_performed = self.cluster_merge_agent.merge(
                initial_clusters, topic
            )

        snapshot["clusters"]["merge_performed"] = merge_performed

        
        if merge_performed:
            message = "Az AI összevont néhány hasonló témájú cikkcsoportot, mert úgy ítélte meg, hogy ugyanarról az eseményről szólnak."
        else:
            message = "Az AI nem talált olyan csoportokat, amiket össze kellett volna vonni."

        if self.demo:
            self.logger.decision(message)
        else:
            print(message)


        # summary logger
        self.logger.info(f"{len(clusters)} végleges témakört azonosított az AI.")

        for idx, cluster in enumerate(clusters, start=1):
            if self.demo:
                print(f"   • {len(cluster)} cikk tartozik ebbe a csoportba.")
            else:
                print(f"[Pipeline] Cluster {idx} | articles={len(cluster)}")

            for article in cluster:
                print(f"  - [{article.source}] {article.title}")

        snapshot["clusters"]["merged"] = [
            [a.title for a in cluster]
            for cluster in clusters
        ]

        # time.sleep(1)

        # --------------------------------------------------
        # 4. SUMMARY
        # --------------------------------------------------
        self.logger.step("4. lépés", "Összefoglaló készítése --> releváns cikkek rövid összefoglalása.")

        if not self.demo:
            print("\n[Pipeline] Generating summaries")
        elif self.demo:
            print("\n[Demo] Az AI most elemzi a cikkeket és összefoglalót készít.")

        summaries: list[str] = []

        for idx, cluster in enumerate(clusters, start=1):
            
            if not self.demo:
                print(f"\n[Pipeline] Summary for cluster {idx}")

            print("\n" + "=" * 60)
            print(f"📰 {idx}. témakör")
            print("=" * 60)

            if self.demo:
                print(f"[Demo] Az AI feldolgozza a {idx}. csoporthoz tartozó cikkeket az összefoglaló készítéséhez.\n")

            # CIKKEK LISTÁZÁSA (riport jellegű)
            for article in cluster:
                preview = article.content[:300] if article.content else ""

                log_and_collect(f"\nCím: {article.title}")
                log_and_collect(f"Forrás: {article.source}")

                if hasattr(article, "published_at"):
                    log_and_collect(f"Időpont: {article.published_at}")

                log_and_collect(f"Rövid kivonat: {preview}...")

            # AI összefoglaló
            print("\nAI összefoglaló:")
            
            summary = self.summary_agent.summarize(cluster, topic)
            
            # deduplikálás
            lines = [l.strip() for l in summary.split("\n") if l.strip()]
            lines = remove_duplicates(lines)
            clean_summary = "\n".join(lines)

            summaries.append(clean_summary)

            print(clean_summary)

            snapshot["summaries"].append({
                "cluster_index": idx,
                "summary": clean_summary,
            })

        # ==================================================
        # FILE EXPORT
        # ==================================================
        export_report(report_output)
        # export_report_md(report_output) # Markdown export opcionális, ha szebb formázást szeretnénk a riportban, de a sima txt is jól használható és könnyen megnyitható bármilyen eszközön.

        # ==================================================
        # PIPELINE VÉGE – SNAPSHOT MENTÉS (FIXEN BENNE VAN)
        # ==================================================
        save_snapshot(snapshot)

        return summaries
