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
import httpx
from dotenv import load_dotenv

# Configure logging to show debug messages
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
from openai import AzureOpenAI
from fastapi import HTTPException
from firebase import db
from models import UserResponse, InterestSelection

# Import new modular configurations
from archetypes import ARCHETYPES, ARCHETYPE_COMPATIBILITY, get_archetype_for_display
from modes import ASSESSMENT_MODES, get_mode_config, get_mode_prompt_context, should_skip_interests, get_interest_requirements
from interests import get_interest_categories, get_life_areas, build_interest_prompt, validate_interests
from prompts import render_system_prompt, infer_tendencies, LIFE_CONTEXT_CATEGORIES, get_life_context_details
from prefetch import init_prefetcher, get_prefetcher

# Load environment variables from .env file
load_dotenv()

# Load Azure OpenAI credentials from environment variables
AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT", "https://ception-ai-service688670829041.cognitiveservices.azure.com")
AZURE_OPENAI_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY", "be2c4fac7e744fb3b2083d0c971e54f8")
AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-5.2-chat")

# Initialize httpx client with connection pooling for better performance
http_client = httpx.Client(
    limits=httpx.Limits(
        max_connections=100,           # Maximum total connections
        max_keepalive_connections=20,  # Keep-alive connections for reuse
        keepalive_expiry=30            # Keep connections alive for 30 seconds
    ),
    timeout=httpx.Timeout(60.0, connect=10.0)  # 60s total, 10s connect timeout
)

# Initialize Azure OpenAI Client with connection pooling
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    http_client=http_client,
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
# PRE-FETCHING HELPER FUNCTIONS
# ============================================================================

async def generate_prefetch_question(
    session_id: str,
    simulated_answer: str,
    simulate_fn=None
) -> dict:
    """
    Async wrapper for question generation used by prefetcher.

    This simulates what would happen if the user selected a specific answer,
    then generates the next question based on that simulated state.

    Args:
        session_id: The session ID
        simulated_answer: The answer key to simulate (e.g., "a", "b", "c")
        simulate_fn: Optional function to update session state (not used in simple mode)

    Returns:
        The generated next question dict
    """
    import asyncio

    # Run the sync generation in a thread pool to not block
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        _generate_with_simulated_answer,
        session_id,
        simulated_answer
    )
    return result


def _generate_with_simulated_answer(session_id: str, simulated_answer: str) -> dict:
    """
    Generate a question as if the user had selected a specific answer.

    This is a lightweight version that doesn't persist the simulated answer,
    just uses it to generate an appropriate next question.
    """
    try:
        session_doc = db.collection("sessions").document(session_id)
        session = session_doc.get().to_dict()
        if not session:
            return {"error": "Invalid session data"}

        current_question = session.get("current_question")
        if not current_question:
            return {"error": "No current question"}

        # Simulate the score update for prediction purposes
        trait = current_question.get("trait")
        simulated_scores = session.get("scores", {}).copy()
        simulated_trait_counts = session.get("trait_counts", {}).copy()

        if current_question["type"] == "multiple-choice":
            option = current_question["options"].get(simulated_answer.lower())
            if option and trait:
                simulated_scores[trait] = simulated_scores.get(trait, 0) + option.get("score", 0)
                simulated_trait_counts[trait] = simulated_trait_counts.get(trait, 0) + 1

        # Generate with simulated context (don't persist these changes)
        mode = session.get("mode", "overall")
        mode_config = get_mode_config(mode)
        question_count = len(session.get("responses", {})) + 1  # +1 for simulated answer
        question_count_target = session.get("question_count_target", 10)

        if question_count >= question_count_target:
            # Would be the last question - don't prefetch finalization
            return {"prefetch_skip": True, "reason": "test_would_complete"}

        # Calculate target trait based on simulated state
        num_traits = len(simulated_trait_counts)
        questions_per_trait = max(1, question_count_target // num_traits)
        trait_needs = {t: questions_per_trait - c for t, c in simulated_trait_counts.items()}
        target_trait = max(trait_needs, key=trait_needs.get)

        # Use same logic as generate_next_question but with simulated state
        freeform_chance = mode_config.get("freeform_probability", 0.15)
        import random
        question_type = "multiple-choice" if random.random() > freeform_chance else "optional-freeform"

        user_interests = session.get("interests", [])
        current_context = None
        context_hooks = []

        if mode in ["deep_dive", "interest"] and user_interests:
            current_context = user_interests[question_count % len(user_interests)]
            context_data = get_life_context_details(current_context)
            context_hooks = context_data.get("scenario_contexts", [])

        # Build simulated answer history
        answer_history = session.get("answer_history", []).copy()
        answer_history.append({
            "question_id": current_question.get("id", ""),
            "question_summary": current_question.get("text", "")[:50] + "...",
            "selected_option": simulated_answer,
            "trait_signals": [trait] if trait else [],
            "response_time": None
        })

        tendencies = infer_tendencies(answer_history)
        trait_scores_detailed = session.get("trait_scores_detailed", {}).copy()
        if trait and trait in trait_scores_detailed:
            if current_question["type"] == "multiple-choice":
                option = current_question["options"].get(simulated_answer.lower())
                if option:
                    trait_scores_detailed[trait]["total"] += option.get("score", 0)
                    trait_scores_detailed[trait]["count"] += 1

        traits_assessed = [t for t, c in simulated_trait_counts.items() if c > 0]

        # Render prompt with simulated state
        next_question_prompt = render_system_prompt(
            mode=mode if mode != "interest" else "deep_dive",
            question_number=question_count + 1,
            total_questions=question_count_target,
            session_id=session_id,
            target_trait=target_trait,
            question_type=question_type,
            previous_answers=answer_history,
            trait_scores=trait_scores_detailed,
            life_contexts=user_interests if mode in ["interest", "deep_dive"] else None,
            current_context=current_context,
            context_scenario_hooks=context_hooks,
            traits_assessed=traits_assessed,
            inferred_tendencies=tendencies
        )

        # Generate question (this is the expensive LLM call)
        response_gpt = client.chat.completions.create(
            messages=[
                {"role": "system", "content": next_question_prompt},
                {"role": "user", "content": "Return only the JSON object as specified."}
            ],
            max_completion_tokens=2000,
            model=AZURE_OPENAI_MODEL_NAME,
            reasoning_effort="low"
        )

        raw_content = response_gpt.choices[0].message.content
        if not raw_content:
            return {"error": "Empty AI response"}

        cleaned_json = raw_content.strip().replace("```json", "").replace("```", "").strip()

        try:
            response_content = json.loads(cleaned_json)
            next_question = response_content.get("next_question", {})
            if not next_question:
                return {"error": "Invalid AI response format"}

            # Mark as prefetched
            next_question["_prefetched"] = True
            next_question["_prefetched_for_answer"] = simulated_answer

            return next_question
        except json.JSONDecodeError:
            return {"error": "Failed to parse AI response JSON"}

    except Exception as e:
        logging.error(f"Prefetch generation error: {e}")
        return {"error": str(e)}


# Initialize the prefetcher (lazy initialization)
def _init_prefetcher_if_needed():
    """Initialize prefetcher on first use."""
    if get_prefetcher() is None:
        init_prefetcher(generate_prefetch_question)


# ============================================================================
# ARCHETYPE PROFILES AND MATCHING SYSTEM
# ============================================================================

# Build ARCHETYPE_PROFILES from the new archetypes module
ARCHETYPE_PROFILES = {
    name: data["big_five_profile"]
    for name, data in ARCHETYPES.items()
}

# Note: ARCHETYPE_COMPATIBILITY is imported from archetypes.py
# Note: ASSESSMENT_MODES is imported from modes.py


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

def start_test(mode: str = "overall") -> dict:
    """
    Start a new personality test session.

    This function generates a new session ID, initializes session data in Firestore,
    and handles mode-specific routing (some modes skip interest selection).

    Args:
        mode: Assessment mode - 'hackathon', 'overall', or 'interest'.
              Defaults to 'overall'.

    Returns:
        dict: A dictionary containing:
            - session_id: The unique session identifier
            - mode: The selected assessment mode
            - mode_config: Configuration for the mode (display name, question count, etc.)
            - ui_flow: Instructions for frontend on what to display next
            - next_question: (Optional) First question if skipping interest selection
            - interest_config: (Optional) Interest selection requirements if needed
    """
    # Validate and get mode configuration
    if mode not in ASSESSMENT_MODES:
        mode = "overall"
    mode_config = get_mode_config(mode)

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
        "scenario_type": mode_config.get("scenario_type", "varied"),
        # New: Answer history for LLM context and pre-fetching
        "answer_history": [],
        # New: Structured trait scores for template
        "trait_scores_detailed": {trait: {"total": 0, "count": 0} for trait in knowledge_base["traits"]},
        # New: Predicted answers from LLM for pre-fetching
        "predicted_next_answer": None,
    }
    db.collection("sessions").document(session_id).set(session_data)

    # Determine UI flow based on mode
    interest_requirements = get_interest_requirements(mode)

    # Build response
    response = {
        "session_id": session_id,
        "mode": mode,
        "mode_config": {
            "display_name": mode_config["display_name"],
            "description": mode_config["description"],
            "duration_label": mode_config["duration_label"],
            "question_count": mode_config["question_count"]
        }
    }

    if should_skip_interests(mode):
        # Hackathon mode - skip interests, go directly to questions
        response["ui_flow"] = {
            "show_interest_selection": False,
            "proceed_directly_to_questions": True
        }
        response["next_question"] = generate_next_question(session_id)
    elif mode_config.get("allow_optional_interests"):
        # Overall mode - optional life context selection (same as deep_dive)
        from prompts import get_all_life_contexts
        response["ui_flow"] = {
            "show_interest_selection": True,
            "interests_optional": True,
            "skip_label": "Skip - assess me across all areas"
        }
        response["interest_config"] = {
            "categories": get_all_life_contexts(),  # Same life contexts as deep_dive
            "optional": True,
            "min": 2,
            "max": 4
        }
    else:
        # Deep dive mode - required life context selection
        from prompts import get_all_life_contexts
        response["ui_flow"] = {
            "show_interest_selection": True,
            "interests_optional": False
        }
        response["interest_config"] = {
            "categories": get_all_life_contexts(),  # Same life contexts as overall mode
            "min": mode_config.get("min_interests", 2),
            "max": mode_config.get("max_interests", 4),
            "allow_custom": True
        }

    return response


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

            # Update detailed trait scores for template
            if "trait_scores_detailed" not in session:
                session["trait_scores_detailed"] = {t: {"total": 0, "count": 0} for t in knowledge_base["traits"]}

            score_added = 0
            if current_question["type"] == "multiple-choice":
                option = current_question["options"].get(selected_key)
                if option:
                    score_added = option.get("score", 0)
            session["trait_scores_detailed"][trait]["total"] += score_added
            session["trait_scores_detailed"][trait]["count"] += 1

            # Add to answer history for LLM context
            if "answer_history" not in session:
                session["answer_history"] = []

            session["answer_history"].append({
                "question_id": user_response.question_id,
                "question_summary": current_question.get("text", "")[:50] + "...",
                "selected_option": selected_key,
                "trait_signals": [trait] if trait else [],
                "response_time": None  # Will be set below
            })

            # Track response time
            current_time = time.time()
            last_time = session.get(
                "last_question_time", session["start_time"])
            response_time = current_time - last_time
            session["last_question_time"] = current_time

            if user_response.question_id:
                session["response_times"][user_response.question_id] = response_time
                # Update response time in the last answer history entry
                if session.get("answer_history"):
                    session["answer_history"][-1]["response_time"] = response_time
            else:
                logging.warning(
                    "Received a response with no valid question_id; skipping response time update")

        session_ref.update({
            "scores": session["scores"],
            "responses": session["responses"],
            "trait_counts": session["trait_counts"],
            "response_times": session["response_times"],
            "last_question_time": session["last_question_time"],
            "answer_history": session.get("answer_history", []),
            "trait_scores_detailed": session.get("trait_scores_detailed", {})
        })

        # Timer disabled - let users complete at their own pace
        # if time.time() - session["start_time"] > 180 and not session["paused"]:
        #     session_ref.update({"paused": True})
        #     return {"test_paused": True, "message": "Time is up! Continue or get your results?"}

        # Check prefetch cache first for faster response
        prefetcher = get_prefetcher()
        cached_question = None
        if prefetcher and current_question:
            question_id = current_question.get("id", "")
            cached_question = prefetcher.get_cached_question_sync(
                session_id=user_response.session_id,
                current_question_id=question_id,
                answer_key=selected_key
            )

        if cached_question:
            logging.info("[PREFETCH] Using cached question - skipping LLM call!")
            # Store the cached question as current
            session_ref.update({"current_question": cached_question})
            result = cached_question
        else:
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
        mode = session.get("mode", "overall")
        mode_config = get_mode_config(mode)

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

        # Freeform probability varies by mode
        freeform_chance = mode_config.get("freeform_probability", 0.15)
        question_type = "multiple-choice" if random.random() > freeform_chance else "optional-freeform"

        # Get user interests/life contexts
        user_interests = session.get("interests", [])

        # Determine current context for deep_dive mode (renamed from 'interest' mode)
        current_context = None
        context_hooks = []
        if mode == "deep_dive" and user_interests:
            current_context = user_interests[question_count % len(user_interests)]
            context_data = get_life_context_details(current_context)
            context_hooks = context_data.get("scenario_contexts", [])
        elif mode == "interest" and user_interests:
            # Legacy support for 'interest' mode -> treat as deep_dive
            current_context = user_interests[question_count % len(user_interests)]
            interest_data = build_interest_prompt(current_context)
            # Extract hooks from interest data if available
            from interests import get_interest_context
            int_context = get_interest_context(current_context)
            context_hooks = int_context.get("scenario_contexts", [])

        # Get answer history and infer tendencies
        answer_history = session.get("answer_history", [])
        tendencies = infer_tendencies(answer_history)

        # Get detailed trait scores for template
        trait_scores_detailed = session.get("trait_scores_detailed", {})

        # Get list of traits already assessed
        traits_assessed = [t for t, c in trait_counts.items() if c > 0]

        # Render the system prompt using Jinja2 template
        next_question_prompt = render_system_prompt(
            mode=mode if mode != "interest" else "deep_dive",  # Normalize mode name
            question_number=question_count + 1,
            total_questions=question_count_target,
            session_id=session_id,
            target_trait=target_trait,
            question_type=question_type,
            previous_answers=answer_history,
            trait_scores=trait_scores_detailed,
            life_contexts=user_interests if mode in ["interest", "deep_dive"] else None,
            current_context=current_context,
            context_scenario_hooks=context_hooks,
            traits_assessed=traits_assessed,
            inferred_tendencies=tendencies
        )
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

            # Extract predicted_next_answer for pre-fetching (Phase 4)
            predicted_next = response_content.get("predicted_next_answer", {})
            if predicted_next:
                logging.debug("Predicted next answer: %s", predicted_next)

            # Store both the question and prediction
            session_doc.update({
                "current_question": next_question,
                "predicted_next_answer": predicted_next
            })

            # Include prediction in response for pre-fetching system
            next_question["_predicted_next"] = predicted_next

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
    Returns rich archetype data including mode-specific insights.

    Args:
        session_id (str): The Firestore session ID.

    Returns:
        dict: A dictionary containing:
            - test_complete (bool): True if the test is finalized.
            - final_scores (dict): The user's raw trait scores.
            - normalized_scores (dict): Scores normalized to 0-100 scale.
            - archetype (dict): Rich archetype data (name, tagline, emoji, description, etc.)
            - archetype_confidence (float): Confidence score for the match (0-100).
            - trait_breakdown (dict): Detailed analysis per trait.
            - all_matches (dict): Similarity scores for all archetypes.
            - personalized_profile (dict): AI-generated personalized insights.
            - mode (str): The assessment mode used.
            - mode_specific (dict): Mode-specific insights (e.g., hackathon superpower).
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
        mode = session.get("mode", "overall")
        interests = session.get("interests", [])

        # Use the cosine similarity-based archetype determination
        archetype_result = determine_archetype(scores, trait_counts)
        archetype_name = archetype_result["archetype"]
        normalized_scores = archetype_result["normalized_scores"]
        confidence = archetype_result["confidence"]
        trait_breakdown = archetype_result["trait_breakdown"]
        all_matches = archetype_result["all_matches"]
        compatibility = archetype_result["compatibility"]

        # Get rich archetype data from archetypes.py
        archetype_data = get_archetype_for_display(archetype_name)
        raw_archetype = ARCHETYPES.get(archetype_name, {})

        # Build mode-specific output schema
        if mode == "hackathon":
            output_schema = """{
  "overview": "<2-3 sentence summary with hackathon context>",
  "hackathon_style": "<How they perform in intense 24-hour sprints>",
  "team_role": "<Their natural role in a hackathon team>",
  "watch_out_for": "<One honest growth area specific to hackathons>"
}"""
        else:
            output_schema = """{
  "overview": "<2-3 sentence engaging summary>",
  "strengths_in_action": "<How their traits manifest in real situations>",
  "growth_edge": "<One honest growth opportunity>",
  "ideal_environment": "<Where they thrive most>"
}"""

        # Build prompt with rich archetype data
        prompt = f"""
You are a personality insight expert. Generate a personalized profile.

ARCHETYPE: {archetype_name}
TAGLINE: {archetype_data.get('tagline', '')}
ZONE OF GENIUS: {archetype_data.get('zone_of_genius', '')}
DEEPEST ASPIRATION: {archetype_data.get('deepest_aspiration', '')}
GROWTH OPPORTUNITY: {archetype_data.get('growth_opportunity', '')}

USER'S BIG FIVE PROFILE (0-100 scale):
{json.dumps(normalized_scores, indent=2)}

TRAIT ANALYSIS:
{json.dumps(trait_breakdown, indent=2)}

ASSESSMENT MODE: {mode}
USER INTERESTS: {json.dumps(interests) if interests else "General assessment"}

IDEAL CREATIVE PARTNERS: {', '.join(archetype_data.get('ideal_partners', []))}

Generate a personalized profile that:
1. References their SPECIFIC trait levels (e.g., "Your high Openness at {normalized_scores.get('Openness', 50):.0f}%...")
2. Feels like it was written specifically for them, not copy-pasted
3. Uses the archetype's themes but personalizes based on their exact scores
4. Is encouraging but honest about growth areas

STRICT JSON RESPONSE FORMAT:
{output_schema}

Return ONLY the JSON object, no markdown or commentary.
"""
        logging.info("Sending prompt for finalizing test results.")
        final_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Return only the JSON object as specified."}
            ],
            max_completion_tokens=4000,
            top_p=1.0,
            model=AZURE_OPENAI_MODEL_NAME,
            reasoning_effort="medium"
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
            personalized_profile = json.loads(cleaned_json)
        except (json.JSONDecodeError, ValueError) as json_err:
            logging.error(
                "Error parsing GPT response: %s. Using fallback.", json_err)
            # Fallback profile using archetype data
            if mode == "hackathon":
                personalized_profile = {
                    "overview": archetype_data.get("description", "")[:200],
                    "hackathon_style": raw_archetype.get("hackathon_superpower", "Bringing unique value to the team"),
                    "team_role": archetype_data.get("team_value", "Contributing your unique strengths"),
                    "watch_out_for": raw_archetype.get("hackathon_pitfall", "Staying balanced under pressure")
                }
            else:
                personalized_profile = {
                    "overview": archetype_data.get("description", ""),
                    "strengths_in_action": archetype_data.get("zone_of_genius", ""),
                    "growth_edge": archetype_data.get("growth_opportunity", ""),
                    "ideal_environment": archetype_data.get("team_value", "")
                }

        # Build mode-specific insights
        mode_specific = {}
        if mode == "hackathon":
            mode_specific = {
                "hackathon_superpower": raw_archetype.get("hackathon_superpower", ""),
                "hackathon_pitfall": raw_archetype.get("hackathon_pitfall", ""),
                "team_value": archetype_data.get("team_value", "")
            }
        elif mode == "interest" and interests:
            mode_specific = {
                "interests_assessed": interests,
                "domain_insight": f"Your {archetype_name} traits shine through in {', '.join(interests[:2])}"
            }

        return {
            "test_complete": True,
            "mode": mode,
            "final_scores": scores,
            "normalized_scores": normalized_scores,
            "archetype": {
                "name": archetype_name,
                "tagline": archetype_data.get("tagline", ""),
                "emoji": archetype_data.get("emoji", ""),
                "color": archetype_data.get("color", "#6B7280"),
                "description": archetype_data.get("description", ""),
                "zone_of_genius": archetype_data.get("zone_of_genius", ""),
                "deepest_aspiration": archetype_data.get("deepest_aspiration", ""),
                "growth_opportunity": archetype_data.get("growth_opportunity", ""),
                "creative_partner": archetype_data.get("creative_partner", ""),
                "team_value": archetype_data.get("team_value", ""),
                "ideal_partners": archetype_data.get("ideal_partners", []),
                "growth_partners": archetype_data.get("growth_partners", [])
            },
            "archetype_confidence": confidence,
            "trait_breakdown": trait_breakdown,
            "all_matches": all_matches,
            "personalized_profile": personalized_profile,
            "mode_specific": mode_specific,
            # Legacy fields for backwards compatibility
            "suggested_archetype": archetype_name,
            "archetype_description": personalized_profile,
            "compatibility": compatibility
        }
    except Exception as e:
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
