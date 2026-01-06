from pydantic import BaseModel
from typing import List, Optional

class QueryPayload(BaseModel):
    question: str
    top_k: int = 3

class FillFormPayload(BaseModel):
    fields: List[str]
    top_k: int = 4
