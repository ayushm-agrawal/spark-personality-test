"""
Badge Engine for Ception Personality Assessment

This module handles checking conditions and awarding badges based on user events.
The engine is event-driven - different events trigger different badge checks.

Event Types:
- assessment_completed: Check badges after test completion
- insight_viewed: Check badges when user reads insight sections
- app_opened: Check badges on app/profile load
"""

import time
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from firebase import db


# ============================================================================
# BADGE EVENT MAPPINGS
# ============================================================================

# Maps events to which badges should be checked
EVENT_BADGE_MAPPINGS = {
    "assessment_completed": [
        "first_spark", "deep_diver", "no_filter", "night_owl",
        "true_north", "mirror_mirror", "unicorn", "renaissance_soul",
        "the_outlier", "beautiful_contradiction"
    ],
    "insight_viewed": [
        "curious_cat", "aha_moment", "blind_spot_hunter", "the_revisitor"
    ],
    "app_opened": [
        "weekly_wanderer"
    ]
}


# ============================================================================
# CORE BADGE SERVICE FUNCTIONS
# ============================================================================

def get_badge_definitions() -> Dict[str, dict]:
    """Load all enabled badge definitions from Firestore."""
    badges_ref = db.collection("badge_definitions")
    badges = {}
    for doc in badges_ref.where("enabled", "==", True).stream():
        badges[doc.id] = doc.to_dict()
    return badges


def get_badge_definition(badge_id: str) -> Optional[dict]:
    """Get a single badge definition."""
    doc = db.collection("badge_definitions").document(badge_id).get()
    if doc.exists:
        return doc.to_dict()
    return None


def check_badges_for_event(
    user_profile: dict,
    event_type: str,
    event_data: dict
) -> List[dict]:
    """
    Main entry point for badge checking.

    Args:
        user_profile: The user's profile data
        event_type: One of "assessment_completed", "insight_viewed", "app_opened"
        event_data: Context data for the event

    Returns:
        List of newly earned badges (badge definition + earned_at)
    """
    if event_type not in EVENT_BADGE_MAPPINGS:
        return []

    badge_ids_to_check = EVENT_BADGE_MAPPINGS[event_type]
    badge_definitions = get_badge_definitions()

    # Get already earned badges to avoid re-awarding
    earned_badge_ids = {b["badge_id"] for b in user_profile.get("badges_earned", [])}

    newly_earned = []

    for badge_id in badge_ids_to_check:
        # Skip if already earned or not defined
        if badge_id in earned_badge_ids:
            continue
        if badge_id not in badge_definitions:
            continue

        badge_def = badge_definitions[badge_id]

        # Skip disabled badges
        if not badge_def.get("enabled", True):
            continue

        # Get the checker function
        checker = BADGE_CHECKERS.get(badge_id)
        if not checker:
            continue

        # Check if badge should be awarded
        try:
            should_award = checker(user_profile, event_data)
            if should_award:
                # Prepare badge award data
                awarded_badge = {
                    "badge_id": badge_id,
                    "display_name": badge_def.get("display_name"),
                    "description": badge_def.get("description"),
                    "icon": badge_def.get("icon"),
                    "rarity": badge_def.get("rarity"),
                    "category": badge_def.get("category"),
                    "points": badge_def.get("points", 0),
                    "earned_at": time.time()
                }
                newly_earned.append(awarded_badge)
        except Exception as e:
            print(f"Error checking badge {badge_id}: {e}")
            continue

    return newly_earned


def award_badges(profile_id: str, badges: List[dict]) -> bool:
    """
    Award badges to a user profile.

    Args:
        profile_id: The Firestore document ID
        badges: List of badge objects to award

    Returns:
        True if successful
    """
    if not badges:
        return True

    try:
        profiles_ref = db.collection("user_profiles")
        profile_doc = profiles_ref.document(profile_id)

        # Get current badges
        profile = profile_doc.get().to_dict()
        current_badges = profile.get("badges_earned", [])

        # Add new badges (only the core fields for storage)
        for badge in badges:
            current_badges.append({
                "badge_id": badge["badge_id"],
                "earned_at": badge["earned_at"],
                "context": badge.get("context", {})
            })

        # Update profile
        profile_doc.update({
            "badges_earned": current_badges,
            "updated_at": time.time()
        })

        return True
    except Exception as e:
        print(f"Error awarding badges: {e}")
        return False


def get_user_badges(user_id: str) -> List[dict]:
    """
    Get all badges earned by a user with full definition details.

    Args:
        user_id: Firebase auth UID

    Returns:
        List of earned badges with definition details
    """
    profiles_ref = db.collection("user_profiles")
    query = profiles_ref.where("user_id", "==", user_id).limit(1)
    docs = list(query.stream())

    if not docs:
        return []

    profile = docs[0].to_dict()
    earned_badges = profile.get("badges_earned", [])
    badge_definitions = get_badge_definitions()

    result = []
    for earned in earned_badges:
        badge_id = earned.get("badge_id")
        badge_def = badge_definitions.get(badge_id, {})

        result.append({
            "badge_id": badge_id,
            "display_name": badge_def.get("display_name", badge_id),
            "description": badge_def.get("description", ""),
            "icon": badge_def.get("icon", ""),
            "rarity": badge_def.get("rarity", "common"),
            "category": badge_def.get("category", ""),
            "points": badge_def.get("points", 0),
            "earned_at": earned.get("earned_at")
        })

    # Sort by earned_at descending (most recent first)
    result.sort(key=lambda x: x.get("earned_at", 0), reverse=True)

    return result


def update_badge_progress(profile_id: str, badge_id: str, progress_data: dict) -> dict:
    """
    Update progress toward a badge.

    Args:
        profile_id: Firestore document ID
        badge_id: The badge being tracked
        progress_data: Progress data to merge

    Returns:
        Updated progress for the badge
    """
    try:
        profiles_ref = db.collection("user_profiles")
        profile_doc = profiles_ref.document(profile_id)

        profile = profile_doc.get().to_dict()
        badge_progress = profile.get("badge_progress", {})

        # Merge progress
        if badge_id not in badge_progress:
            badge_progress[badge_id] = {}

        badge_progress[badge_id].update(progress_data)

        # Save
        profile_doc.update({
            "badge_progress": badge_progress,
            "updated_at": time.time()
        })

        return badge_progress[badge_id]
    except Exception as e:
        print(f"Error updating badge progress: {e}")
        return {}


def get_incomplete_badges_with_progress(user_profile: dict) -> List[dict]:
    """
    Get badges not yet earned with their current progress.

    Args:
        user_profile: The user's profile data

    Returns:
        List of incomplete badges with progress info
    """
    earned_ids = {b["badge_id"] for b in user_profile.get("badges_earned", [])}
    badge_progress = user_profile.get("badge_progress", {})
    badge_definitions = get_badge_definitions()

    incomplete = []
    for badge_id, badge_def in badge_definitions.items():
        if badge_id in earned_ids:
            continue
        if not badge_def.get("enabled", True):
            continue

        progress = badge_progress.get(badge_id, {})

        incomplete.append({
            "badge_id": badge_id,
            "display_name": badge_def.get("display_name"),
            "description": badge_def.get("description"),
            "icon": badge_def.get("icon"),
            "rarity": badge_def.get("rarity"),
            "category": badge_def.get("category"),
            "progress": progress,
            "trigger_conditions": badge_def.get("trigger_conditions", {})
        })

    return incomplete


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_week_string(timestamp: float = None) -> str:
    """Get ISO week string (e.g., '2026-W01') for a timestamp."""
    if timestamp is None:
        timestamp = time.time()
    dt = datetime.fromtimestamp(timestamp)
    return f"{dt.year}-W{dt.isocalendar()[1]:02d}"


def get_date_string(timestamp: float = None) -> str:
    """Get date string (e.g., '2026-01-05') for a timestamp."""
    if timestamp is None:
        timestamp = time.time()
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d")


def calculate_consistency_score(assessments: List[dict]) -> float:
    """
    Calculate consistency score across assessments.

    Returns a score 0-100 where 100 is perfectly consistent.
    """
    if len(assessments) < 2:
        return 100.0

    # Collect scores per trait
    trait_scores = {}
    for assessment in assessments:
        scores = assessment.get("normalized_scores", {})
        for trait, score in scores.items():
            if trait not in trait_scores:
                trait_scores[trait] = []
            trait_scores[trait].append(score)

    if not trait_scores:
        return 100.0

    # Calculate standard deviation for each trait
    std_devs = []
    for trait, scores in trait_scores.items():
        if len(scores) < 2:
            continue
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        std_devs.append(std_dev)

    if not std_devs:
        return 100.0

    # Average standard deviation
    avg_std_dev = sum(std_devs) / len(std_devs)

    # Convert to consistency score (lower std dev = higher consistency)
    # Max std dev for 0-100 range is about 50
    consistency = max(0, 100 - (avg_std_dev * 2))

    return consistency


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2) or len(vec1) == 0:
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def get_trait_percentiles() -> dict:
    """Load trait percentiles from response_statistics."""
    try:
        doc = db.collection("response_statistics").document("trait_percentiles").get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"Error loading percentiles: {e}")

    # Default percentiles
    return {
        "Openness": {"p5": 20, "p25": 40, "p50": 55, "p75": 70, "p95": 90},
        "Conscientiousness": {"p5": 25, "p25": 45, "p50": 60, "p75": 75, "p95": 90},
        "Extraversion": {"p5": 20, "p25": 40, "p50": 55, "p75": 70, "p95": 85},
        "Agreeableness": {"p5": 30, "p25": 50, "p50": 65, "p75": 80, "p95": 95},
        "Emotional_Stability": {"p5": 25, "p25": 45, "p50": 60, "p75": 75, "p95": 90}
    }


# ============================================================================
# BADGE CHECKER FUNCTIONS
# ============================================================================

# --------------------------------------------------------------------------
# CONSISTENCY BADGES
# --------------------------------------------------------------------------

def check_true_north(user_profile: dict, event_data: dict) -> bool:
    """
    True North: Consistent responses across multiple assessments.
    Requires: 3+ assessments with consistency score >= 85%
    """
    test_history = user_profile.get("test_history", [])

    if len(test_history) < 3:
        return False

    consistency = calculate_consistency_score(test_history)
    return consistency >= 85


def check_mirror_mirror(user_profile: dict, event_data: dict) -> bool:
    """
    Mirror Mirror: Same mode twice with consistent results.
    Requires: 2+ assessments in same mode with cosine similarity >= 0.80
    """
    test_history = user_profile.get("test_history", [])

    # Group by mode
    mode_tests = {}
    for test in test_history:
        mode = test.get("mode", "overall")
        if mode not in mode_tests:
            mode_tests[mode] = []
        mode_tests[mode].append(test)

    # Check each mode for consistency
    for mode, tests in mode_tests.items():
        if len(tests) < 2:
            continue

        # Compare first two tests
        scores1 = tests[0].get("normalized_scores", {})
        scores2 = tests[1].get("normalized_scores", {})

        # Build vectors with same trait ordering
        traits = sorted(set(scores1.keys()) & set(scores2.keys()))
        if len(traits) < 3:
            continue

        vec1 = [scores1.get(t, 50) for t in traits]
        vec2 = [scores2.get(t, 50) for t in traits]

        similarity = cosine_similarity(vec1, vec2)
        if similarity >= 0.80:
            return True

    return False


def check_no_filter(user_profile: dict, event_data: dict) -> bool:
    """
    No Filter: Thoughtful responses (avg response time >= 4 seconds).
    Requires: Just completed assessment with avg time >= 4s, min 6 questions
    """
    response_times = event_data.get("response_times", [])

    if len(response_times) < 6:
        return False

    avg_time = sum(response_times) / len(response_times)
    return avg_time >= 4.0


def check_night_owl(user_profile: dict, event_data: dict) -> bool:
    """
    Night Owl: Completed assessment between midnight and 5am.
    """
    timestamp = event_data.get("timestamp", time.time())
    dt = datetime.fromtimestamp(timestamp)

    # Check if hour is between 0 and 5 (midnight to 5am)
    return 0 <= dt.hour < 5


# --------------------------------------------------------------------------
# ENGAGEMENT BADGES
# --------------------------------------------------------------------------

def check_first_spark(user_profile: dict, event_data: dict) -> bool:
    """
    First Spark: Completed first assessment.
    """
    total = user_profile.get("total_assessments_completed", 0)
    return total >= 1


def check_deep_diver(user_profile: dict, event_data: dict) -> bool:
    """
    Deep Diver: Completed 3+ unique modes.
    """
    modes = user_profile.get("assessment_types_completed", [])
    unique_modes = set(modes)
    return len(unique_modes) >= 3


def check_curious_cat(user_profile: dict, event_data: dict) -> bool:
    """
    Curious Cat: Viewed 5+ insight sections.
    """
    insights_viewed = user_profile.get("insights_viewed", {})

    # Count total unique sections viewed across all archetypes
    total_sections = 0
    for archetype, sections in insights_viewed.items():
        if isinstance(sections, dict):
            total_sections += len(sections)

    return total_sections >= 5


def check_weekly_wanderer(user_profile: dict, event_data: dict) -> bool:
    """
    Weekly Wanderer: Returned 4 weeks in a row.
    """
    weekly_visits = user_profile.get("weekly_visits", [])

    if len(weekly_visits) < 4:
        return False

    # Parse weeks and check for consecutive streak
    try:
        # Sort weeks
        sorted_weeks = sorted(set(weekly_visits))

        if len(sorted_weeks) < 4:
            return False

        # Check last 4 weeks for consecutive pattern
        # Parse ISO week format: "2026-W01"
        def parse_week(w):
            parts = w.split("-W")
            return int(parts[0]), int(parts[1])

        # Get current week
        current_year, current_week = parse_week(get_week_string())

        # Check if we have 4 consecutive weeks ending at or near current
        consecutive = 0
        check_year, check_week = current_year, current_week

        for _ in range(4):
            week_str = f"{check_year}-W{check_week:02d}"
            if week_str in sorted_weeks:
                consecutive += 1
            else:
                break

            # Go back one week
            check_week -= 1
            if check_week < 1:
                check_year -= 1
                check_week = 52  # Approximate

        return consecutive >= 4

    except Exception as e:
        print(f"Error checking weekly_wanderer: {e}")
        return False


def check_the_revisitor(user_profile: dict, event_data: dict) -> bool:
    """
    The Revisitor: Viewed insights on 3+ different days.
    """
    badge_progress = user_profile.get("badge_progress", {})
    revisitor_progress = badge_progress.get("the_revisitor", {})

    visit_dates = revisitor_progress.get("visit_dates", [])
    unique_dates = set(visit_dates)

    return len(unique_dates) >= 3


# --------------------------------------------------------------------------
# GROWTH BADGES
# --------------------------------------------------------------------------

def check_aha_moment(user_profile: dict, event_data: dict) -> bool:
    """
    Aha Moment: Viewed all main insight sections for primary archetype.
    Required sections: summary, strengths, blind_spots, team_phases, energy, tips
    """
    insights_viewed = user_profile.get("insights_viewed", {})
    current_archetype = user_profile.get("current_archetype")

    if not current_archetype:
        return False

    # Normalize archetype name for lookup
    archetype_key = current_archetype.lower().replace("the ", "").replace(" ", "_")

    # Check for archetype in insights_viewed
    archetype_sections = None
    for key, sections in insights_viewed.items():
        if archetype_key in key.lower() or key.lower() in archetype_key:
            archetype_sections = sections
            break

    if not archetype_sections or not isinstance(archetype_sections, dict):
        return False

    # Required sections
    required = {"summary", "strengths", "blind_spots", "team_phases", "energy", "tips"}
    viewed = set(archetype_sections.keys())

    return required.issubset(viewed)


def check_blind_spot_hunter(user_profile: dict, event_data: dict) -> bool:
    """
    Blind Spot Hunter: Spent 30+ seconds on blind spots section.
    """
    badge_progress = user_profile.get("badge_progress", {})
    hunter_progress = badge_progress.get("blind_spot_hunter", {})

    seconds_spent = hunter_progress.get("seconds_spent", 0)
    return seconds_spent >= 30


def check_growth_mindset(user_profile: dict, event_data: dict) -> bool:
    """
    Growth Mindset: Trait shifted 20+ points consistently over 5+ assessments.
    This is a legendary badge - intentionally hard to earn.
    """
    test_history = user_profile.get("test_history", [])

    if len(test_history) < 5:
        return False

    # Sort by timestamp
    sorted_history = sorted(test_history, key=lambda x: x.get("completed_at", 0))

    # Compare earliest vs latest
    earliest = sorted_history[0].get("normalized_scores", {})
    latest = sorted_history[-1].get("normalized_scores", {})

    # Also check second-latest to confirm consistency
    second_latest = sorted_history[-2].get("normalized_scores", {}) if len(sorted_history) > 1 else latest

    for trait in earliest.keys():
        if trait not in latest or trait not in second_latest:
            continue

        shift = abs(latest[trait] - earliest[trait])
        shift_confirmed = abs(second_latest[trait] - earliest[trait])

        # Both recent assessments should show the shift
        if shift >= 20 and shift_confirmed >= 15:
            return True

    return False


# --------------------------------------------------------------------------
# QUIRK BADGES
# --------------------------------------------------------------------------

def check_unicorn(user_profile: dict, event_data: dict) -> bool:
    """
    Unicorn: Any trait score >= 95th percentile.
    """
    normalized_scores = event_data.get("normalized_scores", {})
    percentiles = get_trait_percentiles()

    for trait, score in normalized_scores.items():
        trait_percentiles = percentiles.get(trait, {})
        p95 = trait_percentiles.get("p95", 90)

        if score >= p95:
            return True

    return False


def check_renaissance_soul(user_profile: dict, event_data: dict) -> bool:
    """
    Renaissance Soul: All traits within 15 points of each other.
    """
    normalized_scores = event_data.get("normalized_scores", {})

    if len(normalized_scores) < 5:
        return False

    scores = list(normalized_scores.values())
    score_range = max(scores) - min(scores)

    return score_range <= 15


def check_the_outlier(user_profile: dict, event_data: dict) -> bool:
    """
    The Outlier: Gave a response chosen by < 5% of users.

    Note: This requires response frequency tracking which may not be fully
    implemented yet. Returns False until that data is available.
    """
    # TODO: Implement when response frequency tracking is available
    # For now, check if any answer has an explicitly marked rare flag
    answers = event_data.get("answers", [])

    for answer in answers:
        if isinstance(answer, dict) and answer.get("is_rare", False):
            return True

    return False


def check_beautiful_contradiction(user_profile: dict, event_data: dict) -> bool:
    """
    Beautiful Contradiction: High scores on traits that rarely go together.
    Pairs: (Openness + Conscientiousness), (Extraversion + Emotional_Stability)
    Both traits in a pair must be >= 80.
    """
    normalized_scores = event_data.get("normalized_scores", {})

    # Define contradiction pairs
    pairs = [
        ("Openness", "Conscientiousness"),
        ("Extraversion", "Emotional_Stability")
    ]

    for trait1, trait2 in pairs:
        score1 = normalized_scores.get(trait1, 0)
        score2 = normalized_scores.get(trait2, 0)

        if score1 >= 80 and score2 >= 80:
            return True

    return False


# ============================================================================
# BADGE CHECKER REGISTRY
# ============================================================================

BADGE_CHECKERS = {
    # Consistency
    "true_north": check_true_north,
    "mirror_mirror": check_mirror_mirror,
    "no_filter": check_no_filter,
    "night_owl": check_night_owl,
    # Engagement
    "first_spark": check_first_spark,
    "deep_diver": check_deep_diver,
    "curious_cat": check_curious_cat,
    "weekly_wanderer": check_weekly_wanderer,
    "the_revisitor": check_the_revisitor,
    # Growth
    "aha_moment": check_aha_moment,
    "blind_spot_hunter": check_blind_spot_hunter,
    "growth_mindset": check_growth_mindset,
    # Quirk
    "unicorn": check_unicorn,
    "renaissance_soul": check_renaissance_soul,
    "the_outlier": check_the_outlier,
    "beautiful_contradiction": check_beautiful_contradiction,
}


# ============================================================================
# INSIGHT TRACKING
# ============================================================================

def track_insight_view(
    profile_id: str,
    user_profile: dict,
    archetype: str,
    section_name: str,
    time_spent_seconds: int = 0
) -> Tuple[dict, List[dict]]:
    """
    Track when a user views an insight section.

    Args:
        profile_id: Firestore document ID
        user_profile: Current profile data
        archetype: The archetype being viewed
        section_name: The section being viewed (e.g., "blind_spots")
        time_spent_seconds: Time spent on the section

    Returns:
        Tuple of (updated_profile, newly_awarded_badges)
    """
    current_time = time.time()

    # Update insights_viewed
    insights_viewed = user_profile.get("insights_viewed", {})
    if archetype not in insights_viewed:
        insights_viewed[archetype] = {}

    # Track section view
    if section_name not in insights_viewed[archetype]:
        insights_viewed[archetype][section_name] = current_time

    # Update badge progress for the_revisitor
    badge_progress = user_profile.get("badge_progress", {})
    if "the_revisitor" not in badge_progress:
        badge_progress["the_revisitor"] = {"visit_dates": [], "count": 0}

    today = get_date_string()
    if today not in badge_progress["the_revisitor"]["visit_dates"]:
        badge_progress["the_revisitor"]["visit_dates"].append(today)
        badge_progress["the_revisitor"]["count"] = len(badge_progress["the_revisitor"]["visit_dates"])

    # Update badge progress for blind_spot_hunter if viewing blind_spots
    if section_name == "blind_spots" and time_spent_seconds > 0:
        if "blind_spot_hunter" not in badge_progress:
            badge_progress["blind_spot_hunter"] = {"seconds_spent": 0}
        badge_progress["blind_spot_hunter"]["seconds_spent"] += time_spent_seconds
        badge_progress["blind_spot_hunter"]["last_viewed"] = current_time

    # Save updates
    try:
        profiles_ref = db.collection("user_profiles")
        profiles_ref.document(profile_id).update({
            "insights_viewed": insights_viewed,
            "badge_progress": badge_progress,
            "updated_at": current_time
        })
    except Exception as e:
        print(f"Error updating insight tracking: {e}")

    # Update the profile dict for badge checking
    user_profile["insights_viewed"] = insights_viewed
    user_profile["badge_progress"] = badge_progress

    # Check for badges
    event_data = {
        "archetype": archetype,
        "section": section_name,
        "time_spent": time_spent_seconds
    }

    newly_earned = check_badges_for_event(user_profile, "insight_viewed", event_data)

    # Award badges
    if newly_earned:
        award_badges(profile_id, newly_earned)

    return user_profile, newly_earned


def track_app_open(profile_id: str, user_profile: dict) -> Tuple[dict, List[dict]]:
    """
    Track when user opens the app/profile page.
    Updates weekly_visits and checks for weekly_wanderer badge.

    Returns:
        Tuple of (updated_profile, newly_awarded_badges)
    """
    current_time = time.time()
    current_week = get_week_string()

    # Update weekly_visits
    weekly_visits = user_profile.get("weekly_visits", [])
    if current_week not in weekly_visits:
        weekly_visits.append(current_week)

    # Keep only last 8 weeks to prevent unbounded growth
    if len(weekly_visits) > 8:
        weekly_visits = weekly_visits[-8:]

    # Save updates
    try:
        profiles_ref = db.collection("user_profiles")
        profiles_ref.document(profile_id).update({
            "weekly_visits": weekly_visits,
            "last_active_at": current_time,
            "updated_at": current_time
        })
    except Exception as e:
        print(f"Error updating app open tracking: {e}")

    # Update profile dict
    user_profile["weekly_visits"] = weekly_visits
    user_profile["last_active_at"] = current_time

    # Check badges
    newly_earned = check_badges_for_event(user_profile, "app_opened", {})

    # Award badges
    if newly_earned:
        award_badges(profile_id, newly_earned)

    return user_profile, newly_earned
