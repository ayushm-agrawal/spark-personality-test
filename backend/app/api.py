"""
API Routes Module

This module defines the FastAPI routes for the personality test application.
It imports service functions and uses Pydantic models for request validation.
Supports three assessment modes: hackathon, overall, and interest.
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, BackgroundTasks
from services import (
    start_test, submit_response, continue_test, get_results,
    select_interests, store_feedback, _init_prefetcher_if_needed
)
from prefetch import get_prefetcher, init_prefetcher
from models import UserResponse, InterestSelection, FeedbackResponse
from pydantic import BaseModel

# Logger for API operations
api_logger = logging.getLogger("api")
api_logger.setLevel(logging.INFO)

# Import from new modular configurations
from modes import get_all_modes, get_mode_config, get_interest_requirements
from archetypes import ARCHETYPES, ARCHETYPE_COMPATIBILITY, get_archetype_for_display
from interests import get_interest_categories, get_life_areas
from prompts import get_all_life_contexts, LIFE_CONTEXT_CATEGORIES

router = APIRouter()


async def trigger_prefetch(session_id: str, question_id: str, predictions: dict):
    """
    Trigger background prefetching for likely next answers.

    This runs in the background after returning a question to the user,
    pre-generating questions for the most likely answers.
    """
    from services import generate_prefetch_question

    prefetcher = get_prefetcher()
    if prefetcher is None:
        # Initialize prefetcher on first use
        init_prefetcher(generate_prefetch_question)
        prefetcher = get_prefetcher()

    if prefetcher and predictions:
        api_logger.info(f"[API] Triggering prefetch for session {session_id[:8]}...")
        await prefetcher.start_prefetch(
            session_id=session_id,
            current_question_id=question_id,
            predictions=predictions
        )


class SessionRequest(BaseModel):
    """
    Request model for session-related endpoints.

    Attributes:
        session_id (str): The unique identifier for the test session.
    """
    session_id: str


class StartTestRequest(BaseModel):
    """
    Request model for starting a new test session.

    Attributes:
        mode (str): The assessment mode - 'hackathon', 'overall', or 'interest'.
                    Defaults to 'overall'.
    """
    mode: Optional[str] = "overall"


@router.get("/assessment-modes/")
async def get_assessment_modes():
    """
    Returns available assessment modes and their configurations.

    Returns:
        dict: A dictionary containing all available assessment modes with
              display names, descriptions, question counts, and interest requirements.
    """
    return {"modes": get_all_modes()}


@router.get("/interest-categories/")
async def get_interests():
    """
    Returns all interest categories for the deep_dive assessment mode.
    (Legacy endpoint - consider using /life-contexts/ instead)

    Returns:
        dict: A dictionary containing interest categories with icons, colors, and examples.
    """
    return {
        "categories": get_interest_categories(),
        "life_areas": get_life_areas()
    }


@router.get("/life-contexts/")
async def get_life_contexts():
    """
    Returns life context categories for the deep_dive assessment mode.

    Life contexts are areas of life where personality shows up differently:
    - Work & Career
    - Creative Projects
    - Learning & Growth
    - Relationships & Social
    - Challenges & Adversity
    - Personal Time & Energy

    Returns:
        dict: A dictionary containing life context categories with labels, descriptions, and icons.
    """
    return {
        "contexts": get_all_life_contexts(),
        "selection_config": {
            "min": 2,
            "max": 4,
            "title": "What should we explore?",
            "subtitle": "Your archetype will reflect how your personality shows up in these areas. Pick 2-4."
        }
    }


@router.get("/archetypes/")
async def get_archetypes():
    """
    Returns all archetype definitions for display.

    Returns:
        dict: A dictionary containing all archetypes with their profiles.
    """
    archetypes = {}
    for name in ARCHETYPES.keys():
        archetypes[name] = get_archetype_for_display(name)
    return {"archetypes": archetypes}


@router.get("/archetype-compatibility/")
async def get_archetype_compatibility():
    """
    Returns the archetype compatibility mapping.

    Returns:
        dict: A dictionary containing compatibility information for all archetypes.
    """
    return {"compatibility": ARCHETYPE_COMPATIBILITY}


@router.post("/start-test/")
async def start(request: Optional[StartTestRequest] = None, background_tasks: BackgroundTasks = None):
    """
    Initiates a new test session with the specified assessment mode.

    Args:
        request (StartTestRequest): Optional request containing the mode.
            - 'hackathon': Quick 6-question assessment for team collaboration
            - 'overall': Full 10-question personality profile (default)
            - 'deep_dive': Deep-dive into selected life context areas
            - 'interest': (Legacy alias for deep_dive)

    Returns:
        dict: A dictionary containing:
            - session_id: Unique session identifier
            - mode: The selected assessment mode
            - mode_config: Mode configuration (display name, question count, etc.)
            - ui_flow: Instructions for frontend (show interests or proceed to questions)
            - next_question: First question (if skipping interest selection)
            - interest_config: Interest/context selection config (if needed)
    """
    mode = request.mode if request else "overall"
    # Normalize legacy mode name
    if mode == "interest":
        mode = "deep_dive"

    result = start_test(mode=mode)

    # If first question was returned (hackathon mode), trigger prefetch
    if background_tasks and "next_question" in result:
        next_q = result["next_question"]
        predictions = next_q.pop("_predicted_next", None)

        if predictions and predictions.get("probabilities"):
            question_id = next_q.get("id", "")
            probs = predictions.get("probabilities", {})
            api_logger.info(f"[API] First question - scheduling prefetch: {probs}")

            background_tasks.add_task(
                trigger_prefetch,
                result["session_id"],
                question_id,
                probs
            )

    return result


@router.post("/select-interests/")
async def select_interests_api(selection: InterestSelection, background_tasks: BackgroundTasks):
    """
    Saves the user's selected interests and generates the next question.

    Args:
        selection (InterestSelection): The user's selected interests and session ID.
        background_tasks: FastAPI BackgroundTasks for async prefetching.

    Returns:
        dict: A dictionary with a success message and the next question, or an error message.
    """
    result = select_interests(selection)

    # If question was returned, trigger prefetch
    if "next_question" in result:
        next_q = result["next_question"]
        predictions = next_q.pop("_predicted_next", None)

        if predictions and predictions.get("probabilities"):
            question_id = next_q.get("id", "")
            probs = predictions.get("probabilities", {})
            api_logger.info(f"[API] After interests - scheduling prefetch: {probs}")

            background_tasks.add_task(
                trigger_prefetch,
                selection.session_id,
                question_id,
                probs
            )

    return result


@router.post("/submit-response/")
async def submit(response: UserResponse, background_tasks: BackgroundTasks):
    """
    Submits a user's answer for a given question and generates the next question.

    Args:
        response (UserResponse): The user's response containing session ID, question ID, and answer.
        background_tasks: FastAPI BackgroundTasks for async prefetching.

    Returns:
        dict: A dictionary containing the next question or an error message.
    """
    import time
    start_time = time.time()

    result = submit_response(response)
    elapsed = time.time() - start_time
    api_logger.info(f"[API] Question generated in {elapsed:.2f}s")

    # If we got a next question with predictions, trigger prefetching
    if "next_question" in result:
        next_q = result["next_question"]
        predictions = next_q.pop("_predicted_next", None)

        if predictions and predictions.get("probabilities"):
            question_id = next_q.get("id", "")
            probs = predictions.get("probabilities", {})
            api_logger.info(f"[API] Scheduling background prefetch with predictions: {probs}")

            # Schedule prefetch to run in background after response is sent
            background_tasks.add_task(
                trigger_prefetch,
                response.session_id,
                question_id,
                probs
            )

    return result


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


@router.get("/prefetch-stats/")
async def prefetch_stats():
    """
    Returns statistics about the question prefetching system.

    This endpoint is useful for monitoring prefetch performance and cache hit rates.

    Returns:
        dict: A dictionary containing:
            - active_sessions: Number of sessions with prefetched questions
            - total_prefetched: Total number of prefetched questions in memory
            - pending_tasks: Number of prefetch tasks currently running
            - enabled: Whether the prefetcher is initialized
    """
    prefetcher = get_prefetcher()
    if prefetcher is None:
        return {
            "enabled": False,
            "message": "Prefetcher not initialized. Will be initialized on first question generation."
        }
    stats = prefetcher.get_stats()
    stats["enabled"] = True
    return stats
