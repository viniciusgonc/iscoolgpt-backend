from pydantic import BaseModel
from typing import List


class ProviderAnswer(BaseModel):
    provider: str
    answer: str


class AggregatedResponse(BaseModel):
    final_answer: str
    answers: List[ProviderAnswer]


class AskRequest(BaseModel):
    question: str
    providers: List[str]
