# app/llms/huggingface_llm.py

import os
import httpx
from app.llm_base import LLMClient


class HuggingFaceLLM(LLMClient):
    """
    Cliente para o Hugging Face Router usando a API de chat completions,
    compatível com o formato OpenAI.

    Modelo padrão:
      meta-llama/Llama-3.1-8B-Instruct:cerebras

    Você ainda pode sobrescrever via HUGGINGFACE_MODEL se quiser.
    """

    def __init__(self, model_name: str = None):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "HUGGINGFACE_API_KEY não encontrada nas variáveis de ambiente."
            )

        # modelo padrão já definido em código
        self.model_name = model_name or os.getenv(
            "HUGGINGFACE_MODEL",
            "meta-llama/Llama-3.1-8B-Instruct:cerebras",
        )

        # Endpoint do router para chat completions
        self.url = "https://router.huggingface.co/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_messages(self, user_prompt: str):
        """
        Constrói a lista de mensagens no formato de chat (OpenAI-like).
        """
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

        return [
            {"role": "system", "content": system_instructions.strip()},
            {"role": "user", "content": user_prompt},
        ]

    async def ask(self, prompt: str) -> str:
        """
        Envia uma requisição de chat completion para o Hugging Face Router.
        """
        messages = self._build_messages(prompt)

        body = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.6,
        }

        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json=body,
            )

        if response.status_code != 200:
            return (
                f"[ERRO HuggingFace] HTTP {response.status_code}: "
                f"{response.text[:200]}"
            )

        data = response.json()

        # Formato esperado: {"choices": [{"message": {"content": "..."}}]}
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            # fallback útil pra debug se o formato mudar
            return str(data)
