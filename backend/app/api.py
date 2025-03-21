"""
API Routes Module

This module defines the FastAPI routes for the personality test application.
It imports service functions (start_test, submit_response, continue_test, get_results,
select_interests) and uses Pydantic models (UserResponse, InterestSelection) for request validation.
"""

from fastapi import APIRouter
from services import start_test, submit_response, continue_test, get_results, select_interests, store_feedback
from models import UserResponse, InterestSelection, FeedbackResponse
from pydantic import BaseModel

router = APIRouter()


class SessionRequest(BaseModel):
    """
    Request model for session-related endpoints.

    Attributes:
        session_id (str): The unique identifier for the test session.
    """
    session_id: str


@router.post("/start-test/")
async def start():
    """
    Initiates a new test session.

    Returns:
        dict: A dictionary containing the new session ID and the first question.
    """
    return start_test()


@router.post("/select-interests/")
async def select_interests_api(selection: InterestSelection):
    """
    Saves the user's selected interests and generates the next question.

    Args:
        selection (InterestSelection): The user's selected interests and session ID.

    Returns:
        dict: A dictionary with a success message and the next question, or an error message.
    """
    return select_interests(selection)


@router.post("/submit-response/")
async def submit(response: UserResponse):
    """
    Submits a user's answer for a given question and generates the next question.

    Args:
        response (UserResponse): The user's response containing session ID, question ID, and answer.

    Returns:
        dict: A dictionary containing the next question or an error message.
    """
    return submit_response(response)


@router.post("/continue-test/")
async def continue_quiz(request: SessionRequest):
    """
    Resumes a paused test session by unpausing the session and generating the next question.

    Args:
        request (SessionRequest): A request containing the session ID.

    Returns:
        dict: A dictionary with the next question or an error message.
    """
    return continue_test(request.session_id)


@router.post("/get-results/")
async def results(request: SessionRequest):
    """
    Finalizes the test session and retrieves the final results, including the determined archetype.

    Args:
        request (SessionRequest): A request containing the session ID.

    Returns:
        dict: A dictionary containing the final test results, including scores, suggested archetype,
              and a detailed archetype description.
    """
    return get_results(request.session_id)


@router.post("/collect-feedback")
async def feedback(request: FeedbackResponse):
    """Collects the feedback and rating 1-5 given by the user session

    Args:
        request (SessionRequest): A request containing feedback, session_id, timestamp, archetype
    """

    return store_feedback(request.session_id, request.rating, request.timestamp, request.archetype)
