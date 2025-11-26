# app/aggregator.py

import asyncio
import logging
from typing import List, Dict, Callable

from app.schemas import ProviderAnswer, AggregatedResponse
from app.llm_base import LLMClient
from app.llms.openai_llm import OpenAILLM
from app.llms.huggingface_llm import HuggingFaceLLM
from app.llms.gemini_llm import GeminiLLM

logger = logging.getLogger("iscoolgpt.aggregator")

#
# Em vez de instanciar os clients na importação do módulo,
# guardamos "fábricas" (callables que criam instâncias).
#
LLM_FACTORIES: Dict[str, Callable[[], LLMClient]] = {
    "openai": OpenAILLM,
    "huggingface": HuggingFaceLLM,
    "gemini": GeminiLLM,
}


async def aggregate_answers(question: str, providers: List[str]) -> AggregatedResponse:
    """
    Recebe a pergunta e a lista de providers (ex.: ["gemini", "openai"])
    e faz as chamadas em paralelo.

    - Inicializa apenas os providers solicitados.
    - Usa asyncio.gather(return_exceptions=True) para capturar erros
      de cada LLM individualmente.
    - Loga qualquer erro de inicialização ou chamada de provider.
    - Retorna um AggregatedResponse contendo as respostas (ou erros)
      de cada provider.
    """
    tasks = []
    used_providers: List[str] = []

    # 1. Criar instâncias só dos providers solicitados e válidos
    for provider_name in providers:
        factory = LLM_FACTORIES.get(provider_name)
        if factory is None:
            logger.warning(f"[Aggregator] Provider desconhecido solicitado: {provider_name}")
            continue

        try:
            client = factory()
        except Exception as e:
            logger.exception(
                f"[Aggregator] Erro ao inicializar provider '{provider_name}': {e}"
            )
            # não adiciona esse provider à lista; segue para o próximo
            continue

        used_providers.append(provider_name)
        tasks.append(client.ask(question))

    if not tasks:
        # Aqui ainda é útil manter o erro, para o endpoint traduzir em 400
        raise ValueError("Nenhum provider válido foi informado")

    # 2. Executar todas as chamadas de LLM em paralelo.
    #    Se algum provider lançar exceção, ela é capturada na lista de resultados.
    answers_raw = await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Montar a lista de ProviderAnswer (incluindo erros por provider)
    answers: List[ProviderAnswer] = []

    for provider_name, result in zip(used_providers, answers_raw):
        if isinstance(result, Exception):
            # Loga o erro completo para aparecer nos logs (CloudWatch)
            logger.exception(
                f"[Aggregator] Erro ao chamar provider '{provider_name}': {result}"
            )
            answer_text = (
                f"[ERRO no provider '{provider_name}'] "
                f"{type(result).__name__}: {result}"
            )
        else:
            answer_text = result

        answers.append(
            ProviderAnswer(
                provider=provider_name,
                answer=answer_text,
            )
        )

    # 4. Criar a resposta final a partir do que veio de cada provider
    final_parts = [f"{ans.provider.upper()}: {ans.answer}" for ans in answers]
    final_answer = (
        "Resumo gerado a partir das respostas dos modelos (incluindo erros, se houver):\n\n"
        + "\n".join(final_parts)
    )

    return AggregatedResponse(
        final_answer=final_answer,
        answers=answers,
    )
