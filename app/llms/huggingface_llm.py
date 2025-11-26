# app/llms/huggingface_llm.py

import os
import httpx
from app.llm_base import LLMClient


class HuggingFaceLLM(LLMClient):
    def __init__(self, model_name: str = None):

        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "HUGGINGFACE_API_KEY não encontrada nas variáveis de ambiente"
            )

        self.model_name = model_name or os.getenv(
            "HUGGINGFACE_MODEL", "microsoft/Phi-3-mini-4k-instruct"
        )

        self.url = f"https://router.huggingface.co/v1/inference/{self.model_name}"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

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

        full_prompt = f"""{system_instructions}

--- pergunta do usuário ---
{user_prompt}

--- resposta do assistente ---
"""
        return full_prompt.strip()

    async def ask(self, prompt: str) -> str:
        final_prompt = self._build_prompt(prompt)

        payload = {
            "inputs": final_prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.6,
            },
        }

        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json=payload
            )

        if response.status_code != 200:
            return (
                f"[ERRO HuggingFace] HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

        data = response.json()

        try:
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"]
        except Exception:
            pass

        return str(data)
