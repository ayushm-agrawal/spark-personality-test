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
    select_interests, store_feedback, _init_prefetcher_if_needed,
    get_extension_opportunity, accept_extension,
    generate_device_fingerprint, get_or_create_profile, update_profile_after_test
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
        mode (str): The assessment mode - 'hackathon', 'overall', or 'deep_dive'.
                    Defaults to 'overall'.
        interest (str): Optional single interest for deep_dive mode (e.g., "Work", "Fitness").
    """
    mode: Optional[str] = "overall"
    interest: Optional[str] = None


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
    interest = request.interest if request else None
    # Normalize legacy mode name
    if mode == "interest":
        mode = "deep_dive"

    result = start_test(mode=mode, interest=interest)

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


@router.post("/check-extension/")
async def check_extension(request: SessionRequest):
    """
    Check if the test should offer an extension for more accurate results.

    Called after the last standard question to determine if the user should be
    offered 2 additional clarifying questions.

    Args:
        request (SessionRequest): A request containing the session ID.

    Returns:
        dict: A dictionary containing:
            - offer_extension: Boolean indicating if extension should be offered
            - suggested_questions: Number of additional questions (always 2)
            - focus_traits: List of traits that need more signal
            - message: User-facing explanation
    """
    return get_extension_opportunity(request.session_id)


@router.post("/accept-extension/")
async def accept_extension_api(request: SessionRequest, background_tasks: BackgroundTasks):
    """
    Accept the test extension and generate the first clarifying question.

    This adds 2 more questions to the test, focused on ambiguous traits.

    Args:
        request (SessionRequest): A request containing the session ID.
        background_tasks: FastAPI BackgroundTasks for async prefetching.

    Returns:
        dict: A dictionary containing:
            - extension_accepted: True if successful
            - new_question_count: Updated total question count
            - focus_traits: Traits being clarified
            - next_question: First clarifying question
    """
    result = accept_extension(request.session_id)

    # If question was returned, trigger prefetch
    if "next_question" in result and result["next_question"]:
        next_q = result["next_question"]
        predictions = next_q.pop("_predicted_next", None) if isinstance(next_q, dict) else None

        if predictions and predictions.get("probabilities"):
            question_id = next_q.get("id", "")
            probs = predictions.get("probabilities", {})
            api_logger.info(f"[API] Extension question - scheduling prefetch: {probs}")

            background_tasks.add_task(
                trigger_prefetch,
                request.session_id,
                question_id,
                probs
            )

    return result


class ProfileRequest(BaseModel):
    """
    Request model for profile-related endpoints.

    Attributes:
        user_id: Firebase auth UID (optional)
        device_fingerprint: Device fingerprint hash (optional)
    """
    user_id: Optional[str] = None
    device_fingerprint: Optional[str] = None


@router.post("/get-profile/")
async def get_profile(request: ProfileRequest):
    """
    Get or create a user profile.

    Uses user_id (Firebase auth) or device_fingerprint to identify returning users.
    If both are provided and a fingerprint-based profile exists without a user_id,
    the user_id will be linked (account linking).

    Args:
        request (ProfileRequest): Contains user_id and/or device_fingerprint.

    Returns:
        dict: User profile with cumulative scores, test history, and current archetype.
    """
    return get_or_create_profile(
        user_id=request.user_id,
        device_fingerprint=request.device_fingerprint
    )


class UpdateProfileRequest(BaseModel):
    """Request model for updating profile after test."""
    profile_id: str
    session_id: str


@router.post("/update-profile/")
async def update_profile(request: UpdateProfileRequest):
    """
    Update user profile after completing a test (Phase 2.5 weighted approach).

    This should be called after finalize_test to update the user's
    mode-specific profiles with weighted scores. Tests with suspicious
    patterns are down-weighted or excluded.

    Args:
        request (UpdateProfileRequest): Contains profile_id and session_id.

    Returns:
        dict: Updated profile data including holistic archetype info.
    """
    from firebase import db

    # Get session data
    session_doc = db.collection("sessions").document(request.session_id)
    session = session_doc.get().to_dict()
    if not session:
        return {"error": "Invalid session"}

    # Get results from session if finalized
    results = session.get("results", {})
    if not results:
        return {"error": "Test not finalized yet"}

    # Extract confidence and suspicion data for weighted profile update
    confidence = results.get("confidence", {"confidence_pct": 50, "tier": "emerging"})
    suspicious_patterns = results.get("suspicious_patterns", {"suspicious": False, "flags": []})

    # Update profile with weighted scores
    updated_profile = update_profile_after_test(
        request.profile_id,
        session,
        results,
        confidence,
        suspicious_patterns
    )

    # Return holistic data for frontend
    holistic = updated_profile.get("_holistic")
    return {
        "profile_id": request.profile_id,
        "quality_weight": updated_profile.get("_quality_weight"),
        "included_in_profile": updated_profile.get("_included_in_profile"),
        "holistic": {
            "archetype": holistic.get("current_archetype") if holistic else None,
            "confidence": holistic.get("confidence") if holistic else None,
            "stability": holistic.get("stability") if holistic else "new",
            "tests_included": holistic.get("tests_included") if holistic else 0,
            "tests_excluded": holistic.get("tests_excluded") if holistic else 0
        } if holistic else None
    }


@router.get("/profile/{profile_id}")
async def get_profile_view(profile_id: str):
    """
    Get a comprehensive view of a user's profile across all modes.

    Returns mode-specific profiles, deep dive profiles, and test history summary.
    This endpoint enables a Profile page showing all archetypes across modes.

    Args:
        profile_id: Firestore profile document ID

    Returns:
        dict: Profile overview with mode_profiles, deep_dive_profiles, and stats
    """
    from firebase import db

    profile_doc = db.collection("user_profiles").document(profile_id)
    profile = profile_doc.get().to_dict()

    if not profile:
        return {"error": "Profile not found"}

    # Build mode profiles summary
    mode_profiles_summary = {}
    for mode, data in profile.get("mode_profiles", {}).items():
        mode_profiles_summary[mode] = {
            "current_archetype": data.get("current_archetype"),
            "confidence": data.get("confidence"),
            "stability": data.get("stability"),
            "tests_included": data.get("tests_included"),
            "tests_excluded": data.get("tests_excluded")
        }

    # Build deep dive profiles summary
    deep_dive_summary = {}
    for interest, data in profile.get("deep_dive_profiles", {}).items():
        deep_dive_summary[interest] = {
            "current_archetype": data.get("current_archetype"),
            "confidence": data.get("confidence"),
            "stability": data.get("stability"),
            "tests_included": data.get("tests_included")
        }

    # Calculate totals
    test_history = profile.get("test_history", [])
    total_tests = len(test_history)
    included_tests = sum(1 for t in test_history if t.get("included_in_profile", True))
    excluded_tests = total_tests - included_tests

    return {
        "profile_id": profile_id,
        "mode_profiles": mode_profiles_summary,
        "deep_dive_profiles": deep_dive_summary,
        "total_tests": total_tests,
        "tests_included": included_tests,
        "tests_excluded": excluded_tests,
        "member_since": profile.get("created_at"),
        "last_updated": profile.get("updated_at"),
        "current_archetype": profile.get("current_archetype"),  # Most recent
        "username": profile.get("username"),
        "display_name": profile.get("display_name")
    }


# ============================================================================
# USERNAME ENDPOINTS
# ============================================================================

class CheckUsernameRequest(BaseModel):
    username: str


class SetUsernameRequest(BaseModel):
    profile_id: str
    username: str
    display_name: Optional[str] = None


@router.post("/check-username/")
async def check_username(request: CheckUsernameRequest):
    """
    Check if a username is available.

    Args:
        request: CheckUsernameRequest with username to check

    Returns:
        dict: {"available": bool, "username": str}
    """
    from services import is_username_available

    username = request.username.lower().strip()
    available = is_username_available(username)

    return {
        "available": available,
        "username": username
    }


@router.post("/set-username/")
async def set_username_endpoint(request: SetUsernameRequest):
    """
    Set or update username for a profile.

    Args:
        request: SetUsernameRequest with profile_id, username, and optional display_name

    Returns:
        dict: {"success": bool, "username": str} or {"success": false, "error": str}
    """
    from services import set_username

    result = set_username(
        profile_id=request.profile_id,
        username=request.username,
        display_name=request.display_name
    )

    return result


@router.post("/generate-username/")
async def generate_username_endpoint(request: dict):
    """
    Generate a unique username from a display name.

    Args:
        request: {"display_name": str}

    Returns:
        dict: {"username": str}
    """
    from services import generate_unique_username

    display_name = request.get("display_name", "")
    username = generate_unique_username(display_name)

    return {"username": username}


@router.get("/u/{username}")
async def get_public_profile(username: str):
    """
    Get a public profile by username.

    Args:
        username: The username to look up

    Returns:
        dict: Public profile data or {"error": "Profile not found"}
    """
    from services import get_profile_by_username

    profile = get_profile_by_username(username)

    if not profile:
        return {"error": "Profile not found"}

    return profile
