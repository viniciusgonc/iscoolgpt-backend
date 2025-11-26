import os
import asyncio

import pytest

from app.llms.gemini_llm import GeminiLLM


def test_gemini_llm_requires_api_key(monkeypatch):
    """
    Garante que, se a variável de ambiente GEMINI_API_KEY não estiver definida,
    o construtor do GeminiLLM lança um RuntimeError explicando o problema.
    """
    # Remove a variável, se existir
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError) as exc:
        GeminiLLM()

    # Mensagem deve mencionar claramente a variável ausente
    assert "GEMINI_API_KEY" in str(exc.value)


def test_gemini_llm_ask_uses_prompt_engineering(monkeypatch):
    """
    Testa o método ask() sem chamar a API real do Gemini.

    Estratégia:
    - Define uma GEMINI_API_KEY fake, só para passar no __init__.
    - Cria uma instância do GeminiLLM.
    - Substitui o _model interno por um DummyModel que não faz chamada externa.
    - Chama ask() com uma pergunta de Cloud.
    - Verifica:
        - que a resposta vem do DummyModel (RESPOSTA_FAKE)
        - que o prompt enviado ao modelo inclui:
            - o texto do usuário
            - uma parte das instruções fixas (IsCoolGPT)
    """
    # 1) Chave fake para não explodir no __init__
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")

    # 2) Cria o LLM normalmente
    llm = GeminiLLM()

    # 3) DummyModel substitui a chamada real ao Gemini
    class DummyResponse:
        text = "RESPOSTA_FAKE_DO_GEMINI"

    class DummyModel:
        def __init__(self):
            self.last_prompt = None
            self.last_generation_config = None

        def generate_content(self, prompt, generation_config=None):
            # guarda o que foi passado para ver se o prompt foi montado certo
            self.last_prompt = prompt
            self.last_generation_config = generation_config
            return DummyResponse()

    dummy_model = DummyModel()
    llm._model = dummy_model  # type: ignore[attr-defined]

    # 4) Chama o método assíncrono ask() usando asyncio.run
    user_question = "Explique o que é Amazon EC2."
    answer = asyncio.run(llm.ask(user_question))

    # 5) A resposta deve vir do DummyResponse, não da API real
    assert "RESPOSTA_FAKE_DO_GEMINI" in answer

    # 6) O prompt enviado ao modelo deve conter:
    #    - a pergunta do usuário
    #    - alguma parte das instruções do IsCoolGPT
    assert dummy_model.last_prompt is not None
    assert "IsCoolGPT" in dummy_model.last_prompt
    assert "Cloud Computing" in dummy_model.last_prompt
    assert user_question in dummy_model.last_prompt

    # 7) Só para garantir: a temperatura configurada deve ter sido usada
    assert isinstance(dummy_model.last_generation_config, dict)
    assert "temperature" in dummy_model.last_generation_config
