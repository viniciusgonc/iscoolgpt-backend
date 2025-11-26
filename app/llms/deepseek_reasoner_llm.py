# app/llms/deepseek_reasoner_llm.py

import os
import httpx
from app.llm_base import LLMClient


class DeepSeekReasonerLLM(LLMClient):
    """
    Modelo para síntese entre LLMs (Gemini + HuggingFace).
    Modelo recomendado: deepseek-r1
    """

    def __init__(self, model_name: str = None):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise RuntimeError("DEEPSEEK_API_KEY não foi encontrada no ambiente.")

        self.model_name = model_name or os.getenv(
            "DEEPSEEK_REASONER_MODEL", "deepseek-r1"
        )

        self.url = "https://api.deepseek.com/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_synthesis_prompt(self, question: str, gemini: str, hf: str) -> str:
        return f"""
Você é o IsCoolGPT-Sintetizador, especializado em combinar respostas de múltiplos modelos de IA
(Gemini, HuggingFace, etc.) e produzir a versão FINAL mais correta, clara e completa.

Sua tarefa:

1. Leia a pergunta original do usuário.
2. Leia duas respostas fornecidas por outros modelos.
3. Compare as respostas:
   - identifique pontos corretos,
   - elimine contradições,
   - corrija informações imprecisas,
   - melhore explicações fracas.

4. Produza UMA ÚNICA RESPOSTA FINAL:
   - totalmente correta,
   - clara e didática,
   - SEM repetir trechos desnecessários,
   - SEM mencionar os outros modelos,
   - no estilo do IsCoolGPT (explicativo, organizado, educacional).

Regras extras:
- Responda SEMPRE em português brasileiro.
- Use exemplos e analogias somente quando fizer sentido.
- Se houver divergências entre as respostas, escolha a correta.
- Não invente informações.

PERGUNTA DO USUÁRIO:
{question}

RESPOSTA 1 (Gemini):
{gemini}

RESPOSTA 2 (HuggingFace):
{hf}

RESPOSTA FINAL DO ASSISTENTE:
""".strip()

    async def synthesize(self, question: str, gemini: str, hf: str) -> str:
        prompt = self._build_synthesis_prompt(question, gemini, hf)

        body = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        async with httpx.AsyncClient(timeout=50) as client:
            response = await client.post(self.url, headers=self.headers, json=body)

        if response.status_code != 200:
            return f"[ERRO DeepSeek-Reasoner] {response.status_code}: {response.text[:200]}"

        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return str(data)
