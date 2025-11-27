# app/schemas.py

from pydantic import BaseModel
from typing import List


class QuestionRequest(BaseModel):

    question: str
    providers: List[str]


# Alias para compatibilidade com o nome AskRequest
# Se em algum lugar do código alguém importar AskRequest,
# vai funcionar igual.
AskRequest = QuestionRequest


class ProviderAnswer(BaseModel):
    provider: str
    answer: str


class AggregatedResponse(BaseModel):
    final_answer: str
    answers: List[ProviderAnswer]
