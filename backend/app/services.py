"""Quiz functions for the personality test.

This module contains functions for managing a personality test session,
including starting a session, selecting interests, submitting responses,
generating adaptive questions using GPT-4o via Azure OpenAI, finalizing the test,
and determining the best personality archetype. Firestore is used as the data store,
and environment variables are loaded via dotenv.
"""

import time
import json
import uuid
import os
import logging
import random
import math
from dotenv import load_dotenv

# Configure logging to show debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from openai import AzureOpenAI
from fastapi import HTTPException
from firebase import db
from models import UserResponse, InterestSelection

# Load environment variables from .env file
load_dotenv()

# Load Azure OpenAI credentials from environment variables
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT", "https://ception-ai-service688670829041.cognitiveservices.azure.com")
AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY", "***REDACTED-AZURE-OPENAI-KEY***")
AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-5.2-chat")

# Initialize Azure OpenAI Client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# Load the system prompt from a local markdown file
with open("system_prompt.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()


def load_knowledge_base() -> dict:
    """
    Load the knowledge base for the personality test from Firestore.

    Raises:
        RuntimeError: If the knowledge base document "big_five_test" is not found in Firestore.

    Returns:
        dict: A dictionary containing the knowledge base data used to assess personality traits.
    """
    kb_ref = db.collection("knowledge_base").document("big_five_test").get()
    if not kb_ref.exists:
        raise RuntimeError("Knowledge base not found in Firestore!")
    return kb_ref.to_dict()


# Initialize the global knowledge base variable.
knowledge_base = load_knowledge_base()


# ============================================================================
# ARCHETYPE PROFILES AND MATCHING SYSTEM
# ============================================================================

# Ideal archetype profiles as normalized scores (0-100 scale)
# These represent the "ideal" Big Five profile for each archetype
ARCHETYPE_PROFILES = {
    "Visionary": {
        "Openness": 90,
        "Conscientiousness": 50,
        "Extraversion": 75,
        "Agreeableness": 60,
        "Emotional_Stability": 55
    },
    "Operator": {
        "Openness": 45,
        "Conscientiousness": 90,
        "Extraversion": 50,
        "Agreeableness": 65,
        "Emotional_Stability": 70
    },
    "Catalyst": {
        "Openness": 70,
        "Conscientiousness": 55,
        "Extraversion": 90,
        "Agreeableness": 85,
        "Emotional_Stability": 60
    },
    "Pragmatist": {
        "Openness": 55,
        "Conscientiousness": 75,
        "Extraversion": 50,
        "Agreeableness": 60,
        "Emotional_Stability": 90
    },
    "Explorer": {
        "Openness": 85,
        "Conscientiousness": 40,
        "Extraversion": 60,
        "Agreeableness": 55,
        "Emotional_Stability": 70
    }
}

# Team compatibility mapping - which archetypes work best together
ARCHETYPE_COMPATIBILITY = {
    "Visionary": {
        "best_partners": ["Operator", "Pragmatist"],
        "good_partners": ["Catalyst", "Explorer"],
        "complementary_reason": {
            "Operator": "Operators ground your bold ideas and ensure they actually get built",
            "Pragmatist": "Pragmatists help you prioritize and set realistic milestones",
            "Catalyst": "Catalysts amplify your enthusiasm and rally the team around your vision",
            "Explorer": "Explorers share your creative spirit but may need an anchor"
        }
    },
    "Operator": {
        "best_partners": ["Visionary", "Catalyst"],
        "good_partners": ["Pragmatist", "Explorer"],
        "complementary_reason": {
            "Visionary": "Visionaries provide the creative direction you excel at executing",
            "Catalyst": "Catalysts keep team energy high while you focus on delivery",
            "Pragmatist": "Pragmatists share your reliability but you may lack creative tension",
            "Explorer": "Explorers push boundaries that you can help structure"
        }
    },
    "Catalyst": {
        "best_partners": ["Operator", "Pragmatist"],
        "good_partners": ["Visionary", "Explorer"],
        "complementary_reason": {
            "Operator": "Operators provide the structure to channel your team-building energy",
            "Pragmatist": "Pragmatists keep you grounded when your enthusiasm runs high",
            "Visionary": "Visionaries give you inspiring ideas to rally the team around",
            "Explorer": "Explorers match your energy but you may drift without a planner"
        }
    },
    "Pragmatist": {
        "best_partners": ["Visionary", "Catalyst"],
        "good_partners": ["Operator", "Explorer"],
        "complementary_reason": {
            "Visionary": "Visionaries bring the bold ideas you can shape into achievable goals",
            "Catalyst": "Catalysts add the people energy while you maintain steady progress",
            "Operator": "Operators share your reliability—great for execution, may lack innovation",
            "Explorer": "Explorers push you to consider unconventional approaches"
        }
    },
    "Explorer": {
        "best_partners": ["Operator", "Pragmatist"],
        "good_partners": ["Visionary", "Catalyst"],
        "complementary_reason": {
            "Operator": "Operators help you ship your discoveries and experiments",
            "Pragmatist": "Pragmatists help you focus your curiosity on what matters most",
            "Visionary": "Visionaries share your openness—exciting but may lack execution focus",
            "Catalyst": "Catalysts energize your explorations but you need someone to build"
        }
    }
}

# Assessment mode configurations
ASSESSMENT_MODES = {
    "quick": {
        "name": "Quick Mode",
        "description": "Hackathon Personality - Fast 6-question assessment focused on collaboration under pressure",
        "question_count": 6,
        "traits_per_question": 1,
        "question_framing": "hackathon",
        "time_estimate": "2 minutes"
    },
    "standard": {
        "name": "Standard Mode",
        "description": "Team Personality - Balanced 10-question assessment with interest personalization",
        "question_count": 10,
        "traits_per_question": 1,
        "question_framing": "general",
        "time_estimate": "5 minutes"
    },
    "deep": {
        "name": "Deep Mode",
        "description": "Full Profile - Comprehensive 15-question assessment with detailed trait analysis",
        "question_count": 15,
        "traits_per_question": 1,
        "question_framing": "detailed",
        "time_estimate": "10 minutes"
    }
}


def normalize_scores(raw_scores: dict, trait_counts: dict) -> dict:
    """
    Normalize raw trait scores to a 0-100 percentage scale.

    Each trait's score is normalized based on the maximum possible score
    for that trait (number of questions × 2 points max per question).

    Args:
        raw_scores: Dictionary of raw scores per trait
        trait_counts: Dictionary of how many questions were asked per trait

    Returns:
        Dictionary of normalized scores (0-100) per trait
    """
    normalized = {}
    for trait, raw_score in raw_scores.items():
        question_count = trait_counts.get(
            trait, 2)  # Default to 2 if not tracked
        max_possible = question_count * 2  # Max 2 points per question

        if max_possible > 0:
            # Normalize to 0-100 scale
            normalized[trait] = min(100, (raw_score / max_possible) * 100)
        else:
            normalized[trait] = 50  # Default to middle if no questions asked

    return normalized


def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """
    Calculate cosine similarity between two trait profile vectors.

    Args:
        vec_a: First profile as {trait: score} dictionary
        vec_b: Second profile as {trait: score} dictionary

    Returns:
        Cosine similarity score between 0 and 1
    """
    # Get all traits that exist in both vectors
    common_traits = set(vec_a.keys()) & set(vec_b.keys())

    if not common_traits:
        return 0.0

    # Calculate dot product and magnitudes
    dot_product = sum(vec_a[t] * vec_b[t] for t in common_traits)
    magnitude_a = math.sqrt(sum(vec_a[t] ** 2 for t in common_traits))
    magnitude_b = math.sqrt(sum(vec_b[t] ** 2 for t in common_traits))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def determine_archetype(scores: dict, trait_counts: dict = None) -> dict:
    """
    Determine the best matching personality archetype using cosine similarity.

    This function normalizes raw scores to percentages, compares the user's
    profile against ideal archetype profiles using cosine similarity, and
    returns the best match along with confidence scores and trait breakdown.

    Args:
        scores: Dictionary mapping trait names to raw user scores
        trait_counts: Dictionary of how many questions were asked per trait
                     (defaults to 2 per trait if not provided)

    Returns:
        Dictionary containing:
            - archetype: The best matching archetype name
            - confidence: How well the user matches (0-100)
            - normalized_scores: User's normalized trait scores (0-100)
            - all_matches: Similarity scores for all archetypes
            - trait_breakdown: Detailed analysis per trait
    """
    # Use default trait counts if not provided
    if trait_counts is None:
        trait_counts = {trait: 2 for trait in scores.keys()}

    # Normalize user scores to 0-100 scale
    normalized_scores = normalize_scores(scores, trait_counts)

    # Calculate similarity to each archetype profile
    archetype_similarities = {}
    for archetype, profile in ARCHETYPE_PROFILES.items():
        similarity = cosine_similarity(normalized_scores, profile)
        archetype_similarities[archetype] = similarity

    # Find the best matching archetype
    best_archetype = max(archetype_similarities,
                         key=archetype_similarities.get)
    best_similarity = archetype_similarities[best_archetype]

    # Convert similarity to confidence percentage (cosine similarity is typically 0.8-1.0 range)
    # Map from typical range [0.85, 1.0] to [0, 100] for more meaningful display
    confidence = min(100, max(0, (best_similarity - 0.85) / 0.15 * 100))

    # Generate trait breakdown with interpretations
    trait_breakdown = {}
    for trait, score in normalized_scores.items():
        if score >= 75:
            level = "high"
            interpretation = "Strong indicator"
        elif score >= 50:
            level = "moderate"
            interpretation = "Balanced tendency"
        elif score >= 25:
            level = "low-moderate"
            interpretation = "Mild tendency"
        else:
            level = "low"
            interpretation = "Low indicator"

        trait_breakdown[trait] = {
            "score": round(score, 1),
            "level": level,
            "interpretation": interpretation
        }

    # Sort all matches by similarity for display
    sorted_matches = dict(sorted(
        archetype_similarities.items(),
        key=lambda x: x[1],
        reverse=True
    ))

    return {
        "archetype": best_archetype,
        "confidence": round(confidence, 1),
        "normalized_scores": {k: round(v, 1) for k, v in normalized_scores.items()},
        "all_matches": {k: round(v * 100, 1) for k, v in sorted_matches.items()},
        "trait_breakdown": trait_breakdown,
        "compatibility": ARCHETYPE_COMPATIBILITY.get(best_archetype, {})
    }


# ============================================================================
# SESSION MANAGEMENT FUNCTIONS
# ============================================================================

def start_test(mode: str = "standard") -> dict:
    """
    Start a new personality test session.

    This function generates a new session ID, initializes session data in Firestore,
    and generates the first question for the test using GPT-4o.

    Args:
        mode: Assessment mode - 'quick' (6 questions), 'standard' (10 questions),
              or 'deep' (15 questions). Defaults to 'standard'.

    Returns:
        dict: A dictionary containing the session ID, mode info, and the first question
              under the key "next_question".
    """
    # Validate and get mode configuration
    if mode not in ASSESSMENT_MODES:
        mode = "standard"
    mode_config = ASSESSMENT_MODES[mode]

    session_id = str(uuid.uuid4())
    trait_counts = {trait: 0 for trait in knowledge_base["traits"]}
    session_data = {
        "start_time": time.time(),
        "responses": {},
        "interests": [],
        "scores": {trait: 0 for trait in knowledge_base["traits"]},
        "trait_counts": trait_counts,
        "paused": False,
        "optional_responses": {},
        "response_times": {},
        "current_question": None,
        "archetype": None,
        "mode": mode,
        "question_count_target": mode_config["question_count"],
    }
    db.collection("sessions").document(session_id).set(session_data)
    return {
        "session_id": session_id,
        "mode": mode,
        "mode_config": mode_config,
        "next_question": generate_next_question(session_id)
    }


def select_interests(selection: InterestSelection) -> dict:
    """
    Save the user's selected interests to the session and generate the next question.

    Args:
        selection (InterestSelection): An object containing the session ID and a list of interests.

    Returns:
        dict: A dictionary containing a message about the update and the next question under the key
                "next_question".

    If the session is invalid or question generation fails, an error message is returned.
    """
    session_ref = db.collection("sessions").document(selection.session_id)
    session = session_ref.get().to_dict()

    if not session:
        logging.error("Invalid session ID during interest selection")
        return {"error": "Invalid session ID"}

    # Update session with interests
    session_ref.update({"interests": selection.interests})
    next_question = generate_next_question(selection.session_id)

    if not next_question:
        logging.error("No next question generated after interest selection")
        return {"error": "Failed to generate next question", "next_question": None}

    return {"message": "Interests updated successfully.", "next_question": next_question}


def submit_response(user_response: UserResponse):
    """
    Submit a user's answer to a question and update the session state.

    This function stores the user's answer, updates scores based on the current question,
    evaluates freeform answers via GPT-4o if needed, tracks response time, and generates
    the next question.

    Args:
        response (UserResponse): An object containing the session ID, question ID, and
                                    the user's answer.

    Raises:
        HTTPException: If an error occurs during response processing.

    Returns:
        dict: A dictionary with the key "next_question" containing the next question to display,
              or a message indicating test pause if time has expired.
    """
    try:
        logging.info("Submitting response: %s", user_response)
        session_ref = db.collection("sessions").document(
            user_response.session_id)
        session = session_ref.get().to_dict()

        # Ensure required keys exist in the session
        if "responses" not in session:
            session["responses"] = {}
        if "scores" not in session:
            session["scores"] = {
                trait: 0 for trait in knowledge_base["traits"]}
        if "trait_counts" not in session:
            session["trait_counts"] = {t: 0 for t in knowledge_base["traits"]}
        if "response_times" not in session:
            session["response_times"] = {}

        # Store the user response
        session["responses"][user_response.question_id] = user_response.answer

        # Update score and trait count based on the current question stored in the session
        current_question = session.get("current_question")
        trait = current_question.get("trait") if current_question else None

        if current_question:
            selected_key = user_response.answer.strip().lower()

            if current_question["type"] == "multiple-choice":
                option = current_question["options"].get(selected_key)
                if option:
                    session["scores"][trait] += option["score"]

            elif current_question["type"] == "optional-freeform":
                eval_prompt = (
                    f"You are evaluating a freeform personality test answer based on the Big Five trait: '{trait}'.\n\n"
                    f"User's Answer: \"{user_response.answer}\"\n\n"
                    "Briefly analyze this answer, considering tone, sentiment, and keywords to assign a numeric score (0 to 5):\n"
                    " - 0: Not indicative\n - 5: Highly indicative\n\n"
                    "Output STRICTLY in this JSON format (no markdown, no commentary):\n"
                    '{"score": <number>, "reason": "<brief explanation>"}'
                )
                logging.info(f"Evaluating free-form answer for trait: {trait}")
                logging.debug(f"User answer: {user_response.answer}")
                eval_response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": eval_prompt},
                        {"role": "user", "content": "Return ONLY the specified JSON."}
                    ],
                    max_completion_tokens=1000,  # Increased for reasoning models
                    model=AZURE_OPENAI_MODEL_NAME,
                    reasoning_effort="low"  # Use minimal reasoning for simple evaluation
                )
                logging.debug(f"Full eval response: {eval_response}")
                finish_reason = eval_response.choices[0].finish_reason
                logging.debug(f"Finish reason: {finish_reason}")
                eval_content = eval_response.choices[0].message.content

                # Check for refusal
                refusal = getattr(eval_response.choices[0].message, 'refusal', None)
                if refusal:
                    logging.error(f"Model refused to respond: {refusal}")
                    raise ValueError(f"GPT refused to evaluate: {refusal}")

                if not eval_content:
                    # Log everything we can about the response
                    content_filter = getattr(eval_response.choices[0], 'content_filter_results', None)
                    logging.error(f"Empty response! Finish reason: {finish_reason}, Content filter: {content_filter}")
                    logging.error(f"Full message object: {eval_response.choices[0].message}")
                    logging.error(f"User answer was: {user_response.answer}")
                    # Retry once with a simpler prompt
                    logging.info("Retrying with simplified prompt...")
                    retry_response = client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": f"Rate this answer for {trait} trait (0-5): '{user_response.answer}'. Reply with JSON: {{\"score\": N, \"reason\": \"brief\"}}"}
                        ],
                        max_completion_tokens=1000,
                        model=AZURE_OPENAI_MODEL_NAME,
                        reasoning_effort="low"
                    )
                    eval_content = retry_response.choices[0].message.content
                    if not eval_content:
                        raise ValueError(f"GPT returned empty response even on retry. Original filter: {content_filter}")
                cleaned_eval = eval_content.strip().replace("```json", "").replace("```", "").strip()
                eval_json = json.loads(cleaned_eval)
                session["scores"][trait] += eval_json["score"]
                session["optional_responses"][user_response.question_id] = eval_json["reason"]

            # Update trait counts
            session["trait_counts"][trait] += 1

            # Track response time
            current_time = time.time()
            last_time = session.get(
                "last_question_time", session["start_time"])
            response_time = current_time - last_time
            session["last_question_time"] = current_time

            if user_response.question_id:
                session["response_times"][user_response.question_id] = response_time
            else:
                logging.warning(
                    "Received a response with no valid question_id; skipping response time update")

        session_ref.update({
            "scores": session["scores"],
            "responses": session["responses"],
            "trait_counts": session["trait_counts"],
            "response_times": session["response_times"],
            "last_question_time": session["last_question_time"]
        })

        # Timer disabled - let users complete at their own pace
        # if time.time() - session["start_time"] > 180 and not session["paused"]:
        #     session_ref.update({"paused": True})
        #     return {"test_paused": True, "message": "Time is up! Continue or get your results?"}

        result = generate_next_question(user_response.session_id)

        # Check if test is complete (generate_next_question returns finalize_test result)
        if result.get("test_complete"):
            return result

        # Check for errors
        if result.get("error"):
            return result

        # Otherwise it's the next question
        return {"next_question": result}
    except HTTPException as e:
        logging.error("Error in submit_response: %s", e)
        return {"error": "Internal server error while processing your response."}


def generate_next_question(session_id: str) -> dict:
    """
    Generate the next test question using GPT-4o.

    Retrieves the current session data, determines the target trait based on responses so far,
    and sends a prompt to GPT-4o to generate a new question in a strict JSON format.
    Freeform questions occur only 10% of the time, with multiple-choice questions being the default.
    Question count is determined by the session's assessment mode.

    Args:
        session_id (str): The Firestore session ID.

    Returns:
        dict: A dictionary representing the next question if successful; otherwise, a dictionary with an "error" key.
    """
    try:
        session_doc = db.collection("sessions").document(session_id)
        session = session_doc.get().to_dict()
        if not session:
            logging.error("Session not found during question generation")
            return {"error": "Invalid session data"}

        # Get mode-based question count target (default to 10 for backwards compatibility)
        question_count_target = session.get("question_count_target", 10)
        mode = session.get("mode", "standard")
        mode_config = ASSESSMENT_MODES.get(mode, ASSESSMENT_MODES["standard"])

        question_count = len(session.get("responses", {}))
        if question_count >= question_count_target:
            logging.info(
                "Maximum question count reached for mode '%s'. Finalizing test.", mode)
            return finalize_test(session_id)

        trait_counts = session.get("trait_counts", {})

        # Calculate how many questions each trait should get based on mode
        # Quick: 6 questions / 5 traits = ~1.2 questions per trait
        # Standard: 10 questions / 5 traits = 2 questions per trait
        # Deep: 15 questions / 5 traits = 3 questions per trait
        num_traits = len(trait_counts)
        questions_per_trait = max(1, question_count_target // num_traits)

        trait_needs = {trait: questions_per_trait - count for trait,
                       count in trait_counts.items()}
        target_trait = max(trait_needs, key=trait_needs.get)

        # Freeform questions are less common in quick mode, more common in deep mode
        freeform_chance = 0.05 if mode == "quick" else 0.1 if mode == "standard" else 0.2
        question_type = "multiple-choice" if random.random() > freeform_chance else "optional-freeform"

        # Get mode-specific question framing
        question_framing = mode_config.get("question_framing", "general")

        if question_type == "multiple-choice":
            prompt_schema = f"""{{
  "next_question": {{
    "id": "generated_question_{session_id}_{question_count}",
    "trait": "{target_trait}",
    "type": "multiple-choice",
    "text": "<A concise question that does NOT include any option letters or texts>",
    "options": {{
      "a": {{"text": "<Option A text>", "score": <score_value>}},
      "b": {{"text": "<Option B text>", "score": <score_value>}},
      "c": {{"text": "<Option C text>", "score": <score_value>}}
    }},
    "header": "<Based on users previous choice, set a header on top of the next question. Be humorous, concise to keep them engaged. Keep it gender neutral>"
  }}
}}"""
        else:
            prompt_schema = f"""{{
  "next_question": {{
    "id": "optional_freeform_{session_id}_{question_count}",
    "trait": "{target_trait}",
    "type": "optional-freeform",
    "text": "<A clear and simple freeform question that is easy to answer and does NOT include any options and does NOT ask them for any personal information like 'tell me your business idea'>"
    "placeholder": "<A suitable placeholder on how user should answer this question without giving them the answer. Be creative with the response here>"
    "header": "<Based on users previous choice, set a header on top of the next question. For example: if the user responded fast, then you can say 'Wow.. speedy responses'. Keep it gender neutral>"
  }}
}}"""

        user_interests = json.dumps(session["interests"])
        previous_responses = json.dumps(session["responses"])
        previous_response_times = json.dumps(session["response_times"])
        current_trait_scores = json.dumps(session["scores"])
        questions_answered_count = question_count
        trait_counts_str = json.dumps(trait_counts)

        # Mode-specific framing instructions
        framing_instructions = {
            "hackathon": """
- Frame questions around hackathon/sprint scenarios (e.g., "You're in a 24-hour hackathon and...")
- Focus on collaboration under time pressure, handling ambiguity, and rapid decision-making
- Keep scenarios fast-paced and action-oriented""",
            "general": """
- IMPORTANT: Pick ONLY ONE interest from the user's list for each question - rotate through interests
- Create VARIED scenarios: personal projects, side hustles, hobbies, learning new skills, creative endeavors, social situations
- AVOID generic "team project" or "working with others" framings - be more creative and specific
- Examples: "You're learning a new {interest} technique...", "You discover a trending {interest} topic...", "A friend asks for your {interest} advice..."
- Make each question feel fresh and different from the last""",
            "detailed": """
- Ask nuanced questions that explore trait subtleties
- Include scenarios that reveal how traits interact
- Create rich, specific scenarios based on ONE interest at a time
- Allow for more thoughtful, reflective responses"""
        }

        framing_context = framing_instructions.get(
            question_framing, framing_instructions["general"])

        next_question_prompt = f"""
**User Profile:**
- User Interests: {user_interests}
- Previous Responses: {previous_responses}
- Previous Response Times: {previous_response_times}
- Current Trait Scores: {current_trait_scores}
- Target Trait: {target_trait}
- Questions Answered: {questions_answered_count} of {question_count_target}
- Trait Counts: {trait_counts_str}
- Assessment Mode: {mode} ({mode_config['description']})

## MODE-SPECIFIC FRAMING:
{framing_context}

## STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):
{prompt_schema}

Important Constraints:
- NEVER include markdown formatting or commentary in your response.
- NEVER repeat previously asked questions.
- NEVER embed answer options within question texts.
- ALWAYS output strictly valid JSON exactly as defined above.
- ALWAYS personalize the question based on the user interests.
- Follow the mode-specific framing guidelines above.
"""
        logging.info("Sending prompt to GPT for question generation.")
        response_gpt = client.chat.completions.create(
            messages=[
                {"role": "system", "content": next_question_prompt},
                {"role": "user", "content": "Return only the JSON object as specified."}
            ],
            max_completion_tokens=2000,  # Increased for reasoning models
            model=AZURE_OPENAI_MODEL_NAME,
            reasoning_effort="low"  # Use minimal reasoning for question generation
        )

        raw_content = response_gpt.choices[0].message.content
        if not raw_content:
            logging.error("Empty response from GPT for question generation")
            return {"error": "Empty AI response"}
        raw_content = raw_content.strip()
        logging.debug("Raw GPT Response: %s", raw_content)

        cleaned_json = raw_content.replace(
            "```json", "").replace("```", "").strip()

        try:
            response_content = json.loads(cleaned_json)
            next_question = response_content.get("next_question", {})
            if not next_question:
                logging.error("GPT response JSON missing 'next_question' key")
                return {"error": "Invalid AI response format"}
            session_doc.update({"current_question": next_question})
            return next_question
        except json.JSONDecodeError as json_err:
            logging.error(
                "JSON parsing error: %s. Response content: %s", json_err, cleaned_json)
            return {"error": "Failed to parse AI response JSON"}
    except HTTPException as e:
        logging.error(
            "Azure OpenAI API error in generate_next_question: %s", e)
        return {"error": "AI generation failed. Please try again."}


def finalize_test(session_id: str) -> dict:
    """
    Finalize the personality test by generating a personalized archetype summary using GPT-4o.

    Retrieves the session data, determines the best matching archetype using cosine similarity,
    and sends a prompt to GPT-4o to generate a detailed, personalized profile in JSON format.
    If GPT-4o returns malformed JSON, a fallback profile is provided.

    Args:
        session_id (str): The Firestore session ID.

    Returns:
        dict: A dictionary containing:
            - test_complete (bool): True if the test is finalized.
            - final_scores (dict): The user's raw trait scores.
            - normalized_scores (dict): Scores normalized to 0-100 scale.
            - suggested_archetype (str): The determined personality archetype.
            - archetype_confidence (float): Confidence score for the match (0-100).
            - trait_breakdown (dict): Detailed analysis per trait.
            - all_matches (dict): Similarity scores for all archetypes.
            - archetype_description (dict): A detailed profile in JSON format.
            - compatibility (dict): Team compatibility information.
        In case of errors, returns a dictionary with an "error" key.
    """
    try:
        session = db.collection("sessions").document(
            session_id).get().to_dict()
        if not session:
            logging.error("Session not found during test finalization")
            return {"error": "Invalid session ID"}

        scores = session.get("scores", {})
        trait_counts = session.get("trait_counts", {})

        # Use the new cosine similarity-based archetype determination
        archetype_result = determine_archetype(scores, trait_counts)
        archetype = archetype_result["archetype"]
        normalized_scores = archetype_result["normalized_scores"]
        confidence = archetype_result["confidence"]
        trait_breakdown = archetype_result["trait_breakdown"]
        all_matches = archetype_result["all_matches"]
        compatibility = archetype_result["compatibility"]

        output_schema = """{
  "overview": "<Overview summary>",
  "team_work_style": "<Team work style description>",
  "ideal_team_situation": "<Ideal team situation description>",
  "compatible_archetypes": {"<Compatible Archetype 1>": "<Why?>", "<Compatible Archetype 2>": "<Why?>"}
}"""

        # Enhanced prompt with normalized scores and trait breakdown
        prompt = f"""
You are a creative and witty personality archetype expert.
The user has been assessed as a "{archetype}" with {confidence:.0f}% confidence.

Their Big Five trait profile (normalized 0-100 scale):
{json.dumps(normalized_scores, indent=2)}

Trait breakdown:
{json.dumps(trait_breakdown, indent=2)}

Archetype description: {knowledge_base['archetypes'][archetype]['description']}

Best team partners: {', '.join(compatibility.get('best_partners', []))}

Generate an engaging, personalized profile with four sections:
1. Overview (a fun, detailed summary with emojis that reflects their specific trait scores)
2. Team Work Style (how they function in a team based on their unique trait combination)
3. Ideal Team Situation (the hackathon or project environment where they excel)
4. Compatible Archetypes (use the compatibility data to explain WHY these archetypes work well together)

STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):
{output_schema}

Important Constraints:
- Reference their specific trait levels (e.g., "Your high Openness combined with moderate Extraversion...")
- Make it personal and specific to their scores, not generic
- NEVER include markdown formatting or commentary in your response
- ALWAYS output strictly valid JSON exactly as defined above
Return only the JSON object as specified.
"""
        logging.info("Sending prompt to GPT-4o for finalizing test results.")
        final_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Return only the JSON object as specified."}
            ],
            max_completion_tokens=4000,  # Increased for reasoning models - finalization needs more output
            top_p=1.0,
            model=AZURE_OPENAI_MODEL_NAME,
            reasoning_effort="medium"  # Medium reasoning for detailed personality analysis
        )

        raw_content = final_response.choices[0].message.content
        if not raw_content:
            logging.error("Empty response from GPT for finalization")
            raise ValueError("Empty finalization response")
        raw_content = raw_content.strip()
        logging.debug("Raw GPT finalization response: %s", raw_content)

        try:
            cleaned_json = raw_content.replace(
                "```json", "").replace("```", "").strip()
            logging.debug("Cleaned JSON: %s", cleaned_json)
            response_json = json.loads(cleaned_json)
            required_keys = ["overview", "team_work_style",
                             "ideal_team_situation", "compatible_archetypes"]
            if not all(key in response_json for key in required_keys):
                raise ValueError("Incomplete AI response format")

            return {
                "test_complete": True,
                "final_scores": scores,
                "normalized_scores": normalized_scores,
                "suggested_archetype": archetype,
                "archetype_confidence": confidence,
                "trait_breakdown": trait_breakdown,
                "all_matches": all_matches,
                "archetype_description": response_json,
                "compatibility": compatibility
            }
        except (json.JSONDecodeError, ValueError) as json_err:
            logging.error(
                "Error in finalizing test: %s. Falling back to default profile.", json_err)

            # Generate fallback compatible archetypes from compatibility data
            compatible_dict = {}
            for partner in compatibility.get("best_partners", [])[:2]:
                reason = compatibility.get("complementary_reason", {}).get(
                    partner, "Great synergy")
                compatible_dict[partner] = reason

            fallback_profile = {
                "overview": knowledge_base["archetypes"][archetype]["description"],
                "team_work_style": "You bring a unique combination of traits to any team. Your personality profile suggests you can adapt to various team dynamics while maintaining your core strengths.",
                "ideal_team_situation": "Your talents shine brightest in projects that leverage your specific trait combination, whether that's creative brainstorming, steady execution, or team coordination.",
                "compatible_archetypes": compatible_dict if compatible_dict else {
                    "Operator": "Brings structure and reliability",
                    "Catalyst": "Energizes team collaboration"
                }
            }
            return {
                "test_complete": True,
                "final_scores": scores,
                "normalized_scores": normalized_scores,
                "suggested_archetype": archetype,
                "archetype_confidence": confidence,
                "trait_breakdown": trait_breakdown,
                "all_matches": all_matches,
                "archetype_description": fallback_profile,
                "compatibility": compatibility
            }
    except HTTPException as e:
        logging.error("Error finalizing test: %s", e)
        return {"error": "Test finalization failed. Please try again."}


def continue_test(session_id: str) -> dict:
    """
    Resume a paused personality test session.

    Checks that the session exists and is paused, updates the start time,
    and generates the next question to resume the test.

    Args:
        session_id (str): The Firestore session ID.

    Raises:
        HTTPException: If the session is invalid or if the test is not currently paused.

    Returns:
        dict: A dictionary containing the next question under the key "next_question".
    """
    session_ref = db.collection("sessions").document(session_id)
    session = session_ref.get().to_dict()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    if not session["paused"]:
        raise HTTPException(status_code=400, detail="Test is not paused")
    session_ref.update({"paused": False, "start_time": time.time()})
    next_question = generate_next_question(session_id)
    if not next_question:
        return finalize_test(session_id)
    return {"next_question": next_question}


def get_results(session_id: str) -> dict:
    """
    Retrieve the final test results by finalizing the personality test session.

    Args:
        session_id (str): The Firestore session ID.

    Returns:
        dict: The result of finalize_test(), which includes final scores, the suggested archetype,
              and a detailed archetype description.
    """
    results = finalize_test(session_id)
    session_ref = db.collection("sessions").document(
        session_id)
    session_ref.update({"archetype": results["suggested_archetype"]})

    return results


def store_feedback(session_id: str, rating: int, timestamp: float, archetype: str) -> None:
    """
    Save the provided star rating to Firestore with a timestamp.

    Args:
        rating (int): The rating value (e.g., number of stars between 1 and 5).

    Raises:
        Exception: If an error occurs during the Firestore write operation.
    """

    feedback_data = {
        "session_id": session_id,
        "rating": rating + 1,
        "timestamp": timestamp,
        "archetype": archetype
    }
    db.collection("feedback").add(feedback_data)
