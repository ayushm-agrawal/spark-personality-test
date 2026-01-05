"""
Seed script to create archetype_insights collection in Firestore.

Run from backend/app directory:
    python seed_archetype_insights.py

This creates deep insights for all 8 archetypes with concise and deep versions.
"""

import time
from firebase import db


ARCHETYPE_INSIGHTS = {
    # ============================================================================
    # THE ARCHITECT
    # ============================================================================
    "architect": {
        "archetype_id": "architect",
        "display_name": "The Architect",
        "tagline": "Building tomorrow's blueprint, today.",
        "color": "#1B5E20",
        "icon": "building",

        "summary_concise": "You don't just dream—you build. Your mind naturally breaks down complex visions into actionable steps. You're the rare combination of visionary and executor.",

        "summary_deep": """You possess a remarkable ability to hold two seemingly contradictory qualities in balance: visionary thinking and practical execution. While many people are either dreamers or doers, you've developed the capacity to move fluidly between these modes.

Your mind operates like a sophisticated planning engine. When presented with an ambitious goal, you instinctively begin decomposing it into phases, milestones, and tasks. This isn't mere project management—it's how you think. You see structure where others see chaos, and you find genuine satisfaction in creating order from complexity.

What sets you apart from pure planners is your willingness to act. You understand that plans are hypotheses to be tested, not precious documents to be protected. You'll revise a detailed plan without hesitation when reality provides better information. This combination of thoroughness and adaptability makes you exceptionally effective at shipping meaningful work.""",

        "collaboration_strengths": {
            "concise": "You transform chaos into structure without killing creativity. Teams trust you to actually ship what you promise. You ask the practical questions that save weeks of wasted effort.",

            "deep": """Your greatest contribution to any team is your ability to be the bridge between imagination and reality. When a team has exciting ideas but no clear path forward, you naturally step into the role of making those ideas achievable.

You have a gift for asking the right questions at the right time. While others are still enchanted by the potential of an idea, you're already thinking about dependencies, constraints, and sequencing. This isn't pessimism—it's practical wisdom. Your questions don't kill ideas; they strengthen them by revealing which aspects need more thought.

Teams learn to rely on your estimates because you've developed the discipline of accounting for complexity. Where optimistic teammates might promise delivery in two weeks, you factor in the integration challenges, the testing cycles, and the inevitable surprises. Your reliability builds trust, which paradoxically gives you more influence over the team's direction.

Research on high-performing teams consistently shows that successful groups need members who can translate vision into executable plans. You provide this crucial function naturally, often without recognition for how much chaos you're preventing behind the scenes."""
        },

        "potential_blind_spots": {
            "concise": "You may over-engineer when scrappy would do. Perfectionism can delay shipping. You might dismiss 'impractical' ideas that need more exploration.",

            "deep": """Your strength in planning and execution comes with predictable shadow sides that are worth understanding.

The most common trap is over-engineering. Because you can see all the potential complications, you may build for problems that never materialize. The startup graveyard is filled with beautifully architected systems that took too long to ship and missed their market window. Learning when 'good enough' is actually optimal is a lifelong practice for Architects.

You may also struggle with ideas in their early, fragile stages. When someone shares a half-formed concept, your instinct to identify practical challenges can inadvertently crush creativity before it has a chance to develop. The same questions that strengthen mature ideas can kill nascent ones. Consider adopting a 'yes, and' approach in early brainstorming, saving your practical lens for later stages.

Finally, your comfort with structure can make you uncomfortable with genuine ambiguity. Some of the most valuable work happens in the messy middle where the path forward isn't clear. Learning to tolerate—even embrace—uncertainty without immediately reaching for structure can expand your creative range significantly."""
        },

        "team_phases": {
            "ideation": "You help ground brainstorming by asking 'how might we actually build this?' without shutting down creative exploration. Your best contribution is identifying which exciting ideas are also achievable.",
            "execution": "This is where you shine. You break down work into manageable chunks, identify dependencies, and keep the team focused on what matters most. You're often the one who catches scope creep before it derails the timeline.",
            "conflict": "You tend to approach disagreements analytically, looking for the objective truth of the matter. Be mindful that some conflicts are about values or feelings, not just facts. Your instinct to 'solve' interpersonal issues may miss what's really going on.",
            "crunch_time": "Your calm under pressure is an asset. You help the team prioritize ruthlessly when time is short. Just watch your tendency to take on too much yourself rather than delegating."
        },

        "energy_dynamics": {
            "drains": [
                "Endless meetings with no clear outcomes",
                "Projects that keep changing direction without reason",
                "Teammates who don't follow through on commitments",
                "Being asked to execute someone else's poorly-thought-out plan",
                "Environments where planning is dismissed as 'overthinking'"
            ],
            "energizes": [
                "Complex problems with clear success criteria",
                "Autonomy to design your own approach",
                "Working with people who value follow-through",
                "Seeing a plan come together successfully",
                "Teaching others your systematic approach"
            ]
        },

        "actionable_tips": [
            {
                "title": "Implement the 'Two-Week Rule'",
                "description": "Before building any feature or system, ask: 'What's the simplest version we could ship in two weeks?' Force yourself to identify the core value, separate from the nice-to-haves. You can always iterate."
            },
            {
                "title": "Schedule 'Mess Time'",
                "description": "Block time in your calendar for unstructured exploration. No agenda, no deliverables. Let yourself follow curiosity without planning where it leads. This expands your creative range."
            },
            {
                "title": "Practice 'Yes, And' in Brainstorms",
                "description": "In early ideation, commit to building on others' ideas before evaluating them. Your practical questions are valuable, but they're most helpful after ideas have had room to develop."
            },
            {
                "title": "Find Your Alchemist",
                "description": "Seek out a creative partner who thinks differently than you—someone comfortable with ambiguity and experimentation. They'll push your ideas in directions you wouldn't go alone, and you'll help them actually ship."
            }
        ],

        "ideal_team_role": "Technical Lead or Project Architect - the person responsible for turning vision into executable plans and ensuring the team ships quality work on time.",

        "complementary_archetypes": ["alchemist", "catalyst", "luminary"],
        "challenging_pairings": ["architect", "sentinel"],

        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "very_high",
            "Extraversion": "medium_high",
            "Agreeableness": "medium",
            "Emotional_Stability": "high"
        }
    },

    # ============================================================================
    # THE CATALYST
    # ============================================================================
    "catalyst": {
        "archetype_id": "catalyst",
        "display_name": "The Catalyst",
        "tagline": "Sparking change, one idea at a time.",
        "color": "#FF6F00",
        "icon": "lightning",

        "summary_concise": "You're the match that lights the fire. Ideas flow through you like electricity, and your enthusiasm is genuinely contagious. You make things happen that wouldn't happen without you.",

        "summary_deep": """You experience the world as a field of possibilities waiting to be activated. Where others see stable situations, you see potential for transformation. This isn't restlessness—it's a genuine sensitivity to the gap between what is and what could be.

Your energy is your superpower. When you walk into a room, the pace picks up. When you engage with an idea, it takes on new life. This isn't mere enthusiasm; it's a kind of creative voltage that genuinely catalyzes change in systems and people around you.

You're naturally drawn to beginnings. The first spark of a new project, the moment an idea clicks, the energy of starting something from nothing—these are the moments that feel most alive to you. You have an intuitive sense for when a situation is ready for change, and you often provide the activation energy that tips things from potential to kinetic.""",

        "collaboration_strengths": {
            "concise": "You break through stagnation and rally people around new possibilities. Your energy is genuinely contagious. You see connections others miss and aren't afraid to voice the unconventional take.",

            "deep": """Your primary gift to teams is momentum. When projects get stuck—which happens to every project—you're often the one who breaks the logjam. Sometimes this is through sheer energy, sometimes through a reframe that shifts everyone's perspective, sometimes through the willingness to try something different when the safe path isn't working.

You're also remarkably good at cross-pollination. Because you're drawn to many different domains and ideas, you naturally carry insights from one context to another. The solution to a design problem might come from something you read about biology. The breakthrough in team dynamics might come from a technique you saw used in a completely different industry. This pattern-matching across domains is genuinely valuable and often under-recognized.

Teams with Catalysts tend to be more experimental. Your willingness to try things—and to fail quickly—raises the group's tolerance for productive risk-taking. In environments where innovation matters, this cultural contribution may be as valuable as any specific idea you generate.

Research on creative teams shows that the presence of high-energy, idea-generating members correlates with overall team creativity—even when many of those ideas don't pan out. You provide the raw material that others can refine."""
        },

        "potential_blind_spots": {
            "concise": "You may start three projects instead of finishing one. Follow-through requires conscious effort. Your pace can leave others feeling overwhelmed or left behind.",

            "deep": """Your greatest strength—the ability to generate energy and new beginnings—casts a predictable shadow: difficulty with follow-through. Not because you're flaky or uncommitted, but because the middle and end of projects simply don't provide the same neurological reward as the beginning.

This is worth understanding at a deeper level. The initial phase of any project is rich with novelty, possibility, and rapid progress. As projects mature, they require different skills: patience, attention to detail, grinding through obstacles. These aren't inherently less valuable—but they may be less energizing for you. Recognizing this pattern is the first step to working with it rather than against it.

Your pace can also create challenges for teammates. What feels like exciting momentum to you may feel overwhelming to others. Some collaborators need more time to process, to check their work, to make sure they understand before moving forward. Learning to modulate your energy based on what the situation needs—not just what you feel—expands your effectiveness significantly.

Finally, your attraction to novelty can sometimes manifest as a subtle devaluation of maintenance work. Keeping existing systems running, improving established processes, supporting ongoing operations—this work is essential but rarely exciting. Be careful not to unconsciously signal that this work is less important than new initiatives."""
        },

        "team_phases": {
            "ideation": "This is your moment. You generate ideas rapidly, make unexpected connections, and elevate the energy of brainstorming sessions. Just remember to leave space for quieter teammates to contribute.",
            "execution": "This phase requires conscious effort from you. Find ways to stay engaged—perhaps by taking on the parts that involve variety or external communication. Partner with detail-oriented teammates for the sustained attention work.",
            "conflict": "You may try to pivot away from conflict too quickly, missing important issues that need to be worked through. Your optimism is valuable, but make sure it doesn't paper over real problems.",
            "crunch_time": "Your energy is an asset, but watch for burnout—yours and others'. Your tendency to push through can mask exhaustion. Make sure the team is pacing sustainably."
        },

        "energy_dynamics": {
            "drains": [
                "Repetitive tasks with no variation",
                "Extended periods of solo detail work",
                "Environments that punish experimentation",
                "Slow-moving bureaucratic processes",
                "Having to follow rigid procedures"
            ],
            "energizes": [
                "New projects and fresh challenges",
                "Brainstorming with engaged collaborators",
                "Variety and context-switching",
                "Seeing ideas take off and gain momentum",
                "Environments that reward trying new things"
            ]
        },

        "actionable_tips": [
            {
                "title": "Build Finish Systems",
                "description": "Create external structures that help you complete things: accountability partners, public commitments, artificial deadlines. Your energy naturally peaks at the start; design systems that carry you through the middle."
            },
            {
                "title": "Partner with Gardeners",
                "description": "Find collaborators who excel at the sustained attention work you find draining. Genuine partnership means valuing their contribution as equal to yours, not just using them to clean up after your excitement moves on."
            },
            {
                "title": "Practice 'Energy Reads'",
                "description": "Before bringing your full intensity to a situation, check the room. Ask yourself: 'What does this moment need?' Sometimes the answer is your full energy. Sometimes it's restraint."
            },
            {
                "title": "Create a 'Current Projects' Limit",
                "description": "Before starting something new, review what you're already committed to. Set a maximum number of active projects and stick to it. New ideas go in a backlog, not into immediate action."
            }
        ],

        "ideal_team_role": "Innovation Lead or Creative Director - the person who generates new possibilities, breaks through stagnation, and keeps the team from getting too comfortable.",

        "complementary_archetypes": ["gardener", "architect", "sentinel"],
        "challenging_pairings": ["catalyst", "alchemist"],

        "trait_profile": {
            "Openness": "very_high",
            "Conscientiousness": "medium",
            "Extraversion": "very_high",
            "Agreeableness": "medium_high",
            "Emotional_Stability": "medium"
        }
    },

    # ============================================================================
    # THE STRATEGIST
    # ============================================================================
    "strategist": {
        "archetype_id": "strategist",
        "display_name": "The Strategist",
        "tagline": "Three moves ahead, always.",
        "color": "#1A237E",
        "icon": "chess",

        "summary_concise": "While others react, you anticipate. Your mind naturally maps out scenarios, weighing options most people don't even see. When pressure mounts, you get calmer.",

        "summary_deep": """Your mind operates like a chess engine, constantly running simulations and evaluating positions. This isn't cold calculation—it's a form of perception. You simply see the landscape of possibilities more clearly than most people, including the second and third-order consequences that others miss.

What makes you effective isn't just seeing ahead—it's maintaining clarity under pressure. When stakes rise and emotions intensify, you tend to get calmer and more focused. This counter-intuitive response is enormously valuable in high-stakes environments where most people's judgment degrades exactly when it matters most.

You're comfortable with the reality that good strategy sometimes means making decisions that are unpopular in the short term but correct in the long run. This willingness to optimize for outcomes rather than comfort gives you an edge, but it also means you sometimes have to choose between being liked and being right.""",

        "collaboration_strengths": {
            "concise": "You keep everyone oriented toward the actual goal when distractions multiply. Your clarity helps teams make better decisions. You see risks and opportunities that others miss.",

            "deep": """Your primary contribution to teams is clarity of purpose. In any complex endeavor, there are countless distractions, tangents, and shiny objects that can pull a group away from what actually matters. You have an unusual ability to keep the main thing the main thing, gently (or not so gently) redirecting attention when it wanders.

You're also valuable as a devil's advocate—not in the cynical sense, but in the sense of stress-testing ideas before they're implemented. Your ability to think through scenarios means you often spot the flaw in a plan that enthusiastic teammates overlooked. Done well, this makes the team's work more robust. Done poorly, it feels like you're always poking holes without contributing constructively.

Teams often look to you in crisis moments. When everything is going wrong and emotions are running high, your ability to stay calm and think clearly is genuinely stabilizing. You help people move from reactive mode to responsive mode, from 'everything is falling apart' to 'here's what we do next.'

Research on decision-making shows that groups benefit enormously from members who can maintain analytical capability under stress. This is rare and valuable. Just remember that your coolness under pressure can sometimes read as coldness or detachment to teammates who need emotional acknowledgment."""
        },

        "potential_blind_spots": {
            "concise": "You may be too private with your thinking, leaving others confused about your reasoning. Analysis paralysis is a real risk. You might undervalue emotional and relational factors.",

            "deep": """Your ability to see multiple moves ahead is powerful, but it comes with characteristic blind spots.

The most common is keeping your thinking too private. Because you've run the scenarios internally, your conclusions feel obvious to you—but to teammates who haven't had access to your reasoning, they can seem arbitrary or even arrogant. Learning to share your thinking process, not just your conclusions, dramatically increases your influence and makes collaboration smoother.

Analysis paralysis is another trap. When you can see all the ways things might go wrong, it's tempting to keep gathering information and running scenarios rather than committing to action. At some point, more analysis yields diminishing returns. The skill to develop is recognizing when you have 'enough' information to decide—which is almost always less than your mind tells you it needs.

You may also underweight emotional and relational factors in your calculations. These 'soft' variables are genuinely harder to model, but they're often decisive. A strategy that is theoretically optimal but fails to account for human psychology often loses to a 'worse' strategy that people actually execute with commitment. Learning to factor in motivation, trust, and emotional dynamics makes your strategic thinking more realistic."""
        },

        "team_phases": {
            "ideation": "You help evaluate which ideas have legs and which are dead ends. Your scenario-planning reveals hidden potential and hidden risks. Just be careful not to critique too early.",
            "execution": "You excel at prioritization and course-correction. When the original plan meets reality, you help the team adapt without losing sight of the goal. You're good at knowing which deviations matter and which don't.",
            "conflict": "You tend to look for the optimal solution, which is valuable—but make sure you're hearing the underlying concerns, not just the surface positions. Sometimes what looks like a strategic disagreement is actually a values conflict.",
            "crunch_time": "Your clarity under pressure is an enormous asset. You help the team focus on what actually moves the needle. Just remember that others may need more emotional support than you do."
        },

        "energy_dynamics": {
            "drains": [
                "Making decisions without adequate information",
                "Environments driven by politics rather than merit",
                "Having to repeatedly explain your reasoning",
                "Short-term thinking that ignores consequences",
                "Teammates who don't think before acting"
            ],
            "energizes": [
                "Complex problems that reward careful analysis",
                "High-stakes situations where good decisions matter",
                "Working with people who value strategic thinking",
                "Seeing a long-term plan come together",
                "Competitive environments that reward foresight"
            ]
        },

        "actionable_tips": [
            {
                "title": "Narrate Your Thinking",
                "description": "Practice sharing your reasoning process out loud, even when the conclusion seems obvious to you. 'Here's how I'm thinking about this...' builds trust and helps others learn from your perspective."
            },
            {
                "title": "Set Decision Deadlines",
                "description": "When you notice yourself gathering more information, ask: 'Will this change my decision?' Set explicit deadlines for when you'll decide, regardless of remaining uncertainty."
            },
            {
                "title": "Factor in Motivation",
                "description": "For every strategy, ask: 'Will the people involved actually execute this with energy?' A theoretically inferior approach that people commit to often beats an optimal plan that nobody owns."
            },
            {
                "title": "Find a Guide Partner",
                "description": "Collaborate with someone strong in emotional intelligence. They'll help you see the human factors you might otherwise miss, and you'll help them think through consequences more rigorously."
            }
        ],

        "ideal_team_role": "Chief Strategist or Decision Architect - the person who helps the team think clearly about priorities, trade-offs, and long-term positioning.",

        "complementary_archetypes": ["catalyst", "guide", "alchemist"],
        "challenging_pairings": ["strategist", "luminary"],

        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "high",
            "Extraversion": "high",
            "Agreeableness": "medium",
            "Emotional_Stability": "very_high"
        }
    },

    # ============================================================================
    # THE GUIDE
    # ============================================================================
    "guide": {
        "archetype_id": "guide",
        "display_name": "The Guide",
        "tagline": "Lighting the path for others to follow.",
        "color": "#00695C",
        "icon": "compass",

        "summary_concise": "You have a gift for seeing potential—in ideas, in projects, but especially in people. Your impact often happens in moments others don't see: the encouragement that changes everything.",

        "summary_deep": """You possess an unusual sensitivity to human potential. Where others see a person as they are, you naturally perceive who they could become. This isn't wishful thinking—it's a form of pattern recognition, honed through deep attention to people and their development over time.

Your influence often works through subtle channels that don't show up on org charts or get recognized in meetings. The question you asked that reframed someone's thinking. The encouragement you offered before a crucial moment. The space you created for someone to step up. These interventions are easy to overlook but often decisive.

You understand intuitively that helping others succeed isn't a zero-sum game. When the people around you flourish, the whole system benefits—including you. This orientation toward multiplication rather than competition shapes how you show up in teams and relationships.""",

        "collaboration_strengths": {
            "concise": "You make everyone around you more effective and confident. You ask the questions that change conversations. You notice when someone's contribution gets overlooked and you amplify it.",

            "deep": """Your primary contribution is multiplying the effectiveness of everyone around you. This is genuinely rare and often undervalued in cultures that celebrate individual achievement. But research on high-performing teams consistently shows that the presence of 'multipliers'—people who make others better—is one of the strongest predictors of group success.

You have a gift for reading the emotional undercurrents in groups. While others focus on the explicit content of discussions, you're tracking who's disengaged, who's holding back, who needs recognition, who's struggling. This emotional intelligence lets you make interventions that others don't even see the need for.

You're also skilled at creating psychological safety—the sense that it's okay to take risks, ask questions, and make mistakes without judgment. Research by Google's Project Aristotle identified psychological safety as the single best predictor of team performance. This isn't about being nice; it's about creating the conditions where people can do their best work.

Finally, you often serve as a bridge between people and perspectives that might otherwise clash. Your ability to see the validity in different positions and to translate between different communication styles makes collaboration smoother. Teams with Guides tend to have fewer destructive conflicts because small tensions get addressed before they escalate."""
        },

        "potential_blind_spots": {
            "concise": "You may prioritize harmony over honest feedback. Taking care of everyone else can mean neglecting yourself. You might avoid conflict that actually needs to happen.",

            "deep": """Your orientation toward supporting others, while genuine and valuable, comes with predictable blind spots.

The most common is conflict avoidance. Because you're attuned to relational dynamics, you may feel conflict more acutely than others—and therefore be more motivated to smooth it over. But some conflicts are necessary. Some honest feedback is uncomfortable but essential. Some tensions need to surface rather than be managed underground. Learning to distinguish between destructive conflict (to be minimized) and productive conflict (to be facilitated) expands your effectiveness significantly.

You may also struggle with putting your own oxygen mask on first. Your attunement to others' needs can mean that your own needs consistently take last priority. This isn't sustainable, and it eventually degrades your ability to show up for others. The metaphor of the oxygen mask is apt: you genuinely cannot help others effectively if you're depleted.

Finally, your belief in people's potential can sometimes blind you to their actual performance. Not everyone will grow into what they could be. Some people need accountability more than encouragement. Learning to hold the tension between believing in potential and demanding current excellence is a crucial development edge for Guides."""
        },

        "team_phases": {
            "ideation": "You create space for all voices to be heard, especially quieter ones. You ask the questions that deepen ideas and draw out insights. Just make sure your facilitation doesn't prevent you from contributing your own perspectives.",
            "execution": "You help maintain team cohesion and motivation when the work gets hard. You notice when people are struggling and provide support. Be careful not to take on others' emotional burdens to the point of depleting yourself.",
            "conflict": "You often see conflicts coming before they erupt and can sometimes prevent them. When they do occur, you're skilled at finding common ground. The challenge is knowing when to let conflict play out rather than resolving it prematurely.",
            "crunch_time": "You help the team stay connected and functional under stress. Your ability to read the room tells you who needs support and when. Make sure you're not the only one doing the emotional labor."
        },

        "energy_dynamics": {
            "drains": [
                "Environments where people are treated as interchangeable",
                "Persistent negativity or cynicism",
                "Being unable to help someone who's struggling",
                "Seeing potential wasted due to bad systems",
                "Having your relational contributions overlooked"
            ],
            "energizes": [
                "Watching someone grow into their potential",
                "Deep conversations that create insight",
                "Teams where people genuinely support each other",
                "Being asked for your perspective on people situations",
                "Creating environments where others thrive"
            ]
        },

        "actionable_tips": [
            {
                "title": "Schedule Self-Care Non-Negotiably",
                "description": "Put your own renewal activities on the calendar with the same commitment you'd give to helping someone else. Your effectiveness depends on your reserves."
            },
            {
                "title": "Practice Uncomfortable Honesty",
                "description": "When you notice yourself softening feedback to preserve the relationship, ask: 'What does this person actually need to hear?' Kind honesty serves people better than comfortable silence."
            },
            {
                "title": "Let Some Conflicts Happen",
                "description": "Before intervening in a tension, ask: 'Does this need to be resolved, or does it need to be worked through?' Some conflicts are productive and shouldn't be short-circuited."
            },
            {
                "title": "Partner with Strategists",
                "description": "Find collaborators who are strong on analytical thinking. They'll help you think through decisions more rigorously, while you'll help them factor in the human elements they might miss."
            }
        ],

        "ideal_team_role": "Team Coach or Culture Steward - the person who ensures the team stays healthy, connected, and developing, even when focused on external deliverables.",

        "complementary_archetypes": ["strategist", "alchemist", "architect"],
        "challenging_pairings": ["guide", "catalyst"],

        "trait_profile": {
            "Openness": "high",
            "Conscientiousness": "medium_high",
            "Extraversion": "high",
            "Agreeableness": "very_high",
            "Emotional_Stability": "medium_high"
        }
    },

    # ============================================================================
    # THE ALCHEMIST
    # ============================================================================
    "alchemist": {
        "archetype_id": "alchemist",
        "display_name": "The Alchemist",
        "tagline": "Transforming the ordinary into extraordinary.",
        "color": "#6A1B9A",
        "icon": "wand",

        "summary_concise": "You see what others walk past. Where they see a problem, you see raw material. Your mind works through synthesis—combining ideas into something that didn't exist before.",

        "summary_deep": """You experience reality differently than most people. Where others see fixed categories and conventional uses, you see fluidity and possibility. A problem isn't just something to solve—it's raw material to transform into something unexpected and often beautiful.

Your creative process is fundamentally synthetic. Rather than following linear paths from problem to solution, your mind gathers fragments from disparate sources and finds unexpected connections. The insight that solves a technical challenge might come from a poem. The design that feels inevitable in retrospect drew from architecture, cooking, and something you half-remembered from childhood.

You need space to let this process work. Your best ideas often don't arrive through effort but through incubation—the background processing that happens when you're walking, showering, or just staring out a window. This can look like idleness to others, but it's essential to how you think.""",

        "collaboration_strengths": {
            "concise": "You ask 'what if' when everyone else is stuck on 'what is'. Your unexpected connections generate breakthroughs. The work you create has depth that others discover over time.",

            "deep": """Your primary contribution is bringing genuinely novel perspectives to problems that have resisted conventional approaches. When a team is stuck, it's often because they're thinking about the problem in limiting ways. Your ability to see from entirely different angles can break these logjams.

You're also valuable as a source of what's called 'combinatorial creativity'—the ability to connect ideas from different domains in ways that generate new possibilities. This is increasingly recognized as essential to innovation. Pure expertise in one field tends to produce incremental improvements; transformative breakthroughs often come from unexpected cross-pollination of the kind you do naturally.

The depth of your work is another contribution that may not be immediately apparent. You tend to create things with layers—meaning that reveals itself over time. This isn't showing off; it's a natural result of how your mind works. In contexts where lasting impact matters more than quick wins, this depth is genuinely valuable.

Finally, you often serve as permission structure for others' creativity. Your willingness to think unconventionally and share half-formed ideas makes it safer for others to do the same. Teams with Alchemists tend to have richer creative cultures because you model what's possible."""
        },

        "potential_blind_spots": {
            "concise": "Perfectionism can delay shipping. You might dismiss 'practical' concerns as uncreative. Working alone too much limits your impact and isolates you.",

            "deep": """Your depth and originality are genuine strengths, but they come with characteristic shadows.

Perfectionism is the most common trap. Because you can see what the work could be, anything less feels like compromise. But the gap between 'done' and 'perfect' is often invisible to others and not worth the cost. Learning to ship work that's good enough—trusting that iteration will get you where perfectionism can't—is a crucial skill to develop.

You may also undervalue practical constraints. When someone raises concerns about feasibility, timeline, or budget, it's tempting to hear this as an attack on creativity. But constraints aren't the enemy of creativity; they're often the crucible that shapes it. Some of your best work probably emerged from tight constraints that forced unexpected solutions.

Working in isolation is another risk. Your creative process benefits from solitude, but too much isolation cuts you off from the collision of perspectives that generates your best work. The balance is tricky: enough alone time for incubation, enough interaction for cross-pollination.

Finally, you may struggle to explain your thinking in ways others can follow. The connections that seem obvious to you often aren't visible to others. Learning to build bridges from your intuitive leaps to others' understanding increases your influence significantly."""
        },

        "team_phases": {
            "ideation": "You bring unexpected perspectives that reframe problems entirely. Your best contributions often come when you've had time to sit with a challenge before the meeting. Consider sharing half-formed ideas—they often spark others' creativity.",
            "execution": "The detail work of implementation can feel tedious. Partner with Architects or Gardeners who find this energizing. Your role might be quality passes that ensure the depth isn't lost in execution.",
            "conflict": "You may retreat into your own world when tensions arise. Your unique perspective is actually valuable in conflicts—sometimes the breakthrough comes from reframing the disagreement entirely.",
            "crunch_time": "You're capable of deep focus when inspired. The 2am breakthrough is genuinely possible for you. Just watch for diminishing returns when pushing through exhaustion."
        },

        "energy_dynamics": {
            "drains": [
                "Environments that don't allow time for thinking",
                "Being asked to just 'execute someone else's vision'",
                "Excessive meetings and social obligations",
                "Work that doesn't allow for creativity or depth",
                "Having ideas dismissed as 'impractical'"
            ],
            "energizes": [
                "Unstructured time to explore and connect ideas",
                "Problems that haven't been solved before",
                "Working with materials or concepts at a deep level",
                "Collaborators who appreciate your unconventional thinking",
                "Creating something that makes people feel or see differently"
            ]
        },

        "actionable_tips": [
            {
                "title": "Ship Early and Iterate",
                "description": "Set a 'minimum viable' threshold and commit to sharing work when you hit it—not when it feels 'ready'. Your first 80% often contains the magic; the last 20% is usually invisible to others."
            },
            {
                "title": "Schedule Collaboration",
                "description": "Solitude is essential for your process, but isolation limits your impact. Build regular touchpoints with collaborators into your routine, even when it feels like interruption."
            },
            {
                "title": "Practice Translation",
                "description": "After an intuitive leap, ask: 'How would I explain this to someone who doesn't think like me?' Building these bridges increases your influence and sometimes reveals new dimensions in your own thinking."
            },
            {
                "title": "Partner with Architects",
                "description": "Find collaborators who excel at execution and structure. They'll help you ship your ideas, while you'll help them see possibilities they'd otherwise miss. This complementary partnership is powerful."
            }
        ],

        "ideal_team_role": "Creative Lead or Innovation Catalyst - the person who brings fresh perspectives, generates unexpected solutions, and ensures the work has genuine depth.",

        "complementary_archetypes": ["architect", "guide", "catalyst"],
        "challenging_pairings": ["alchemist", "sentinel"],

        "trait_profile": {
            "Openness": "very_high",
            "Conscientiousness": "medium",
            "Extraversion": "low",
            "Agreeableness": "medium_high",
            "Emotional_Stability": "high"
        }
    },

    # ============================================================================
    # THE GARDENER
    # ============================================================================
    "gardener": {
        "archetype_id": "gardener",
        "display_name": "The Gardener",
        "tagline": "Nurturing growth, cultivating excellence.",
        "color": "#2E7D32",
        "icon": "seedling",

        "summary_concise": "You play the long game. While others chase quick wins, you're building something that compounds. You notice what needs attention before it becomes urgent.",

        "summary_deep": """You understand intuitively what most people have to learn painfully: that sustainable results come from sustained attention, that the most valuable things in life compound over time, and that cultivation beats force.

Your patience isn't passive waiting—it's active cultivation. You notice what needs watering before it wilts, what needs pruning before it overgrows, what needs time before it's ready to harvest. This attentiveness to the rhythms of growth gives you power that impatient approaches can't match.

You're naturally oriented toward systems and sustainability. Quick fixes that create long-term problems don't appeal to you. You'd rather build something that grows stronger over time than win the sprint and collapse at the marathon. This long-term orientation is increasingly valuable in a world obsessed with immediate results.""",

        "collaboration_strengths": {
            "concise": "You keep momentum going when initial excitement fades. You create environments where people and projects thrive. Your consistency becomes the foundation others can build on.",

            "deep": """Your primary contribution is sustainability. In any significant endeavor, there's a pattern: initial enthusiasm generates rapid early progress, then reality sets in, and the hard work of maintaining momentum begins. This is where many projects die—not from lack of good ideas, but from lack of sustained attention. You excel in exactly this zone.

You're also exceptional at creating conditions for growth rather than forcing outcomes directly. This applies to projects, teams, and individuals. Instead of pushing for specific results, you tend to cultivate environments where good results emerge naturally. This approach is less controllable but often more effective, especially for complex adaptive systems like teams and organizations.

Your consistency builds trust over time. People learn that you'll be there, doing good work, regardless of external recognition or excitement. This reliability becomes a resource that others can depend on, which enables them to take risks they wouldn't otherwise take.

Research on team performance shows that sustained effort over time beats sporadic intensity. You embody this insight. Your contribution may be less visible than the dramatic interventions, but it's often more decisive."""
        },

        "potential_blind_spots": {
            "concise": "You might take on everyone else's emotional labor. Advocating for yourself can feel unnatural. You may be slow to respond when situations genuinely need urgency.",

            "deep": """Your orientation toward nurturing and sustaining, while valuable, comes with characteristic blind spots.

The most common is taking on others' burdens to an unsustainable degree. Because you're attuned to what needs attention, you may find yourself carrying more than your share—of emotional labor, of maintenance work, of keeping things running while others chase shiny objects. This generosity is genuine, but it's not sustainable if it's not reciprocated.

You may also struggle to advocate for your own needs. The same attentiveness you apply to others doesn't always extend to yourself. Learning to give your own development and wellbeing the same quality attention you give to others is essential—not as selfishness, but as the foundation for continued service.

Your patience, while generally a strength, can become a weakness in situations that genuinely require urgency. Sometimes things need to move fast. Sometimes waiting isn't cultivation—it's avoidance. Learning to distinguish between patient cultivation and inappropriate delay is important.

Finally, your focus on sustainability can sometimes manifest as resistance to necessary disruption. Some systems need to be broken before they can be improved. Growth sometimes requires destruction of what existed before. Being too attached to preservation can block necessary transformation."""
        },

        "team_phases": {
            "ideation": "You ensure that practical sustainability is considered alongside exciting possibilities. You might ask: 'How will we maintain this?' or 'What happens in month six, not just month one?'",
            "execution": "This is your zone. While others' attention wanders, yours stays steady. You catch the small issues before they become big ones. You keep the team connected to their original purpose.",
            "conflict": "You often absorb conflict to keep things functional, which can be helpful but also depleting. Make sure you're not always the one doing the peacemaking labor.",
            "crunch_time": "You keep the team functional when others are burning out. You notice when people need breaks, food, or encouragement. Just make sure you're taking care of yourself too."
        },

        "energy_dynamics": {
            "drains": [
                "Environments that only reward flashy achievements",
                "Chronic under-resourcing of maintenance work",
                "Being taken for granted by those you support",
                "Short-term thinking that ignores sustainability",
                "Having to constantly justify the value of cultivation"
            ],
            "energizes": [
                "Watching something you've nurtured flourish",
                "Working with people who value sustainability",
                "Having autonomy over how you structure your work",
                "Long-term projects that reward patience",
                "Creating systems that run smoothly"
            ]
        },

        "actionable_tips": [
            {
                "title": "Track Your Giving",
                "description": "Keep a simple log of what you give and what you receive. Not to keep score, but to notice patterns. If it's consistently unbalanced, something needs to change."
            },
            {
                "title": "Practice Urgency",
                "description": "Identify situations that genuinely require speed and practice responding to them. Not everything needs patient cultivation—some things need decisive action."
            },
            {
                "title": "Make Your Work Visible",
                "description": "Sustainability work often happens in the background. Find ways to make your contributions visible, not for ego, but so they're properly valued and resourced."
            },
            {
                "title": "Partner with Catalysts",
                "description": "Find collaborators who bring energy and urgency. They'll push you to move faster when needed, while you'll help them build something that lasts."
            }
        ],

        "ideal_team_role": "Operations Lead or Team Health Steward - the person who ensures sustainable progress, maintains what's been built, and keeps the team functional over the long haul.",

        "complementary_archetypes": ["catalyst", "luminary", "strategist"],
        "challenging_pairings": ["gardener", "alchemist"],

        "trait_profile": {
            "Openness": "medium_high",
            "Conscientiousness": "high",
            "Extraversion": "medium",
            "Agreeableness": "very_high",
            "Emotional_Stability": "high"
        }
    },

    # ============================================================================
    # THE LUMINARY
    # ============================================================================
    "luminary": {
        "archetype_id": "luminary",
        "display_name": "The Luminary",
        "tagline": "Illuminating what could be.",
        "color": "#F9A825",
        "icon": "lightbulb",

        "summary_concise": "You see the world as it could be, and you help others see it too. Your optimism isn't naive—it's generative. You make the future feel not just possible, but inevitable.",

        "summary_deep": """You possess what might be called 'constructive vision'—the ability to see potential futures so vividly that they begin to feel real to others too. This isn't fantasy or wishful thinking; it's a form of leadership that works by changing what people believe is possible.

Your optimism is genuinely generative. When you believe in someone's potential, that belief often helps them access capabilities they didn't know they had. When you paint a vision of what could be, you're not just describing a destination—you're activating the motivation and creativity needed to get there. This effect is well-documented in research on expectation and performance.

You're comfortable at the edge of what's known, where ambiguity makes most people anxious. You find possibility energizing rather than threatening, and you're drawn to questions that don't yet have answers. This tolerance for uncertainty combined with genuine optimism makes you effective in contexts where new things need to be created.""",

        "collaboration_strengths": {
            "concise": "You keep everyone inspired when the work gets hard. Your vision creates alignment and motivation. You help people believe in possibilities they wouldn't otherwise see.",

            "deep": """Your primary contribution is inspiration—not the motivational-poster kind, but the genuine kind that helps people access their best work. When a team loses sight of why their work matters, you reconnect them. When individuals doubt their capabilities, you hold the vision of what they're becoming.

You're also skilled at what might be called 'vision integration'—taking diverse perspectives and synthesizing them into a coherent picture that everyone can see themselves in. This is valuable in contexts where alignment matters but can't be forced. You help people discover shared purpose rather than having it imposed on them.

Your comfort with ambiguity makes you valuable in early-stage work where the path forward isn't clear. While others need a detailed plan before they can commit, you can generate momentum based on direction alone. This pioneering orientation is essential for innovation but can create challenges when more structured approaches are needed.

Research on leadership consistently shows that effective leaders articulate compelling visions and help others believe in possibilities beyond current reality. You do this naturally. Just remember that vision without execution is hallucination—you need partners who can help translate inspiration into results."""
        },

        "potential_blind_spots": {
            "concise": "You may overpromise what can be delivered. Grounding dreams in concrete steps requires conscious effort. Your optimism can dismiss legitimate concerns as 'negativity'.",

            "deep": """Your visionary orientation, while genuinely valuable, comes with predictable blind spots.

The most common is the gap between vision and execution. You can see the destination so clearly that the obstacles in the way can seem like mere details to be worked out later. But those details often determine success or failure. Learning to value the translation work—turning vision into plans into actions—increases your effectiveness significantly.

Your optimism can also become a liability when it dismisses legitimate concerns. When someone raises a problem with your vision, it's tempting to hear this as negativity or lack of imagination. But some concerns are valid, and the ability to distinguish between genuine obstacles and mere pessimism is crucial. 'Yes, and' is powerful; 'yes, but' sometimes has a point.

Overpromising is a related risk. Because you can see what's possible so vividly, you may commit to more than can actually be delivered. This erodes trust over time. Learning to buffer your estimates and underpromise relative to your vision creates space for exceeding expectations rather than falling short.

Finally, your comfort with ambiguity can leave others feeling untethered. Not everyone is energized by possibility; some people need more structure and certainty. Learning to provide enough grounding for teammates who need it—without losing the expansive vision—is an important balancing act."""
        },

        "team_phases": {
            "ideation": "You excel at expanding possibility space and helping the team think bigger. Your vision of what could be is genuinely inspiring. Just remember to leave room for grounding conversations about feasibility.",
            "execution": "This phase requires partnering with detail-oriented teammates. Your role might be maintaining motivation and reconnecting the team to purpose when the work gets tedious. Don't disappear when the 'boring' work begins.",
            "conflict": "You tend to look for the higher-level perspective that transcends the immediate disagreement. This can be helpful, but make sure you're not bypassing conflicts that need to be worked through at the ground level.",
            "crunch_time": "Your ability to maintain optimism under pressure is valuable for team morale. The pitch that wins often comes from your capacity to paint a compelling vision. Just make sure the vision is deliverable."
        },

        "energy_dynamics": {
            "drains": [
                "Cynical environments that dismiss possibility",
                "Excessive focus on problems without solutions",
                "Being limited to only 'realistic' options",
                "Bureaucratic processes that kill momentum",
                "People who don't believe in their own potential"
            ],
            "energizes": [
                "Early-stage projects full of possibility",
                "Helping others see what they could become",
                "Environments that value bold thinking",
                "Articulating visions that resonate with others",
                "Working at the frontier of what's known"
            ]
        },

        "actionable_tips": [
            {
                "title": "Buffer Your Estimates",
                "description": "Whatever timeline or outcome you're imagining, add 50% to your estimates before committing. You can always exceed expectations; falling short erodes trust."
            },
            {
                "title": "Partner for Execution",
                "description": "Actively seek collaborators who are strong on implementation. Your vision creates the 'why'; they create the 'how'. This partnership is more powerful than either alone."
            },
            {
                "title": "Distinguish Concerns from Negativity",
                "description": "When someone raises a problem with your vision, ask: 'Is this person protecting something real, or are they just being pessimistic?' The answer isn't always obvious—investigate before dismissing."
            },
            {
                "title": "Ground in Specifics",
                "description": "Practice translating inspiration into concrete next steps. What's the first thing that needs to happen? What would success look like in measurable terms? This grounds your vision without limiting it."
            }
        ],

        "ideal_team_role": "Vision Keeper or Inspiring Leader - the person who articulates why the work matters, keeps the team connected to possibility, and helps people believe in what they're building.",

        "complementary_archetypes": ["gardener", "sentinel", "architect"],
        "challenging_pairings": ["luminary", "strategist"],

        "trait_profile": {
            "Openness": "very_high",
            "Conscientiousness": "medium",
            "Extraversion": "high",
            "Agreeableness": "high",
            "Emotional_Stability": "medium_high"
        }
    },

    # ============================================================================
    # THE SENTINEL
    # ============================================================================
    "sentinel": {
        "archetype_id": "sentinel",
        "display_name": "The Sentinel",
        "tagline": "Steady hands in turbulent times.",
        "color": "#37474F",
        "icon": "shield",

        "summary_concise": "When others panic, you focus. Crisis doesn't rattle you—it clarifies your thinking. Your presence is stabilizing, and your reliability lets others take risks.",

        "summary_deep": """You possess an unusual capacity to maintain effectiveness under conditions that degrade most people's performance. When pressure mounts and emotions intensify, something in you shifts into a calmer, more focused state. This isn't suppression—it's a genuine capacity for equanimity that's rare and valuable.

Your reliability is the foundation that enables others' risk-taking. Because people know you'll be there, doing consistent work, catching what falls through the cracks, they feel safer being bold. This contribution is easy to overlook but often decisive. The most spectacular creative leaps happen because someone was holding the ground.

You notice risks others dismiss. Your mind naturally runs threat scenarios and identifies vulnerabilities. This isn't pessimism—it's pattern recognition applied to what could go wrong. In contexts where failure is costly, this anticipatory awareness is enormously valuable.""",

        "collaboration_strengths": {
            "concise": "You create psychological safety that enables everyone else's creativity. Your calm under pressure stabilizes the team. You catch risks others miss and hold things together when everything's falling apart.",

            "deep": """Your primary contribution is stability—not the boring kind, but the enabling kind. Research on psychological safety shows that people are more creative, more willing to take risks, and more likely to speak up when they feel fundamentally safe. You create that safety simply by being consistently reliable and calm.

You're also valuable as a risk spotter. Your mind naturally identifies what could go wrong, which allows for prevention rather than reaction. This isn't pessimism; it's realism in service of success. Teams with effective Sentinels make fewer unforced errors because potential problems get caught earlier.

In crisis situations, your equanimity becomes actively stabilizing. When others are panicking, your calm is contagious. You help shift the group from reactive mode—where decisions are driven by fear—to responsive mode, where decisions can be made rationally. This is genuinely valuable in high-stakes environments.

Finally, you often serve as organizational memory and continuity. You remember what was decided and why. You maintain the systems and processes that keep things running. This institutional knowledge and stewardship is easy to take for granted until it's gone."""
        },

        "potential_blind_spots": {
            "concise": "You might be so reliable that others stop pulling their weight. Your risk-awareness can shade into excessive caution. Asking for help before reaching your limit is important.",

            "deep": """Your stability and reliability, while genuine strengths, come with characteristic blind spots.

The most common is enabling others' irresponsibility. Because you're always there, picking up slack, catching what falls—others may unconsciously rely on this more than is healthy for anyone. You can end up carrying more than your share while others coast. Learning to let things fail when others don't do their part—strategically and in low-stakes situations—teaches people to step up.

Your risk-awareness can also shade into excessive caution. Not every risk needs to be mitigated; some risks are worth taking. Learning to distinguish between risks that warrant concern and risks that are acceptable costs of progress is important. Otherwise, your valuable early warning system becomes an obstacle to necessary action.

You may also struggle to ask for help before reaching your limit. Your capacity for independent functioning is real, but it's not unlimited. The pattern of handling everything until you can't—and then suddenly can't—creates its own problems. Building in earlier check-ins and requests for support creates more sustainable patterns.

Finally, your emotional steadiness can sometimes read as coldness or lack of investment. Others may not realize how much you care because your care doesn't look like enthusiasm or emotional expression. Finding ways to communicate engagement that match your natural style but are readable by others improves your relationships."""
        },

        "team_phases": {
            "ideation": "You help ground discussions in reality without killing creativity. Your role is often to ask: 'What could go wrong?' and 'Have we thought about...?' Just be mindful of timing—this is more helpful later in ideation than at the start.",
            "execution": "You excel at maintaining quality and catching issues. Your steady attention to detail ensures that the work is actually solid. You're often the one debugging at 4am because someone needs to be.",
            "conflict": "You tend to stay calm when others get heated, which can be stabilizing. Be careful that your equanimity doesn't read as dismissiveness—sometimes you need to explicitly acknowledge that the stakes matter.",
            "crunch_time": "This is where your capacity for sustained, calm focus is most valuable. You help the team stay functional when panic is tempting. Just watch your own limits—you have them, even if they're higher than most."
        },

        "energy_dynamics": {
            "drains": [
                "Chronic chaos with no one taking responsibility",
                "Being the only one who follows through",
                "Environments that punish raising concerns",
                "Having your reliability taken for granted",
                "Constant firefighting without systemic improvement"
            ],
            "energizes": [
                "Maintaining complex systems that need attention",
                "Being trusted with high-stakes responsibilities",
                "Working with people who appreciate reliability",
                "Creating order and preventing problems",
                "Knowing your presence is genuinely stabilizing"
            ]
        },

        "actionable_tips": [
            {
                "title": "Let Small Things Fail",
                "description": "Strategically choose low-stakes situations to not step in. Let others experience the consequences of not following through. This teaches responsibility better than your reliable backup."
            },
            {
                "title": "Communicate Your Limits",
                "description": "Practice asking for help before you're depleted. A simple 'I'm at capacity' or 'I need support on this' is more sustainable than heroic solo efforts."
            },
            {
                "title": "Distinguish Risk from Opportunity",
                "description": "When you notice a risk, ask: 'Is this a risk that could sink us, or is it an acceptable cost of a worthwhile opportunity?' Some risks are worth taking."
            },
            {
                "title": "Partner with Luminaries",
                "description": "Find collaborators who bring vision and optimism. They'll help you see possibilities you might otherwise dismiss, while you'll help ground their aspirations in achievable reality."
            }
        ],

        "ideal_team_role": "Quality Guardian or Resilience Lead - the person who ensures reliability, catches risks early, and maintains stability that enables everyone else to take creative risks.",

        "complementary_archetypes": ["luminary", "catalyst", "guide"],
        "challenging_pairings": ["sentinel", "architect"],

        "trait_profile": {
            "Openness": "medium",
            "Conscientiousness": "very_high",
            "Extraversion": "medium_low",
            "Agreeableness": "medium_high",
            "Emotional_Stability": "very_high"
        }
    }
}


def seed_archetype_insights(dry_run: bool = False):
    """
    Seed all archetype insights to Firestore.

    Args:
        dry_run: If True, just print what would be done without making changes
    """
    insights_ref = db.collection("archetype_insights")

    print(f"{'[DRY RUN] ' if dry_run else ''}Seeding {len(ARCHETYPE_INSIGHTS)} archetype insights...\n")

    created = 0
    updated = 0
    errors = []

    for archetype_id, insight in ARCHETYPE_INSIGHTS.items():
        try:
            # Check if already exists
            existing = insights_ref.document(archetype_id).get()

            # Add timestamps
            insight_data = {
                **insight,
                "updated_at": time.time()
            }

            if existing.exists:
                print(f"  Updating: {archetype_id} ({insight['display_name']})")
                if not dry_run:
                    insights_ref.document(archetype_id).update(insight_data)
                updated += 1
            else:
                insight_data["created_at"] = time.time()
                print(f"  Creating: {archetype_id} ({insight['display_name']})")
                if not dry_run:
                    insights_ref.document(archetype_id).set(insight_data)
                created += 1

        except Exception as e:
            error_msg = f"Error with {archetype_id}: {str(e)}"
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


def verify_insights():
    """Verify all archetype insights exist and print summary."""
    insights_ref = db.collection("archetype_insights")

    print("Verifying archetype_insights collection...\n")

    all_insights = list(insights_ref.stream())

    print(f"Total archetypes: {len(all_insights)}")

    for doc in all_insights:
        insight = doc.to_dict()
        name = insight.get("display_name", "Unknown")
        has_deep = bool(insight.get("summary_deep"))
        has_tips = len(insight.get("actionable_tips", []))
        print(f"  - {name}: deep_summary={'Yes' if has_deep else 'No'}, tips={has_tips}")


if __name__ == "__main__":
    import sys

    if "--verify" in sys.argv:
        verify_insights()
    elif "--dry-run" in sys.argv or "-n" in sys.argv:
        print("=" * 50)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 50)
        print()
        seed_archetype_insights(dry_run=True)
    else:
        print("=" * 50)
        print("SEED ARCHETYPE INSIGHTS")
        print("=" * 50)
        response = input("\nThis will create/update archetype insights. Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        print()
        seed_archetype_insights(dry_run=False)

    print("\nDone!")
