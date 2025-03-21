"""Module defines PyDantic Models
    """
from typing import List
from pydantic import BaseModel


class UserResponse(BaseModel):
    """
    Model representing a user's response to a personality test question.

    Attributes:
        session_id (str): The unique identifier for the test session.
        question_id (str): The identifier of the question being answered.
        answer (str): The user's answer, typically representing an option key or freeform text.
    """
    session_id: str
    question_id: str
    answer: str


class InterestSelection(BaseModel):
    """
    Model representing a user's interest selection at the start of the test.

    Attributes:
        session_id (str): The unique identifier for the test session.
        interests (List[str]): A list of interests selected or entered by the user.
    """
    session_id: str
    interests: List[str]


class FeedbackResponse(BaseModel):
    """Model representing user provided feedback at the end of the test

    Attributes:
        session_id (str): The unique identifier for the test session.
        rating (int): The rating provided by the user.
        timestamp (float): The timestamp the rating was provided.
        archetype (str): The archetype of the user who provided rating.
    """
    session_id: str
    rating: int
    timestamp: float
    archetype: str
