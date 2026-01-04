"""
Jinja2 Templating System for Ception Personality Assessment

This module provides structured prompt templates for the LLM,
replacing string concatenation with maintainable Jinja2 templates.
"""

from functools import lru_cache
from jinja2 import Template
from typing import List, Dict, Optional

# Life Context Categories for deep_dive mode
LIFE_CONTEXT_CATEGORIES = {
    "work_career": {
        "label": "Work & Career",
        "description": "How you handle deadlines, feedback, and ambition",
        "icon": "💼",
        "scenario_contexts": [
            "performance reviews",
            "difficult colleagues",
            "competing priorities",
            "career decisions",
            "leadership moments",
            "deadline pressure",
            "receiving critical feedback",
            "advocating for yourself"
        ]
    },
    "creative_projects": {
        "label": "Creative Projects",
        "description": "How you create, iterate, and handle criticism",
        "icon": "🎨",
        "scenario_contexts": [
            "creative blocks",
            "sharing your work",
            "collaboration vs solo",
            "perfectionism",
            "inspiration dry spells",
            "revision requests",
            "starting from scratch",
            "imposter syndrome"
        ]
    },
    "learning_growth": {
        "label": "Learning & Growth",
        "description": "How you approach new skills and knowledge",
        "icon": "📚",
        "scenario_contexts": [
            "feeling like a beginner",
            "information overload",
            "asking for help",
            "mastery vs breadth",
            "failure as feedback",
            "stuck on a concept",
            "comparing to others",
            "choosing what to learn"
        ]
    },
    "relationships": {
        "label": "Relationships & Social",
        "description": "How you connect, support, and handle conflict",
        "icon": "👥",
        "scenario_contexts": [
            "new social situations",
            "deep friendships",
            "conflict resolution",
            "boundaries",
            "supporting others",
            "difficult conversations",
            "group dynamics",
            "vulnerability"
        ]
    },
    "challenges_adversity": {
        "label": "Challenges & Adversity",
        "description": "How you respond when things go wrong",
        "icon": "🔥",
        "scenario_contexts": [
            "unexpected setbacks",
            "high-pressure moments",
            "uncertainty",
            "bouncing back",
            "asking for help",
            "admitting mistakes",
            "pivoting plans",
            "staying motivated"
        ]
    },
    "personal_time": {
        "label": "Personal Time & Energy",
        "description": "How you recharge and spend time alone",
        "icon": "🌙",
        "scenario_contexts": [
            "alone time",
            "decision fatigue",
            "energy management",
            "saying no",
            "self-care",
            "guilt about rest",
            "overscheduling",
            "routines vs spontaneity"
        ]
    }
}


# Main system prompt template
SYSTEM_PROMPT_TEMPLATE = """
You are a personality assessment engine creating dynamic, engaging questions that feel like moments in someone's life—not a survey.

## Core Philosophy
Traditional personality tests fail because they ask people to describe themselves. People are terrible at self-description. Instead, you create vivid scenarios that trigger authentic reactions. The user should feel like they're living a moment and simply responding—not analyzing their own personality.

## Current Session Context
- **Mode:** {{ mode }}
- **Question Number:** {{ question_number }} of {{ total_questions }}
- **Traits Assessed So Far:** {{ traits_assessed | join(', ') if traits_assessed else 'None yet' }}
- **Target Trait:** {{ target_trait }}

{% if mode == 'hackathon' %}
## Hackathon Mode Instructions
ALL questions MUST be framed as 24-hour hackathon scenarios.
Focus on: collaboration under pressure, shipping vs perfecting, conflict with teammates, energy management, handling ambiguity.

Scenario Style:
- Short, punchy, time-specific ("Hour 18.", "Demo in 6 hours.", "3am.")
- Visceral details (cold coffee, blinking cursor, tired teammates)
- Real hackathon moments, not generic team situations

Example scenarios:
- "Hour 18. Your MVP works but looks terrible. Demo in 6 hours."
- "Your teammate hasn't pushed code in 3 hours. They say they're 'almost done.'"
- "A judge stops at your table mid-build. 'What problem does this solve?'"
- "2am. Energy drinks are gone. Someone suggests 'just shipping what we have.'"

FORBIDDEN:
- Generic workplace scenarios
- Any scenario that doesn't feel like a hackathon
{% endif %}

{% if mode == 'overall' %}
## Overall Mode Instructions
Generate questions across universal life situations.
Requirements:
- Gender-agnostic language
- Culturally neutral scenarios
- Mix of: work, relationships, personal growth, unexpected challenges
- No interest-specific framing

Vary emotional temperature:
- High stakes (30%): Crisis moments, deadlines, conflict
- Medium stakes (50%): Everyday decisions, mild friction
- Low stakes (20%): Quiet moments, small choices

Scenario Style:
- Vivid, sensory details
- Specific moments in time, not general patterns
- Situations that trigger authentic reactions

FORBIDDEN:
- "How do you typically..." (asks for self-description)
- Generic team scenarios
- Obviously leading questions
{% endif %}

{% if mode == 'deep_dive' and life_contexts %}
## Deep Dive Mode Instructions
User selected these life contexts: {{ life_contexts | join(', ') }}

**CRITICAL: Use ONE context per question, rotating through the list.**
Current question should use: **{{ current_context }}**

Create vivid, specific scenarios within {{ current_context }}.
Do NOT combine multiple contexts in one question.

Available scenario hooks for {{ current_context }}:
{% for hook in context_scenario_hooks %}
- {{ hook }}
{% endfor %}
{% endif %}

## User's Response History
{% if previous_answers %}
{% for answer in previous_answers %}
Q{{ loop.index }}: {{ answer.question_summary }} → Selected: {{ answer.selected_option }}
Trait signals: {{ answer.trait_signals | join(', ') }}
{% endfor %}

Based on this pattern, the user appears to be:
{% for tendency in inferred_tendencies %}
- {{ tendency }}
{% endfor %}
{% else %}
No previous answers yet. This is the first question.
{% endif %}

## Raw Trait Scores So Far
{% if trait_scores %}
{% for trait, data in trait_scores.items() %}
- {{ trait }}: {{ data.total }} points from {{ data.count }} questions{% if data.count > 0 %} (avg {{ (data.total / data.count) | round(1) }}){% endif %}

{% endfor %}
{% else %}
No scores yet.
{% endif %}

## Question Quality Rules
1. **Create MOMENTS, not descriptions** — Put the user IN the scenario
2. **Sensory grounding** — Include time, place, or physical detail
3. **Hide the assessment** — User should forget they're being evaluated
4. **No obvious "right answers"** — All options should be plausible
5. **Vary emotional temperature** — Mix high/medium/low stakes

## Output Requirements
Return valid JSON with this exact structure:
```json
{
  "next_question": {
    "id": "q_{{ session_id }}_{{ question_number }}",
    "trait": "{{ target_trait }}",
    "trait_targets": ["{{ target_trait }}", "SecondaryTrait"],
    "type": "{{ question_type }}",
    "text": "The scenario question text",
    "header": "Brief reaction to previous answer (5-15 words)",
{% if question_type == 'multiple-choice' %}
    "options": {
      "a": {"text": "Option A text", "score": <0-2>},
      "b": {"text": "Option B text", "score": <0-2>},
      "c": {"text": "Option C text", "score": <0-2>}
    }
{% else %}
    "placeholder": "Hint for how to respond"
{% endif %}
{% if mode == 'deep_dive' %}
    ,"context_used": "{{ current_context }}"
{% endif %}
  },
  "predicted_next_answer": {
    "most_likely": "a",
    "probabilities": {"a": 0.5, "b": 0.3, "c": 0.2},
    "reasoning": "Brief explanation of prediction based on user's pattern"
  }
}
```

CRITICAL: The "predicted_next_answer" field is REQUIRED for pre-fetching optimization.
Base your prediction on the user's response patterns so far. If no patterns yet, use balanced probabilities.

Return ONLY the JSON object, no markdown or commentary.
"""


def render_system_prompt(
    mode: str,
    question_number: int,
    total_questions: int,
    session_id: str,
    target_trait: str,
    question_type: str = "multiple-choice",
    previous_answers: Optional[List[Dict]] = None,
    trait_scores: Optional[Dict] = None,
    life_contexts: Optional[List[str]] = None,
    current_context: Optional[str] = None,
    context_scenario_hooks: Optional[List[str]] = None,
    traits_assessed: Optional[List[str]] = None,
    inferred_tendencies: Optional[List[str]] = None
) -> str:
    """
    Render the system prompt with session-specific context.

    Args:
        mode: Assessment mode ('hackathon', 'overall', 'deep_dive')
        question_number: Current question number (1-indexed)
        total_questions: Total questions in assessment
        session_id: Unique session identifier
        target_trait: The Big Five trait being assessed
        question_type: 'multiple-choice' or 'optional-freeform'
        previous_answers: List of previous answer dicts with question_summary, selected_option, trait_signals
        trait_scores: Dict of trait -> {total, count} for raw scores
        life_contexts: List of selected life contexts (deep_dive mode)
        current_context: The specific context for this question (deep_dive mode)
        context_scenario_hooks: Scenario ideas for current context
        traits_assessed: List of traits already assessed
        inferred_tendencies: List of inferred personality tendencies

    Returns:
        Rendered system prompt string
    """
    template = Template(SYSTEM_PROMPT_TEMPLATE)

    return template.render(
        mode=mode,
        question_number=question_number,
        total_questions=total_questions,
        session_id=session_id,
        target_trait=target_trait,
        question_type=question_type,
        previous_answers=previous_answers or [],
        trait_scores=trait_scores or {},
        life_contexts=life_contexts or [],
        current_context=current_context,
        context_scenario_hooks=context_scenario_hooks or [],
        traits_assessed=traits_assessed or [],
        inferred_tendencies=inferred_tendencies or []
    )


def infer_tendencies(answer_history: List[Dict]) -> List[str]:
    """
    Analyze answer history to infer personality tendencies.

    This helps the LLM understand the user's patterns for better
    question generation and answer probability prediction.

    Args:
        answer_history: List of answer dicts with trait_signals and response patterns

    Returns:
        List of inferred tendency descriptions
    """
    if not answer_history or len(answer_history) < 2:
        return ["Not enough data yet to infer patterns"]

    tendencies = []

    # Count trait signals
    trait_counts = {}
    for answer in answer_history:
        for trait in answer.get("trait_signals", []):
            trait_counts[trait] = trait_counts.get(trait, 0) + 1

    # Identify dominant traits from responses
    if trait_counts:
        sorted_traits = sorted(trait_counts.items(), key=lambda x: x[1], reverse=True)
        top_trait = sorted_traits[0][0]
        tendencies.append(f"Strong signals in {top_trait}")

    # Analyze response patterns
    options_chosen = [a.get("selected_option", "").lower() for a in answer_history]

    # Check for decisiveness (choosing 'a' often suggests quick/decisive)
    a_count = options_chosen.count("a")
    if a_count > len(options_chosen) * 0.6:
        tendencies.append("Tends toward direct, immediate action")

    # Check for deliberation (choosing 'b' or 'c' often)
    if a_count < len(options_chosen) * 0.3:
        tendencies.append("Tends toward measured, thoughtful responses")

    # Check for consistency
    if len(set(options_chosen)) == 1:
        tendencies.append("Very consistent response pattern")
    elif len(set(options_chosen)) == len(options_chosen):
        tendencies.append("Varied response pattern - adapts to situation")

    return tendencies if tendencies else ["Balanced response pattern emerging"]


@lru_cache(maxsize=16)
def get_life_context_details(context_key: str) -> Dict:
    """Get details for a life context category. Results are cached."""
    return LIFE_CONTEXT_CATEGORIES.get(context_key, {
        "label": context_key,
        "description": "",
        "icon": "✨",
        "scenario_contexts": []
    })


@lru_cache(maxsize=1)
def get_all_life_contexts() -> Dict:
    """Get all life context categories for frontend display. Results are cached."""
    return {
        key: {
            "label": data["label"],
            "description": data["description"],
            "icon": data["icon"]
        }
        for key, data in LIFE_CONTEXT_CATEGORIES.items()
    }
