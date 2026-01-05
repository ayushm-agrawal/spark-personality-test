"""
Backfill script to add usernames for existing user profiles.

Run from backend/app directory:
    python backfill_usernames.py

This will:
1. Find all user_profiles without a username
2. Fetch display_name from Firebase Auth if not stored
3. Generate a unique username from display_name or user_id
4. Update each profile with the generated username
"""

import time
from firebase import db
from firebase_admin import auth
from services import generate_unique_username, generate_random_suffix


def get_display_name_from_auth(user_id):
    """Fetch display name from Firebase Auth for a given user_id."""
    if not user_id:
        return None
    try:
        user = auth.get_user(user_id)
        return user.display_name
    except Exception as e:
        print(f"    Could not fetch auth info for {user_id}: {e}")
        return None


def backfill_usernames(dry_run=False):
    """
    Backfill usernames for all existing profiles that don't have one.

    Args:
        dry_run: If True, just print what would be done without making changes
    """
    profiles_ref = db.collection("user_profiles")

    # Get all profiles
    all_profiles = list(profiles_ref.stream())

    print(f"Found {len(all_profiles)} total profiles")

    profiles_without_username = []
    profiles_with_username = []

    for doc in all_profiles:
        profile = doc.to_dict()
        if profile.get("username"):
            profiles_with_username.append(doc.id)
        else:
            profiles_without_username.append((doc.id, profile))

    print(f"  - {len(profiles_with_username)} already have usernames")
    print(f"  - {len(profiles_without_username)} need usernames")

    if not profiles_without_username:
        print("\nNo profiles need backfilling!")
        return

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Generating usernames...\n")

    updated_count = 0
    errors = []

    for profile_id, profile in profiles_without_username:
        # Try to get a name to base username on
        display_name = profile.get("display_name")
        user_id = profile.get("user_id")

        # If no display_name stored, try to fetch from Firebase Auth
        if not display_name and user_id:
            print(f"  {profile_id[:8]}... fetching display_name from Auth...")
            display_name = get_display_name_from_auth(user_id)

        # Generate username
        if display_name:
            base_name = display_name
        elif user_id:
            # Use first part of user_id as fallback
            base_name = f"user-{user_id[:8]}"
        else:
            # Random username
            base_name = f"user-{generate_random_suffix(8)}"

        try:
            username = generate_unique_username(base_name)

            print(f"  {profile_id[:8]}... -> @{username} (from: {display_name or user_id or 'random'})")

            if not dry_run:
                update_data = {
                    "username": username,
                    "username_set_at": time.time(),
                    "updated_at": time.time()
                }
                # Also save display_name if we fetched it from Auth
                if display_name and not profile.get("display_name"):
                    update_data["display_name"] = display_name

                profiles_ref.document(profile_id).update(update_data)

            updated_count += 1

        except Exception as e:
            error_msg = f"Error processing {profile_id}: {str(e)}"
            print(f"  ERROR: {error_msg}")
            errors.append(error_msg)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Results:")
    print(f"  - Updated: {updated_count}")
    print(f"  - Errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    import sys

    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if dry_run:
        print("=" * 50)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 50)
    else:
        print("=" * 50)
        print("BACKFILL USERNAMES")
        print("=" * 50)
        response = input("\nThis will update existing profiles. Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    print()
    backfill_usernames(dry_run=dry_run)
    print("\nDone!")
