from typing import List

from agents.base_client import LLMClient
from models.article import Article


class SummaryAgent:
    """
    Creates a short summary for a cluster of related articles.
    """

    def __init__(self, llm_client: LLMClient, demo: bool = False):
        self.llm = llm_client
        self.demo = demo

    def summarize(self, cluster: List[Article], topic: str) -> str:
        if not self.demo:
            print("[SummaryAgent] Starting summary")
            print(f"[SummaryAgent] Topic: {topic}")
            print(f"[SummaryAgent] Articles in cluster: {len(cluster)}")

        prompt = self._build_prompt(cluster, topic)

        if not self.demo:
            print("[SummaryAgent] Sending prompt to Ollama")
        
        response = self.llm.complete(prompt)
        
        if not self.demo:
            print("[SummaryAgent] Raw response:")
            print(response)

        return response.strip()

    def _build_prompt(self, cluster: List[Article], topic: str) -> str:
        article_blocks = []

        MAX_CHARS_PER_ARTICLE = 500  # tudatosan alacsony

        for article in cluster:
            block = (
                f"Source: {article.source}\n"
                f"Title: {article.title}\n"
                f"Content:\n"
                f"{article.content[:MAX_CHARS_PER_ARTICLE]}\n"
            )
            article_blocks.append(block)

        articles_text = "\n---\n".join(article_blocks)

        return f"""
You are a news summarization assistant.

Task:
Create a concise, factual summary about the topic "{topic}"
based ONLY on the articles below.
If the article is unrelated, explicitly say so instead of forcing a summary.

Rules:
- The summary MUST be written in Hungarian.
- Use bullet points.
- Focus on the main facts and developments.
- Do NOT invent information.
- Do NOT add opinions or analysis.
- If articles repeat the same information, mention it only once.
- Keep the summary short (max 5 bullet points).

Critical rules:
- ONLY use information that is explicitly present in the provided articles.
- Do NOT introduce any external facts, names, or events.
- If there is insufficient information, say it briefly and clearly.

Articles:
\"\"\"
{articles_text}
\"\"\"

Summary:
""".strip()