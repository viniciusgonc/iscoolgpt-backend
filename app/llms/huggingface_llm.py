# app/llms/huggingface_llm.py

from app.llm_base import LLMClient

class HuggingFaceLLM(LLMClient):
    async def ask(self, prompt: str) -> str:
        return f"[HuggingFace simulated response]: {prompt}"