"""
Authentication helpers.

Provides Firebase ID token verification for FastAPI routes.
Profile-mutation routes use `verify_profile_owner` to enforce that the
authenticated user owns the profile they are modifying.
"""

from typing import Optional

from fastapi import Header, HTTPException
from firebase_admin import auth as firebase_auth

from firebase import db


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def verify_id_token(authorization: Optional[str] = Header(None)) -> str:
    """FastAPI dependency: verify Firebase ID token, return the user's uid."""
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    uid = decoded.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Token missing uid claim")
    return uid


def verify_profile_owner(profile_id: str, uid: str) -> dict:
    """
    Confirm the authenticated uid owns the given profile.

    Returns the profile dict on success; raises HTTPException otherwise.
    """
    if not profile_id:
        raise HTTPException(status_code=400, detail="profile_id required")
    profile_doc = db.collection("user_profiles").document(profile_id).get()
    if not profile_doc.exists:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_doc.to_dict()
    owner_uid = profile.get("user_id")
    if not owner_uid:
        raise HTTPException(
            status_code=403,
            detail="Profile is not linked to an account; sign in to claim it before modifying.",
        )
    if owner_uid != uid:
        raise HTTPException(status_code=403, detail="Not authorized to modify this profile")
    return profile
