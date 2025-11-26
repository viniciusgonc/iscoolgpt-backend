# app/aggregator.py

import asyncio
import logging
from typing import List, Dict, Callable

from app.schemas import ProviderAnswer, AggregatedResponse
from app.llm_base import LLMClient

from app.llms.huggingface_llm import HuggingFaceLLM
from app.llms.gemini_llm import GeminiLLM
from app.llms.deepseek_chat_llm import DeepSeekChatLLM
from app.llms.deepseek_reasoner_llm import DeepSeekReasonerLLM

logger = logging.getLogger("iscoolgpt.aggregator")


# ------------------------------------------------------
# Providers disponíveis para modo SINGLE
# ------------------------------------------------------
LLM_FACTORIES: Dict[str, Callable[[], LLMClient]] = {
    "huggingface": HuggingFaceLLM,
    "gemini": GeminiLLM,
    "deepseek": DeepSeekChatLLM,  # deepseek modo CHAT
}


# ------------------------------------------------------
# Função principal — agora com modo FUSION
# ------------------------------------------------------
async def aggregate_answers(question: str, providers: List[str]) -> AggregatedResponse:
    """
    Agora suporta 4 modos:
      - ["gemini"]
      - ["huggingface"]
      - ["deepseek"]
      - ["fusion"]  → Gemini + HF + DeepSeek-R1 (síntese final)
    """

    # --------------------------------------------------
    # 1. MODO FUSION
    # --------------------------------------------------
    if "fusion" in providers:
        return await _run_fusion_mode(question)

    # --------------------------------------------------
    # 2. MODO SINGLE PROVIDER
    # --------------------------------------------------
    tasks = []
    used_providers: List[str] = []

    for provider_name in providers:
        factory = LLM_FACTORIES.get(provider_name)
        if factory is None:
            logger.warning(f"[Aggregator] Provider desconhecido: {provider_name}")
            continue

        try:
            client = factory()
        except Exception as e:
            logger.exception(f"[Aggregator] Falha ao inicializar {provider_name}: {e}")
            continue

        used_providers.append(provider_name)
        tasks.append(client.ask(question))

    if not tasks:
        raise ValueError("Nenhum provider válido foi informado.")

    # Executa tudo em paralelo
    answers_raw = await asyncio.gather(*tasks, return_exceptions=True)

    answers: List[ProviderAnswer] = []

    for provider_name, result in zip(used_providers, answers_raw):
        if isinstance(result, Exception):
            logger.exception(
                f"[Aggregator] Erro ao chamar provider '{provider_name}': {result}"
            )
            text = f"[ERRO no provider '{provider_name}'] {type(result).__name__}: {result}"
        else:
            text = result

        answers.append(ProviderAnswer(provider=provider_name, answer=text))

    # Final answer simples (sem razão)
    final_answer = "\n".join(
        [f"{ans.provider.upper()}: {ans.answer}" for ans in answers]
    )

    return AggregatedResponse(final_answer=final_answer, answers=answers)


# ------------------------------------------------------
# Função auxiliar do modo FUSION
# ------------------------------------------------------
async def _run_fusion_mode(question: str) -> AggregatedResponse:
    """
    Executa:
      - Gemini
      - HuggingFace
    E depois usa DeepSeek-R1 para sintetizar.
    """

    gemini = GeminiLLM()
    hf = HuggingFaceLLM()
    reasoner = DeepSeekReasonerLLM()

    # 1. Rodar Gemini e HF em paralelo
    gemini_task = gemini.ask(question)
    hf_task = hf.ask(question)

    gemini_resp, hf_resp = await asyncio.gather(
        gemini_task, hf_task, return_exceptions=True
    )

    answers_list: List[ProviderAnswer] = []

    # Gemini
    if isinstance(gemini_resp, Exception):
        logger.exception(f"[Fusion] Erro Gemini: {gemini_resp}")
        g_text = f"[ERRO Gemini] {type(gemini_resp).__name__}: {gemini_resp}"
    else:
        g_text = gemini_resp

    answers_list.append(ProviderAnswer(provider="gemini", answer=g_text))

    # HuggingFace
    if isinstance(hf_resp, Exception):
        logger.exception(f"[Fusion] Erro HF: {hf_resp}")
        h_text = f"[ERRO HF] {type(hf_resp).__name__}: {hf_resp}"
    else:
        h_text = hf_resp

    answers_list.append(ProviderAnswer(provider="huggingface", answer=h_text))

    # 2. Rodar DeepSeek-R1 (síntese)
    try:
        final_answer = await reasoner.synthesize(
            question,
            g_text,
            h_text
        )
    except Exception as e:
        logger.exception(f"[Fusion] Erro no DeepSeek Reasoner: {e}")
        final_answer = (
            "[ERRO DeepSeek Reasoner] "
            f"{type(e).__name__}: {e}"
        )

    # 3. Retornar tudo
    return AggregatedResponse(
        final_answer=final_answer,
        answers=answers_list,
    )
