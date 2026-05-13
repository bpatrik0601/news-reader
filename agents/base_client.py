from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    Base interface for all LLM clients.
    Agents must depend ONLY on this interface.
    """

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """
        Execute a single prompt and return the model's text response.
        """
        pass

    @abstractmethod
    def model_id(self) -> str:
        """
        Return a stable identifier for the underlying model
        (used for logging, snapshotting, and replay).
        """
        pass