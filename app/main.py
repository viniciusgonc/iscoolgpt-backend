# app/main.py

from fastapi import FastAPI, HTTPException
from app.schemas import QuestionRequest, AggregatedResponse
from app.aggregator import aggregate_answers

app = FastAPI(
    title="IsCoolGPT - Multi LLM API",
    description="API que conulta múltiplas LLMs e gera um resposta final agregada",
    version="1.0.0"
)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AggregatedResponse)
async def ask_question(request: QuestionRequest):
    try:
        result = await aggregate_answers(request.question, request.providers)
        return result
    except ValueError as e:
        #caso utuário envia provider inválido
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Erro qualquer inesperado
        raise HTTPException(status_code=500, detail="Erro interno no servidor")
    