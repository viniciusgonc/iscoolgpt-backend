# app/llms/gemini_llm.py

from app.llm_base import LLMClient

class GeminiLLM(LLMClient):
    async def ask(self, prompt: str) -> str:
        return f"[Gemini simulated response]: {prompt}"