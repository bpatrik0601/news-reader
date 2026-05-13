import requests
from agents.base_client import LLMClient


class OllamaClient(LLMClient):
    """
    Ollama-based LLM client (e.g. Qwen).
    Implements the generic LLMClient interface.
    """

    def __init__(
        self,
        model: str = "mistral-nemo:12b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.2,
        num_ctx: int = 8192,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.num_ctx = num_ctx

    def complete(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            },
            timeout=180,
        )

        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    def model_id(self) -> str:
        """
        Stable model identifier for snapshotting and replay.
        """
        return self.model