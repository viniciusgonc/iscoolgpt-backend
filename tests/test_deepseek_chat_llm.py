import os
import pytest
from app.llms.deepseek_chat_llm import DeepSeekChatLLM


@pytest.mark.asyncio
async def test_deepseek_chat_smoke():

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY não está definida.")

    llm = DeepSeekChatLLM()

    question = "Explique rapidamente o que é Amazon EC2."
    answer = await llm.ask(question)

    print("RESPOSTA DEEPSEEK:", answer)

    assert isinstance(answer, str)
    assert len(answer.strip()) > 0
