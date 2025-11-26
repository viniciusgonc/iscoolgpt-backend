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

        # modelo padrão definido em código (pode sobrescrever via HUGGINGFACE_MODEL)
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
        Prompt enxuto e focado em respostas curtas.
        """
        system_instructions = """
Você é o IsCoolGPT, um assistente especializado em Cloud Computing (AWS, GCP, Azure).

Objetivo:
- Explicar conceitos de forma correta e didática.
- Ajudar em dúvidas sobre arquitetura, redes, segurança, IAM, containers, serverless e observabilidade.
- Dar dicas rápidas de estudo para certificações quando fizer sentido.

Regras de resposta:
- Responda SEMPRE em português brasileiro.
- Seja direto e objetivo.
- Use no máximo 3 parágrafos curtos ou 5 bullet points.
- Foque no essencial para o entendimento.
- Se o usuário pedir código, comandos de CLI ou YAML/Terraform, explique rapidamente o que fazem e em qual contexto são usados.
- Se a pergunta estiver confusa ou incompleta, diga brevemente o que está faltando.
""".strip()

        return [
            {"role": "system", "content": system_instructions},
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
            "max_tokens": 256,   # << respostas mais curtas
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
