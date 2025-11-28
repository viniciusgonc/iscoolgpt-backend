# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import QuestionRequest, AggregatedResponse
from app.aggregator import aggregate_answers

app = FastAPI(
    title="IsCoolGPT - Multi LLM API",
    version="1.0.0",
    description="API que consulta múltiplas LLMs e gera uma resposta final agregada",
)

# ---------------------------------------------------------
# 🚀 CORS liberado para rodar o front local e em produção
# ---------------------------------------------------------
origins = [
    "http://localhost:5173",   # front local com Vite
    "https://localhost:5173",
    "http://frontend-iscoolgpt.s3-website-us-east-1.amazonaws.com/"  # (caso rode com https local)
    
    # depois você adiciona o domínio final, exemplo:
    # "https://app.iscoolgpt.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Rotas
# ---------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AggregatedResponse)
async def ask(payload: QuestionRequest):
    # processa tudo normalmente
    result = await aggregate_answers(payload.question, payload.providers)
    return result
