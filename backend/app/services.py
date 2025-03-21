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
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from fastapi import HTTPException
from firebase import db
from models import UserResponse, InterestSelection

# Load environment variables from .env file
load_dotenv()

# Load Azure OpenAI credentials from environment variables
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME")

# Initialize Azure OpenAI Client
client = ChatCompletionsClient(
    endpoint=AZURE_OPENAI_ENDPOINT,
    credential=AzureKeyCredential(AZURE_OPENAI_API_KEY),
)

# Load the system prompt from a local markdown file
with open("system_prompt.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Optionally, send the system prompt at session startup
response = client.complete(
    messages=[SystemMessage(content=system_prompt)],
    max_tokens=500,
    temperature=0.8,
    top_p=1.0,
    model=AZURE_OPENAI_MODEL_NAME
)


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


def start_test() -> dict:
    """
    Start a new personality test session.

    This function generates a new session ID, initializes session data in Firestore,
    and generates the first question for the test using GPT-4o.

    Returns:
        dict: A dictionary containing the session ID and the first question under the
                key "next_question".
    """
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
    }
    db.collection("sessions").document(session_id).set(session_data)
    return {"session_id": session_id, "next_question": generate_next_question(session_id)}


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
                eval_response = client.complete(
                    messages=[
                        SystemMessage(content=eval_prompt),
                        UserMessage(content="Return ONLY the specified JSON.")
                    ],
                    max_tokens=100,
                    temperature=0.6,
                    model=AZURE_OPENAI_MODEL_NAME
                )
                eval_json = json.loads(
                    eval_response.choices[0].message.content.strip())
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

        if time.time() - session["start_time"] > 180 and not session["paused"]:
            session_ref.update({"paused": True})
            return {"test_paused": True, "message": "Time is up! Continue or get your results?"}

        next_question = generate_next_question(user_response.session_id)
        if not next_question:
            return finalize_test(user_response.session_id)

        return {"next_question": next_question}
    except HTTPException as e:
        logging.error("Error in submit_response: %s", e)
        return {"error": "Internal server error while processing your response."}


def generate_next_question(session_id: str) -> dict:
    """
    Generate the next test question using GPT-4o.

    Retrieves the current session data, determines the target trait based on responses so far,
    and sends a prompt to GPT-4o to generate a new question in a strict JSON format.
    Freeform questions occur only 10% of the time, with multiple-choice questions being the default.

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

        question_count = len(session.get("responses", {}))
        if question_count >= 10:
            logging.info("Maximum question count reached. Finalizing test.")
            return finalize_test(session_id)

        trait_counts = session.get("trait_counts", {})
        trait_needs = {trait: 2 - count for trait,
                       count in trait_counts.items()}
        target_trait = max(trait_needs, key=trait_needs.get)

        question_type = "multiple-choice" if random.random() < 0.9 else "optional-freeform"

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

        next_question_prompt = f"""
**User Profile:**
- User Interests: {user_interests}
- Previous Responses: {previous_responses}
- Previous Response Times: {previous_response_times}
- Current Trait Scores: {current_trait_scores}
- Target Trait: {target_trait}
- Questions Answered: {questions_answered_count} of 10
- Trait Counts: {trait_counts_str}

## STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):
{prompt_schema}

Important Constraints:
- NEVER include markdown formatting or commentary in your response.
- NEVER repeat previously asked questions.
- NEVER embed answer options within question texts.
- ALWAYS output strictly valid JSON exactly as defined above.
- ALWAYS personalize the question based on the user interests.
"""
        logging.info("Sending prompt to GPT-4o for question generation.")
        response_gpt = client.complete(
            messages=[
                SystemMessage(content=next_question_prompt),
                UserMessage(
                    content="Return only the JSON object as specified.")
            ],
            max_tokens=500,
            temperature=0.8,
            model=AZURE_OPENAI_MODEL_NAME
        )

        raw_content = response_gpt.choices[0].message.content.strip()
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

    Retrieves the session data, determines the best matching archetype, and sends a prompt to GPT-4o
    to generate a detailed, personalized profile in a strict JSON format. If GPT-4o returns
    malformed JSON, a fallback profile is provided.

    Args:
        session_id (str): The Firestore session ID.

    Returns:
        dict: A dictionary containing:
            - test_complete (bool): True if the test is finalized.
            - final_scores (dict): The user's final trait scores.
            - suggested_archetype (str): The determined personality archetype.
            - archetype_description (dict): A detailed profile in JSON format.
        In case of errors, returns a dictionary with an "error" key.
    """
    try:
        session = db.collection("sessions").document(
            session_id).get().to_dict()
        if not session:
            logging.error("Session not found during test finalization")
            return {"error": "Invalid session ID"}

        scores = session.get("scores", {})
        archetype = determine_archetype(scores)

        output_schema = """{
  "overview": "<Overview summary>",
  "team_work_style": "<Team work style description>",
  "ideal_team_situation": "<Ideal team situation description>",
  "compatible_archetypes": {"<Compatible Archetype 1>": "<Why?>", "<Compatible Archetype 2>": "<Why?>", "...": "..."}
}"""
        prompt = f"""
You are a creative and witty personality archetype expert.
Given these Big Five scores:
{json.dumps(scores, indent=2)}
And the archetype description: {knowledge_base['archetypes'][archetype]['description']},
generate an engaging, personalized profile with four sections:
1. Overview (a fun and long summary with emojis and examples)
2. Team Work Style (how you function in a team)
3. Ideal Team Situation (the environment where you excel)
4. Best Archetypes to work with (Who you work best with)

STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):
{output_schema}

Important Constraints:
- NEVER include markdown formatting or commentary in your response.
- ALWAYS output strictly valid JSON exactly as defined above.
Return only the JSON object as specified.
"""
        logging.info("Sending prompt to GPT-4o for finalizing test results.")
        final_response = client.complete(
            messages=[
                SystemMessage(content=prompt),
                UserMessage(
                    content="Return only the JSON object as specified.")
            ],
            max_tokens=1000,
            temperature=0.9,
            top_p=1.0,
            model=AZURE_OPENAI_MODEL_NAME
        )

        raw_content = final_response.choices[0].message.content.strip()
        logging.debug("Raw GPT finalization response: %s", raw_content)

        try:
            if not raw_content:
                raise ValueError("Empty finalization response")
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
                "suggested_archetype": archetype,
                "archetype_description": response_json
            }
        except (json.JSONDecodeError, ValueError) as json_err:
            logging.error(
                "Error in finalizing test: %s. Falling back to default profile.", json_err)
            fallback_profile = {
                "overview": knowledge_base["archetypes"][archetype]["description"],
                "team_work_style": "You bring creativity and flexibility, thriving in environments that allow exploration and experimentation. You excel at uncovering novel solutions and pushing the boundaries of what's possible.",
                "ideal_team_situation": "Your talents shine brightest in projects that are innovative, dynamic, and offer opportunities to challenge conventional thinking and explore new ideas.",
                "compatible_archetypes": "Visionary (shares creativity and openness to new ideas), Pragmatist (balances your adventurous spirit with practical planning), Catalyst (energizes collaboration)."
            }
            return {
                "test_complete": True,
                "final_scores": scores,
                "suggested_archetype": archetype,
                "archetype_description": fallback_profile
            }
    except HTTPException as e:
        logging.error("Error finalizing test: %s", e)
        return {"error": "Test finalization failed. Please try again."}


def determine_archetype(scores: dict) -> str:
    """
    Determine the best matching personality archetype based on the user's trait scores.

    Compares the user's scores against the criteria for each archetype
    in the knowledge base by assigning numerical thresholds for each
    level (e.g., 'high', 'medium_high', 'medium', 'low') and calculates
    a match score. The archetype with the highest match score is selected.
    If no archetype matches well, "Explorer" is returned as default.

    Args:
        scores (dict): A dictionary mapping trait names to user scores.

    Returns:
        str: The name of the determined personality archetype.
    """
    best_match = None
    highest_match_score = -1

    # Assign numerical values to criteria levels for easier comparison
    level_thresholds = {"high": 5, "medium_high": 4, "medium": 3, "low": 0}

    for archetype, data in knowledge_base["archetypes"].items():
        criteria = data["criteria"]
        match_score = 0

        for trait, level in criteria.items():
            required = level_thresholds[level]
            user_score = scores.get(trait, 0)

            if user_score >= required:
                match_score += (user_score - required) + 1
            else:
                match_score -= (required - user_score)

        if match_score > highest_match_score:
            highest_match_score = match_score
            best_match = archetype

    if highest_match_score <= 0:
        return "Explorer"
    return best_match


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
