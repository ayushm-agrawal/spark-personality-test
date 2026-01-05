"""
Firestore Seeding Script

Seeds the following collections:
1. badge_definitions - 16 badge definitions for the badge system
2. archetype_insights - Deep insights for all 8 archetypes

Run with: python seed_firestore.py
"""

import time
from firebase import db

# ============================================================================
# BADGE DEFINITIONS
# ============================================================================

BADGE_DEFINITIONS = {
    # CONSISTENCY BADGES
    "true_north": {
        "display_name": "True North",
        "description": "Your responses are remarkably consistent across multiple assessments. You know who you are.",
        "icon": "compass",
        "rarity": "rare",
        "category": "consistency",
        "points": 50,
        "enabled": True,
        "trigger_conditions": {
            "min_assessments": 3,
            "consistency_score": 85
        }
    },
    "mirror_mirror": {
        "display_name": "Mirror Mirror",
        "description": "Same test mode, consistent results. Your self-awareness is on point.",
        "icon": "mirror",
        "rarity": "uncommon",
        "category": "consistency",
        "points": 30,
        "enabled": True,
        "trigger_conditions": {
            "same_mode_tests": 2,
            "similarity_threshold": 0.80
        }
    },
    "no_filter": {
        "display_name": "No Filter",
        "description": "You take your time with each question. Thoughtful responses lead to accurate results.",
        "icon": "hourglass",
        "rarity": "common",
        "category": "consistency",
        "points": 15,
        "enabled": True,
        "trigger_conditions": {
            "avg_response_time": 4,
            "min_questions": 6
        }
    },
    "night_owl": {
        "display_name": "Night Owl",
        "description": "Completed an assessment in the quiet hours between midnight and 5am.",
        "icon": "owl",
        "rarity": "uncommon",
        "category": "consistency",
        "points": 20,
        "enabled": True,
        "trigger_conditions": {
            "hour_range": [0, 5]
        }
    },

    # ENGAGEMENT BADGES
    "first_spark": {
        "display_name": "First Spark",
        "description": "You took your first assessment. The journey of self-discovery begins!",
        "icon": "sparkles",
        "rarity": "common",
        "category": "engagement",
        "points": 10,
        "enabled": True,
        "trigger_conditions": {
            "assessments_completed": 1
        }
    },
    "deep_diver": {
        "display_name": "Deep Diver",
        "description": "You've explored 3+ different assessment modes. Curious minds want the full picture.",
        "icon": "scuba",
        "rarity": "rare",
        "category": "engagement",
        "points": 40,
        "enabled": True,
        "trigger_conditions": {
            "unique_modes": 3
        }
    },
    "curious_cat": {
        "display_name": "Curious Cat",
        "description": "You've explored 5+ insight sections. Knowledge is power!",
        "icon": "cat",
        "rarity": "common",
        "category": "engagement",
        "points": 15,
        "enabled": True,
        "trigger_conditions": {
            "sections_viewed": 5
        }
    },
    "weekly_wanderer": {
        "display_name": "Weekly Wanderer",
        "description": "You've returned 4 weeks in a row. Consistency is key to growth.",
        "icon": "footprints",
        "rarity": "rare",
        "category": "engagement",
        "points": 50,
        "enabled": True,
        "trigger_conditions": {
            "consecutive_weeks": 4
        }
    },
    "the_revisitor": {
        "display_name": "The Revisitor",
        "description": "Viewed insights on 3+ different days. Self-reflection is a practice.",
        "icon": "refresh",
        "rarity": "uncommon",
        "category": "engagement",
        "points": 25,
        "enabled": True,
        "trigger_conditions": {
            "unique_visit_days": 3
        }
    },

    # GROWTH BADGES
    "aha_moment": {
        "display_name": "Aha Moment",
        "description": "You've read all the main insight sections for your archetype. Full understanding unlocked!",
        "icon": "lightbulb",
        "rarity": "uncommon",
        "category": "growth",
        "points": 35,
        "enabled": True,
        "trigger_conditions": {
            "all_sections_viewed": True
        }
    },
    "blind_spot_hunter": {
        "display_name": "Blind Spot Hunter",
        "description": "Spent 30+ seconds on your blind spots. Confronting weaknesses takes courage.",
        "icon": "magnifier",
        "rarity": "uncommon",
        "category": "growth",
        "points": 25,
        "enabled": True,
        "trigger_conditions": {
            "blind_spots_time": 30
        }
    },
    "growth_mindset": {
        "display_name": "Growth Mindset",
        "description": "A trait shifted 20+ points over 5+ assessments. Real growth, documented.",
        "icon": "seedling",
        "rarity": "legendary",
        "category": "growth",
        "points": 100,
        "enabled": True,
        "trigger_conditions": {
            "trait_shift": 20,
            "min_assessments": 5
        }
    },

    # QUIRK BADGES
    "unicorn": {
        "display_name": "Unicorn",
        "description": "You scored in the 95th percentile for a trait. Rare and remarkable!",
        "icon": "unicorn",
        "rarity": "rare",
        "category": "quirk",
        "points": 45,
        "enabled": True,
        "trigger_conditions": {
            "percentile": 95
        }
    },
    "renaissance_soul": {
        "display_name": "Renaissance Soul",
        "description": "All your traits within 15 points of each other. Perfectly balanced, as all things should be.",
        "icon": "palette",
        "rarity": "rare",
        "category": "quirk",
        "points": 40,
        "enabled": True,
        "trigger_conditions": {
            "max_trait_range": 15
        }
    },
    "the_outlier": {
        "display_name": "The Outlier",
        "description": "You chose a response picked by less than 5% of users. Marching to your own drum!",
        "icon": "star",
        "rarity": "rare",
        "category": "quirk",
        "points": 35,
        "enabled": True,
        "trigger_conditions": {
            "rare_response_threshold": 5
        }
    },
    "beautiful_contradiction": {
        "display_name": "Beautiful Contradiction",
        "description": "High scores on traits that rarely go together. You contain multitudes.",
        "icon": "masks",
        "rarity": "legendary",
        "category": "quirk",
        "points": 75,
        "enabled": True,
        "trigger_conditions": {
            "contradiction_pair_1": "Openness,Conscientiousness",
            "contradiction_pair_2": "Extraversion,Emotional_Stability",
            "min_score": 80
        }
    }
}


# ============================================================================
# ARCHETYPE INSIGHTS
# ============================================================================

ARCHETYPE_INSIGHTS = {
    "architect": {
        "archetype_id": "architect",
        "display_name": "The Architect",
        "tagline": "Building tomorrow's blueprint, today.",
        "icon": "🏗️",
        "color": "#1E3A5F",
        "quick_insights": {
            "zone_of_genius": "Turning creative chaos into structured, actionable plans",
            "deepest_aspiration": "Building something that lasts and works beautifully",
            "growth_edge": "Letting 'good enough' be good enough"
        },
        "team_context": {
            "role_title": "The Blueprint Builder",
            "role_description": "Creates the plans that turn wild ideas into shipped reality. The bridge between dreamers and doers.",
            "dream_team": ["catalyst", "guide"],
            "creative_partner": "catalyst"
        },
        "summary_concise": "You transform ambitious visions into actionable plans. Your rare combination of creativity and execution means you don't just dream - you build. Teams rely on you to bring structure to chaos without killing the creative spark.",
        "summary_deep": "You transform ambitious visions into actionable plans with a rare combination of strategic thinking and follow-through execution. While others get lost in possibilities, you're already sketching the blueprint.\n\nYour mind naturally breaks down complex problems into manageable components, seeing both the forest and the trees. You're equally at home in blue-sky brainstorming sessions and heads-down deep work sprints. This versatility makes you invaluable in any team setting.\n\nAt your core, you're driven by a desire to create something that outlasts you - work that has real impact and stands the test of time. Your standards are high, sometimes impossibly so, but that's what produces exceptional results.",
        "trait_profile": {
            "Openness": 75,
            "Conscientiousness": 85,
            "Extraversion": 60,
            "Agreeableness": 55,
            "Emotional_Stability": 70
        },
        "collaboration_strengths": {
            "concise": [
                "Transforms abstract ideas into concrete action plans",
                "Maintains momentum through structured progress",
                "Balances innovation with practical constraints"
            ],
            "deep": [
                "Transforms abstract ideas into concrete action plans that teams can actually execute",
                "Maintains momentum through structured progress tracking and clear milestones",
                "Balances innovation with practical constraints, knowing when to push boundaries and when to ship",
                "Creates sustainable systems that work even when you're not there to maintain them",
                "Provides the organizational backbone that lets creative types do their best work"
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "May over-engineer when simpler solutions would work",
                "Can struggle to 'let go' of projects to other owners",
                "Tendency to prioritize polish over speed when scrappy would do"
            ],
            "deep": [
                "May over-engineer solutions when a simpler approach would achieve the goal faster",
                "Can struggle to delegate or 'let go' of projects, wanting to maintain control over quality",
                "Tendency to prioritize polish over shipping speed, especially under pressure",
                "Might dismiss input that doesn't fit your mental model of how things should work",
                "Risk of burning out by taking on too much responsibility for outcomes"
            ]
        },
        "team_phases": {
            "forming": {
                "strength": "Quickly establishes structure and clarity",
                "watch_for": "Don't overwhelm new team with processes too early"
            },
            "storming": {
                "strength": "Provides steady direction amid chaos",
                "watch_for": "Avoid being seen as inflexible when adapting"
            },
            "norming": {
                "strength": "Codifies effective practices into systems",
                "watch_for": "Leave room for organic evolution"
            },
            "performing": {
                "strength": "Ensures sustainable high performance",
                "watch_for": "Celebrate wins, don't just move to next challenge"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Bringing order to chaos",
                "Seeing a plan come together",
                "Building something from scratch",
                "Having dedicated deep work time"
            ],
            "drained_by": [
                "Endless meetings without decisions",
                "Constantly changing requirements",
                "Working without clear end goals",
                "Being asked to compromise on quality"
            ]
        },
        "actionable_tips": [
            "Start with the minimum viable plan. You can always add complexity later.",
            "Set explicit 'good enough' criteria before starting to prevent over-engineering.",
            "Schedule regular 'letting go' moments where you hand off control intentionally.",
            "Pair with a Catalyst to inject energy when projects get too procedural.",
            "Document your systems so others can run them without you."
        ],
        "ideal_team_role": "Technical Lead, Project Architect, Systems Designer",
        "complementary_archetypes": ["The Alchemist", "The Catalyst"],
        "challenging_pairings": [
            {
                "archetype": "The Luminary",
                "challenge": "Their vision may seem unrealistic to your practical mindset",
                "opportunity": "They can help you dream bigger while you ground their ideas"
            }
        ]
    },

    "catalyst": {
        "archetype_id": "catalyst",
        "display_name": "The Catalyst",
        "tagline": "Sparking change, one idea at a time.",
        "icon": "⚡",
        "color": "#FF6F00",
        "quick_insights": {
            "zone_of_genius": "Sparking energy and possibilities when everyone else is stuck",
            "deepest_aspiration": "Igniting change that matters",
            "growth_edge": "Following through after the spark"
        },
        "team_context": {
            "role_title": "The Spark Plug",
            "role_description": "Generates the energy and ideas that get things moving. The person who breaks through stagnation.",
            "dream_team": ["architect", "strategist"],
            "creative_partner": "architect"
        },
        "summary_concise": "You're the spark that ignites momentum. Ideas flow through you like electricity, and your enthusiasm is genuinely contagious. You see connections others miss and bring energy that makes things happen.",
        "summary_deep": "You're the match that lights the fire. Ideas flow through you like electricity, and your enthusiasm is genuinely contagious. You see connections others miss and aren't afraid to voice the unconventional take.\n\nPeople feel more creative just being around you. The world needs your energy - you make things happen that wouldn't happen without you. Your ability to pivot quickly and rally others around new possibilities is what teams need when they're stuck.\n\nYour deepest drive is being the spark that starts something bigger than yourself. You're not interested in maintaining the status quo - you want to change it.",
        "trait_profile": {
            "Openness": 90,
            "Conscientiousness": 50,
            "Extraversion": 85,
            "Agreeableness": 65,
            "Emotional_Stability": 55
        },
        "collaboration_strengths": {
            "concise": [
                "Breaks through stagnation with fresh energy",
                "Rallies people around new possibilities",
                "Pivots quickly when plans aren't working"
            ],
            "deep": [
                "Breaks through team stagnation with infectious energy and fresh perspectives",
                "Rallies people around new possibilities when momentum has stalled",
                "Pivots quickly and enthusiastically when original plans aren't working",
                "Brings diverse ideas together in unexpected combinations",
                "Creates psychological permission for others to take creative risks"
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "May start new initiatives before finishing current ones",
                "Energy can overwhelm quieter team members",
                "Follow-through after initial excitement fades"
            ],
            "deep": [
                "May start three projects before finishing one, leaving work incomplete",
                "Your high energy can inadvertently overwhelm or exhaust quieter team members",
                "Follow-through is challenging once the initial excitement fades",
                "Might dismiss detailed planning as 'killing the vibe'",
                "Risk of burnout from running on enthusiasm without sustainable pacing"
            ]
        },
        "team_phases": {
            "forming": {
                "strength": "Generates excitement and buy-in quickly",
                "watch_for": "Make space for more reserved voices"
            },
            "storming": {
                "strength": "Reframes conflicts as opportunities",
                "watch_for": "Don't brush past legitimate concerns"
            },
            "norming": {
                "strength": "Keeps things from becoming too routine",
                "watch_for": "Respect the value of stability"
            },
            "performing": {
                "strength": "Brings fresh energy when teams plateau",
                "watch_for": "Don't disrupt what's already working"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "New ideas and possibilities",
                "Collaborative brainstorming",
                "Breaking through barriers",
                "Inspiring others to action"
            ],
            "drained_by": [
                "Repetitive routine tasks",
                "Excessive process and bureaucracy",
                "Working in isolation",
                "Ideas being shut down without exploration"
            ]
        },
        "actionable_tips": [
            "Partner with an Architect to ensure your ideas get properly executed.",
            "Set a 'one in, one out' rule: finish something before starting something new.",
            "Schedule follow-up reminders for initiatives you've started.",
            "Consciously make space for quieter voices in group settings.",
            "Build in sustainability: your energy is finite even when it doesn't feel like it."
        ],
        "ideal_team_role": "Innovation Lead, Workshop Facilitator, Change Agent",
        "complementary_archetypes": ["The Gardener", "The Architect"],
        "challenging_pairings": [
            {
                "archetype": "The Sentinel",
                "challenge": "Your pace may feel chaotic to their need for stability",
                "opportunity": "They can ground your ideas while you push them past comfort zones"
            }
        ]
    },

    "strategist": {
        "archetype_id": "strategist",
        "display_name": "The Strategist",
        "tagline": "Three moves ahead, always.",
        "icon": "♟️",
        "color": "#1A237E",
        "quick_insights": {
            "zone_of_genius": "Seeing the whole board while others focus on one piece",
            "deepest_aspiration": "Orchestrating wins that look inevitable in hindsight",
            "growth_edge": "Letting others in on your thinking earlier"
        },
        "team_context": {
            "role_title": "The Navigator",
            "role_description": "Keeps everyone oriented toward the actual goal when distractions multiply.",
            "dream_team": ["catalyst", "guide"],
            "creative_partner": "catalyst"
        },
        "summary_concise": "While others react, you anticipate. Your mind naturally maps out scenarios, weighing options others don't even see. When pressure mounts, you get calmer - because you've already thought through what comes next.",
        "summary_deep": "While others react, you anticipate. Your mind naturally maps out scenarios, weighing options most people don't even see. You're not cold - you're clear.\n\nWhen the pressure mounts, you get calmer, because you've already thought through what comes next. Teams look to you when the stakes are highest. Your ability to see the whole board while others focus on one piece is your superpower.\n\nYour deepest drive is orchestrating wins that look inevitable in hindsight. You want to be the one who saw around corners before anyone else knew there were corners to see.",
        "trait_profile": {
            "Openness": 70,
            "Conscientiousness": 80,
            "Extraversion": 70,
            "Agreeableness": 50,
            "Emotional_Stability": 85
        },
        "collaboration_strengths": {
            "concise": [
                "Sees the whole picture while others focus on details",
                "Stays calm under pressure",
                "Knows what to cut before building it"
            ],
            "deep": [
                "Sees the whole strategic picture while others focus on immediate details",
                "Stays remarkably calm under pressure, providing stability for the team",
                "Knows which features to cut before wasting time building them",
                "Anticipates obstacles and prepares contingencies in advance",
                "Makes complex decisions quickly with high accuracy"
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "May struggle to share thinking until fully formed",
                "Analysis paralysis when quick decisions are needed",
                "Can seem cold or dismissive to emotional concerns"
            ],
            "deep": [
                "May struggle to share your thinking process until conclusions are fully formed",
                "Analysis paralysis can strike when quick, gut decisions are needed",
                "Can seem cold or dismissive when others raise emotional concerns",
                "Might undervalue ideas that don't fit your strategic framework",
                "Risk of optimizing for the wrong goal if initial assumptions were flawed"
            ]
        },
        "team_phases": {
            "forming": {
                "strength": "Quickly identifies optimal team structure",
                "watch_for": "Share your thinking, don't just announce conclusions"
            },
            "storming": {
                "strength": "Sees through surface conflicts to root causes",
                "watch_for": "Acknowledge emotions, not just logic"
            },
            "norming": {
                "strength": "Optimizes team processes for efficiency",
                "watch_for": "Efficiency isn't everything"
            },
            "performing": {
                "strength": "Keeps team aligned on strategic goals",
                "watch_for": "Leave room for serendipity"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Complex problems to solve",
                "High-stakes situations",
                "Making decisions that matter",
                "Having all the information"
            ],
            "drained_by": [
                "Emotional decisions without logic",
                "Repeated discussions of settled issues",
                "Working with incomplete information",
                "Being asked to 'just trust your gut'"
            ]
        },
        "actionable_tips": [
            "Practice thinking out loud - let others into your process earlier.",
            "Set time limits for analysis: 'I'll decide by X even if I'm not 100% sure.'",
            "Pair with a Guide to ensure you're not missing emotional dynamics.",
            "Check your assumptions explicitly - write them down and verify.",
            "Leave 20% of your plan flexible for unexpected opportunities."
        ],
        "ideal_team_role": "Strategy Lead, Decision Architect, Risk Analyst",
        "complementary_archetypes": ["The Catalyst", "The Guide"],
        "challenging_pairings": [
            {
                "archetype": "The Alchemist",
                "challenge": "Their intuitive process may frustrate your need for clear reasoning",
                "opportunity": "They can help you see possibilities your frameworks miss"
            }
        ]
    },

    "guide": {
        "archetype_id": "guide",
        "display_name": "The Guide",
        "tagline": "Lighting the path for others",
        "icon": "🧭",
        "color": "#EC4899",
        "quick_insights": {
            "zone_of_genius": "Making people feel seen and creating space for every voice",
            "deepest_aspiration": "Building teams where everyone belongs and thrives",
            "growth_edge": "Saying the hard thing when harmony isn't helping"
        },
        "team_context": {
            "role_title": "The Connector",
            "role_description": "Weaves relationships that make collaboration actually work. The glue that holds teams together.",
            "dream_team": ["architect", "strategist"],
            "creative_partner": "alchemist"
        },
        "summary_concise": "You're a Guide — someone who uplifts and connects. You combine warmth, social energy, and genuine curiosity about people in a way that makes others feel seen and supported. Teams with you in them feel safer, more inclusive, and more willing to take creative risks.\n\nYou're the person others come to when they need perspective, encouragement, or help navigating a difficult conversation. You read rooms intuitively, sensing tension before it erupts and creating space for voices that might otherwise go unheard.\n\nYour challenge is balancing your care for others with your own needs. You may avoid necessary conflict to preserve harmony, or take on too much because saying no feels like letting people down. Your growth edge is learning that sometimes the most helpful thing is honesty, not comfort.",
        "summary_deep": "You're a Guide — someone whose combination of high agreeableness, high extraversion, and high openness creates a powerful presence for connection and support. You don't just like people; you're genuinely curious about them. You don't just want harmony; you actively create the conditions for it. This makes you invaluable in any team that needs to function as more than a collection of individuals.\n\nYour gift is making people feel seen. In conversations, you listen actively, ask questions that show genuine interest, and remember details that matter to people. This isn't manipulation or networking — it's authentic care expressed through attention. People open up to you because they sense you're actually interested, not just performing interest.\n\nYou create psychological safety naturally. Research shows teams perform better when members feel safe to take risks, share ideas, and admit mistakes. Your presence contributes to this safety. You celebrate others' contributions, smooth over awkward moments, and create inclusive dynamics where quieter voices get heard.\n\nYour openness adds intellectual dimension to your relational gifts. You're not just warm; you're curious. You explore ideas, consider multiple perspectives, and help teams integrate diverse viewpoints. This combination of heart and mind makes you an effective facilitator, mediator, and culture-builder.\n\nThe shadow side of your gifts is conflict avoidance. Your deep desire for harmony can lead you to smooth over problems that need addressing, avoid giving critical feedback, or suppress your own needs to keep others happy. Learning that conflict can be caring — that honest feedback is a gift — is your growth edge.",
        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "medium",
            "Extraversion": "high",
            "Agreeableness": "high",
            "Emotional_Stability": "medium"
        },
        "collaboration_strengths": {
            "concise": [
                "You create psychological safety that enables creative risk-taking",
                "You draw out quieter voices and ensure diverse perspectives get heard",
                "You're a natural mediator who helps teams navigate conflict constructively",
                "Your genuine interest in others builds trust and loyalty quickly"
            ],
            "deep": [
                "Your collaboration superpower is creating conditions where others do their best work. Research shows that psychological safety is among the strongest predictors of team performance. You create this safety naturally.",
                "You're an exceptional listener in a world of people waiting to talk. When teammates share ideas, concerns, or problems, you give them full attention and ask follow-up questions.",
                "You notice the people who aren't speaking and create space for them. In meetings dominated by louder voices, you might say 'I'd love to hear what others think' or directly invite quieter colleagues to share.",
                "Your mediation skills help teams navigate conflict without destruction. When tensions arise, you can see multiple perspectives and help others see them too.",
                "Your network tends to be deep rather than just wide. Because you invest genuinely in relationships, people feel connected to you beyond transactional interactions."
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "You may avoid necessary conflict, allowing problems to grow",
                "Your difficulty saying no can lead to overcommitment and burnout",
                "You might prioritize others' needs so consistently that your own go unmet",
                "Critical feedback may feel so uncomfortable that you soften it into uselessness"
            ],
            "deep": [
                "Your greatest strength casts the longest shadow. The same desire for harmony that makes you valuable can prevent you from addressing problems directly.",
                "Research shows that highly agreeable people are more likely to use 'obliging' or 'avoiding' conflict styles. Learning to embrace productive conflict is essential growth.",
                "You're vulnerable to burnout through overgiving. Because helping others energizes you in the moment, you might not notice the cumulative drain until you're exhausted.",
                "Your openness to others' perspectives can shade into difficulty holding your own position. Your voice matters too, and teams need you to advocate for your views.",
                "You might unconsciously enable dysfunction. If someone behaves badly and you smooth it over, you haven't addressed the behavior."
            ]
        },
        "team_phases": {
            "ideation": {
                "strength": "You actively draw out others' ideas and create an inclusive environment where all voices feel welcome",
                "watch_for": "Be mindful that your own ideas matter too — don't just facilitate, contribute"
            },
            "execution": {
                "strength": "You support team members emotionally, help resolve interpersonal blockers, and maintain morale",
                "watch_for": "You may struggle to hold others accountable or push back on scope creep"
            },
            "conflict": {
                "strength": "You're a natural mediator who helps people see each other's perspectives",
                "watch_for": "Watch for smoothing over too quickly — some conflicts need to be worked through"
            },
            "crunch_time": {
                "strength": "You prioritize team well-being and morale, which helps sustain effort",
                "watch_for": "You may sacrifice your own needs to help others, leading to personal burnout"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Facilitating collaborative discussions",
                "Mentoring others and watching them grow",
                "Building authentic connections",
                "Creating inclusive team culture",
                "Helping resolve conflicts constructively"
            ],
            "drained_by": [
                "Persistent conflict without resolution",
                "Competitive, zero-sum environments",
                "Delivering harsh feedback or criticism",
                "Feeling that your contributions aren't valued",
                "Extended time alone without meaningful connection"
            ]
        },
        "actionable_tips": [
            {"title": "Practice 'kind candor'", "description": "You can be caring AND direct. Practice delivering difficult messages with warmth: 'I value our relationship, which is why I want to share something that might be hard to hear...' The feedback itself is the caring part."},
            {"title": "Build boundary scripts", "description": "Prepare phrases for saying no: 'I can't take that on right now, but here's what I can do...' Having scripts makes boundaries easier in the moment."},
            {"title": "Schedule self-care like meetings", "description": "You prioritize others' needs naturally; you have to be intentional about your own. Put recovery time in your calendar and treat it as non-negotiable."},
            {"title": "Let discomfort do its work", "description": "Not every uncomfortable moment needs smoothing. Sometimes people need to sit with feedback or feel the weight of their choices."},
            {"title": "Document your contributions", "description": "Your behind-the-scenes relationship work often goes unnoticed. Keep a log of your impact — conflicts resolved, team members supported, connections made."}
        ],
        "ideal_team_role": "People Manager, Team Facilitator, Culture Lead, HR Partner, or Customer Success — roles that leverage your relationship skills and genuine care for others.",
        "complementary_archetypes": ["The Architect", "The Strategist", "The Sentinel"],
        "challenging_pairings": [
            {
                "archetype": "The Sentinel",
                "challenge": "Their task focus and emotional reserve may feel cold to your relational warmth",
                "opportunity": "You can help them connect while they help you ground in practicality"
            }
        ]
    },

    "alchemist": {
        "archetype_id": "alchemist",
        "display_name": "The Alchemist",
        "tagline": "Transforming through introspection",
        "icon": "🔮",
        "color": "#0D9488",
        "quick_insights": {
            "zone_of_genius": "Synthesizing insights others miss through deep, quiet thinking",
            "deepest_aspiration": "Transforming complexity into elegant clarity",
            "growth_edge": "Sharing your thinking before it's fully formed"
        },
        "team_context": {
            "role_title": "The Deep Thinker",
            "role_description": "Processes what others rush past. When they finally speak, it shifts the conversation.",
            "dream_team": ["catalyst", "gardener"],
            "creative_partner": "catalyst"
        },
        "summary_concise": "You're an Alchemist — someone who transforms through deep, introspective creativity. Your mind works differently from the people who dominate most rooms. While they process out loud, you process inward, emerging with insights that surprise people with their originality and depth.\n\nYou combine creative imagination with quiet focus and steady emotional composure. This means you can explore unconventional ideas without the volatility that sometimes accompanies high creativity. You're the calm innovator, the thoughtful contrarian, the person who sees what others miss because you're actually looking rather than talking.\n\nYour challenge is visibility. Your best work happens internally, and you may not share it until it's fully formed — or at all. Learning to externalize your thinking earlier helps your contributions land.",
        "summary_deep": "You're an Alchemist — someone whose combination of high openness, low extraversion, and high emotional stability creates a distinctive thinking style. Where high-extraversion creatives process ideas through conversation, you process through reflection. Where some creative types are emotionally volatile, you bring steady composure to your explorations. This makes you the team's quiet innovator.\n\nYour mind works in a pattern that's easily underestimated. In meetings, you might not say much. Extroverted colleagues may fill the airtime with ideas that are half-formed but confidently expressed. You're listening, synthesizing, considering angles they haven't thought of. When you do speak, it's because you have something substantive.\n\nThis pattern means your contributions are often higher quality but lower frequency. Research shows introverts tend to produce fewer ideas in group brainstorming but generate ideas of equal or higher quality when given individual thinking time. You're not less creative; you're differently creative.\n\nYour emotional stability is a quiet asset. High openness is sometimes associated with emotional intensity — the passionate artist archetype. But your version of creativity comes with groundedness. You can explore unconventional ideas without getting destabilized by them. You can receive criticism of your work without spiraling.\n\nYour shadow side is invisibility. You may not realize how little of your thinking reaches others. Ideas that feel fully developed to you have never actually been shared. Learning to externalize your process, not just your conclusions, helps others appreciate your contributions.",
        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "medium",
            "Extraversion": "low",
            "Agreeableness": "medium",
            "Emotional_Stability": "high"
        },
        "collaboration_strengths": {
            "concise": [
                "You bring deep, synthesized thinking that catches what others miss",
                "Your emotional stability makes you a calm presence during team stress",
                "You excel in written communication and asynchronous collaboration",
                "When you speak, it carries weight because people learn your contributions are substantive"
            ],
            "deep": [
                "Your collaboration superpower is depth. While others generate volume, you generate insight. You notice patterns, connections, and implications that faster-moving teammates overlook.",
                "You're an exceptional written communicator. Where conversation can feel draining, writing allows you to craft your thoughts precisely. In a world increasingly reliant on written communication, this is more valuable than ever.",
                "Your emotional stability provides anchoring during turbulent times. When deadlines loom, conflicts escalate, or plans fall apart, you don't add to the chaos. Your calm isn't disengagement — it's composure.",
                "You're comfortable with ambiguity and complexity. Your openness means you don't need premature closure. You can hold multiple possibilities in mind and sit with uncertainty longer than colleagues who need quick answers.",
                "You bring independent perspective. Because you don't need external validation as much as extroverts do, you're less susceptible to groupthink."
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "Your voice can get lost in fast-paced discussions",
                "You might not share ideas until they're fully formed, missing opportunities for earlier input",
                "Your quiet demeanor may be misread as disengagement",
                "You might assume others understand what you haven't actually communicated"
            ],
            "deep": [
                "Your biggest challenge is being seen and heard. In meetings dominated by extroverted colleagues, you might not speak at all. Your ideas stay in your head, and the team loses access to them.",
                "You might overestimate how much you've communicated. Because ideas feel fully developed in your mind, you may assume others can see what you see. But they can't.",
                "Your comfort with ambiguity can shade into analysis paralysis. Knowing when to keep exploring versus when to commit is an ongoing calibration.",
                "You may withdraw when you most need to engage. Under stress or in conflict, your instinct might be to pull back and process internally. But sometimes teams need real-time input.",
                "Social capital requires investment that doesn't come naturally to you. Finding ways to build relationships that work for your style matters for your influence."
            ]
        },
        "team_phases": {
            "ideation": {
                "strength": "You generate innovative ideas but may not voice them immediately",
                "watch_for": "Request advance notice for brainstorms so you can prepare. Don't wait for the perfect moment to share"
            },
            "execution": {
                "strength": "You thrive in focused, independent work with steady, quality-driven output",
                "watch_for": "Make sure to communicate progress — your quiet reliability might be invisible if you don't actively share updates"
            },
            "conflict": {
                "strength": "Your emotional stability helps you remain calm and objective",
                "watch_for": "You might withdraw rather than engage in heated moments; try to stay present even when uncomfortable"
            },
            "crunch_time": {
                "strength": "You handle deadline pressure without panicking and maintain cognitive clarity",
                "watch_for": "Be available even when you'd prefer to work alone — your calm presence helps others"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Deep focused work on meaningful problems",
                "Exploring novel ideas and unconventional approaches",
                "One-on-one conversations with curious people",
                "Written communication and asynchronous collaboration",
                "Autonomy over how and when you work"
            ],
            "drained_by": [
                "Extended meetings without breaks",
                "Large group brainstorming with rapid-fire dynamics",
                "Being put on the spot for immediate answers",
                "Open-office environments with constant interruption",
                "Superficial socializing without substantive conversation"
            ]
        },
        "actionable_tips": [
            {"title": "Request meeting agendas in advance", "description": "Ask for topics ahead of time so you can prepare your thoughts. Frame it as wanting to contribute more thoughtfully. This simple request ensures your ideas make it into the room."},
            {"title": "Find an extroverted ally", "description": "Partner with a colleague who naturally amplifies ideas. Share your thinking with them privately, and they can help champion it in group settings."},
            {"title": "Create contribution channels beyond meetings", "description": "Ask if you can submit written ideas before or after discussions. Propose a shared doc for brainstorming, or follow up meetings with your additional thoughts via email."},
            {"title": "Practice sharing before you're ready", "description": "Your instinct is to wait until thinking is complete. But sharing at 70% lets others contribute and gets your ideas into consideration earlier. 'I'm still working this out, but here's where I am...'"},
            {"title": "Schedule recharge during collaborative periods", "description": "Know your limits and protect your energy. Block focus time around meetings. Find quiet spaces. Your best contributions come when you're resourced, not depleted."}
        ],
        "ideal_team_role": "Research Lead, Creative Strategist, Writer, Analyst, or Technical Specialist — roles requiring deep thinking and quality over speed. You excel when given autonomy and complex problems.",
        "complementary_archetypes": ["The Catalyst", "The Gardener", "The Guide"],
        "challenging_pairings": [
            {
                "archetype": "The Catalyst",
                "challenge": "Their rapid-fire energy may feel overwhelming to your reflective process",
                "opportunity": "They can help amplify your ideas while you provide depth to their breadth"
            }
        ]
    },

    "gardener": {
        "archetype_id": "gardener",
        "display_name": "The Gardener",
        "tagline": "Nurturing what matters",
        "icon": "🌱",
        "color": "#166534",
        "quick_insights": {
            "zone_of_genius": "Nurturing both people and projects to sustainable growth",
            "deepest_aspiration": "Creating conditions where others flourish",
            "growth_edge": "Protecting your own energy as fiercely as others'"
        },
        "team_context": {
            "role_title": "The Cultivator",
            "role_description": "Tends to what others plant. The reliable force that turns potential into results.",
            "dream_team": ["luminary", "architect"],
            "creative_partner": "luminary"
        },
        "summary_concise": "You're a Gardener — someone who nurtures people and projects with patient, reliable care. You're the person who remembers the details others forget, follows through when others move on, and creates the conditions where people and work can thrive.\n\nYou combine warmth with discipline. You genuinely care about people AND you get things done. This makes you the glue in teams — the one who maintains relationships while keeping work on track. People trust you because you're both kind and reliable.\n\nYour challenge is boundaries. Your helpful nature means you may take on more than your share, say yes when you should say no, or avoid conflict to preserve harmony. Learning that caring for yourself is part of caring for others helps sustain your gifts.",
        "summary_deep": "You're a Gardener — someone whose combination of high agreeableness and high conscientiousness creates a powerful foundation for nurturing both people and work. Research shows this trait combination produces the strongest emphasis on team synergy and collective success. You're not just nice, and you're not just organized — you're both, and that combination is rarer and more valuable than either alone.\n\nYour approach to work is fundamentally relational. You don't just complete tasks; you consider how your work affects others. You don't just manage projects; you manage the human dynamics around them. This means you often catch things that purely task-focused people miss — the colleague who's struggling, the stakeholder who needs extra communication.\n\nYou're the person others can count on. When you commit to something, it gets done. When you say you'll help, you actually help. This reliability builds trust quickly. Teams with a Gardener develop a sense of safety — someone is watching out for the details, someone is following through.\n\nYour conscientiousness expresses through care rather than control. You're organized because organization reduces stress for everyone. You track details because dropped details create problems for people. Your systems and structures serve relationship goals, not just efficiency goals.\n\nThe shadow side of your gifts is self-neglect. You may care for others so consistently that you neglect your own needs. You may avoid difficult conversations because they threaten harmony. Learning that sustainable giving requires receiving — and that honest feedback is a form of care — helps you thrive long-term.",
        "trait_profile": {
            "Openness": "medium",
            "Conscientiousness": "high",
            "Extraversion": "medium",
            "Agreeableness": "high",
            "Emotional_Stability": "medium"
        },
        "collaboration_strengths": {
            "concise": [
                "You're the reliable backbone of team execution — organized, thorough, and consistent",
                "You create psychological safety through warmth AND follow-through",
                "You notice struggling teammates and offer support",
                "Your combination of care and competence makes you deeply trusted"
            ],
            "deep": [
                "Your collaboration superpower is being the person who makes teams actually work. Not the flashy visionary, not the charismatic leader — the person who ensures things happen and people are okay.",
                "You compensate for what others lack. When creative types generate ideas but don't follow through, you ensure follow-through happens. When driven types push too hard, you notice who's struggling.",
                "Your reliability is a form of respect. When you say you'll do something, you do it. This consistency signals to others that they matter. Over time, this builds deep trust.",
                "You create systems that serve people. Your organizational instinct isn't about control; it's about reducing friction and stress for everyone.",
                "You notice what others miss in the human dimension. You see early warning signs of burnout, frustration, or disengagement. Teams with a Gardener tend to have fewer interpersonal crises."
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "You may take on too much because saying no feels like failing others",
                "Your conflict avoidance can let problems fester",
                "You might suppress your own opinions to maintain harmony",
                "Under pressure, you may become rigid or controlling about details"
            ],
            "deep": [
                "Your helpful nature can become self-destructive. Because helping others feels good in the moment, you might not notice the cumulative drain until you're exhausted or resentful.",
                "Your desire for harmony can prevent necessary honesty. You might avoid giving critical feedback, telling yourself the person isn't ready to hear it, when really you're avoiding your own discomfort.",
                "You may lose yourself in service to others. If someone asked you what you need, you might not know. You might define yourself through your usefulness rather than your inherent worth.",
                "Under stress, your conscientiousness can tip into rigidity. You might become controlling about details, frustrated when others don't follow systems.",
                "Your preference for harmony might suppress valuable perspectives. If you consistently hold back opinions that might create disagreement, the team loses input they need."
            ]
        },
        "team_phases": {
            "ideation": {
                "strength": "You encourage all voices and support others' ideas generously. You help document and organize what's generated",
                "watch_for": "Watch for holding back your own ideas to maintain group harmony — your perspective adds value too"
            },
            "execution": {
                "strength": "This is where you shine. You're organized, reliable, and thorough. You track progress and help struggling teammates",
                "watch_for": "Watch for taking on too much yourself rather than letting others own their commitments"
            },
            "conflict": {
                "strength": "You naturally mediate and seek compromise",
                "watch_for": "Be mindful of smoothing over too quickly — some conflicts need to be fully processed"
            },
            "crunch_time": {
                "strength": "You're a reliable presence who meets commitments even under pressure",
                "watch_for": "Remember that your wellbeing matters too — sustainable pace serves everyone better than heroic burnout"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Seeing others succeed because of your support",
                "Creating and maintaining helpful systems",
                "Clear goals with meaningful progress",
                "Harmonious, appreciative team relationships",
                "Completing work to a high standard"
            ],
            "drained_by": [
                "Interpersonal conflict, especially prolonged",
                "Chaotic, disorganized environments",
                "Teammates who repeatedly fail to follow through",
                "Feeling taken for granted or unappreciated",
                "Competitive, zero-sum dynamics"
            ]
        },
        "actionable_tips": [
            {"title": "Practice boundary scripts", "description": "Prepare phrases for protecting your capacity: 'I can help with X after I complete Y' or 'I don't have bandwidth for that right now — here's who might.' Having scripts ready makes it easier to say no."},
            {"title": "Schedule self-care like it's a meeting", "description": "You'll always prioritize others unless you're intentional about yourself. Block recovery time, protect it like a commitment to someone else, and don't apologize for it."},
            {"title": "Voice concerns early, before they grow", "description": "Your instinct is to wait, hope things improve, or handle problems yourself. Practice raising concerns when they're small: 'I'm noticing X and wanted to flag it early.'"},
            {"title": "Ask for what you need", "description": "You might not be used to receiving help. Practice making requests: 'I could use support on this' or 'It would help me if you could...' Receiving isn't selfish."},
            {"title": "Partner with assertive teammates", "description": "If you struggle with direct confrontation, collaborate with someone who doesn't. They can voice what you're reluctant to say. This isn't weakness; it's strategic self-awareness."}
        ],
        "ideal_team_role": "Project Coordinator, Team Culture Lead, Operations Manager, Customer Success, or Support Role — anywhere your reliability and care create value.",
        "complementary_archetypes": ["The Luminary", "The Alchemist", "The Architect"],
        "challenging_pairings": [
            {
                "archetype": "The Catalyst",
                "challenge": "Their constant pivots and energy may feel chaotic to your steady approach",
                "opportunity": "You can help them follow through while they help you embrace change"
            }
        ]
    },

    "luminary": {
        "archetype_id": "luminary",
        "display_name": "The Luminary",
        "tagline": "Illuminating possibilities",
        "icon": "✨",
        "color": "#EAB308",
        "quick_insights": {
            "zone_of_genius": "Illuminating possibilities that inspire and include everyone",
            "deepest_aspiration": "Creating change that genuinely helps people",
            "growth_edge": "Championing fewer ideas more deeply"
        },
        "team_context": {
            "role_title": "The Visionary",
            "role_description": "Sees futures others can't imagine yet. Makes innovation feel exciting rather than threatening.",
            "dream_team": ["sentinel", "architect"],
            "creative_partner": "sentinel"
        },
        "summary_concise": "You're a Luminary — someone who illuminates possibilities through creative vision and genuine care for people. You see potential everywhere: in ideas, in projects, in others. And your warmth means you don't just see it — you help people see it in themselves.\n\nYou make innovation feel safe rather than threatening. Your openness generates ideas while your agreeableness ensures those ideas consider human impact. You're the creative who doesn't alienate people, the visionary who brings others along.\n\nYour challenge is grounding. You may generate more possibilities than can realistically be pursued, or avoid the critical evaluation that separates good ideas from great ones. Learning to champion your best ideas deeply rather than all ideas broadly helps your vision land.",
        "summary_deep": "You're a Luminary — someone whose combination of high openness and high agreeableness creates a distinctive kind of creative presence. Where some creative types are abrasive or self-focused, you're generous. Where some people-oriented types are conventional, you're imaginative. This combination makes you a creative force that actually works well with others.\n\nYour creativity has an inherently human orientation. When you generate ideas, you're naturally thinking about how they'll affect people. You consider usability, accessibility, emotional impact. This isn't a constraint on your creativity; it's a direction for it.\n\nYou're an idea champion, not just an idea generator. Many creative people struggle to get their ideas adopted because they can't bring others along. But your agreeableness means you're attuned to others' concerns, you collaborate naturally, and you can adjust your proposals based on feedback without feeling attacked.\n\nYou make innovation feel safe. Some creative types scare people with how different their ideas are. But your warmth creates trust that lets people engage with novelty. They know you care about them, so they're more willing to take creative risks with you.\n\nThe shadow side of your gifts is difficulty with criticism. Your agreeableness may make you reluctant to hear or give negative feedback. You might fall in love with ideas that aren't actually good, and your warmth might prevent the honest evaluation needed to improve them.",
        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "medium",
            "Extraversion": "medium-high",
            "Agreeableness": "high",
            "Emotional_Stability": "medium"
        },
        "collaboration_strengths": {
            "concise": [
                "You generate creative ideas that consider human impact from the start",
                "You champion innovations while maintaining relationships",
                "You create conditions where others feel safe to think expansively",
                "Your combination of creativity and warmth makes you persuasive without being pushy"
            ],
            "deep": [
                "Your collaboration superpower is making creativity feel collaborative rather than competitive. Your agreeableness gives you flexibility — you can take feedback, integrate others' contributions, and let ideas evolve.",
                "You're naturally inclusive in creative processes. You notice when someone hasn't contributed and create openings for them. You build on others' ideas rather than dismissing them.",
                "Your ideas tend to have natural buy-in because you've considered stakeholders from the start. Your proposals are more practical and face less resistance during implementation.",
                "You're persuasive without being pushy. Your warmth means people want to engage with your ideas. Your collaborative nature means you're trying to find the best answer together.",
                "You help others see possibilities in themselves. Your combination of vision and care means you notice people's potential and help them see it."
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "You may generate more ideas than can be realistically pursued",
                "Your warmth might prevent necessary critical evaluation of your own work",
                "You might over-commit to maintain relationships",
                "Routine execution may bore you before projects are complete"
            ],
            "deep": [
                "Your idea abundance can overwhelm rather than inspire. Learning to curate your own output, to develop your best ideas deeply rather than presenting many ideas shallowly, increases your impact.",
                "Your agreeableness can undermine creative quality. Great creative work often requires killing ideas. But your warmth might prevent you from critically evaluating your own work.",
                "You may commit to too much because saying no feels rejecting. Protecting focus time for deep creative work requires saying no to some opportunities.",
                "Routine execution may lose you. The beginning of projects is exciting — exploring, imagining, possibilities. But projects need sustained effort through less glamorous phases.",
                "You might avoid necessary conflict over creative direction. Sometimes creative work requires championing a direction against resistance."
            ]
        },
        "team_phases": {
            "ideation": {
                "strength": "You absolutely thrive here. You generate possibilities, build on others' ideas, and create inclusive dynamics",
                "watch_for": "Watch for idea volume — sharing your top 3 ideas with development beats mentioning 10 ideas in passing"
            },
            "execution": {
                "strength": "Find the creative challenges within execution: optimizing, solving unexpected problems, making the work better",
                "watch_for": "You may lose energy as novelty fades. Partner with execution-focused teammates"
            },
            "conflict": {
                "strength": "You seek harmony through understanding all perspectives, which can be valuable",
                "watch_for": "Watch for over-compromising — sometimes creative direction requires choosing, not blending"
            },
            "crunch_time": {
                "strength": "You rally teams with inspiring vision and genuine care. You help people remember why the work matters",
                "watch_for": "Watch for adding new ideas when the team needs to execute on existing ones"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Exploring new concepts with engaged collaborators",
                "Helping others develop their ideas and potential",
                "Collaborative creative sessions with diverse input",
                "Work with clear positive impact on people",
                "Recognition for creative contributions"
            ],
            "drained_by": [
                "Rigid environments that dismiss new ideas",
                "Routine, repetitive tasks without creative challenge",
                "Conflict that feels unresolvable",
                "Working in isolation without collaboration",
                "Tasks that feel meaningless or disconnected from impact"
            ]
        },
        "actionable_tips": [
            {"title": "Develop ideas deeply before sharing widely", "description": "Your instinct is to share early and often. But a few well-developed proposals land better than many half-formed suggestions. Before brainstorms, pick your top idea and prepare to articulate it compellingly."},
            {"title": "Practice giving critical feedback", "description": "Your warmth can prevent necessary honesty. Practice phrases like 'I love the direction, and I think it could be stronger if...' Feedback is care, not criticism."},
            {"title": "Block focus time for execution", "description": "Your calendar might fill with collaborative sessions that energize you but fragment your focus. Protect blocks for the sustained work that turns ideas into reality."},
            {"title": "Champion fewer things more strongly", "description": "If you advocate for everything, you advocate for nothing. Choose the ideas, projects, or people you believe in most and invest your influence there."},
            {"title": "Partner with critical thinkers", "description": "Find teammates who are comfortable challenging ideas — and invite them to challenge yours. Their critical eye helps you separate good ideas from great ones."}
        ],
        "ideal_team_role": "Creative Lead, Design Thinking Facilitator, User Experience Advocate, Brand or Culture Lead — roles that leverage creative vision with human centeredness.",
        "complementary_archetypes": ["The Sentinel", "The Architect", "The Strategist"],
        "challenging_pairings": [
            {
                "archetype": "The Sentinel",
                "challenge": "Their focus on risks and stability may feel like pessimism to your possibility-thinking",
                "opportunity": "They can help you build visions that survive contact with reality"
            }
        ]
    },

    "sentinel": {
        "archetype_id": "sentinel",
        "display_name": "The Sentinel",
        "tagline": "Steadfast and dependable",
        "icon": "🛡️",
        "color": "#475569",
        "quick_insights": {
            "zone_of_genius": "Providing steadfast reliability when everything else is chaos",
            "deepest_aspiration": "Being the foundation others can build on",
            "growth_edge": "Making your contributions visible without self-promotion"
        },
        "team_context": {
            "role_title": "The Anchor",
            "role_description": "Holds steady when others waver. The quiet force that ensures what needs to happen, happens.",
            "dream_team": ["luminary", "catalyst"],
            "creative_partner": "luminary"
        },
        "summary_concise": "You're a Sentinel — someone who provides steadfast reliability when everything around you is chaos. You're the anchor, the backstop, the person who quietly ensures that what needs to happen actually happens. While others chase novelty or generate drama, you maintain.\n\nYour combination of high conscientiousness, high emotional stability, and low extraversion creates a distinctive profile: deeply reliable, remarkably calm, and focused on substance over show. You're not the loudest voice in the room, but you might be the one people depend on most.\n\nYour challenge is visibility. Your quiet competence can be overlooked while louder colleagues get credit. Learning to communicate your contributions without violating your nature helps ensure your value is recognized.",
        "summary_deep": "You're a Sentinel — someone whose combination of high conscientiousness, high emotional stability, and low extraversion creates a rare profile of reliable composure. You're the team member who delivers what they promise, stays calm when others panic, and does excellent work without requiring the spotlight. In a world that often rewards flash over substance, your substance is your superpower.\n\nYour reliability isn't just about completing tasks. It's about being predictable in the best sense — people know what they're getting with you. You don't overpromise, you don't create drama, you don't require management attention. This might sound boring, but it's actually incredibly valuable.\n\nYour emotional stability is particularly important in high-pressure environments. When deadlines loom or crises emerge, you don't add to the chaos. You stay focused, clear-headed, and productive. Research shows that low-neuroticism individuals function like emotional anchors for teams.\n\nYour introversion means you're comfortable working independently for long stretches. You don't need constant social input or external validation to stay motivated. Give you a meaningful problem and adequate time, and you'll solve it thoroughly.\n\nThe shadow side of your gifts is invisibility. Your quiet competence may go unnoticed while louder colleagues attract attention. Your emotional stability might be misread as not caring. Learning to advocate for yourself without violating your nature is essential growth.",
        "trait_profile": {
            "Openness": "medium",
            "Conscientiousness": "high",
            "Extraversion": "low",
            "Agreeableness": "medium",
            "Emotional_Stability": "high"
        },
        "collaboration_strengths": {
            "concise": [
                "You're the anchor when everything's unstable — reliable, calm, and consistent",
                "You produce high-quality work independently without requiring supervision",
                "Your composure under pressure helps regulate team anxiety",
                "Your commitments can be counted on absolutely"
            ],
            "deep": [
                "Your collaboration superpower is being the foundation others can build on. In teams full of creative but unreliable types, or driven but volatile types, you're the stabilizing element.",
                "Your work quality tends to be high because you don't cut corners to chase speed. You think things through, check your work, and deliver polished outputs.",
                "You're self-directed in a way that frees leadership attention. You don't need constant check-ins, validation, or course correction.",
                "Your emotional composure is a team asset during stressful periods. Your ability to think clearly when others are reactive often makes you the de facto problem-solver in crisis moments.",
                "You excel in roles requiring sustained, focused effort. Where easily distracted colleagues struggle with deep work, you can maintain concentration for hours."
            ]
        },
        "potential_blind_spots": {
            "concise": [
                "Your quiet reliability may be overlooked; you might need to advocate for yourself more",
                "Your low extraversion can leave you out of informal networks where information flows",
                "You might resist changes that disrupt your systems",
                "Your stability might seem like lack of engagement to more emotional colleagues"
            ],
            "deep": [
                "Your biggest challenge is visibility in organizations that reward presence over performance. While you're doing excellent work, more extroverted colleagues might be building relationships and capturing attention.",
                "Your introversion can create information gaps. Informal conversations often contain valuable information. Finding ways to engage socially that work for your style helps close this gap.",
                "Your preference for stability can become resistance to necessary change. Building your tolerance for change, and distinguishing between changes worth resisting and changes to embrace, is ongoing growth.",
                "Your emotional stability might be misread by more expressive colleagues. You might need to explicitly acknowledge emotions before problem-solving.",
                "Your self-sufficiency might shade into isolation. Making an effort to reach out and build relationships — even when it doesn't feel necessary — creates goodwill you'll benefit from."
            ]
        },
        "team_phases": {
            "ideation": {
                "strength": "You listen carefully and evaluate feasibility. You contribute practical considerations others overlook",
                "watch_for": "Your best contributions often come after reflection, so request advance notice when possible"
            },
            "execution": {
                "strength": "This is where you excel. You meet every deadline, follow through on every commitment, and maintain quality throughout",
                "watch_for": "Make sure to communicate progress so your work is visible"
            },
            "conflict": {
                "strength": "You remain objective and unemotional, which can be clarifying",
                "watch_for": "You might not actively engage in conflict even when your input would help — push yourself to contribute"
            },
            "crunch_time": {
                "strength": "You're the teammate everyone wants in a crisis. You maintain composure, focus, and productivity when others are spiraling",
                "watch_for": "Be available even when you'd prefer to work alone — your calm presence helps others"
            }
        },
        "energy_dynamics": {
            "energized_by": [
                "Clear goals with meaningful progress",
                "Autonomy over how and when you work",
                "Quiet work environments with focused time",
                "Seeing projects through to completion",
                "Recognition for quality and reliability"
            ],
            "drained_by": [
                "Constant interruptions and fragmented attention",
                "Unpredictable environments with shifting priorities",
                "Colleagues who are unreliable or create unnecessary drama",
                "Extended social events without breaks",
                "Decisions made without adequate information or deliberation"
            ]
        },
        "actionable_tips": [
            {"title": "Provide regular updates without being asked", "description": "Your quiet reliability can be invisible. Send proactive updates on your work: 'Here's where things stand.' This makes your contributions visible without requiring you to self-promote."},
            {"title": "Build relationships one-on-one", "description": "Group socializing might drain you, but relationships matter for influence and information. Schedule coffee chats or walking meetings with key colleagues."},
            {"title": "Prepare contributions in advance", "description": "In meetings, extroverts often dominate early airtime. Prepare what you want to say beforehand and share it early, before the conversation moves on."},
            {"title": "Practice flexibility with small changes", "description": "Build your change tolerance by consciously accepting minor disruptions. This creates capacity for when larger changes are unavoidable."},
            {"title": "Acknowledge emotions before problem-solving", "description": "When colleagues share frustrations, pause before offering solutions. Try: 'That sounds really frustrating' or 'I can see why that's stressful.' This helps more emotional colleagues feel heard."}
        ],
        "ideal_team_role": "Operations Manager, Quality Controller, Risk Manager, Technical Lead, or Analyst — roles requiring reliability, thoroughness, and sustained focus.",
        "complementary_archetypes": ["The Luminary", "The Guide", "The Catalyst"],
        "challenging_pairings": [
            {
                "archetype": "The Catalyst",
                "challenge": "Their constant energy and pivots may feel destabilizing to your need for consistency",
                "opportunity": "You can help them finish things while they help you embrace necessary change"
            }
        ]
    }
}


def seed_badge_definitions():
    """Seed badge_definitions collection."""
    print("Seeding badge_definitions...")

    batch = db.batch()
    badges_ref = db.collection("badge_definitions")

    for badge_id, badge_data in BADGE_DEFINITIONS.items():
        doc_ref = badges_ref.document(badge_id)
        batch.set(doc_ref, badge_data)

    batch.commit()
    print(f"  - Created {len(BADGE_DEFINITIONS)} badge definitions")


def seed_archetype_insights():
    """Seed archetype_insights collection."""
    print("Seeding archetype_insights...")

    batch = db.batch()
    insights_ref = db.collection("archetype_insights")

    for archetype_id, insight_data in ARCHETYPE_INSIGHTS.items():
        doc_ref = insights_ref.document(archetype_id)
        batch.set(doc_ref, insight_data)

    batch.commit()
    print(f"  - Created {len(ARCHETYPE_INSIGHTS)} archetype insights")


def main():
    """Run all seeding operations."""
    print("=" * 60)
    print("Firestore Seeding Script")
    print("=" * 60)

    start_time = time.time()

    try:
        seed_badge_definitions()
        seed_archetype_insights()

        elapsed = time.time() - start_time
        print("=" * 60)
        print(f"Seeding completed successfully in {elapsed:.2f}s")
        print("=" * 60)

    except Exception as e:
        print(f"Error during seeding: {e}")
        raise


if __name__ == "__main__":
    main()
