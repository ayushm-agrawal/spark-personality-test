from pydantic import BaseModel
from typing import List


class UserResponse(BaseModel):
    session_id: str
    question_id: str
    answer: str


class InterestSelection(BaseModel):
    session_id: str
    interests: List[str]
