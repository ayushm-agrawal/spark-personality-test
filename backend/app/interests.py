"""
Interest Categories for Ception Personality Assessment

Provides rich interest categories for the "interest" mode
and optional life areas for the "overall" mode.
"""

# Full interest categories for "interest" mode
INTEREST_CATEGORIES = {
    "Technology": {
        "id": "technology",
        "icon": "💻",
        "color": "#3B82F6",
        "examples": ["coding", "AI/ML", "startups", "hardware", "cybersecurity"],
        "scenario_contexts": [
            "debugging at midnight",
            "shipping features under pressure",
            "tech stack decisions",
            "learning new frameworks",
            "code review conflicts",
            "production outages",
            "technical interviews",
            "open source contributions"
        ],
        "insider_terms": [
            "PR reviews", "sprint planning", "tech debt",
            "deployment", "refactoring", "pair programming"
        ]
    },

    "Design": {
        "id": "design",
        "icon": "🎨",
        "color": "#EC4899",
        "examples": ["UI/UX", "graphic design", "product design", "visual art", "branding"],
        "scenario_contexts": [
            "client revision requests",
            "creative blocks",
            "design system decisions",
            "aesthetic disagreements",
            "user testing feedback",
            "deadline crunches",
            "portfolio reviews",
            "design critiques"
        ],
        "insider_terms": [
            "whitespace", "hierarchy", "iterations",
            "mockups", "design system", "user flows"
        ]
    },

    "Business": {
        "id": "business",
        "icon": "📈",
        "color": "#10B981",
        "examples": ["entrepreneurship", "strategy", "marketing", "finance", "consulting"],
        "scenario_contexts": [
            "investor pitches",
            "negotiation moments",
            "market pivots",
            "team hiring decisions",
            "competitor launches",
            "budget constraints",
            "partnership deals",
            "customer churn"
        ],
        "insider_terms": [
            "runway", "burn rate", "PMF",
            "go-to-market", "unit economics", "churn"
        ]
    },

    "Content": {
        "id": "content",
        "icon": "✍️",
        "color": "#8B5CF6",
        "examples": ["writing", "video", "podcasting", "social media", "journalism"],
        "scenario_contexts": [
            "blank page moments",
            "editing decisions",
            "audience feedback",
            "creative direction conflicts",
            "viral moments",
            "content fatigue",
            "collaboration dynamics",
            "platform algorithm changes"
        ],
        "insider_terms": [
            "hook", "engagement", "algorithm",
            "thumbnail", "retention", "monetization"
        ]
    },

    "Music & Audio": {
        "id": "music",
        "icon": "🎵",
        "color": "#F59E0B",
        "examples": ["production", "performance", "composition", "sound design", "DJing"],
        "scenario_contexts": [
            "studio sessions",
            "live performance pressure",
            "creative differences with collaborators",
            "perfectionism in mixing",
            "gear decisions",
            "writer's block",
            "feedback from listeners",
            "industry networking"
        ],
        "insider_terms": [
            "mix", "master", "DAW",
            "stems", "session", "drop"
        ]
    },

    "Games": {
        "id": "games",
        "icon": "🎮",
        "color": "#EF4444",
        "examples": ["game dev", "esports", "game design", "streaming", "speedrunning"],
        "scenario_contexts": [
            "playtesting feedback",
            "game balance decisions",
            "community management",
            "crunch time releases",
            "competitive pressure",
            "feature cuts",
            "bug prioritization",
            "player retention"
        ],
        "insider_terms": [
            "meta", "nerf", "buff",
            "QA", "build", "patch"
        ]
    },

    "Science & Research": {
        "id": "science",
        "icon": "🔬",
        "color": "#06B6D4",
        "examples": ["research", "academia", "data science", "experiments", "publishing"],
        "scenario_contexts": [
            "hypothesis failures",
            "peer review feedback",
            "methodology debates",
            "breakthrough moments",
            "grant applications",
            "lab dynamics",
            "publication pressure",
            "replication challenges"
        ],
        "insider_terms": [
            "p-value", "methodology", "citations",
            "reproducibility", "peer review", "grant"
        ]
    },

    "Creative Arts": {
        "id": "creative_arts",
        "icon": "🎭",
        "color": "#D946EF",
        "examples": ["photography", "film", "theater", "dance", "fine art"],
        "scenario_contexts": [
            "exhibition deadlines",
            "artistic vision conflicts",
            "creative vulnerability",
            "audience reception",
            "collaboration dynamics",
            "commercial vs artistic choices",
            "critique sessions",
            "creative dry spells"
        ],
        "insider_terms": [
            "composition", "lighting", "blocking",
            "exhibition", "portfolio", "commission"
        ]
    },

    "Other": {
        "id": "other",
        "icon": "✨",
        "color": "#6B7280",
        "examples": ["your unique passion"],
        "allow_custom": True,
        "custom_prompt": "Tell us about your interest...",
        "scenario_contexts": [],
        "insider_terms": []
    }
}


# Simpler life areas for optional context in "overall" mode
LIFE_AREAS = [
    {
        "id": "work",
        "label": "Work & Career",
        "icon": "💼",
        "description": "Professional situations and career decisions"
    },
    {
        "id": "creative",
        "label": "Creative Projects",
        "icon": "🎨",
        "description": "Making things and creative pursuits"
    },
    {
        "id": "social",
        "label": "Social & Relationships",
        "icon": "👥",
        "description": "Interactions with friends, family, and community"
    },
    {
        "id": "learning",
        "label": "Learning & Growth",
        "icon": "📚",
        "description": "Skill development and personal growth"
    }
]


def get_interest_categories() -> dict:
    """Get all interest categories for frontend display."""
    return {
        category: {
            "id": data["id"],
            "icon": data["icon"],
            "color": data["color"],
            "examples": data["examples"],
            "allow_custom": data.get("allow_custom", False)
        }
        for category, data in INTEREST_CATEGORIES.items()
    }


def get_life_areas() -> list:
    """Get life areas for overall mode optional context."""
    return LIFE_AREAS


def get_interest_context(interest: str) -> dict:
    """Get scenario contexts and insider terms for an interest."""
    # Check if it's a known category
    for category, data in INTEREST_CATEGORIES.items():
        if category.lower() == interest.lower() or data["id"] == interest.lower():
            return {
                "name": category,
                "scenario_contexts": data["scenario_contexts"],
                "insider_terms": data["insider_terms"]
            }

    # Custom interest - return generic context
    return {
        "name": interest,
        "scenario_contexts": [
            "challenging moments",
            "collaboration dynamics",
            "creative decisions",
            "time pressure",
            "feedback and criticism"
        ],
        "insider_terms": []
    }


def build_interest_prompt(interest: str) -> str:
    """Build a prompt section for a specific interest."""
    context = get_interest_context(interest)

    prompt = f"""
INTEREST: {context['name']}

Create scenarios that feel authentic to someone deeply involved in {context['name']}.

Scenario Inspiration:
{chr(10).join(f"- {s}" for s in context['scenario_contexts'][:4])}
"""

    if context["insider_terms"]:
        prompt += f"""
Domain Language (use naturally, don't force):
{', '.join(context['insider_terms'][:6])}
"""

    return prompt


def validate_interests(interests: list, mode: str, min_count: int = 2, max_count: int = 4) -> dict:
    """Validate interest selection for a given mode."""
    if mode == "hackathon":
        return {"valid": True, "interests": []}

    if mode == "overall":
        # Optional interests
        return {"valid": True, "interests": interests or []}

    if mode == "interest":
        if not interests:
            return {
                "valid": False,
                "error": f"Please select at least {min_count} interests"
            }
        if len(interests) < min_count:
            return {
                "valid": False,
                "error": f"Please select at least {min_count} interests"
            }
        if len(interests) > max_count:
            return {
                "valid": False,
                "error": f"Please select at most {max_count} interests"
            }
        return {"valid": True, "interests": interests}

    return {"valid": True, "interests": interests or []}
