import pytest
from unittest.mock import AsyncMock, patch

from app.aggregator import aggregate_answers


@pytest.mark.asyncio
async def test_single_gemini():
    """
    Testa o fluxo simples: providers=["gemini"].
    O GeminiLLM.ask() é mockado para não chamar a API real.
    """
    with patch("app.llms.gemini_llm.GeminiLLM.ask", new_callable=AsyncMock) as mock_ask:
        mock_ask.return_value = "Resposta Gemini OK"

        result = await aggregate_answers("O que é EC2?", ["gemini"])

        assert result.final_answer.startswith("GEMINI:")
        assert len(result.answers) == 1
        assert result.answers[0].provider == "gemini"
        assert result.answers[0].answer == "Resposta Gemini OK"


@pytest.mark.asyncio
async def test_single_huggingface():
    """
    Testa fluxo: providers=["huggingface"].
    """
    with patch("app.llms.huggingface_llm.HuggingFaceLLM.ask", new_callable=AsyncMock) as mock_hf:
        mock_hf.return_value = "Resposta HF OK"

        result = await aggregate_answers("O que é VPC?", ["huggingface"])

        assert result.final_answer.startswith("HUGGINGFACE:")
        assert result.answers[0].provider == "huggingface"
        assert result.answers[0].answer == "Resposta HF OK"


@pytest.mark.asyncio
async def test_fusion_mode():
    """
    Testa o modo fusion, garantindo:
    - Gemini → resposta mockada
    - HF → resposta mockada
    - Reasoner → resposta final mockada
    """
    with patch("app.llms.gemini_llm.GeminiLLM.ask", new_callable=AsyncMock) as mock_gemini:
        with patch("app.llms.huggingface_llm.HuggingFaceLLM.ask", new_callable=AsyncMock) as mock_hf:
            with patch("app.llms.gemini_reasoner_llm.GeminiReasonerLLM.synthesize", new_callable=AsyncMock) as mock_reasoner:

                mock_gemini.return_value = "Resp Gemini"
                mock_hf.return_value = "Resp HF"
                mock_reasoner.return_value = "Resp Final Fusion"

                result = await aggregate_answers("Explique EC2", ["fusion"])

                assert result.final_answer == "Resp Final Fusion"

                # Checa lista "answers"
                assert len(result.answers) == 2
                providers = {a.provider for a in result.answers}
                assert providers == {"gemini", "huggingface"}

                # Respostas individuais
                assert result.answers[0].answer in ["Resp Gemini", "Resp HF"]
                assert result.answers[1].answer in ["Resp Gemini", "Resp HF"]
