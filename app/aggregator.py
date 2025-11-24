# app/aggregator.py

import asyncio
from typing import List

from app.schemas import ProviderAnswer, AggregatedResponse
from app.llms.openai_llm import OpenAILLM
from app.llms.huggingface_llm import HuggingFaceLLM
from app.llms.gemini_llm import GeminiLLM

LLM_PROVIDERS = {
    "openai": OpenAILLM(),
    "huggingface": HuggingFaceLLM(),
    "gemini": GeminiLLM(),
}

async def aggregate_answers(question: str, providers: List[str]) -> AggregatedResponse:
    # 1. Filtra apenas providers válidos e cria tasks assíncronas
    tasks = []
    used_providers = []

    for provider_name in providers:
        client = LLM_PROVIDERS.get(provider_name)
        if client is not None:
            used_providers.append(provider_name)
            tasks.append(client.ask(question))

    if not tasks:

        raise ValueError("Nenhum provider válido foi informado")
    
    # 2. Executar todas as chamadas de LLM em paralelo
    answers_raw = await asyncio.gather(*tasks)

    # 3. Montar a lista de ProviderAnswer

    answers: List[ProviderAnswer] = []
    for provider_name, answer_text in zip(used_providers, answers_raw):
        answers.append(
            ProviderAnswer(
                provider=provider_name,
                answer=answer_text,
            )
        )

    # 4. Criar uma resposta final "fake" (por enquanto)

    final_parts = [f"{ans.provider.upper()}: {ans.answer}" for ans in answers]
    final_answer = (
        "Resumo gerado a partir das respostas dos modelos: \n\n"
        + "\n".join(final_parts)
    )

    return AggregatedResponse(
        final_answer=final_answer,
        answers=answers,
    )