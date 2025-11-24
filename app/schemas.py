# app/schemas.py

from pydantic import BaseModel
from typing import List

class QuestionRequest(BaseModel):
    question: str
    providers: List[str]

class ProviderAnswer(BaseModel):
    provider: str
    answer: str

class AggregatedResponse(BaseModel):
    final_answer: str
    answers: List[ProviderAnswer]
