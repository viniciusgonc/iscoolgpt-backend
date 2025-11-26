# app/llms/deepseek_chat_llm.py

import os
import httpx
from app.llm_base import LLMClient


class DeepSeekChatLLM(LLMClient):
    """
    Modo chatbot normal (similar ao Gemini/HF).
    Modelo: deepseek-chat
    """

    def __init__(self, model_name: str = None):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY não foi encontrada no ambiente.")

        self.model_name = model_name or os.getenv(
            "DEEPSEEK_CHAT_MODEL", "deepseek-chat"
        )

        self.url = "https://api.deepseek.com/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # prompt igual ao Gemini
    def _build_prompt(self, user_prompt: str) -> str:
        system_instructions = """
Você é o IsCoolGPT, um assistente especializado em estudos de Cloud Computing.

Seu foco principal é:
- Explicar conceitos de AWS, GCP e Azure de forma didática.
- Ajudar em dúvidas sobre arquitetura, serviços gerenciados, redes, segurança, IAM,
  containers, serverless, observabilidade e boas práticas.
- Sempre que fizer sentido, conectar a explicação com:
    - exemplos práticos,
    - analogias simples,
    - e dicas de estudo para certificações (por exemplo: AWS Cloud Practitioner,
      AWS Solutions Architect Associate, Azure Fundamentals, etc.).

Regras de resposta:
- Responda SEMPRE em português brasileiro.
- Seja direto, mas não superficial.
- Se o usuário pedir código, comandos de CLI ou YAML/Terraform, explique o que
  eles fazem e em qual contexto são usados.
- Se a pergunta estiver confusa ou incompleta, explique o que está faltando e
  sugira como melhorar a pergunta.
"""

        return f"{system_instructions}\n\n--- pergunta do usuário ---\n{user_prompt}\n"

    async def ask(self, prompt: str) -> str:
        final_prompt = self._build_prompt(prompt)

        body = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": final_prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json=body
            )

        if response.status_code != 200:
            return f"[ERRO DeepSeek-Chat] {response.status_code}: {response.text[:200]}"

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return str(data)
