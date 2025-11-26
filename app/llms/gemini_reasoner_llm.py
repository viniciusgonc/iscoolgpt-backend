# app/llms/gemini_reasoner_llm.py

import os
from typing import Optional
import logging

import anyio
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.llm_base import LLMClient

logger = logging.getLogger(__name__)


class GeminiReasonerLLM(LLMClient):
    """
    Modelo Gemini usado como "funil" (reasoner) para sintetizar
    as respostas.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        name: Optional[str] = None,
    ) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não encontrada nas variáveis de ambiente."
            )

        genai.configure(api_key=api_key)

        # Usa o mesmo modelo que está OK no GeminiLLM
        self.model_name = model_name or "gemini-2.5-flash"
        self.temperature = temperature
        self.name = name or f"gemini-reasoner-{self.model_name}"

        # Desliga filtros de segurança (conteúdo vem de outros LLMs)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
        )

    # ----------------------------------------------------------------------
    # Prompt de síntese mais robusto (sem ficar neurótico com tamanho)
    # ----------------------------------------------------------------------
    def _build_synthesis_prompt(self, question: str, gemini: str, hf: str) -> str:
        return f"""
Você é o IsCoolGPT, um assistente especializado em Cloud Computing (AWS, GCP e Azure),
agindo agora como um sintetizador de respostas.

Você receberá:
- uma pergunta de um aluno;
- duas respostas geradas por outros assistentes.

Sua tarefa é:
1. Ler com atenção a pergunta do aluno.
2. Ler as duas respostas.
3. Identificar o que está correto e útil em cada resposta.
4. Corrigir eventuais erros ou pontos confusos.
5. Organizar as informações em uma única resposta final, clara e didática.

Regras importantes:
- Responda SEMPRE em português brasileiro.
- Explique de forma direta, mas sem ser superficial.
- Foque em ajudar o aluno a entender o conceito de forma prática.
- Use exemplos ou analogias apenas se achar realmente necessário.
- NÃO mencione que está lendo respostas de outros modelos.
- NÃO fale em "Resposta 1", "Resposta 2" ou "outros assistentes".
- Entregue apenas a resposta final, como se fosse você mesmo respondendo ao aluno.

Pergunta do aluno:
{question}

Resposta A:
{gemini}

Resposta B:
{hf}

Agora produza apenas a RESPOSTA FINAL para o aluno:
""".strip()

    # ----------------------------------------------------------------------
    # Síntese final
    # ----------------------------------------------------------------------
    async def synthesize(self, question: str, gemini: str, hf: str) -> str:
        prompt = self._build_synthesis_prompt(question, gemini, hf)

        def _call_gemini() -> str:
            try:
                response = self._model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.temperature,
                        # sem max_output_tokens aqui – deixa o modelo decidir
                    },
                )

                # .text pode lançar ValueError se não houver Part (safety / saída vazia)
                return response.text

            except ValueError:
                # Ex.: finish_reason de safety ou nenhuma parte gerada
                msg = "Erro: o Gemini bloqueou a resposta do reasoner (Safety Filter ou saída vazia)."
                if "response" in locals() and hasattr(response, "prompt_feedback"):
                    logger.warning(
                        f"[GeminiReasoner] Feedback de segurança: {response.prompt_feedback}"
                    )
                return msg

            except Exception as e:
                logger.exception(f"[GeminiReasoner] Erro inesperado: {e}")
                return f"Erro inesperado no Gemini Reasoner: {str(e)}"

        answer = await anyio.to_thread.run_sync(_call_gemini)
        return answer

    async def ask(self, prompt: str) -> str:
        raise NotImplementedError(
            "Use synthesize() para esta classe."
        )
