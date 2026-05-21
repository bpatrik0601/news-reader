import re
import difflib
from typing import List

from agents.base_client import LLMClient
from models.article import Article


class ClusterMergeAgent:
    """
    Merges clusters that actually describe the same underlying news event.
    Uses an LLM to decide "same story?" at cluster level (YES/NO only),
    with a cheap prefilter to avoid too many LLM calls.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        title_similarity_gate: float = 0.35,
        number_overlap_gate: bool = True,
    ):
        self.llm = llm_client
        self.title_similarity_gate = title_similarity_gate
        self.number_overlap_gate = number_overlap_gate
    
    def merge(self, clusters: List[List[Article]], topic: str) -> tuple[List[List[Article]], bool]:
        print("[ClusterMergeAgent] Starting cluster-merge")
        print(f"[ClusterMergeAgent] Input clusters: {len(clusters)}")

        if len(clusters) <= 1:
            return clusters, False

        merged_any_global = False

        merged_any = True
        while merged_any:
            merged_any = False

            i = 0
            while i < len(clusters):
                j = i + 1
                while j < len(clusters):
                    a = clusters[i]
                    b = clusters[j]

                    if not self._prefilter(a, b):
                        j += 1
                        continue

                    print(f"[ClusterMergeAgent] Candidate merge: cluster {i+1} <-> cluster {j+1}")
                    if self._llm_says_same_story(a, b, topic):
                        print(f"[ClusterMergeAgent] → MERGED cluster {j+1} into cluster {i+1}")
                        clusters[i] = clusters[i] + clusters[j]
                        del clusters[j]

                        merged_any = True
                        # j stays the same index after deletion, so do not j += 1
                        merged_any_global = True

                    else:
                        print(f"[ClusterMergeAgent] → NOT merged")
                        j += 1

                i += 1

        print(f"[ClusterMergeAgent] Merge finished | output clusters: {len(clusters)}")
        return clusters, merged_any_global

    # --------------------------
    # Prefilter (cheap)
    # --------------------------
    def _prefilter(self, cluster_a: List[Article], cluster_b: List[Article]) -> bool:
        """
        Return True if it's worth asking the LLM.
        No domain keyword lists; only generic signals:
        - loose title similarity
        - shared numbers (optional)
        """
        titles_a = " | ".join([a.title for a in cluster_a[:3]]).lower()
        titles_b = " | ".join([b.title for b in cluster_b[:3]]).lower()

        title_sim = difflib.SequenceMatcher(None, titles_a, titles_b).ratio()

        if title_sim >= self.title_similarity_gate:
            return True

        if self.number_overlap_gate:
            nums_a = self._extract_numbers(titles_a + " " + self._cluster_snippet(cluster_a))
            nums_b = self._extract_numbers(titles_b + " " + self._cluster_snippet(cluster_b))
            if nums_a and nums_b and (nums_a & nums_b):
                return True

        return False

    def _extract_numbers(self, text: str) -> set[str]:
        # generic numeric tokens: 80, 80.000, 80,000, 80 milliárd etc. -> capture number parts
        found = re.findall(r"\d+(?:[.,]\d+)?", text)
        return set(found)

    def _cluster_snippet(self, cluster: List[Article], max_chars_per_article: int = 200) -> str:
        parts = []
        for art in cluster[:2]:  # keep it small
            parts.append((art.content or "")[:max_chars_per_article])
        return " ".join(parts).lower()

    # --------------------------
    # LLM decision
    # --------------------------
    def _llm_says_same_story(self, cluster_a: List[Article], cluster_b: List[Article], topic: str) -> bool:
        prompt = self._build_prompt(cluster_a, cluster_b, topic)

        print("[ClusterMergeAgent] Sending prompt to Ollama")
        response = self.llm.complete(prompt)
        print(f"[ClusterMergeAgent] Raw response: {response}")

        normalized = response.strip().lower()
        return normalized == "yes"

    def _build_prompt(self, cluster_a: List[Article], cluster_b: List[Article], topic: str) -> str:
        a_text = self._format_cluster(cluster_a, label="A")
        b_text = self._format_cluster(cluster_b, label="B")

        return f"""
You are a strict news clustering assistant.

Task:
Decide whether Cluster A and Cluster B describe the SAME underlying news event/story
related to the topic "{topic}", even if wording differs.

Rules:
- Answer with EXACTLY one word: YES or NO.
- Do NOT explain.
- Answer YES only if they refer to the same underlying event (same key actors + same key facts).
- If unsure, answer NO.

{a_text}

{b_text}

Answer:
""".strip()

    def _format_cluster(self, cluster: List[Article], label: str) -> str:
        MAX_ARTICLES = 3
        MAX_CHARS_PER_ARTICLE = 250

        lines = [f"Cluster {label}:"]
        for idx, art in enumerate(cluster[:MAX_ARTICLES], start=1):
            snippet = (art.content or "")[:MAX_CHARS_PER_ARTICLE]
            lines.append(f"{idx}) Source: {art.source}")
            lines.append(f"   Title: {art.title}")
            lines.append(f"   Snippet: {snippet}")
        return "\n".join(lines)