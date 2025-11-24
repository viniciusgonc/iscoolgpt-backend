from abc import ABC, abstractmethod

class LLMClient(ABC):

    @abstractmethod
    async def ask(self, prompt: str) -> str:
        pass