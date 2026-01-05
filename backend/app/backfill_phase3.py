"""
Backfill script for Phase 3 database schema updates.

Run from backend/app directory:
    python backfill_phase3.py --dry-run    # Preview changes
    python backfill_phase3.py              # Apply changes
    python backfill_phase3.py --verify     # Verify migration

This will:
1. Add new Phase 3 fields to existing user profiles
2. Calculate engagement stats from test_history
3. Award historical badges based on existing data
"""

import time
import sys
from datetime import datetime
from firebase import db


# Badge checking functions
def check_first_spark(profile: dict) -> bool:
    """Check if user completed at least 1 assessment."""
    return profile.get("total_assessments_completed", 0) >= 1


def check_deep_diver(profile: dict) -> bool:
    """Check if user completed 3+ unique modes."""
    modes = profile.get("assessment_types_completed", [])
    return len(set(modes)) >= 3


def check_night_owl(profile: dict) -> bool:
    """Check if any assessment was completed between midnight and 5am."""
    test_history = profile.get("test_history", [])
    for test in test_history:
        completed_at = test.get("completed_at")
        if completed_at:
            # Handle both timestamp formats
            if isinstance(completed_at, (int, float)):
                dt = datetime.fromtimestamp(completed_at)
            else:
                continue
            if 0 <= dt.hour < 5:
                return True
    return False


def check_no_filter(profile: dict) -> bool:
    """Check if user had thoughtful response times (avg >= 4 seconds)."""
    test_history = profile.get("test_history", [])
    total_time = 0
    total_questions = 0

    for test in test_history:
        response_times = test.get("response_times", [])
        if response_times:
            total_time += sum(response_times)
            total_questions += len(response_times)

    if total_questions >= 6:
        avg_time = total_time / total_questions
        return avg_time >= 4.0

    return False


def check_mirror_mirror(profile: dict) -> bool:
    """Check if user took same mode twice with consistent results."""
    test_history = profile.get("test_history", [])
    mode_tests = {}

    for test in test_history:
        mode = test.get("mode", "overall")
        if mode not in mode_tests:
            mode_tests[mode] = []
        mode_tests[mode].append(test)

    # Check if any mode has 2+ tests with same archetype
    for mode, tests in mode_tests.items():
        if len(tests) >= 2:
            archetypes = [t.get("archetype") for t in tests if t.get("archetype")]
            if len(archetypes) >= 2:
                # Check if first two have same archetype
                if archetypes[0] == archetypes[1]:
                    return True

    return False


def check_unicorn(profile: dict) -> bool:
    """Check if user has any trait score >= 95."""
    mode_profiles = profile.get("mode_profiles", {})
    for mode_data in mode_profiles.values():
        weighted_scores = mode_data.get("weighted_scores", {})
        for trait, score_data in weighted_scores.items():
            if isinstance(score_data, dict):
                total = score_data.get("weight_total", 0)
                if total > 0:
                    score = score_data.get("weighted_sum", 0) / total
                    if score >= 95:
                        return True
    return False


def check_renaissance_soul(profile: dict) -> bool:
    """Check if all traits are within 15 points of each other."""
    mode_profiles = profile.get("mode_profiles", {})
    for mode_data in mode_profiles.values():
        weighted_scores = mode_data.get("weighted_scores", {})
        scores = []
        for trait, score_data in weighted_scores.items():
            if isinstance(score_data, dict):
                total = score_data.get("weight_total", 0)
                if total > 0:
                    score = score_data.get("weighted_sum", 0) / total
                    scores.append(score)
        if len(scores) >= 5:
            score_range = max(scores) - min(scores)
            if score_range <= 15:
                return True
    return False


# Badge definitions for backfill
BACKFILL_BADGES = [
    ("first_spark", check_first_spark),
    ("deep_diver", check_deep_diver),
    ("night_owl", check_night_owl),
    ("no_filter", check_no_filter),
    ("mirror_mirror", check_mirror_mirror),
    ("unicorn", check_unicorn),
    ("renaissance_soul", check_renaissance_soul),
]


def calculate_engagement_stats(profile: dict) -> dict:
    """Calculate engagement statistics from test_history."""
    test_history = profile.get("test_history", [])

    # Total assessments
    total = len(test_history)

    # Unique modes completed
    modes = set()
    consistency_scores = []

    for test in test_history:
        mode = test.get("mode", "overall")
        modes.add(mode)

        # Extract consistency score if available
        archetype_confidence = test.get("archetype_confidence")
        if archetype_confidence:
            consistency_scores.append(archetype_confidence)

    return {
        "total_assessments_completed": total,
        "assessment_types_completed": list(modes),
        "consistency_scores": consistency_scores
    }


def award_badges(profile: dict, dry_run: bool = False) -> list:
    """Check and award badges based on profile data."""
    existing_badges = {b["badge_id"] for b in profile.get("badges_earned", [])}
    new_badges = []
    current_time = time.time()

    for badge_id, check_func in BACKFILL_BADGES:
        if badge_id not in existing_badges:
            if check_func(profile):
                new_badges.append({
                    "badge_id": badge_id,
                    "earned_at": current_time,
                    "context": {"source": "backfill", "backfill_date": current_time}
                })

    return new_badges


def backfill_profile(profile_id: str, profile: dict, dry_run: bool = False) -> dict:
    """Backfill a single profile with Phase 3 fields."""
    current_time = time.time()

    # Calculate engagement stats
    stats = calculate_engagement_stats(profile)

    # Default values for new fields
    updates = {
        # Badge tracking
        "badges_earned": profile.get("badges_earned", []),
        "badge_progress": profile.get("badge_progress", {}),
        # Engagement tracking
        "total_assessments_completed": stats["total_assessments_completed"],
        "assessment_types_completed": stats["assessment_types_completed"],
        "insights_viewed": profile.get("insights_viewed", {}),
        "last_active_at": profile.get("updated_at", current_time),
        "weekly_visits": profile.get("weekly_visits", []),
        "consistency_scores": stats["consistency_scores"],
        # Display preferences
        "insight_mode": profile.get("insight_mode", "concise"),
        "badges_visibility": profile.get("badges_visibility", "public"),
        # Timestamp
        "updated_at": current_time
    }

    # Award historical badges
    temp_profile = {**profile, **updates}
    new_badges = award_badges(temp_profile, dry_run)
    if new_badges:
        updates["badges_earned"] = updates["badges_earned"] + new_badges

    return updates, new_badges


def run_backfill(dry_run: bool = False, batch_size: int = 100):
    """Run the Phase 3 backfill migration."""
    profiles_ref = db.collection("user_profiles")

    print(f"{'[DRY RUN] ' if dry_run else ''}Phase 3 Backfill Migration")
    print("=" * 50)

    # Get all profiles
    all_profiles = list(profiles_ref.stream())
    total = len(all_profiles)

    print(f"\nFound {total} profiles to process")

    updated = 0
    badges_awarded = 0
    errors = []
    badge_counts = {}

    for i, doc in enumerate(all_profiles):
        profile_id = doc.id
        profile = doc.to_dict()

        try:
            # Check if already has Phase 3 fields
            has_phase3 = "badges_earned" in profile

            updates, new_badges = backfill_profile(profile_id, profile, dry_run)

            # Count badges
            for badge in new_badges:
                badge_id = badge["badge_id"]
                badge_counts[badge_id] = badge_counts.get(badge_id, 0) + 1

            if new_badges or not has_phase3:
                if not dry_run:
                    profiles_ref.document(profile_id).update(updates)
                updated += 1
                badges_awarded += len(new_badges)

                if new_badges:
                    badge_names = [b["badge_id"] for b in new_badges]
                    print(f"  [{i+1}/{total}] {profile_id[:8]}... +{len(new_badges)} badges: {', '.join(badge_names)}")
                elif not has_phase3:
                    print(f"  [{i+1}/{total}] {profile_id[:8]}... added Phase 3 fields")

        except Exception as e:
            error_msg = f"Error with {profile_id}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

        # Progress indicator for large batches
        if (i + 1) % batch_size == 0:
            print(f"\n  Progress: {i+1}/{total} ({((i+1)/total)*100:.1f}%)\n")

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  - Profiles updated: {updated}")
    print(f"  - Badges awarded: {badges_awarded}")
    print(f"  - Errors: {len(errors)}")

    if badge_counts:
        print(f"\nBadges awarded by type:")
        for badge_id, count in sorted(badge_counts.items(), key=lambda x: -x[1]):
            print(f"  - {badge_id}: {count}")

    if errors:
        print("\nErrors:")
        for err in errors[:10]:  # Show first 10 errors
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


def verify_migration():
    """Verify the migration was successful."""
    profiles_ref = db.collection("user_profiles")

    print("Verifying Phase 3 Migration...")
    print("=" * 50)

    all_profiles = list(profiles_ref.stream())
    total = len(all_profiles)

    with_phase3 = 0
    with_badges = 0
    total_badges = 0
    missing_fields = []

    required_fields = [
        "badges_earned",
        "badge_progress",
        "total_assessments_completed",
        "assessment_types_completed",
        "insights_viewed",
        "last_active_at",
        "weekly_visits",
        "consistency_scores",
        "insight_mode",
        "badges_visibility"
    ]

    for doc in all_profiles:
        profile = doc.to_dict()

        # Check for Phase 3 fields
        has_all = all(field in profile for field in required_fields)
        if has_all:
            with_phase3 += 1

            badges = profile.get("badges_earned", [])
            if badges:
                with_badges += 1
                total_badges += len(badges)
        else:
            missing = [f for f in required_fields if f not in profile]
            missing_fields.append((doc.id, missing))

    print(f"\nTotal profiles: {total}")
    print(f"With Phase 3 fields: {with_phase3} ({with_phase3/total*100:.1f}%)")
    print(f"With badges: {with_badges}")
    print(f"Total badges awarded: {total_badges}")

    if missing_fields:
        print(f"\nProfiles missing fields: {len(missing_fields)}")
        for profile_id, missing in missing_fields[:5]:
            print(f"  - {profile_id[:8]}...: missing {', '.join(missing)}")
        if len(missing_fields) > 5:
            print(f"  ... and {len(missing_fields) - 5} more")
    else:
        print("\nAll profiles have required Phase 3 fields!")


if __name__ == "__main__":
    if "--verify" in sys.argv:
        verify_migration()
    elif "--dry-run" in sys.argv or "-n" in sys.argv:
        print("=" * 50)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 50)
        print()
        run_backfill(dry_run=True)
    else:
        print("=" * 50)
        print("PHASE 3 BACKFILL MIGRATION")
        print("=" * 50)
        print("""
This will:
1. Add Phase 3 fields to all existing profiles
2. Calculate engagement statistics from history
3. Award historical badges based on existing data
        """)
        response = input("Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
        run_backfill(dry_run=False)

    print("\nDone!")
