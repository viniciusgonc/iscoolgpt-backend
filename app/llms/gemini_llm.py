# app/llms/gemini_llm.py

import os
from typing import Optional

import anyio
import google.generativeai as genai

from app.llm_base import LLMClient

class GeminiLLM(LLMClient):
    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        name: Optional[str] = None,
    ) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não encontrada nas variáveis de ambiente. "
                "Defina essa variável no ECS Task Definition ou no ambiente local."
            )
        
        genai.configure(api_key=api_key)

        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature

        self._model = genai.GenerativeModel(self.model_name)

        self.name = name or f"gemini-{self.model_name}"
    
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
"""
        return full_prompt
    
    async def ask(self, prompt: str) -> str:

        final_prompt = self._build_prompt(prompt)

        def _call_gemini() -> str:
            response = self._model.generate_content(
                final_prompt,
                generation_config={"temperature": self.temperature},
            )

            text = getattr(response, "text", None)
            if text:
                return text
            
            try:
                candidates = getattr(response, "candidates", []) or []
                if candidates:
                    parts = getattr(candidates[0], "content", None).parts
                    if parts:
                        return "".join(p.text for p in parts if getattr(p, "text", None))
            except Exception:
                pass

            return "Não foi possível extair o texto da resposta do Gemini"
        
        answer = await anyio.to_thread.run_sync(_call_gemini)
        return answer