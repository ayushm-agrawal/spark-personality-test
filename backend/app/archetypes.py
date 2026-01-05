"""
Archetype Definitions for Ception Personality Assessment

Inspired by Adobe Creative Types, these archetypes represent compelling
personality profiles that map to Big Five trait combinations. Each archetype
is designed to feel like an identity people want to share.
"""

from functools import lru_cache

# Big Five trait levels for matching
TRAIT_LEVELS = {
    "very_low": (0, 20),
    "low": (20, 40),
    "medium": (40, 60),
    "medium_high": (60, 75),
    "high": (75, 90),
    "very_high": (90, 100)
}


ARCHETYPES = {
    "The Architect": {
        "tagline": "Building tomorrow's blueprint, today.",
        "color": "#1B5E20",  # Deep green
        "emoji": "🏗️",
        "zone_of_genius": "Turning ambitious visions into executable plans",
        "deepest_aspiration": "Creating something that outlasts you",
        "growth_opportunity": "Embracing imperfection and enjoying the journey",
        "creative_partner": "The Alchemist",
        "description": "You don't just dream—you build. While others get lost in possibilities, you're already sketching the blueprint. Your mind naturally breaks down complex visions into actionable steps, and you won't rest until the foundation is solid. You're the rare combination of visionary and executor, equally comfortable in brainstorming sessions and deep work sprints.",
        "team_value": "The one who actually ships. Transforms chaos into structure without killing creativity.",
        "hackathon_superpower": "Scoping the MVP that actually wins",
        "hackathon_pitfall": "Over-engineering when scrappy would do",
        "big_five_profile": {
            "Openness": 75,
            "Conscientiousness": 85,
            "Extraversion": 60,
            "Agreeableness": 55,
            "Emotional_Stability": 70
        }
    },

    "The Catalyst": {
        "tagline": "Sparking change, one idea at a time.",
        "color": "#FF6F00",  # Vibrant orange
        "emoji": "⚡",
        "zone_of_genius": "Igniting momentum and bringing energy to any room",
        "deepest_aspiration": "Being the spark that starts something bigger",
        "growth_opportunity": "Following through after the initial excitement fades",
        "creative_partner": "The Gardener",
        "description": "You're the match that lights the fire. Ideas flow through you like electricity, and your enthusiasm is genuinely contagious. You see connections others miss and aren't afraid to voice the unconventional take. People feel more creative just being around you. The world needs your energy—you make things happen that wouldn't happen without you.",
        "team_value": "The energy source. Breaks through stagnation and rallies people around new possibilities.",
        "hackathon_superpower": "Pivoting when the original idea isn't working",
        "hackathon_pitfall": "Starting three projects instead of finishing one",
        "big_five_profile": {
            "Openness": 90,
            "Conscientiousness": 50,
            "Extraversion": 85,
            "Agreeableness": 65,
            "Emotional_Stability": 55
        }
    },

    "The Strategist": {
        "tagline": "Three moves ahead, always.",
        "color": "#1A237E",  # Deep indigo
        "emoji": "♟️",
        "zone_of_genius": "Seeing the whole board while others focus on one piece",
        "deepest_aspiration": "Orchestrating wins that look inevitable in hindsight",
        "growth_opportunity": "Letting others in on your thinking earlier",
        "creative_partner": "The Catalyst",
        "description": "While others react, you anticipate. Your mind naturally maps out scenarios, weighing options most people don't even see. You're not cold—you're clear. When the pressure mounts, you get calmer, because you've already thought through what comes next. Teams look to you when the stakes are highest.",
        "team_value": "The navigator. Keeps everyone oriented toward the actual goal when distractions multiply.",
        "hackathon_superpower": "Knowing which features to cut before building them",
        "hackathon_pitfall": "Analysis paralysis when quick decisions are needed",
        "big_five_profile": {
            "Openness": 70,
            "Conscientiousness": 80,
            "Extraversion": 70,
            "Agreeableness": 50,
            "Emotional_Stability": 85
        }
    },

    "The Guide": {
        "tagline": "Lighting the path for others to follow.",
        "color": "#00695C",  # Teal
        "emoji": "🧭",
        "zone_of_genius": "Helping others discover what they're capable of",
        "deepest_aspiration": "Leaving people better than you found them",
        "growth_opportunity": "Putting your own oxygen mask on first",
        "creative_partner": "The Strategist",
        "description": "You have a gift for seeing potential—in ideas, in projects, but especially in people. You're the one who asks the question that changes the conversation, who notices when someone's contribution gets overlooked. Your impact often happens in moments others don't see: the encouragement before the big pitch, the reframe that unsticks someone's thinking.",
        "team_value": "The multiplier. Makes everyone around them more effective and confident.",
        "hackathon_superpower": "Resolving team conflicts before they derail everything",
        "hackathon_pitfall": "Prioritizing harmony over honest feedback",
        "big_five_profile": {
            "Openness": 75,
            "Conscientiousness": 60,
            "Extraversion": 75,
            "Agreeableness": 90,
            "Emotional_Stability": 65
        }
    },

    "The Alchemist": {
        "tagline": "Transforming the ordinary into extraordinary.",
        "color": "#6A1B9A",  # Deep purple
        "emoji": "🔮",
        "zone_of_genius": "Finding meaning and beauty in unexpected places",
        "deepest_aspiration": "Creating something that makes people feel understood",
        "growth_opportunity": "Sharing your work before it feels 'ready'",
        "creative_partner": "The Architect",
        "description": "You see what others walk past. Where they see a problem, you see raw material. Your mind works through synthesis—combining ideas, experiences, and observations into something that didn't exist before. You need space to think, and your best insights often come from unexpected sources. The work you create has layers others discover over time.",
        "team_value": "The depth-finder. Asks 'what if' when everyone else is stuck on 'what is'.",
        "hackathon_superpower": "The 2am breakthrough that changes everything",
        "hackathon_pitfall": "Perfectionism when 'good enough' would win",
        "big_five_profile": {
            "Openness": 95,
            "Conscientiousness": 55,
            "Extraversion": 35,
            "Agreeableness": 60,
            "Emotional_Stability": 70
        }
    },

    "The Gardener": {
        "tagline": "Nurturing growth, cultivating excellence.",
        "color": "#2E7D32",  # Forest green
        "emoji": "🌱",
        "zone_of_genius": "Creating environments where people and projects thrive",
        "deepest_aspiration": "Building something sustainable that grows beyond you",
        "growth_opportunity": "Advocating for your own needs as strongly as others'",
        "creative_partner": "The Catalyst",
        "description": "You play the long game. While others chase quick wins, you're building something that compounds. You have patience others don't—not passive waiting, but active cultivation. You notice what needs attention before it becomes urgent. The projects and people you invest in tend to flourish because you give them what they actually need, not what's easiest.",
        "team_value": "The sustainer. Keeps momentum going when initial excitement fades.",
        "hackathon_superpower": "Keeping the team functional at hour 20",
        "hackathon_pitfall": "Taking on everyone else's emotional labor",
        "big_five_profile": {
            "Openness": 60,
            "Conscientiousness": 80,
            "Extraversion": 55,
            "Agreeableness": 85,
            "Emotional_Stability": 75
        }
    },

    "The Luminary": {
        "tagline": "Illuminating what could be.",
        "color": "#F9A825",  # Golden yellow
        "emoji": "✨",
        "zone_of_genius": "Painting visions that inspire others to act",
        "deepest_aspiration": "Changing how people see what's possible",
        "growth_opportunity": "Grounding dreams in concrete next steps",
        "creative_partner": "The Gardener",
        "description": "You see the world as it could be, and you help others see it too. Your optimism isn't naive—it's generative. You genuinely believe in people's potential, and somehow that belief helps them access it. You're drawn to the edge of what's known, comfortable with ambiguity that makes others anxious. Your gift is making the future feel not just possible, but inevitable.",
        "team_value": "The vision-holder. Keeps everyone inspired when the work gets hard.",
        "hackathon_superpower": "The pitch that makes judges lean in",
        "hackathon_pitfall": "Overpromising what can be built in 24 hours",
        "big_five_profile": {
            "Openness": 90,
            "Conscientiousness": 45,
            "Extraversion": 70,
            "Agreeableness": 80,
            "Emotional_Stability": 60
        }
    },

    "The Sentinel": {
        "tagline": "Steady hands in turbulent times.",
        "color": "#37474F",  # Steel gray
        "emoji": "🛡️",
        "zone_of_genius": "Staying effective when everything is falling apart",
        "deepest_aspiration": "Being the person others can count on, no matter what",
        "growth_opportunity": "Asking for help before reaching your limit",
        "creative_partner": "The Luminary",
        "description": "When others panic, you focus. Crisis doesn't rattle you—it clarifies your thinking. You're the one people instinctively turn to when things go sideways, not because you have all the answers, but because your presence is stabilizing. You notice risks others dismiss and prepare for scenarios others don't imagine. Your reliability isn't boring—it's the foundation that lets others take risks.",
        "team_value": "The anchor. Creates psychological safety that enables everyone else's creativity.",
        "hackathon_superpower": "Debugging at 4am when everyone else has lost focus",
        "hackathon_pitfall": "Being so reliable that others stop pulling their weight",
        "big_five_profile": {
            "Openness": 50,
            "Conscientiousness": 85,
            "Extraversion": 40,
            "Agreeableness": 65,
            "Emotional_Stability": 90
        }
    }
}


# Compatibility matrix for creative partnerships
ARCHETYPE_COMPATIBILITY = {
    "The Architect": {
        "ideal_partners": ["The Alchemist", "The Catalyst"],
        "growth_partners": ["The Luminary"],
        "complementary_strengths": "Your structure meets their creativity"
    },
    "The Catalyst": {
        "ideal_partners": ["The Gardener", "The Architect"],
        "growth_partners": ["The Sentinel"],
        "complementary_strengths": "Your energy meets their sustainability"
    },
    "The Strategist": {
        "ideal_partners": ["The Catalyst", "The Guide"],
        "growth_partners": ["The Alchemist"],
        "complementary_strengths": "Your clarity meets their intuition"
    },
    "The Guide": {
        "ideal_partners": ["The Strategist", "The Alchemist"],
        "growth_partners": ["The Architect"],
        "complementary_strengths": "Your empathy meets their vision"
    },
    "The Alchemist": {
        "ideal_partners": ["The Architect", "The Guide"],
        "growth_partners": ["The Catalyst"],
        "complementary_strengths": "Your depth meets their execution"
    },
    "The Gardener": {
        "ideal_partners": ["The Catalyst", "The Luminary"],
        "growth_partners": ["The Strategist"],
        "complementary_strengths": "Your patience meets their urgency"
    },
    "The Luminary": {
        "ideal_partners": ["The Gardener", "The Sentinel"],
        "growth_partners": ["The Architect"],
        "complementary_strengths": "Your vision meets their grounding"
    },
    "The Sentinel": {
        "ideal_partners": ["The Luminary", "The Catalyst"],
        "growth_partners": ["The Guide"],
        "complementary_strengths": "Your stability meets their dynamism"
    }
}


def get_archetype_profile(archetype_name: str) -> dict:
    """Get the Big Five profile for an archetype as normalized values."""
    if archetype_name not in ARCHETYPES:
        return None
    return ARCHETYPES[archetype_name]["big_five_profile"]


def get_archetype_names() -> list:
    """Get list of all archetype names."""
    return list(ARCHETYPES.keys())


@lru_cache(maxsize=16)
def get_archetype_for_display(archetype_name: str) -> dict:
    """Get archetype data formatted for frontend display. Results are cached."""
    if archetype_name not in ARCHETYPES:
        return None

    archetype = ARCHETYPES[archetype_name]
    compatibility = ARCHETYPE_COMPATIBILITY.get(archetype_name, {})

    return {
        "name": archetype_name,
        "tagline": archetype["tagline"],
        "color": archetype["color"],
        "emoji": archetype["emoji"],
        "description": archetype["description"],
        "zone_of_genius": archetype["zone_of_genius"],
        "deepest_aspiration": archetype["deepest_aspiration"],
        "growth_opportunity": archetype["growth_opportunity"],
        "creative_partner": archetype["creative_partner"],
        "team_value": archetype["team_value"],
        "hackathon_superpower": archetype.get("hackathon_superpower", ""),
        "hackathon_pitfall": archetype.get("hackathon_pitfall", ""),
        "ideal_partners": compatibility.get("ideal_partners", []),
        "growth_partners": compatibility.get("growth_partners", []),
        "big_five_profile": archetype.get("big_five_profile", {})
    }
