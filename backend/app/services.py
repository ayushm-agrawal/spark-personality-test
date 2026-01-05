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
import hashlib
import httpx
from typing import Optional
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

        # Get single interest for deep dive mode
        single_interest = session.get("interest")

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
            life_contexts=user_interests if mode in ["interest", "deep_dive"] and not single_interest else None,
            current_context=current_context,
            context_scenario_hooks=context_hooks,
            traits_assessed=traits_assessed,
            inferred_tendencies=tendencies,
            single_interest=single_interest
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
        Dictionary containing:
        - Normalized scores (0-100) per trait
        - 'low_confidence' flag if variance is too low
        - 'variance' score
    """
    normalized = {}
    for trait, raw_score in raw_scores.items():
        question_count = trait_counts.get(trait, 0)

        if question_count == 0:
            # No questions asked for this trait - use neutral 50
            normalized[trait] = 50
            logging.warning(f"No questions asked for trait {trait}, defaulting to 50")
            continue

        max_possible = question_count * 2  # Max 2 points per question

        # Handle edge case where raw_score exceeds max (shouldn't happen but be defensive)
        if raw_score > max_possible:
            logging.warning(f"Raw score {raw_score} exceeds max {max_possible} for {trait}, capping")
            raw_score = max_possible

        # Normalize to 0-100 scale, capped at 100
        normalized[trait] = min(100, max(0, (raw_score / max_possible) * 100))

    return normalized


def validate_llm_question(question: dict, target_trait: str, focused_traits: list) -> dict:
    """
    Validate that an LLM-generated question meets our requirements.

    Args:
        question: The generated question dict
        target_trait: The trait we asked for
        focused_traits: List of valid traits for this assessment

    Returns:
        Dict with 'valid' boolean and 'issues' list
    """
    issues = []

    # Check trait matches what we asked for
    question_trait = question.get("trait", "")
    if question_trait != target_trait:
        issues.append(f"Wrong trait: asked for {target_trait}, got {question_trait}")

    # Check trait is in focused list
    if focused_traits and question_trait not in focused_traits:
        issues.append(f"Trait {question_trait} not in focused traits: {focused_traits}")

    # Check options have proper score distribution for multiple-choice
    if question.get("type") == "multiple-choice":
        options = question.get("options", {})
        if options:
            scores = [opt.get("score", -1) for opt in options.values()]

            # Check we have exactly scores 0, 1, 2
            expected_scores = {0, 1, 2}
            actual_scores = set(scores)

            if actual_scores != expected_scores:
                issues.append(f"Invalid score distribution: {scores}. Expected [0, 1, 2]")

            # Check all scores are valid (0, 1, or 2)
            for score in scores:
                if score not in [0, 1, 2]:
                    issues.append(f"Invalid score value: {score}")

    # Check required fields
    required_fields = ["id", "trait", "type", "text"]
    for field in required_fields:
        if not question.get(field):
            issues.append(f"Missing required field: {field}")

    return {
        "valid": len(issues) == 0,
        "issues": issues
    }


def fix_question_scores(question: dict) -> dict:
    """
    Attempt to fix invalid score distributions in a question.

    If scores are like [2, 2, 1] or [1, 1, 0], remap them to [2, 1, 0].
    """
    if question.get("type") != "multiple-choice":
        return question

    options = question.get("options", {})
    if not options:
        return question

    # Get current scores
    option_keys = list(options.keys())
    scores = [options[k].get("score", 0) for k in option_keys]

    # If scores are already valid, return as-is
    if set(scores) == {0, 1, 2}:
        return question

    # Sort options by score descending and reassign [2, 1, 0]
    sorted_keys = sorted(option_keys, key=lambda k: options[k].get("score", 0), reverse=True)

    fixed_scores = [2, 1, 0]
    for i, key in enumerate(sorted_keys):
        if i < len(fixed_scores):
            options[key]["score"] = fixed_scores[i]

    question["options"] = options
    logging.info(f"Fixed question scores: original {scores} → [2, 1, 0]")

    return question


def check_score_confidence(normalized_scores: dict) -> dict:
    """
    Check confidence level of normalized scores and return detailed tier information.

    Three tiers based on score differentiation:
    - "clear": Strong differentiation, high confidence (70-95%)
    - "emerging": Moderate differentiation, medium confidence (40-70%)
    - "unclear": Low differentiation, low confidence (20-40%)

    Args:
        normalized_scores: Dictionary of normalized scores (0-100)

    Returns:
        Dictionary with:
        - tier: "clear", "emerging", or "unclear"
        - confidence_pct: Percentage confidence value
        - explanation: User-facing explanation (for emerging/unclear)
        - ambiguous_traits: List of traits in the 40-60% zone
        - score_range: Max - min of scores
        - std_dev: Standard deviation
    """
    if not normalized_scores:
        return {
            "tier": "unclear",
            "confidence_pct": 20,
            "explanation": "No scores available to analyze.",
            "ambiguous_traits": [],
            "score_range": 0,
            "std_dev": 0
        }

    scores = list(normalized_scores.values())
    mean_score = sum(scores) / len(scores)
    variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
    std_dev = math.sqrt(variance)
    score_range = max(scores) - min(scores)

    # Find ambiguous traits (those scoring between 40-60%)
    ambiguous_traits = [
        trait for trait, score in normalized_scores.items()
        if 40 <= score <= 60
    ]

    # Determine tier based on score differentiation
    if score_range >= 50 and std_dev >= 20:
        # Clear differentiation - high confidence
        tier = "clear"
        # Map to 70-95% range based on how strong the differentiation is
        confidence_pct = min(95, 70 + (score_range - 50) * 0.5 + (std_dev - 20) * 0.5)
        explanation = None
    elif score_range >= 25 or std_dev >= 12:
        # Moderate differentiation - emerging profile
        tier = "emerging"
        # Map to 40-70% range
        confidence_pct = min(70, max(40, 40 + (score_range - 25) * 0.6 + (std_dev - 12) * 1.0))
        explanation = "We see a pattern forming but need more signal to be certain. Your results may refine as you take more tests."
    else:
        # Low differentiation - unclear
        tier = "unclear"
        # Map to 20-40% range
        confidence_pct = max(20, min(40, 20 + score_range * 0.8))
        explanation = "Your responses were fairly balanced across traits. This could mean you're adaptable, or we need more questions to find your pattern."

    return {
        "tier": tier,
        "confidence_pct": round(confidence_pct, 1),
        "explanation": explanation,
        "ambiguous_traits": ambiguous_traits,
        "score_range": round(score_range, 2),
        "std_dev": round(std_dev, 2),
        # Legacy fields for backwards compatibility
        "low_confidence": tier != "clear",
        "variance": round(variance, 2),
        "reason": explanation
    }


def get_extension_opportunity(session_id: str) -> dict:
    """
    Wrapper to get extension opportunity by session ID.
    """
    session_doc = db.collection("sessions").document(session_id)
    session = session_doc.get().to_dict()
    if not session:
        return {"offer_extension": False, "error": "Invalid session"}
    return check_extension_opportunity(session)


def accept_extension(session_id: str) -> dict:
    """
    Accept the test extension and add 2 more clarifying questions.

    This function:
    1. Gets the extension opportunity info
    2. Updates the session to increase question count by 2
    3. Stores the focus traits for targeted question generation
    4. Returns the first extended question

    Args:
        session_id: The session ID

    Returns:
        Dictionary with next_question or error
    """
    session_doc = db.collection("sessions").document(session_id)
    session = session_doc.get().to_dict()

    if not session:
        return {"error": "Invalid session"}

    extension = check_extension_opportunity(session)

    if not extension.get("offer_extension"):
        return {"error": "Extension not available", "reason": extension.get("reason")}

    # Update session for extension
    new_question_count = session.get("question_count_target", 10) + 2
    focus_traits = extension.get("focus_traits", [])

    session_doc.update({
        "question_count_target": new_question_count,
        "extension_accepted": True,
        "extension_focus_traits": focus_traits
    })

    # Generate the next question (will be a clarifying question)
    next_question = generate_next_question(session_id)

    return {
        "extension_accepted": True,
        "new_question_count": new_question_count,
        "focus_traits": focus_traits,
        "next_question": next_question
    }


def check_extension_opportunity(session: dict) -> dict:
    """
    Check if the test should offer an extension for more accurate results.

    Extension is offered when:
    1. Not already at max questions for the mode
    2. Confidence tier is not "clear"
    3. There are ambiguous traits or under-sampled traits

    Args:
        session: The session dictionary

    Returns:
        Dictionary with:
        - offer_extension: Boolean
        - suggested_questions: Number of additional questions (always 2)
        - focus_traits: List of traits that need more signal
        - message: User-facing explanation
    """
    mode = session.get("mode", "overall")
    current_count = len(session.get("responses", {}))

    # Max questions per mode
    max_questions = {
        "hackathon": 10,
        "overall": 15,
        "deep_dive": 15
    }
    max_for_mode = max_questions.get(mode, 15)

    # If already at max, don't offer
    if current_count >= max_for_mode:
        return {
            "offer_extension": False,
            "reason": "Already at maximum questions for this mode"
        }

    # Calculate current confidence
    scores = session.get("scores", {})
    trait_counts = session.get("trait_counts", {})

    if not scores or not trait_counts:
        return {
            "offer_extension": False,
            "reason": "No scores yet"
        }

    normalized = normalize_scores(scores, trait_counts)
    confidence = check_score_confidence(normalized)

    # If already clear, don't offer
    if confidence.get("tier") == "clear":
        return {
            "offer_extension": False,
            "reason": "Confidence already clear"
        }

    # Find ambiguous traits (40-60%)
    ambiguous_traits = confidence.get("ambiguous_traits", [])

    # If no ambiguous traits, find least-questioned traits
    if not ambiguous_traits:
        # Sort traits by question count, take 2 lowest
        sorted_traits = sorted(trait_counts.items(), key=lambda x: x[1])
        focus_traits = [t[0] for t in sorted_traits[:2]]
    else:
        # Take up to 2 ambiguous traits
        focus_traits = ambiguous_traits[:2]

    # Format trait names for display
    trait_display = " and ".join(focus_traits).replace("_", " ")

    return {
        "offer_extension": True,
        "suggested_questions": 2,
        "focus_traits": focus_traits,
        "message": f"Want sharper results? 2 more questions would help clarify your {trait_display}.",
        "current_confidence": confidence.get("tier"),
        "confidence_pct": confidence.get("confidence_pct")
    }


def detect_suspicious_patterns(session: dict) -> dict:
    """
    Detect suspicious answering patterns that may indicate random/invalid responses.

    Checks for:
    1. Speed flag: Average response time < 2 seconds
    2. Uniform flag: All answers are the same option (e.g., all "a")
    3. Pattern flag: Repeating pattern like a,b,c,a,b,c
    4. Average flag: All trait scores in the 40-60% range

    Args:
        session: The session dictionary with answer history and scores

    Returns:
        Dictionary with:
        - suspicious: True if any high severity flag OR 2+ flags
        - flags: List of flag objects with type, severity, description
        - warning: User-facing warning message
        - suggestion: Suggestion for improvement
    """
    flags = []
    answer_history = session.get("answer_history", [])
    response_times = session.get("response_times", {})

    # Debug logging
    logging.info(f"[SUSPICIOUS] Checking patterns - answer_history count: {len(answer_history)}")
    logging.info(f"[SUSPICIOUS] response_times: {response_times}")

    # Extract just the answer keys (a, b, c) from history
    answer_keys = [a.get("selected_option", "").lower() for a in answer_history if a.get("selected_option")]
    logging.info(f"[SUSPICIOUS] answer_keys: {answer_keys}")

    # 1. Speed check: Average response time < 2 seconds
    if response_times:
        times = list(response_times.values())
        logging.info(f"[SUSPICIOUS] Speed check - times: {times}, count: {len(times)}")
        if len(times) >= 3:
            avg_time = sum(times) / len(times)
            logging.info(f"[SUSPICIOUS] Speed check - avg_time: {avg_time:.2f}s (threshold: 2.0s)")
            if avg_time < 2.0:
                flags.append({
                    "type": "speed",
                    "severity": "medium",
                    "description": f"Average response time was {avg_time:.1f}s (very fast)",
                    "avg_response_time": round(avg_time, 2)
                })

    # 2. Uniform check: All same answer (4+ questions)
    if len(answer_keys) >= 4:
        unique_answers = set(answer_keys)
        logging.info(f"[SUSPICIOUS] Uniform check - unique_answers: {unique_answers}")
        if len(unique_answers) == 1:
            flags.append({
                "type": "uniform",
                "severity": "high",
                "description": f"All {len(answer_keys)} answers were '{answer_keys[0]}'"
            })

    # 3. Pattern check: Repeating pattern like a,b,c,a,b,c (6+ questions)
    if len(answer_keys) >= 6:
        # Check for 2-length and 3-length repeating patterns
        for pattern_len in [2, 3]:
            pattern = answer_keys[:pattern_len]
            is_repeating = True
            for i in range(len(answer_keys)):
                if answer_keys[i] != pattern[i % pattern_len]:
                    is_repeating = False
                    break
            if is_repeating:
                flags.append({
                    "type": "pattern",
                    "severity": "high",
                    "description": f"Answers followed repeating pattern: {','.join(pattern)}"
                })
                break

    # 4. Average check: All normalized scores in 40-60% range
    scores = session.get("scores", {})
    trait_counts = session.get("trait_counts", {})
    if scores and trait_counts:
        normalized = normalize_scores(scores, trait_counts)
        all_average = all(40 <= score <= 60 for score in normalized.values() if score > 0)
        if all_average and len([s for s in normalized.values() if s > 0]) >= 3:
            flags.append({
                "type": "average",
                "severity": "low",
                "description": "All trait scores fell in the middle range (40-60%)"
            })

    # Determine if suspicious
    high_severity_count = sum(1 for f in flags if f["severity"] == "high")
    total_flags = len(flags)

    suspicious = high_severity_count >= 1 or total_flags >= 2

    logging.info(f"[SUSPICIOUS] Final result - flags: {[f['type'] for f in flags]}, high_severity: {high_severity_count}, suspicious: {suspicious}")

    result = {
        "suspicious": suspicious,
        "flags": flags,
        "flag_count": total_flags
    }

    if suspicious:
        result["warning"] = "Your responses showed some unusual patterns. Results may not fully reflect your personality."
        result["suggestion"] = "For more accurate results, try taking the test again and spend a moment considering each question."

    return result


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


def euclidean_similarity(vec_a: dict, vec_b: dict) -> float:
    """
    Calculate similarity based on Euclidean distance between two profiles.

    Unlike cosine similarity (which measures angle), Euclidean distance
    measures how CLOSE a user's profile is to each archetype. This penalizes
    being far from an archetype's profile even if proportionally similar.

    Args:
        vec_a: First profile as {trait: score} dictionary (user's scores)
        vec_b: Second profile as {trait: score} dictionary (archetype profile)

    Returns:
        Similarity score between 0 and 1 (higher = more similar)
    """
    # Get all traits that exist in both vectors
    common_traits = set(vec_a.keys()) & set(vec_b.keys())

    if not common_traits:
        return 0.0

    # Calculate Euclidean distance
    squared_diff_sum = sum((vec_a[t] - vec_b[t]) ** 2 for t in common_traits)
    distance = math.sqrt(squared_diff_sum)

    # Convert distance to similarity score
    # Max possible distance for 5 traits with 0-100 range: sqrt(5 * 100^2) ≈ 223.6
    max_distance = math.sqrt(len(common_traits) * (100 ** 2))

    # Normalize to 0-1 range (1 = identical, 0 = maximally different)
    similarity = 1 - (distance / max_distance)

    return max(0, similarity)


def combined_similarity(vec_a: dict, vec_b: dict, cosine_weight: float = 0.4) -> float:
    """
    Calculate a combined similarity score using both cosine and Euclidean metrics.

    Args:
        vec_a: First profile as {trait: score} dictionary
        vec_b: Second profile as {trait: score} dictionary
        cosine_weight: Weight for cosine similarity (default 0.4, euclidean gets 0.6)

    Returns:
        Combined similarity score between 0 and 1
    """
    cosine_sim = cosine_similarity(vec_a, vec_b)
    euclidean_sim = euclidean_similarity(vec_a, vec_b)

    euclidean_weight = 1 - cosine_weight
    return (cosine_sim * cosine_weight) + (euclidean_sim * euclidean_weight)


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

    # Calculate similarity to each archetype profile using combined metric
    # (weighted average of cosine similarity and Euclidean similarity)
    archetype_similarities = {}
    for archetype, profile in ARCHETYPE_PROFILES.items():
        similarity = combined_similarity(normalized_scores, profile, cosine_weight=0.4)
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

    # Check score confidence
    score_confidence = check_score_confidence(normalized_scores)

    return {
        "archetype": best_archetype,
        "confidence": round(confidence, 1),
        "normalized_scores": {k: round(v, 1) for k, v in normalized_scores.items()},
        "all_matches": {k: round(v * 100, 1) for k, v in sorted_matches.items()},
        "trait_breakdown": trait_breakdown,
        "compatibility": ARCHETYPE_COMPATIBILITY.get(best_archetype, {}),
        "score_confidence": score_confidence
    }


# ============================================================================
# SESSION MANAGEMENT FUNCTIONS
# ============================================================================

def start_test(mode: str = "overall", interest: str = None) -> dict:
    """
    Start a new personality test session.

    This function generates a new session ID, initializes session data in Firestore,
    and handles mode-specific routing (some modes skip interest selection).

    Args:
        mode: Assessment mode - 'hackathon', 'overall', or 'deep_dive'.
              Defaults to 'overall'.
        interest: Optional single interest/context for deep_dive mode.
                  If provided, skips interest selection and goes directly to questions.

    Returns:
        dict: A dictionary containing:
            - session_id: The unique session identifier
            - mode: The selected assessment mode
            - mode_config: Configuration for the mode (display name, question count, etc.)
            - ui_flow: Instructions for frontend on what to display next
            - next_question: (Optional) First question if skipping interest selection
            - interest_config: (Optional) Interest selection requirements if needed
            - interest: (Optional) The interest context for deep_dive mode
    """
    # Validate and get mode configuration
    if mode not in ASSESSMENT_MODES:
        mode = "overall"
    mode_config = get_mode_config(mode)

    session_id = str(uuid.uuid4())

    # Determine which traits to assess based on mode
    traits_focus = mode_config.get("traits_focus", ["all"])
    if traits_focus == ["all"] or "all" in traits_focus:
        focused_traits = knowledge_base["traits"]
    else:
        focused_traits = traits_focus

    trait_counts = {trait: 0 for trait in focused_traits}
    session_data = {
        "start_time": time.time(),
        "responses": {},
        "interests": [],
        "interest": interest,  # Single interest for deep_dive mode (new flow)
        "scores": {trait: 0 for trait in focused_traits},
        "trait_counts": trait_counts,
        "focused_traits": focused_traits,  # Store for later use
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
        "trait_scores_detailed": {trait: {"total": 0, "count": 0} for trait in focused_traits},
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
    elif mode == "deep_dive" and interest:
        # Deep dive with single interest provided - skip to questions
        response["ui_flow"] = {
            "show_interest_selection": False,
            "proceed_directly_to_questions": True
        }
        response["interest"] = interest
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

        # Track the score added for this answer (used for both MC and freeform)
        score_added_to_session = 0

        if current_question:
            selected_key = user_response.answer.strip().lower()

            if current_question["type"] == "multiple-choice":
                option = current_question["options"].get(selected_key)
                if option:
                    score_added_to_session = option["score"]
                    session["scores"][trait] += score_added_to_session

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
                # Scale freeform score (0-5) to match multiple-choice scale (0-2)
                freeform_score = eval_json.get("score", 0)
                score_added_to_session = (freeform_score / 5) * 2  # Convert 0-5 to 0-2
                session["scores"][trait] += score_added_to_session
                session["optional_responses"][user_response.question_id] = eval_json["reason"]
                logging.debug(f"Freeform score: {freeform_score}/5 → scaled: {score_added_to_session:.2f}/2")

            # Update trait counts
            session["trait_counts"][trait] += 1

            # Update detailed trait scores for template
            if "trait_scores_detailed" not in session:
                session["trait_scores_detailed"] = {t: {"total": 0, "count": 0} for t in knowledge_base["traits"]}

            # Use the score we already calculated above (works for both MC and freeform)
            session["trait_scores_detailed"][trait]["total"] += score_added_to_session
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
        focused_traits = session.get("focused_traits", list(trait_counts.keys()))

        # Calculate how many questions each trait should get based on mode
        # Hackathon: 6 questions / 3 traits = 2 questions per trait
        # Standard: 10 questions / 5 traits = 2 questions per trait
        # Deep: 10 questions / 5 traits = 2 questions per trait
        num_traits = len(focused_traits)
        questions_per_trait = max(1, question_count_target // num_traits)

        # Only consider focused traits when calculating needs
        trait_needs = {trait: questions_per_trait - trait_counts.get(trait, 0)
                       for trait in focused_traits}
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

        # Get single interest for deep dive mode (new flow)
        single_interest = session.get("interest")  # Freeform interest text

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
            life_contexts=user_interests if mode in ["interest", "deep_dive"] and not single_interest else None,
            current_context=current_context,
            context_scenario_hooks=context_hooks,
            traits_assessed=traits_assessed,
            inferred_tendencies=tendencies,
            focused_traits=focused_traits,
            questions_per_trait=questions_per_trait,
            trait_needs=trait_needs,
            single_interest=single_interest
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

            # Validate the generated question
            validation = validate_llm_question(next_question, target_trait, focused_traits)
            if not validation["valid"]:
                logging.warning(f"LLM question validation failed: {validation['issues']}")
                # Attempt to fix score distribution
                next_question = fix_question_scores(next_question)
                # Force correct trait if wrong
                if next_question.get("trait") != target_trait:
                    logging.warning(f"Forcing trait from {next_question.get('trait')} to {target_trait}")
                    next_question["trait"] = target_trait

            # Extract predicted_next_answer for pre-fetching (Phase 4)
            predicted_next = response_content.get("predicted_next_answer", {})
            if predicted_next:
                logging.debug("Predicted next answer: %s", predicted_next)

            # Store both the question and prediction
            # Also set last_question_time so response time is measured from when question is shown
            session_doc.update({
                "current_question": next_question,
                "predicted_next_answer": predicted_next,
                "last_question_time": time.time()  # Track when question was displayed
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
        single_interest = session.get("interest")  # Single interest for deep_dive

        if mode == "hackathon":
            mode_specific = {
                "hackathon_superpower": raw_archetype.get("hackathon_superpower", ""),
                "hackathon_pitfall": raw_archetype.get("hackathon_pitfall", ""),
                "team_value": archetype_data.get("team_value", "")
            }
        elif mode == "deep_dive" and single_interest:
            # Single interest deep dive - new flow
            mode_specific = {
                "interest": single_interest,
                "interest_insight": f"In {single_interest}, you show up as {archetype_name}.",
                "contextualized_tagline": f"At {single_interest}, you're {archetype_name}"
            }
        elif mode == "interest" and interests:
            mode_specific = {
                "interests_assessed": interests,
                "domain_insight": f"Your {archetype_name} traits shine through in {', '.join(interests[:2])}"
            }

        # Get detailed confidence info
        score_confidence = archetype_result.get("score_confidence", check_score_confidence(normalized_scores))

        # Check for suspicious patterns
        suspicious_patterns = detect_suspicious_patterns(session)

        # Calculate quality weight for profile integration (Phase 2.5)
        confidence_pct = score_confidence.get("confidence_pct", confidence)
        quality_weight = calculate_test_quality_weight(
            confidence_pct,
            suspicious_patterns.get("suspicious", False),
            suspicious_patterns.get("flags", [])
        )
        included_in_profile = quality_weight >= 0.15

        # Store results in session for profile update
        db.collection("sessions").document(session_id).update({
            "results": {
                "archetype": archetype_name,
                "normalized_scores": normalized_scores,
                "confidence": score_confidence,
                "suspicious_patterns": suspicious_patterns,
                "quality_weight": quality_weight,
                "included_in_profile": included_in_profile
            }
        })

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
            "confidence": {
                "tier": score_confidence.get("tier", "emerging"),
                "confidence_pct": confidence_pct,
                "explanation": score_confidence.get("explanation"),
                "ambiguous_traits": score_confidence.get("ambiguous_traits", [])
            },
            "trait_breakdown": trait_breakdown,
            "all_matches": all_matches,
            "personalized_profile": personalized_profile,
            "mode_specific": mode_specific,
            "interest": single_interest,  # For deep_dive mode with single interest
            "suspicious_patterns": suspicious_patterns if suspicious_patterns.get("suspicious") else None,
            # Quality weighting data (Phase 2.5)
            "quality_weight": quality_weight,
            "included_in_profile": included_in_profile,
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


# =============================================================================
# Profile Persistence Functions
# =============================================================================

def generate_device_fingerprint(headers: dict) -> str:
    """
    Generate a device fingerprint from request headers.

    Creates a hash from browser characteristics for device identification.
    This is a best-effort approach for MVP - not cryptographically secure.

    Args:
        headers: Dictionary of HTTP headers from the request

    Returns:
        32-character SHA256 hash of combined signals
    """
    signals = [
        headers.get("User-Agent", ""),
        headers.get("Accept-Language", ""),
        headers.get("Sec-CH-UA", ""),
        headers.get("Sec-CH-UA-Platform", ""),
    ]

    combined = "|".join(signals)
    hash_obj = hashlib.sha256(combined.encode())
    return hash_obj.hexdigest()[:32]


# ============================================================================
# HOLISTIC PROFILE FUNCTIONS (Phase 2.5)
# ============================================================================

def calculate_test_quality_weight(confidence_pct: float, suspicious: bool, flags: list) -> float:
    """
    Calculate how much this test should contribute to holistic profile.

    Logic:
    - Base weight = confidence_pct / 100 (0.0 to 1.0)
    - If suspicious, multiply by 0.1 (heavy penalty)
    - Specific flag penalties:
      - "uniform" flag (all same answers): multiply by 0.0 (exclude entirely)
      - "pattern" flag (a,b,c,a,b,c): multiply by 0.0 (exclude entirely)
      - "speed" flag only: multiply by 0.5 (might be experienced user)
      - "average" flag only: multiply by 0.8 (might be genuinely balanced)

    Args:
        confidence_pct: Confidence percentage from check_score_confidence (0-100)
        suspicious: Whether suspicious patterns were detected
        flags: List of flag dictionaries from detect_suspicious_patterns

    Returns:
        Float between 0.0 and 1.0 representing test quality weight
    """
    base_weight = confidence_pct / 100.0

    # Extract flag types
    flag_types = [f.get("type", "") for f in flags] if flags else []

    # Check for exclusion flags (gaming behavior) - these get 0 weight
    if "uniform" in flag_types or "pattern" in flag_types:
        logging.info(f"[QUALITY] Test excluded due to gaming flags: {flag_types}")
        return 0.0

    weight = base_weight

    if suspicious:
        # Heavy penalty for suspicious tests
        weight *= 0.1
        logging.info(f"[QUALITY] Suspicious test penalty applied: {base_weight:.2f} -> {weight:.2f}")
    else:
        # Lighter penalties for individual flags
        if "speed" in flag_types:
            weight *= 0.5
            logging.info(f"[QUALITY] Speed flag penalty applied")
        if "average" in flag_types:
            weight *= 0.8
            logging.info(f"[QUALITY] Average flag penalty applied")

    final_weight = round(weight, 2)
    logging.info(f"[QUALITY] Final weight: {final_weight} (confidence: {confidence_pct}%, suspicious: {suspicious}, flags: {flag_types})")

    return final_weight


def get_traits_for_mode(mode: str) -> list:
    """
    Get the list of traits assessed for a given mode.

    Args:
        mode: Assessment mode ('hackathon', 'overall', 'deep_dive')

    Returns:
        List of trait names
    """
    mode_config = get_mode_config(mode)
    traits_focus = mode_config.get("traits_focus", ["all"])

    if traits_focus == ["all"] or "all" in traits_focus:
        return ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Emotional_Stability"]
    else:
        return traits_focus


def calculate_holistic_scores(weighted_scores: dict) -> dict:
    """
    Convert weighted sums to normalized 0-100 scores.

    Args:
        weighted_scores: Dict of trait -> {"weighted_sum": float, "weight_total": float}

    Returns:
        Dict of trait -> normalized score (0-100)
    """
    holistic = {}
    for trait, data in weighted_scores.items():
        if data["weight_total"] > 0:
            holistic[trait] = round(data["weighted_sum"] / data["weight_total"], 1)
        else:
            holistic[trait] = 50.0  # Neutral default
    return holistic


def calculate_stability(archetype_history: list) -> str:
    """
    Determine if results are converging, stable, or inconsistent.

    Args:
        archetype_history: List of archetype names from past tests

    Returns:
        One of: "new", "converging", "stable", "inconsistent"
    """
    if len(archetype_history) < 2:
        return "new"

    # Look at last 3 tests (or fewer if not enough)
    recent = archetype_history[-3:]
    unique_archetypes = set(recent)

    if len(unique_archetypes) == 1:
        if len(archetype_history) >= 3:
            return "stable"
        else:
            return "converging"
    elif len(unique_archetypes) == 2 and len(recent) >= 3:
        # 2 out of 3 same = converging
        from collections import Counter
        counts = Counter(recent)
        if max(counts.values()) >= 2:
            return "converging"

    return "inconsistent"


def normalize_interest(interest: str) -> str:
    """
    Normalize interest string for consistent keying.

    Handles variations like "Work", "work", "my job" -> "work"

    Args:
        interest: Raw interest string from user

    Returns:
        Normalized canonical interest key
    """
    if not interest:
        return ""

    # Lowercase and strip
    normalized = interest.lower().strip()

    # Common synonyms mapping to canonical keys
    synonyms = {
        "work": ["job", "career", "office", "professional", "at work", "my job", "my work", "workplace"],
        "relationships": ["relationship", "dating", "love", "partner", "my relationship", "romantic"],
        "fitness": ["gym", "health", "exercise", "working out", "sports", "training", "wellness"],
        "family": ["parenting", "kids", "children", "home", "my family", "parent"],
        "creative": ["creativity", "art", "creative projects", "side projects", "hobbies", "artistic"],
        "learning": ["education", "school", "study", "studying", "growth", "self-improvement"]
    }

    for canonical, variants in synonyms.items():
        if normalized in variants or normalized == canonical:
            return canonical

    # If no match, return cleaned original
    return normalized


def update_mode_profile(profile: dict, mode: str, normalized_scores: dict,
                        archetype_name: str, quality_weight: float) -> bool:
    """
    Update the mode-specific profile with weighted scores from this test.

    Args:
        profile: The user profile dictionary (will be modified in place)
        mode: Assessment mode ('hackathon', 'overall', 'deep_dive')
        normalized_scores: Normalized trait scores (0-100) from this test
        archetype_name: Archetype determined for this test
        quality_weight: Quality weight for this test (0.0 to 1.0)

    Returns:
        bool: True if test was included in profile, False if excluded
    """
    # Initialize mode_profiles if doesn't exist
    if "mode_profiles" not in profile:
        profile["mode_profiles"] = {}

    # Initialize this mode's profile if doesn't exist
    if mode not in profile["mode_profiles"]:
        traits = get_traits_for_mode(mode)
        profile["mode_profiles"][mode] = {
            "weighted_scores": {t: {"weighted_sum": 0.0, "weight_total": 0.0} for t in traits},
            "tests_included": 0,
            "tests_excluded": 0,
            "current_archetype": None,
            "archetype_history": [],
            "stability": "new",
            "confidence": 0
        }

    mode_profile = profile["mode_profiles"][mode]

    # Inclusion threshold
    INCLUSION_THRESHOLD = 0.15
    included = quality_weight >= INCLUSION_THRESHOLD

    if included:
        # Add weighted scores
        for trait, score in normalized_scores.items():
            if trait in mode_profile["weighted_scores"]:
                mode_profile["weighted_scores"][trait]["weighted_sum"] += score * quality_weight
                mode_profile["weighted_scores"][trait]["weight_total"] += quality_weight

        mode_profile["tests_included"] += 1
        mode_profile["archetype_history"].append(archetype_name)
        logging.info(f"[PROFILE] Test included in {mode} profile with weight {quality_weight}")
    else:
        mode_profile["tests_excluded"] += 1
        logging.info(f"[PROFILE] Test excluded from {mode} profile (weight {quality_weight} < {INCLUSION_THRESHOLD})")

    # Recalculate holistic archetype from weighted scores
    if mode_profile["weighted_scores"]:
        holistic_scores = calculate_holistic_scores(mode_profile["weighted_scores"])

        # Only recalculate if we have actual data
        if any(data["weight_total"] > 0 for data in mode_profile["weighted_scores"].values()):
            # Create fake trait_counts for determine_archetype (each trait counted once per included test)
            fake_trait_counts = {t: mode_profile["tests_included"] for t in holistic_scores.keys()}
            holistic_result = determine_archetype(holistic_scores, fake_trait_counts)

            mode_profile["current_archetype"] = holistic_result["archetype"]
            mode_profile["confidence"] = holistic_result.get("score_confidence", {}).get("confidence_pct", 0)

    mode_profile["stability"] = calculate_stability(mode_profile["archetype_history"])

    return included


def update_deep_dive_profile(profile: dict, interest: str, normalized_scores: dict,
                             archetype_name: str, quality_weight: float) -> bool:
    """
    Update the deep dive profile for a specific interest with weighted scores.

    Args:
        profile: The user profile dictionary (will be modified in place)
        interest: Normalized interest key (e.g., "work", "relationships")
        normalized_scores: Normalized trait scores (0-100) from this test
        archetype_name: Archetype determined for this test
        quality_weight: Quality weight for this test (0.0 to 1.0)

    Returns:
        bool: True if test was included in profile, False if excluded
    """
    # Initialize deep_dive_profiles if doesn't exist
    if "deep_dive_profiles" not in profile:
        profile["deep_dive_profiles"] = {}

    # Initialize this interest's profile if doesn't exist
    if interest not in profile["deep_dive_profiles"]:
        traits = get_traits_for_mode("deep_dive")
        profile["deep_dive_profiles"][interest] = {
            "weighted_scores": {t: {"weighted_sum": 0.0, "weight_total": 0.0} for t in traits},
            "tests_included": 0,
            "tests_excluded": 0,
            "current_archetype": None,
            "archetype_history": [],
            "stability": "new",
            "confidence": 0
        }

    interest_profile = profile["deep_dive_profiles"][interest]

    # Inclusion threshold
    INCLUSION_THRESHOLD = 0.15
    included = quality_weight >= INCLUSION_THRESHOLD

    if included:
        # Add weighted scores
        for trait, score in normalized_scores.items():
            if trait in interest_profile["weighted_scores"]:
                interest_profile["weighted_scores"][trait]["weighted_sum"] += score * quality_weight
                interest_profile["weighted_scores"][trait]["weight_total"] += quality_weight

        interest_profile["tests_included"] += 1
        interest_profile["archetype_history"].append(archetype_name)
        logging.info(f"[PROFILE] Test included in deep_dive/{interest} profile with weight {quality_weight}")
    else:
        interest_profile["tests_excluded"] += 1
        logging.info(f"[PROFILE] Test excluded from deep_dive/{interest} profile (weight {quality_weight} < {INCLUSION_THRESHOLD})")

    # Recalculate holistic archetype from weighted scores
    if interest_profile["weighted_scores"]:
        holistic_scores = calculate_holistic_scores(interest_profile["weighted_scores"])

        # Only recalculate if we have actual data
        if any(data["weight_total"] > 0 for data in interest_profile["weighted_scores"].values()):
            fake_trait_counts = {t: interest_profile["tests_included"] for t in holistic_scores.keys()}
            holistic_result = determine_archetype(holistic_scores, fake_trait_counts)

            interest_profile["current_archetype"] = holistic_result["archetype"]
            interest_profile["confidence"] = holistic_result.get("score_confidence", {}).get("confidence_pct", 0)

    interest_profile["stability"] = calculate_stability(interest_profile["archetype_history"])

    return included


def get_or_create_profile(user_id: str = None, device_fingerprint: str = None) -> dict:
    """
    Get existing profile or create a new one.

    Resolution order:
    1. If user_id provided, look for profile with that user_id
    2. If not found but device_fingerprint provided, look for profile with that fingerprint
    3. If found by fingerprint and user_id was provided, link them (account linking)
    4. If no profile found, create new one

    Args:
        user_id: Firebase auth UID (optional)
        device_fingerprint: Device fingerprint hash (optional)

    Returns:
        Dictionary with profile data and profile_id
    """
    profiles_ref = db.collection("user_profiles")

    # 1. Try to find by user_id
    if user_id:
        query = profiles_ref.where("user_id", "==", user_id).limit(1)
        docs = list(query.stream())
        if docs:
            profile = docs[0].to_dict()
            profile["profile_id"] = docs[0].id
            return profile

    # 2. Try to find by device fingerprint
    if device_fingerprint:
        query = profiles_ref.where("device_fingerprint", "==", device_fingerprint).limit(1)
        docs = list(query.stream())
        if docs:
            profile = docs[0].to_dict()
            profile["profile_id"] = docs[0].id

            # 3. Link user_id if provided (account linking)
            if user_id and not profile.get("user_id"):
                docs[0].reference.update({
                    "user_id": user_id,
                    "updated_at": time.time()
                })
                profile["user_id"] = user_id

            return profile

    # 4. Create new profile with Phase 3 schema
    current_time = time.time()
    new_profile = {
        "user_id": user_id,
        "device_fingerprint": device_fingerprint,
        "created_at": current_time,
        "updated_at": current_time,
        # Mode-specific profiles with weighted scores (Phase 2.5)
        "mode_profiles": {},
        # Deep dive profiles keyed by normalized interest
        "deep_dive_profiles": {},
        # Full test history with quality metrics
        "test_history": [],
        # Legacy fields for backwards compatibility
        "cumulative_scores": {
            "Openness": {"total_points": 0, "total_questions": 0},
            "Conscientiousness": {"total_points": 0, "total_questions": 0},
            "Extraversion": {"total_points": 0, "total_questions": 0},
            "Agreeableness": {"total_points": 0, "total_questions": 0},
            "Emotional_Stability": {"total_points": 0, "total_questions": 0}
        },
        "current_archetype": None,
        "overall_confidence": 0,
        # Phase 3: Badge tracking
        "badges_earned": [],  # Array of {badge_id, earned_at, context}
        "badge_progress": {},  # Progress toward incomplete badges
        # Phase 3: Engagement tracking (for badge triggers)
        "total_assessments_completed": 0,
        "assessment_types_completed": [],  # Which modes they've done
        "insights_viewed": {},  # {archetype: {section: timestamp}}
        "last_active_at": current_time,
        "weekly_visits": [],  # Array of timestamps for streak tracking
        "consistency_scores": [],  # Scores from each assessment
        # Phase 3: Profile display preferences
        "insight_mode": "concise",  # "concise" or "deep"
        "badges_visibility": "public"  # "public" or "private"
    }

    doc_ref = profiles_ref.add(new_profile)
    new_profile["profile_id"] = doc_ref[1].id

    return new_profile


# ============================================================================
# USERNAME SYSTEM
# ============================================================================

import re
import string

def clean_name_part(name: str) -> str:
    """Clean a name part for use in username - lowercase, alphanumeric only."""
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())


def generate_random_suffix(length: int = 4) -> str:
    """Generate a random alphanumeric suffix."""
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def is_username_available(username: str) -> bool:
    """Check if a username is available (not taken by another user)."""
    if not username or len(username) < 3:
        return False

    profiles_ref = db.collection("user_profiles")
    query = profiles_ref.where("username", "==", username.lower()).limit(1)
    docs = list(query.stream())
    return len(docs) == 0


def generate_unique_username(display_name: str) -> str:
    """
    Generate a short, unique username from a display name.

    Strategy (tries in order):
    1. First name only: "ayush"
    2. First name + first initial of last: "ayusha"
    3. First name + first 3 chars of last: "ayushagr"
    4. First name + last name abbreviated: "ayushagra"
    5. First name + incrementing number: "ayush1", "ayush2", ...
    """
    if not display_name:
        return f"user{generate_random_suffix(4)}"

    # Split into parts
    parts = display_name.strip().split()
    first_name = clean_name_part(parts[0]) if parts else ""
    last_name = clean_name_part(parts[-1]) if len(parts) > 1 else ""
    middle_parts = [clean_name_part(p) for p in parts[1:-1]] if len(parts) > 2 else []

    if not first_name:
        return f"user{generate_random_suffix(4)}"

    # Try progressively longer combinations
    candidates = []

    # 1. First name only
    candidates.append(first_name)

    if last_name and last_name != first_name:
        # 2. First name + first initial of last name
        candidates.append(f"{first_name}{last_name[0]}")

        # 3. First name + first 2-3 chars of last name
        if len(last_name) >= 2:
            candidates.append(f"{first_name}{last_name[:2]}")
        if len(last_name) >= 3:
            candidates.append(f"{first_name}{last_name[:3]}")
        if len(last_name) >= 4:
            candidates.append(f"{first_name}{last_name[:4]}")

        # 4. With middle initial if present
        if middle_parts:
            candidates.append(f"{first_name}{middle_parts[0][0]}{last_name[0]}")

    # Try each candidate
    for candidate in candidates:
        if len(candidate) >= 3 and is_username_available(candidate):
            return candidate

    # 5. First name + incrementing number
    base = first_name if len(first_name) >= 3 else f"{first_name}{last_name[:2] if last_name else ''}"
    for i in range(1, 100):
        candidate = f"{base}{i}"
        if is_username_available(candidate):
            return candidate

    # Fallback: add random suffix
    return f"{base}{generate_random_suffix(3)}"


def set_username(profile_id: str, username: str, display_name: str = None) -> dict:
    """
    Set or update the username for a profile.

    Args:
        profile_id: Firestore profile document ID
        username: The desired username (will be lowercased)
        display_name: Optional display name to store

    Returns:
        dict with success status and the username
    """
    username = username.lower().strip()

    # Validate username format
    if not re.match(r'^[a-z0-9][a-z0-9-]{1,28}[a-z0-9]$', username):
        return {"success": False, "error": "Username must be 3-30 characters, alphanumeric and dashes only"}

    # Check if available
    profiles_ref = db.collection("user_profiles")

    # Check current profile
    profile_doc = profiles_ref.document(profile_id)
    profile = profile_doc.get().to_dict()

    if not profile:
        return {"success": False, "error": "Profile not found"}

    # If this profile already has this username, it's fine
    if profile.get("username") == username:
        return {"success": True, "username": username}

    # Check if taken by someone else
    if not is_username_available(username):
        return {"success": False, "error": "Username is already taken"}

    # Update the profile
    update_data = {
        "username": username,
        "username_set_at": time.time(),
        "updated_at": time.time()
    }
    if display_name:
        update_data["display_name"] = display_name

    profile_doc.update(update_data)

    return {"success": True, "username": username}


def get_profile_by_username(username: str) -> dict:
    """
    Get a public profile view by username.

    Returns:
        dict with public profile data or None if not found
    """
    if not username:
        return None

    username = username.lower().strip()
    profiles_ref = db.collection("user_profiles")
    query = profiles_ref.where("username", "==", username).limit(1)
    docs = list(query.stream())

    if not docs:
        return None

    profile = docs[0].to_dict()
    profile_id = docs[0].id

    # Build public profile view (similar to get_profile_view but with username)
    mode_profiles_summary = {}
    for mode, data in profile.get("mode_profiles", {}).items():
        if data.get("current_archetype"):
            mode_profiles_summary[mode] = {
                "current_archetype": data.get("current_archetype"),
                "confidence": data.get("confidence", 0),
                "stability": data.get("stability", "new"),
                "tests_included": data.get("tests_included", 0),
            }

    deep_dive_summary = {}
    for interest, data in profile.get("deep_dive_profiles", {}).items():
        if data.get("current_archetype"):
            deep_dive_summary[interest] = {
                "current_archetype": data.get("current_archetype"),
                "confidence": data.get("confidence", 0),
                "stability": data.get("stability", "new"),
                "tests_included": data.get("tests_included", 0),
            }

    return {
        "profile_id": profile_id,
        "username": profile.get("username"),
        "display_name": profile.get("display_name"),
        "mode_profiles": mode_profiles_summary,
        "deep_dive_profiles": deep_dive_summary,
        "current_archetype": profile.get("current_archetype"),
        "member_since": profile.get("created_at"),
        "total_tests": len(profile.get("test_history", [])),
    }


def update_profile_after_test(profile_id: str, session: dict, result: dict,
                              confidence: dict, suspicion: dict) -> dict:
    """
    Update user profile after completing a test with quality weighting (Phase 2.5).

    Uses weighted score accumulation to build holistic profiles per mode.
    Tests with suspicious patterns are down-weighted or excluded.

    Args:
        profile_id: Firestore profile document ID
        session: The session dictionary
        result: The finalized test result (with archetype, normalized_scores, etc.)
        confidence: Confidence data from check_score_confidence
        suspicion: Suspicion data from detect_suspicious_patterns

    Returns:
        Updated profile dictionary with holistic data
    """
    profile_ref = db.collection("user_profiles").document(profile_id)
    profile = profile_ref.get().to_dict()

    if not profile:
        return {"error": "Profile not found"}

    mode = session.get("mode", "overall")
    session_id = session.get("session_id") or profile_id[:8]  # Fallback
    scores = session.get("scores", {})
    trait_counts = session.get("trait_counts", {})
    interest = session.get("interest")  # For deep dive mode
    normalized_scores = result.get("normalized_scores", {})
    archetype_name = result.get("archetype", {}).get("name") if isinstance(result.get("archetype"), dict) else result.get("archetype")

    # Initialize mode_profiles if doesn't exist (for older profiles)
    if "mode_profiles" not in profile:
        profile["mode_profiles"] = {}

    # Calculate quality weight
    confidence_pct = confidence.get("confidence_pct", 50)
    suspicious = suspicion.get("suspicious", False)
    flags = suspicion.get("flags", [])
    quality_weight = calculate_test_quality_weight(confidence_pct, suspicious, flags)

    # Update mode or deep_dive profile with weighted scores
    if mode == "deep_dive" and interest:
        normalized_interest = normalize_interest(interest)
        included = update_deep_dive_profile(
            profile, normalized_interest, normalized_scores, archetype_name, quality_weight
        )
    else:
        included = update_mode_profile(
            profile, mode, normalized_scores, archetype_name, quality_weight
        )

    # Create enhanced test record for history
    test_record = {
        "session_id": session_id,
        "mode": mode,
        "interest": interest,
        "date": time.time(),
        "raw_scores": scores,
        "normalized_scores": normalized_scores,
        "archetype": archetype_name,
        "confidence_pct": confidence_pct,
        "confidence_tier": confidence.get("tier", "emerging"),
        "suspicious": suspicious,
        "flags": flags,
        "quality_weight": quality_weight,
        "included_in_profile": included,
        "response_times": list(session.get("response_times", {}).values()),
        "answer_count": len(session.get("answer_history", []))
    }

    # Update test history (keep last 50 for auditability)
    test_history = profile.get("test_history", [])
    test_history.append(test_record)
    if len(test_history) > 50:
        test_history = test_history[-50:]

    # Legacy: Update cumulative scores for backwards compatibility
    cumulative = profile.get("cumulative_scores", {})
    for trait, score in scores.items():
        if trait not in cumulative:
            cumulative[trait] = {"total_points": 0, "total_questions": 0}
        cumulative[trait]["total_points"] += score
        cumulative[trait]["total_questions"] += trait_counts.get(trait, 0)

    # Legacy: Update current_archetype (most recent)
    profile["current_archetype"] = archetype_name
    profile["overall_confidence"] = confidence_pct

    # Write all updates
    profile_ref.update({
        "mode_profiles": profile.get("mode_profiles", {}),
        "deep_dive_profiles": profile.get("deep_dive_profiles", {}),
        "test_history": test_history,
        "cumulative_scores": cumulative,
        "current_archetype": archetype_name,
        "overall_confidence": confidence_pct,
        "updated_at": time.time()
    })

    profile["test_history"] = test_history
    profile["cumulative_scores"] = cumulative

    # Add holistic data to return
    if mode == "deep_dive" and interest:
        normalized_interest = normalize_interest(interest)
        holistic = profile.get("deep_dive_profiles", {}).get(normalized_interest)
    else:
        holistic = profile.get("mode_profiles", {}).get(mode)

    profile["_holistic"] = holistic
    profile["_quality_weight"] = quality_weight
    profile["_included_in_profile"] = included

    return profile


def get_profile_context_for_llm(profile: dict) -> Optional[dict]:
    """
    Build context from profile history to help LLM generate better questions.

    Args:
        profile: User profile dictionary

    Returns:
        Context object for LLM, or None if no useful history
    """
    if not profile:
        return None

    test_history = profile.get("test_history", [])
    if not test_history:
        return None

    cumulative = profile.get("cumulative_scores", {})

    # Find under-sampled traits (total_questions < 4)
    weak_traits = []
    for trait, data in cumulative.items():
        if data.get("total_questions", 0) < 4:
            weak_traits.append(trait)

    # Calculate cumulative normalized scores
    cumulative_scores = {}
    for trait, data in cumulative.items():
        total_q = data.get("total_questions", 0)
        if total_q > 0:
            max_possible = total_q * 2  # Max 2 points per question
            normalized = (data.get("total_points", 0) / max_possible) * 100
            cumulative_scores[trait] = round(normalized, 1)

    context = {
        "tests_completed": len(test_history),
        "current_archetype": profile.get("current_archetype"),
        "overall_confidence": profile.get("overall_confidence"),
        "weak_traits": weak_traits,
        "cumulative_scores": cumulative_scores,
        "llm_instruction": None
    }

    # Build LLM instruction
    if weak_traits or len(test_history) > 0:
        instruction_parts = []

        if profile.get("current_archetype"):
            instruction_parts.append(
                f"User's current archetype is {profile['current_archetype']} "
                f"with {profile.get('overall_confidence', 0):.0f}% confidence."
            )

        if weak_traits:
            instruction_parts.append(
                f"These traits need more signal: {', '.join(weak_traits)}. "
                "Prioritize questions that assess these traits."
            )

        if len(test_history) > 1:
            instruction_parts.append(
                f"User has taken {len(test_history)} tests. "
                "Avoid repeating similar scenarios they've likely seen before."
            )

        context["llm_instruction"] = " ".join(instruction_parts)

    return context if context.get("llm_instruction") else None
