"""
Seed and manage response_statistics collection for percentile tracking.

Run from backend/app directory:
    python seed_statistics.py --init       # Initialize collection
    python seed_statistics.py --update     # Update statistics from current data
    python seed_statistics.py --verify     # Verify collection

This creates and maintains:
- global_stats: Total counts
- trait_percentiles: Distribution data for each trait
- archetype_distribution: User counts per archetype
"""

import time
import sys
from collections import defaultdict
from firebase import db


def initialize_statistics():
    """Initialize the response_statistics collection with default structure."""
    stats_ref = db.collection("response_statistics")
    current_time = time.time()

    print("Initializing response_statistics collection...\n")

    # Global stats document
    global_stats = {
        "total_assessments": 0,
        "total_users": 0,
        "total_profiles": 0,
        "last_updated": current_time,
        "created_at": current_time
    }

    # Trait percentiles document
    trait_percentiles = {
        "Openness": {"p5": 20, "p25": 40, "p50": 55, "p75": 70, "p95": 90},
        "Conscientiousness": {"p5": 25, "p25": 45, "p50": 60, "p75": 75, "p95": 90},
        "Extraversion": {"p5": 20, "p25": 40, "p50": 55, "p75": 70, "p95": 85},
        "Agreeableness": {"p5": 30, "p25": 50, "p50": 65, "p75": 80, "p95": 95},
        "Emotional_Stability": {"p5": 25, "p25": 45, "p50": 60, "p75": 75, "p95": 90},
        "last_updated": current_time,
        "sample_size": 0,
        "created_at": current_time
    }

    # Archetype distribution document
    archetype_distribution = {
        "counts": {
            "The Architect": 0,
            "The Catalyst": 0,
            "The Strategist": 0,
            "The Guide": 0,
            "The Alchemist": 0,
            "The Gardener": 0,
            "The Luminary": 0,
            "The Sentinel": 0
        },
        "percentages": {
            "The Architect": 0,
            "The Catalyst": 0,
            "The Strategist": 0,
            "The Guide": 0,
            "The Alchemist": 0,
            "The Gardener": 0,
            "The Luminary": 0,
            "The Sentinel": 0
        },
        "total": 0,
        "last_updated": current_time,
        "created_at": current_time
    }

    # Response frequencies document (for rare response detection)
    response_frequencies = {
        "question_responses": {},  # Will be populated as questions are answered
        "rare_threshold": 0.05,  # 5% threshold for "outlier" badge
        "last_updated": current_time,
        "created_at": current_time
    }

    # Write documents
    print("  Creating global_stats...")
    stats_ref.document("global_stats").set(global_stats)

    print("  Creating trait_percentiles...")
    stats_ref.document("trait_percentiles").set(trait_percentiles)

    print("  Creating archetype_distribution...")
    stats_ref.document("archetype_distribution").set(archetype_distribution)

    print("  Creating response_frequencies...")
    stats_ref.document("response_frequencies").set(response_frequencies)

    print("\nDone! Created 4 documents in response_statistics collection.")


def update_statistics():
    """Update statistics from current profile data."""
    print("Updating statistics from current data...\n")

    profiles_ref = db.collection("user_profiles")
    stats_ref = db.collection("response_statistics")
    current_time = time.time()

    # Collect data
    all_profiles = list(profiles_ref.stream())

    total_profiles = len(all_profiles)
    total_assessments = 0
    archetype_counts = defaultdict(int)
    trait_scores = defaultdict(list)

    print(f"Processing {total_profiles} profiles...")

    for doc in all_profiles:
        profile = doc.to_dict()

        # Count assessments
        test_history = profile.get("test_history", [])
        total_assessments += len(test_history)

        # Count archetypes
        current_archetype = profile.get("current_archetype")
        if current_archetype:
            archetype_counts[current_archetype] += 1

        # Collect trait scores for percentile calculation
        mode_profiles = profile.get("mode_profiles", {})
        for mode_data in mode_profiles.values():
            weighted_scores = mode_data.get("weighted_scores", {})
            for trait, score_data in weighted_scores.items():
                if isinstance(score_data, dict):
                    total = score_data.get("weight_total", 0)
                    if total > 0:
                        score = score_data.get("weighted_sum", 0) / total
                        trait_scores[trait].append(score)

    # Calculate percentiles
    def calculate_percentiles(scores):
        if not scores:
            return {"p5": 20, "p25": 40, "p50": 55, "p75": 70, "p95": 90}
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        return {
            "p5": sorted_scores[int(n * 0.05)] if n > 0 else 20,
            "p25": sorted_scores[int(n * 0.25)] if n > 0 else 40,
            "p50": sorted_scores[int(n * 0.50)] if n > 0 else 55,
            "p75": sorted_scores[int(n * 0.75)] if n > 0 else 70,
            "p95": sorted_scores[int(n * 0.95)] if n > 0 else 90
        }

    # Update global stats
    print("\n  Updating global_stats...")
    stats_ref.document("global_stats").update({
        "total_assessments": total_assessments,
        "total_profiles": total_profiles,
        "last_updated": current_time
    })

    # Update trait percentiles
    print("  Updating trait_percentiles...")
    percentile_update = {"last_updated": current_time}
    sample_size = 0
    for trait, scores in trait_scores.items():
        percentile_update[trait] = calculate_percentiles(scores)
        sample_size = max(sample_size, len(scores))
    percentile_update["sample_size"] = sample_size
    stats_ref.document("trait_percentiles").update(percentile_update)

    # Update archetype distribution
    print("  Updating archetype_distribution...")
    total_archetypes = sum(archetype_counts.values())
    percentages = {}
    for archetype, count in archetype_counts.items():
        if total_archetypes > 0:
            percentages[archetype] = round(count / total_archetypes * 100, 1)
        else:
            percentages[archetype] = 0

    stats_ref.document("archetype_distribution").update({
        "counts": dict(archetype_counts),
        "percentages": percentages,
        "total": total_archetypes,
        "last_updated": current_time
    })

    print(f"\nStatistics updated!")
    print(f"  - Total profiles: {total_profiles}")
    print(f"  - Total assessments: {total_assessments}")
    print(f"  - Trait score samples: {sample_size}")
    print(f"  - Archetypes tracked: {total_archetypes}")


def verify_statistics():
    """Verify the response_statistics collection."""
    stats_ref = db.collection("response_statistics")

    print("Verifying response_statistics collection...\n")

    docs = ["global_stats", "trait_percentiles", "archetype_distribution", "response_frequencies"]

    for doc_id in docs:
        doc = stats_ref.document(doc_id).get()
        if doc.exists:
            data = doc.to_dict()
            last_updated = data.get("last_updated", 0)
            updated_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(last_updated)) if last_updated else "Never"
            print(f"  {doc_id}: EXISTS (updated: {updated_str})")

            # Show some stats
            if doc_id == "global_stats":
                print(f"    - Total profiles: {data.get('total_profiles', 0)}")
                print(f"    - Total assessments: {data.get('total_assessments', 0)}")
            elif doc_id == "archetype_distribution":
                total = data.get("total", 0)
                print(f"    - Total archetypes: {total}")
                if total > 0:
                    counts = data.get("counts", {})
                    top3 = sorted(counts.items(), key=lambda x: -x[1])[:3]
                    for arch, count in top3:
                        print(f"    - {arch}: {count}")
            elif doc_id == "trait_percentiles":
                sample = data.get("sample_size", 0)
                print(f"    - Sample size: {sample}")
        else:
            print(f"  {doc_id}: MISSING")

    print("\nDone!")


def get_trait_percentile(trait: str, score: float) -> int:
    """Get the percentile rank for a trait score."""
    stats_ref = db.collection("response_statistics")
    doc = stats_ref.document("trait_percentiles").get()

    if not doc.exists:
        return 50  # Default to median

    data = doc.to_dict()
    trait_data = data.get(trait, {})

    # Find percentile bracket
    if score <= trait_data.get("p5", 20):
        return 5
    elif score <= trait_data.get("p25", 40):
        return 25
    elif score <= trait_data.get("p50", 55):
        return 50
    elif score <= trait_data.get("p75", 70):
        return 75
    elif score <= trait_data.get("p95", 90):
        return 95
    else:
        return 99


def increment_assessment_count():
    """Increment the global assessment counter (call after each assessment)."""
    stats_ref = db.collection("response_statistics")
    from google.cloud.firestore import Increment

    stats_ref.document("global_stats").update({
        "total_assessments": Increment(1),
        "last_updated": time.time()
    })


if __name__ == "__main__":
    if "--init" in sys.argv:
        print("=" * 50)
        print("INITIALIZE STATISTICS COLLECTION")
        print("=" * 50)
        response = input("\nThis will create/reset the statistics collection. Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
        initialize_statistics()

    elif "--update" in sys.argv:
        print("=" * 50)
        print("UPDATE STATISTICS FROM DATA")
        print("=" * 50)
        print()
        update_statistics()

    elif "--verify" in sys.argv:
        verify_statistics()

    else:
        print("Usage:")
        print("  python seed_statistics.py --init     # Initialize collection")
        print("  python seed_statistics.py --update   # Update from current data")
        print("  python seed_statistics.py --verify   # Verify collection")
