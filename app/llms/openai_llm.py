#app/llms/openai_llm.py

from app.llm_base import LLMClient

class OpenAILLM(LLMClient):
    async def ask(self, prompt: str) -> str:
        return f"[OpenAI simulated response]: {prompt}"