import os
import pytest

from app.llms.huggingface_llm import HuggingFaceLLM


@pytest.mark.asyncio
async def test_huggingface_smoke():
    """
    Teste simples para verificar se:
    - a HUGGINGFACE_API_KEY está definida
    - o modelo responde sem erro
    """
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not api_key:
        pytest.skip("HUGGINGFACE_API_KEY não está definida no ambiente de teste")

    llm = HuggingFaceLLM()

    question = "Explique em uma frase o que é Amazon EC2."
    answer = await llm.ask(question)

    print("RESPOSTA HF:", answer)

    assert isinstance(answer, str)
    assert len(answer.strip()) > 0
