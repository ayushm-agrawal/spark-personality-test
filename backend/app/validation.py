"""
Input validation utilities for API endpoints.

Provides validation functions for common input types to prevent
invalid data from reaching the service layer.
"""

import re
from typing import Optional, Tuple
from fastapi import HTTPException


# Valid assessment modes
VALID_MODES = {'hackathon', 'overall', 'deep_dive'}

# Session ID constraints
SESSION_ID_MAX_LENGTH = 100
SESSION_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Username constraints
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$|^[a-z0-9]$')

# Interest/string input constraints
MAX_INTEREST_LENGTH = 100
MAX_DISPLAY_NAME_LENGTH = 100


def validate_session_id(session_id: Optional[str]) -> str:
    """
    Validate session ID format.

    Args:
        session_id: The session ID to validate

    Returns:
        The validated session ID (stripped)

    Raises:
        HTTPException: If validation fails
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    session_id = session_id.strip()

    if len(session_id) > SESSION_ID_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Session ID must be at most {SESSION_ID_MAX_LENGTH} characters"
        )

    if not SESSION_ID_PATTERN.match(session_id):
        raise HTTPException(
            status_code=400,
            detail="Session ID must contain only alphanumeric characters, hyphens, and underscores"
        )

    return session_id


def validate_mode(mode: Optional[str]) -> str:
    """
    Validate assessment mode.

    Args:
        mode: The mode to validate

    Returns:
        The validated mode (lowercase)

    Raises:
        HTTPException: If validation fails
    """
    if not mode:
        return "overall"  # Default mode

    mode = mode.strip().lower()

    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Must be one of: {', '.join(sorted(VALID_MODES))}"
        )

    return mode


def validate_interest(interest: Optional[str]) -> Optional[str]:
    """
    Validate interest string for deep_dive mode.

    Args:
        interest: The interest to validate

    Returns:
        The validated interest (stripped) or None

    Raises:
        HTTPException: If validation fails
    """
    if not interest:
        return None

    interest = interest.strip()

    if len(interest) > MAX_INTEREST_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Interest must be at most {MAX_INTEREST_LENGTH} characters"
        )

    # Basic sanitization - remove potentially dangerous characters
    # Allow letters, numbers, spaces, and common punctuation
    if not re.match(r'^[\w\s&,.-]+$', interest, re.UNICODE):
        raise HTTPException(
            status_code=400,
            detail="Interest contains invalid characters"
        )

    return interest


def validate_username(username: str) -> str:
    """
    Validate username format.

    Args:
        username: The username to validate

    Returns:
        The validated username (lowercase)

    Raises:
        HTTPException: If validation fails
    """
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")

    username = username.strip().lower()

    if len(username) < USERNAME_MIN_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Username must be at least {USERNAME_MIN_LENGTH} characters"
        )

    if len(username) > USERNAME_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Username must be at most {USERNAME_MAX_LENGTH} characters"
        )

    if not USERNAME_PATTERN.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must contain only lowercase letters, numbers, hyphens, and underscores, and cannot start or end with a hyphen or underscore"
        )

    return username


def validate_display_name(display_name: Optional[str]) -> Optional[str]:
    """
    Validate display name.

    Args:
        display_name: The display name to validate

    Returns:
        The validated display name (stripped) or None

    Raises:
        HTTPException: If validation fails
    """
    if not display_name:
        return None

    display_name = display_name.strip()

    if len(display_name) > MAX_DISPLAY_NAME_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Display name must be at most {MAX_DISPLAY_NAME_LENGTH} characters"
        )

    return display_name


def validate_profile_id(profile_id: Optional[str]) -> str:
    """
    Validate profile ID format (similar to session ID).

    Args:
        profile_id: The profile ID to validate

    Returns:
        The validated profile ID

    Raises:
        HTTPException: If validation fails
    """
    if not profile_id:
        raise HTTPException(status_code=400, detail="Profile ID is required")

    profile_id = profile_id.strip()

    if len(profile_id) > SESSION_ID_MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Profile ID is too long"
        )

    if not SESSION_ID_PATTERN.match(profile_id):
        raise HTTPException(
            status_code=400,
            detail="Profile ID contains invalid characters"
        )

    return profile_id


def validate_rating(rating: int) -> int:
    """
    Validate feedback rating.

    Args:
        rating: The rating value (0-4)

    Returns:
        The validated rating

    Raises:
        HTTPException: If validation fails
    """
    if not isinstance(rating, int) or rating < 0 or rating > 4:
        raise HTTPException(
            status_code=400,
            detail="Rating must be an integer between 0 and 4"
        )

    return rating


def sanitize_string(value: str, max_length: int = 500) -> str:
    """
    Sanitize a generic string input.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length

    Returns:
        The sanitized string
    """
    if not value:
        return ""

    value = value.strip()

    if len(value) > max_length:
        value = value[:max_length]

    return value


# Patterns that indicate prompt-injection or XSS attempts in LLM-generated
# content. The model should never produce HTML/JS, so the presence of any of
# these is treated as untrusted and stripped from the rendered output.
_LLM_UNSAFE_PATTERNS = [
    re.compile(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*script\b[^>]*/?\s*>", re.IGNORECASE),
    re.compile(r"<\s*iframe\b[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*iframe\b[^>]*/?\s*>", re.IGNORECASE),
    re.compile(r"<\s*object\b[^>]*>.*?<\s*/\s*object\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*embed\b[^>]*/?\s*>", re.IGNORECASE),
    re.compile(r"\son[a-z]+\s*=\s*(['\"]).*?\1", re.IGNORECASE | re.DOTALL),  # onclick=..., onload=...
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:\s*text/html", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
]


def scrub_llm_text(value):
    """
    Strip HTML/JS-injection patterns from an LLM-generated string.

    The model is prompted to return plain text; any script tags, inline event
    handlers, or javascript: URLs that slip through are treated as a prompt
    injection attempt and removed before the text is returned to clients.
    Non-strings pass through unchanged.
    """
    if not isinstance(value, str):
        return value
    cleaned = value
    for pat in _LLM_UNSAFE_PATTERNS:
        cleaned = pat.sub("", cleaned)
    return cleaned


def scrub_llm_question(question: dict) -> dict:
    """
    Recursively scrub every string field of an LLM-generated question dict.

    Applies scrub_llm_text to the question text, each option's text/label,
    and any nested "predicted_next_answer"/metadata strings. Mutates and
    returns the same dict for convenience.
    """
    if not isinstance(question, dict):
        return question

    for key, value in list(question.items()):
        if isinstance(value, str):
            question[key] = scrub_llm_text(value)
        elif isinstance(value, dict):
            scrub_llm_question(value)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str):
                    value[i] = scrub_llm_text(item)
                elif isinstance(item, dict):
                    scrub_llm_question(item)

    return question
