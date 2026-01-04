"""
Upload/Update Knowledge Base to Firestore

This script updates the Firestore knowledge_base with:
- Big Five traits
- New archetypes from archetypes.py
"""

from firebase import db
from archetypes import ARCHETYPES, ARCHETYPE_COMPATIBILITY

# Big Five traits
TRAITS = [
    "Openness",
    "Conscientiousness",
    "Extraversion",
    "Agreeableness",
    "Emotional_Stability"
]

def upload_knowledge_base():
    """Upload the knowledge base to Firestore."""

    # Build archetypes dict for Firestore (simplified version for backwards compatibility)
    archetypes_for_firestore = {}
    for name, data in ARCHETYPES.items():
        archetypes_for_firestore[name] = {
            "description": data["description"],
            "tagline": data["tagline"],
            "color": data["color"],
            "emoji": data["emoji"],
            "zone_of_genius": data["zone_of_genius"],
            "deepest_aspiration": data["deepest_aspiration"],
            "growth_opportunity": data["growth_opportunity"],
            "creative_partner": data["creative_partner"],
            "team_value": data["team_value"],
            "hackathon_superpower": data["hackathon_superpower"],
            "hackathon_pitfall": data["hackathon_pitfall"],
            "big_five_profile": data["big_five_profile"]
        }

    knowledge_base = {
        "traits": TRAITS,
        "archetypes": archetypes_for_firestore,
        "archetype_compatibility": ARCHETYPE_COMPATIBILITY
    }

    # Upload to Firestore
    doc_ref = db.collection("knowledge_base").document("big_five_test")
    doc_ref.set(knowledge_base)

    print("Knowledge base uploaded successfully!")
    print(f"  - Traits: {len(TRAITS)}")
    print(f"  - Archetypes: {len(archetypes_for_firestore)}")
    for name in archetypes_for_firestore:
        print(f"    - {name}")


if __name__ == "__main__":
    upload_knowledge_base()
