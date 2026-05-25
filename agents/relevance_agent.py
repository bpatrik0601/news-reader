from agents.base_client import LLMClient


class RelevanceAgent:
    """
    Determines whether an article is relevant to a given topic.

    Mistral-friendly behavior:
    - Fast deterministic check for explicit topic mention
    - LLM decision only for borderline cases
    """

    def __init__(self, llm_client: LLMClient, debug: bool = False):
        self.llm = llm_client
        self.debug = debug

    def is_relevant(self, article_text: str, topic: str) -> bool:
        
        if self.debug:
            print("[RelevanceAgent] Checking relevance")
            print(f"[RelevanceAgent] Topic: {topic}")
            print(f"[RelevanceAgent] Text length: {len(article_text)}")

        # --------------------------------------------------
        # 1️⃣ FAST, DETERMINISTIC PATH
        # --------------------------------------------------
        if topic.lower() in article_text.lower():
            if self.debug:
                print("[RelevanceAgent] Explicit topic match found → YES")
            return True

        # --------------------------------------------------
        # 2️⃣ LLM DECISION (ONLY IF NEEDED)
        # --------------------------------------------------
        prompt = self._build_prompt(article_text, topic)

        if self.debug:
            print("[RelevanceAgent] Sending prompt to Ollama")
        response = self.llm.complete(prompt)

        if self.debug:
            print(f"[RelevanceAgent] Raw response: {response}")

        decision = response.strip().lower() == "yes"
        
        if self.debug:
            print(f"[RelevanceAgent] Decision: {'YES' if decision else 'NO'}")

        return decision

    def _build_prompt(self, article_text: str, topic: str) -> str:
        return f"""
You are a relevance classification assistant.

Task:
Decide whether the following news article is relevant to the topic "{topic}".

Important:
- Answer YES if the topic is a main subject OR
  if the topic is a significant role, position, or focus in the article.
- Answer NO only if the topic is clearly unrelated.
- Minor wording differences do NOT make it unrelated.

Rules:
- Answer with EXACTLY one word: YES or NO.
- Do NOT explain your answer.

Article:
\"\"\"
{article_text}
\"\"\"

Answer:
""".strip()
