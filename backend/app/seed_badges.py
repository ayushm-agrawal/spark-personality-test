"""
Seed script to create badge_definitions collection in Firestore.

Run from backend/app directory:
    python seed_badges.py

This will create all 19 badge definitions for the Phase 3 badge system.
"""

import time
from firebase import db


BADGE_DEFINITIONS = [
    # ============================================================================
    # CONSISTENCY BADGES
    # ============================================================================
    {
        "badge_id": "true_north",
        "display_name": "True North",
        "description": "Your responses are remarkably consistent across assessments. You know who you are.",
        "category": "consistency",
        "icon": "compass",
        "rarity": "rare",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "min_assessments": 3,
            "consistency_threshold": 0.85
        },
        "points": 100,
        "enabled": True,
        "sort_order": 1
    },
    {
        "badge_id": "mirror_mirror",
        "display_name": "Mirror, Mirror",
        "description": "Took the same assessment twice with consistent results. Your self-perception is reliable.",
        "category": "consistency",
        "icon": "mirror",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "same_mode_count": 2,
            "consistency_threshold": 0.80
        },
        "points": 50,
        "enabled": True,
        "sort_order": 2
    },
    {
        "badge_id": "no_filter",
        "display_name": "No Filter",
        "description": "You took your time and answered thoughtfully. No rushing through self-discovery.",
        "category": "consistency",
        "icon": "hourglass",
        "rarity": "common",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "min_avg_response_time": 4.0,
            "min_questions": 6
        },
        "points": 25,
        "enabled": True,
        "sort_order": 3
    },
    {
        "badge_id": "night_owl",
        "display_name": "Night Owl",
        "description": "Completed an assessment after midnight. Some self-reflection happens best in the quiet hours.",
        "category": "consistency",
        "icon": "owl",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "hour_range": [0, 5]
        },
        "points": 30,
        "enabled": True,
        "sort_order": 4
    },

    # ============================================================================
    # ENGAGEMENT BADGES
    # ============================================================================
    {
        "badge_id": "first_spark",
        "display_name": "First Spark",
        "description": "You took your first step on the journey of self-discovery.",
        "category": "engagement",
        "icon": "sparkles",
        "rarity": "common",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "assessments_completed": 1
        },
        "points": 10,
        "enabled": True,
        "sort_order": 10
    },
    {
        "badge_id": "deep_diver",
        "display_name": "Deep Diver",
        "description": "You've explored multiple dimensions of your personality across different modes.",
        "category": "engagement",
        "icon": "scuba",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "unique_modes_completed": 3
        },
        "points": 75,
        "enabled": True,
        "sort_order": 11
    },
    {
        "badge_id": "curious_cat",
        "display_name": "Curious Cat",
        "description": "You've read through multiple insight sections. Knowledge is power.",
        "category": "engagement",
        "icon": "cat",
        "rarity": "common",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "insights_sections_viewed": 5
        },
        "points": 20,
        "enabled": True,
        "sort_order": 12
    },
    {
        "badge_id": "weekly_wanderer",
        "display_name": "Weekly Wanderer",
        "description": "You've returned four weeks in a row. Self-discovery is a practice, not an event.",
        "category": "engagement",
        "icon": "footprints",
        "rarity": "rare",
        "trigger_type": "scheduled",
        "trigger_conditions": {
            "consecutive_weeks": 4
        },
        "points": 150,
        "enabled": True,
        "sort_order": 13
    },
    {
        "badge_id": "the_revisitor",
        "display_name": "The Revisitor",
        "description": "You've come back to re-read your insights multiple times. Reflection deepens understanding.",
        "category": "engagement",
        "icon": "refresh",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "insight_revisits": 3
        },
        "points": 40,
        "enabled": True,
        "sort_order": 14
    },

    # ============================================================================
    # GROWTH BADGES
    # ============================================================================
    {
        "badge_id": "aha_moment",
        "display_name": "Aha! Moment",
        "description": "You've read every section of your personality insights. Now you really know yourself.",
        "category": "growth",
        "icon": "lightbulb",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "full_insight_read": True
        },
        "points": 60,
        "enabled": True,
        "sort_order": 20
    },
    {
        "badge_id": "blind_spot_hunter",
        "display_name": "Blind Spot Hunter",
        "description": "You spent time reading about your potential blind spots. It takes courage to face our shadows.",
        "category": "growth",
        "icon": "magnifier",
        "rarity": "rare",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "blind_spots_section_time": 30
        },
        "points": 80,
        "enabled": True,
        "sort_order": 21
    },
    {
        "badge_id": "growth_mindset",
        "display_name": "Growth Mindset",
        "description": "Your profile has evolved over time. People can change, and you're proof.",
        "category": "growth",
        "icon": "seedling",
        "rarity": "legendary",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "trait_shift_detected": True,
            "min_assessments": 5
        },
        "points": 200,
        "enabled": True,
        "sort_order": 22
    },

    # ============================================================================
    # QUIRK BADGES
    # ============================================================================
    {
        "badge_id": "unicorn",
        "display_name": "Unicorn",
        "description": "You scored in the top 5% on one of your traits. Embrace what makes you unique.",
        "category": "quirk",
        "icon": "unicorn",
        "rarity": "rare",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "percentile_threshold": 95
        },
        "points": 100,
        "enabled": True,
        "sort_order": 30
    },
    {
        "badge_id": "renaissance_soul",
        "display_name": "Renaissance Soul",
        "description": "Your traits are remarkably balanced. You contain multitudes.",
        "category": "quirk",
        "icon": "palette",
        "rarity": "rare",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "balance_threshold": 15
        },
        "points": 100,
        "enabled": True,
        "sort_order": 31
    },
    {
        "badge_id": "the_outlier",
        "display_name": "The Outlier",
        "description": "You gave a response that fewer than 5% of people choose. You see things differently.",
        "category": "quirk",
        "icon": "star",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "rare_response_threshold": 0.05
        },
        "points": 50,
        "enabled": True,
        "sort_order": 32
    },
    {
        "badge_id": "beautiful_contradiction",
        "display_name": "Beautiful Contradiction",
        "description": "You scored high on traits that rarely go together. You defy easy categorization.",
        "category": "quirk",
        "icon": "masks",
        "rarity": "legendary",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "contradiction_pair_1": "Openness,Conscientiousness",
            "contradiction_pair_2": "Extraversion,Emotional_Stability",
            "threshold": 80
        },
        "points": 200,
        "enabled": True,
        "sort_order": 33
    },

    # ============================================================================
    # SOCIAL BADGES (disabled until team features launch)
    # ============================================================================
    {
        "badge_id": "team_builder",
        "display_name": "Team Builder",
        "description": "You invited your first team member. Collaboration begins with connection.",
        "category": "social",
        "icon": "users",
        "rarity": "common",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "team_invites_sent": 1
        },
        "points": 25,
        "enabled": False,
        "sort_order": 40
    },
    {
        "badge_id": "bridge_builder",
        "display_name": "Bridge Builder",
        "description": "You've compared profiles with multiple colleagues. Understanding others helps you work together.",
        "category": "social",
        "icon": "bridge",
        "rarity": "uncommon",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "profile_comparisons": 3
        },
        "points": 60,
        "enabled": False,
        "sort_order": 41
    },
    {
        "badge_id": "full_house",
        "display_name": "Full House",
        "description": "Your team has all archetypes represented. Diversity is your superpower.",
        "category": "social",
        "icon": "cards",
        "rarity": "legendary",
        "trigger_type": "automatic",
        "trigger_conditions": {
            "team_archetype_coverage": 8
        },
        "points": 250,
        "enabled": False,
        "sort_order": 42
    }
]


def seed_badge_definitions(dry_run: bool = False):
    """
    Seed all badge definitions to Firestore.

    Args:
        dry_run: If True, just print what would be done without making changes
    """
    badges_ref = db.collection("badge_definitions")

    print(f"{'[DRY RUN] ' if dry_run else ''}Seeding {len(BADGE_DEFINITIONS)} badge definitions...\n")

    created = 0
    updated = 0
    errors = []

    for badge in BADGE_DEFINITIONS:
        badge_id = badge["badge_id"]

        try:
            # Check if badge already exists
            existing = badges_ref.document(badge_id).get()

            # Add timestamps
            badge_data = {
                **badge,
                "updated_at": time.time()
            }

            if existing.exists:
                print(f"  Updating: {badge_id} ({badge['display_name']})")
                if not dry_run:
                    badges_ref.document(badge_id).update(badge_data)
                updated += 1
            else:
                badge_data["created_at"] = time.time()
                print(f"  Creating: {badge_id} ({badge['display_name']})")
                if not dry_run:
                    badges_ref.document(badge_id).set(badge_data)
                created += 1

        except Exception as e:
            error_msg = f"Error with {badge_id}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  - Created: {created}")
    print(f"  - Updated: {updated}")
    print(f"  - Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")


def verify_badges():
    """Verify all badges exist and print summary."""
    badges_ref = db.collection("badge_definitions")

    print("Verifying badge_definitions collection...\n")

    all_badges = list(badges_ref.stream())

    print(f"Total badges: {len(all_badges)}")

    # Group by category
    by_category = {}
    by_rarity = {}
    enabled_count = 0

    for doc in all_badges:
        badge = doc.to_dict()
        cat = badge.get("category", "unknown")
        rarity = badge.get("rarity", "unknown")

        by_category[cat] = by_category.get(cat, 0) + 1
        by_rarity[rarity] = by_rarity.get(rarity, 0) + 1

        if badge.get("enabled", True):
            enabled_count += 1

    print(f"\nBy Category:")
    for cat, count in sorted(by_category.items()):
        print(f"  - {cat}: {count}")

    print(f"\nBy Rarity:")
    for rarity, count in sorted(by_rarity.items()):
        print(f"  - {rarity}: {count}")

    print(f"\nEnabled: {enabled_count} / {len(all_badges)}")


if __name__ == "__main__":
    import sys

    if "--verify" in sys.argv:
        verify_badges()
    elif "--dry-run" in sys.argv or "-n" in sys.argv:
        print("=" * 50)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 50)
        print()
        seed_badge_definitions(dry_run=True)
    else:
        print("=" * 50)
        print("SEED BADGE DEFINITIONS")
        print("=" * 50)
        response = input("\nThis will create/update badge definitions. Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
        seed_badge_definitions(dry_run=False)

    print("\nDone!")
