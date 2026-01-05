"""
Backfill Script: Migrate Historical Assessments to user_profiles

This script migrates historical assessment data from the frontend's
`users/{userId}/assessments` collection to the backend's `user_profiles`
collection, enabling holistic profile features for existing users.

Run this script once after deploying Phase 2.5 features.

Usage:
    python backfill_profiles.py [--dry-run]
"""

import time
import logging
import argparse
from firebase import db
from services import (
    calculate_test_quality_weight,
    update_mode_profile,
    update_deep_dive_profile,
    normalize_interest,
    calculate_stability,
    ARCHETYPES
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default confidence for historical data (no suspicious pattern data available)
DEFAULT_CONFIDENCE_PCT = 60
DEFAULT_QUALITY_WEIGHT = 0.6  # 60% confidence = 0.6 base weight


def get_all_users():
    """Get all users from the users collection."""
    users_ref = db.collection("users")
    return users_ref.stream()


def get_user_assessments(user_id: str):
    """Get all assessments for a user, ordered by completion date."""
    assessments_ref = db.collection("users").document(user_id).collection("assessments")
    query = assessments_ref.order_by("completedAt")
    return query.stream()


def get_or_create_profile(user_id: str, dry_run: bool = False):
    """Get existing profile or create a new one for backfill."""
    profiles_ref = db.collection("user_profiles")

    # Check if profile already exists
    query = profiles_ref.where("user_id", "==", user_id).limit(1)
    docs = list(query.stream())

    if docs:
        profile = docs[0].to_dict()
        profile["_doc_id"] = docs[0].id
        profile["_exists"] = True
        return profile

    # Create new profile structure (don't save yet if dry run)
    new_profile = {
        "user_id": user_id,
        "device_fingerprint": None,
        "created_at": time.time(),
        "updated_at": time.time(),
        "mode_profiles": {},
        "deep_dive_profiles": {},
        "test_history": [],
        "cumulative_scores": {
            "Openness": {"total_points": 0, "total_questions": 0},
            "Conscientiousness": {"total_points": 0, "total_questions": 0},
            "Extraversion": {"total_points": 0, "total_questions": 0},
            "Agreeableness": {"total_points": 0, "total_questions": 0},
            "Emotional_Stability": {"total_points": 0, "total_questions": 0}
        },
        "current_archetype": None,
        "overall_confidence": 0
    }

    new_profile["_exists"] = False
    return new_profile


def process_assessment(profile: dict, assessment: dict, assessment_id: str):
    """Process a single assessment and update the profile."""
    mode = assessment.get("mode", "overall")
    archetype = assessment.get("archetype", {})
    archetype_name = archetype.get("name") if isinstance(archetype, dict) else archetype
    normalized_scores = assessment.get("normalizedScores", {})
    completed_at = assessment.get("completedAt")
    mode_specific = assessment.get("modeSpecific", {})

    # Skip if no archetype determined
    if not archetype_name:
        return False

    # Convert Firestore timestamp if needed
    if hasattr(completed_at, 'timestamp'):
        completed_timestamp = completed_at.timestamp()
    elif completed_at:
        completed_timestamp = completed_at
    else:
        completed_timestamp = time.time()

    # Use default quality weight for historical data (no suspicious pattern data)
    quality_weight = DEFAULT_QUALITY_WEIGHT

    # Normalize scores to expected format if needed
    if not normalized_scores:
        # Try to reconstruct from trait breakdown
        trait_breakdown = assessment.get("traitBreakdown", {})
        for trait, data in trait_breakdown.items():
            if isinstance(data, dict) and "score" in data:
                normalized_scores[trait] = data["score"]

    # Handle different modes
    interest = mode_specific.get("interest") or mode_specific.get("interests_assessed", [None])[0] if mode_specific else None

    if mode == "deep_dive" and interest:
        normalized_interest = normalize_interest(interest)
        update_deep_dive_profile(
            profile, normalized_interest, normalized_scores, archetype_name, quality_weight
        )
    else:
        update_mode_profile(
            profile, mode, normalized_scores, archetype_name, quality_weight
        )

    # Add to test history
    test_record = {
        "session_id": assessment.get("sessionId") or assessment_id,
        "mode": mode,
        "interest": interest,
        "date": completed_timestamp,
        "normalized_scores": normalized_scores,
        "archetype": archetype_name,
        "confidence_pct": DEFAULT_CONFIDENCE_PCT,
        "confidence_tier": "emerging",  # Default tier for historical
        "suspicious": False,
        "flags": [],
        "quality_weight": quality_weight,
        "included_in_profile": True,  # All historical data included
        "backfilled": True  # Mark as backfilled
    }

    if "test_history" not in profile:
        profile["test_history"] = []
    profile["test_history"].append(test_record)

    # Update legacy fields
    profile["current_archetype"] = archetype_name
    profile["overall_confidence"] = DEFAULT_CONFIDENCE_PCT

    return True


def save_profile(profile: dict, dry_run: bool = False):
    """Save the profile to Firestore."""
    doc_id = profile.pop("_doc_id", None)
    exists = profile.pop("_exists", False)

    if dry_run:
        logger.info(f"  [DRY RUN] Would {'update' if exists else 'create'} profile")
        return

    profile["updated_at"] = time.time()

    if exists and doc_id:
        db.collection("user_profiles").document(doc_id).update(profile)
    else:
        db.collection("user_profiles").add(profile)


def set_has_seen_profile_false(user_id: str, dry_run: bool = False):
    """Set hasSeenProfile=false for user to trigger the profile badge."""
    if dry_run:
        logger.info(f"  [DRY RUN] Would set hasSeenProfile=false for user {user_id[:8]}...")
        return

    user_ref = db.collection("users").document(user_id)
    user_ref.update({
        "hasSeenProfile": False
    })


def backfill_user(user_id: str, user_data: dict, dry_run: bool = False) -> dict:
    """Backfill a single user's profile from their assessments."""
    stats = {
        "assessments_found": 0,
        "assessments_processed": 0,
        "profile_created": False,
        "profile_updated": False,
        "skipped": False,
        "badge_set": False
    }

    # Get user's assessments
    assessments = list(get_user_assessments(user_id))
    stats["assessments_found"] = len(assessments)

    if not assessments:
        stats["skipped"] = True
        return stats

    # Get or create profile
    profile = get_or_create_profile(user_id, dry_run)
    stats["profile_created"] = not profile.get("_exists", False)

    # Check if already backfilled
    existing_history = profile.get("test_history", [])
    if existing_history and any(t.get("backfilled") for t in existing_history):
        logger.info(f"  User {user_id[:8]}... already backfilled, checking for new assessments")
        # Only process assessments not in history
        existing_session_ids = {t.get("session_id") for t in existing_history}
    else:
        existing_session_ids = set()

    # Process each assessment
    for assessment_doc in assessments:
        assessment = assessment_doc.to_dict()
        assessment_id = assessment_doc.id

        # Skip if already in history
        session_id = assessment.get("sessionId") or assessment_id
        if session_id in existing_session_ids:
            continue

        success = process_assessment(profile, assessment, assessment_id)
        if success:
            stats["assessments_processed"] += 1

    # Save profile if we processed any assessments
    if stats["assessments_processed"] > 0:
        save_profile(profile, dry_run)
        stats["profile_updated"] = True

        # Set hasSeenProfile=false to trigger the badge for existing users
        # Only if user hasn't already seen profile (hasSeenProfile not set or false)
        has_seen = user_data.get("hasSeenProfile", None)
        if has_seen is None:  # Only set if never set before
            set_has_seen_profile_false(user_id, dry_run)
            stats["badge_set"] = True

    return stats


def run_backfill(dry_run: bool = False):
    """Run the full backfill process."""
    logger.info("=" * 60)
    logger.info("Starting Profile Backfill")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    logger.info("=" * 60)

    total_stats = {
        "users_processed": 0,
        "users_skipped": 0,
        "profiles_created": 0,
        "profiles_updated": 0,
        "assessments_processed": 0,
        "badges_set": 0,
        "errors": 0
    }

    # Get all users
    users = list(get_all_users())
    logger.info(f"Found {len(users)} users to process")

    for i, user_doc in enumerate(users):
        user_id = user_doc.id
        user_data = user_doc.to_dict()

        logger.info(f"\n[{i+1}/{len(users)}] Processing user: {user_id[:8]}...")

        try:
            stats = backfill_user(user_id, user_data, dry_run)

            if stats["skipped"]:
                logger.info(f"  Skipped (no assessments)")
                total_stats["users_skipped"] += 1
            else:
                badge_msg = " (badge set)" if stats.get("badge_set") else ""
                logger.info(f"  Found {stats['assessments_found']} assessments, processed {stats['assessments_processed']}{badge_msg}")

                total_stats["users_processed"] += 1
                total_stats["assessments_processed"] += stats["assessments_processed"]

                if stats["profile_created"]:
                    total_stats["profiles_created"] += 1
                if stats["profile_updated"]:
                    total_stats["profiles_updated"] += 1
                if stats.get("badge_set"):
                    total_stats["badges_set"] += 1

        except Exception as e:
            logger.error(f"  Error processing user {user_id}: {e}")
            total_stats["errors"] += 1

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Backfill Complete!")
    logger.info("=" * 60)
    logger.info(f"Users processed:      {total_stats['users_processed']}")
    logger.info(f"Users skipped:        {total_stats['users_skipped']}")
    logger.info(f"Profiles created:     {total_stats['profiles_created']}")
    logger.info(f"Profiles updated:     {total_stats['profiles_updated']}")
    logger.info(f"Assessments migrated: {total_stats['assessments_processed']}")
    logger.info(f"Badges set:           {total_stats['badges_set']}")
    logger.info(f"Errors:               {total_stats['errors']}")

    return total_stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill user_profiles from historical assessments")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    args = parser.parse_args()

    run_backfill(dry_run=args.dry_run)
