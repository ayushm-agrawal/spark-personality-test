"""
Assessment Mode Configurations for Ception

Three distinct modes that change how the assessment behaves:
- hackathon: Quick, pressure-focused, no interest selection
- overall: Balanced life assessment, optional interests
- interest: Deep dive into user's passion areas, required interests
"""

ASSESSMENT_MODES = {
    "hackathon": {
        "display_name": "Hackathon Mode",
        "description": "How you collaborate under pressure. 6 quick questions.",
        "duration_label": "~2 minutes",
        "question_count": 6,
        "requires_interests": False,
        "allow_optional_interests": False,
        "interest_context": "hackathon",
        "traits_focus": ["Conscientiousness", "Extraversion", "Emotional_Stability"],
        "scenario_type": "hackathon_pressure",
        "freeform_probability": 0.1,  # Less freeform in quick mode
        "prompt_context": """
CONTEXT: This is a HACKATHON personality assessment.
ALL questions MUST be framed around 24-hour hackathon/sprint scenarios.

Focus Areas:
- Collaboration under extreme time pressure
- Shipping vs. perfecting (MVP mindset)
- Handling teammate conflicts at 3am
- Energy and focus management
- Dealing with ambiguity and pivots
- Demo day pressure

Scenario Style:
- Short, punchy, time-specific ("Hour 18.", "Demo in 6 hours.", "3am.")
- Visceral details (cold coffee, blinking cursor, tired teammates)
- Real hackathon moments, not generic team situations

EXAMPLE SCENARIOS:
- "Hour 18. Your MVP works but looks terrible. Demo in 6 hours."
- "Your teammate hasn't pushed code in 3 hours. They say they're 'almost done.'"
- "The wifi dies. Your code is on your laptop. Teammate's code is on theirs."
- "A judge stops at your table mid-build. 'What problem does this solve?'"
- "2am. Energy drinks are gone. Someone suggests 'just shipping what we have.'"
- "The feature you cut yesterday would've won. You're sure of it."

FORBIDDEN:
- Generic workplace scenarios
- "Imagine you're in a team meeting..."
- Any scenario that doesn't feel like a hackathon
"""
    },

    "overall": {
        "display_name": "Full Profile",
        "description": "Your personality across all areas of life. Comprehensive assessment.",
        "duration_label": "~5 minutes",
        "question_count": 10,
        "requires_interests": False,
        "allow_optional_interests": True,
        "interest_context": "general_life",
        "traits_focus": ["all"],
        "scenario_type": "varied_life_situations",
        "freeform_probability": 0.15,
        "prompt_context": """
CONTEXT: This is a GENERAL personality assessment across life situations.

Create VARIED scenarios spanning:
- Professional moments (not just meetings—specific situations)
- Personal projects and hobbies
- Social dynamics and relationships
- Creative challenges and blocks
- Problem-solving and decision moments
- Moments of success and setback

Emotional Temperature Mix:
- HIGH stakes: "Demo day. Nothing works. 10 minutes."
- MEDIUM stakes: "A colleague disagrees with your approach publicly."
- LOW stakes: "You stumble on a technique you've never seen before."

Scenario Style:
- Vivid, sensory details
- Specific moments in time, not general patterns
- Situations that trigger authentic reactions
- Mix of work, creative, social, and personal contexts

FORBIDDEN:
- "How do you typically..." (asks for self-description)
- Generic team scenarios
- Combining multiple contexts in one question
- Obviously leading questions
"""
    },

    "deep_dive": {
        "display_name": "Deep Dive",
        "description": "How your personality shows up in the areas of life you care about most.",
        "duration_label": "~5 minutes",
        "question_count": 10,
        "requires_interests": True,
        "allow_optional_interests": False,
        "min_interests": 2,
        "max_interests": 4,
        "interest_context": "life_contexts",
        "traits_focus": ["all"],
        "scenario_type": "context_specific",
        "freeform_probability": 0.2,  # More freeform for deeper exploration
        "prompt_context": """
CONTEXT: This is a LIFE CONTEXT personality assessment.

The user has selected specific areas of their life to explore.
CRITICAL RULE: Each question uses EXACTLY ONE life context from the user's list.
Rotate through contexts: If contexts are [A, B, C], questions go A, B, C, A, B, C...

For each life context, create scenarios that:
- Feel authentic to that area of life
- Reveal personality through context-specific challenges
- Use realistic, relatable details

FORBIDDEN:
- "When dealing with work and relationships..."
- Combining multiple contexts in one question
- Generic scenarios that could apply to any context
- Surface-level or cliche situations

REQUIRED:
- Deep, specific scenarios within each life context
- Situations that feel real and personal
- Scenarios that trigger authentic reactions
"""
    },
    # Legacy alias for backwards compatibility
    "interest": {
        "display_name": "Deep Dive",
        "description": "How your personality shows up in the areas of life you care about most.",
        "duration_label": "~5 minutes",
        "question_count": 10,
        "requires_interests": True,
        "allow_optional_interests": False,
        "min_interests": 2,
        "max_interests": 4,
        "interest_context": "life_contexts",
        "traits_focus": ["all"],
        "scenario_type": "context_specific",
        "freeform_probability": 0.2,
        "prompt_context": """
CONTEXT: This is a LIFE CONTEXT personality assessment.
(Legacy mode - redirects to deep_dive)
"""
    }
}


def get_mode_config(mode: str) -> dict:
    """Get configuration for a specific mode."""
    return ASSESSMENT_MODES.get(mode, ASSESSMENT_MODES["overall"])


def get_all_modes() -> dict:
    """Get all mode configurations for frontend display."""
    return {
        mode: {
            "display_name": config["display_name"],
            "description": config["description"],
            "duration_label": config["duration_label"],
            "question_count": config["question_count"],
            "requires_interests": config["requires_interests"],
            "allow_optional_interests": config.get("allow_optional_interests", False)
        }
        for mode, config in ASSESSMENT_MODES.items()
    }


def get_mode_prompt_context(mode: str, interests: list = None, question_number: int = 0) -> str:
    """
    Get the prompt context for a specific mode.

    For interest mode, this also handles interest rotation.
    """
    config = get_mode_config(mode)
    base_context = config["prompt_context"]

    if mode == "interest" and interests:
        # Determine which interest to use for this question
        current_interest = interests[question_number % len(interests)]
        interest_context = f"""
CURRENT QUESTION INTEREST: {current_interest}
This question MUST be specifically about {current_interest}.
Do NOT mention any other interests.
Create a vivid, specific scenario within the {current_interest} domain.
"""
        return base_context + interest_context

    return base_context


def should_skip_interests(mode: str) -> bool:
    """Check if a mode should skip interest selection."""
    config = get_mode_config(mode)
    return not config["requires_interests"]


def get_interest_requirements(mode: str) -> dict:
    """Get interest selection requirements for a mode."""
    config = get_mode_config(mode)

    if not config["requires_interests"] and not config.get("allow_optional_interests"):
        return {"required": False, "show_selection": False}

    if config.get("allow_optional_interests"):
        return {
            "required": False,
            "show_selection": True,
            "optional": True,
            "skip_label": "Skip - assess me across all areas"
        }

    return {
        "required": True,
        "show_selection": True,
        "min": config.get("min_interests", 2),
        "max": config.get("max_interests", 4)
    }
