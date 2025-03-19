import time
import json
import uuid
import re
import os
import logging
import random
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from fastapi import HTTPException
from backend.app.firebase import db
from backend.app.models import UserResponse, InterestSelection

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


def load_knowledge_base():
    kb_ref = db.collection("knowledge_base").document("big_five_test").get()
    if not kb_ref.exists:
        raise RuntimeError("Knowledge base not found in Firestore!")
    return kb_ref.to_dict()


knowledge_base = load_knowledge_base()


def create_session():
    session_id = str(uuid.uuid4())
    # Initialize trait_counts to track how many times each trait has been addressed.
    trait_counts = {trait: 0 for trait in knowledge_base["traits"]}
    session_data = {
        "start_time": time.time(),
        "responses": {},
        "scores": {trait: 0 for trait in knowledge_base["traits"]},
        "paused": False,
        "interests": [],
        "trait_counts": trait_counts,
        "optional_responses": {},
        "response_times": {},
        "current_question": None
    }
    db.collection("sessions").document(session_id).set(session_data)
    logging.info(f"Session created: {session_id}")
    return session_id


def start_test():
    session_id = str(uuid.uuid4())
    trait_counts = {trait: 0 for trait in knowledge_base["traits"]}
    session_data = {
        "start_time": time.time(),
        "responses": {},
        "interests": [],
        "scores": {trait: 0 for trait in knowledge_base["traits"]},
        "trait_counts": trait_counts,
        "paused": False,
        "current_question": None
    }
    db.collection("sessions").document(session_id).set(session_data)
    return {"session_id": session_id, "next_question": generate_next_question(session_id)}


def select_interests(selection: InterestSelection):
    session_ref = db.collection("sessions").document(selection.session_id)
    session = session_ref.get().to_dict()

    if not session:
        logging.error("Invalid session ID during interest selection.")
        return {"error": "Invalid session ID"}

    # Update session with interests
    session_ref.update({"interests": selection.interests})
    next_question = generate_next_question(selection.session_id)

    if not next_question:
        logging.error("No next question generated after interest selection.")
        return {"error": "Failed to generate next question", "next_question": None}

    return {"message": "Interests updated successfully.", "next_question": next_question}


def submit_response(response: UserResponse):
    try:
        logging.info(f"Submitting response: {response}")
        session_ref = db.collection("sessions").document(response.session_id)
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
        session["responses"][response.question_id] = response.answer

        # Update the score and trait count based on the current question stored in the session
        current_question = session.get("current_question")
        if current_question and "trait" in current_question:
            trait = current_question["trait"]
            # Look up the option score using the answer key (if multiple-choice)
            selected_key = response.answer.strip().lower()
            if current_question.get("type") == "multiple-choice":
                option = current_question["options"].get(selected_key)
                if option:
                    session["scores"][trait] += option["score"]
            # Update trait counts
            trait_counts = session.get(
                "trait_counts", {t: 0 for t in knowledge_base["traits"]})
            trait_counts[trait] = trait_counts.get(trait, 0) + 1
            session["trait_counts"] = trait_counts

            # Calculate response time safely
            current_time = time.time()
            last_time = session.get(
                "last_question_time", session["start_time"])
            response_time = current_time - last_time
            # Only update response_times if a valid question_id exists
            if response.question_id:
                session["response_times"][response.question_id] = response_time
            else:
                logging.warning(
                    "Received a response with no valid question_id; skipping response time update.")
            session["last_question_time"] = current_time

        session_ref.update({
            "scores": session["scores"],
            "responses": session["responses"],
            "trait_counts": session["trait_counts"],
            "response_times": session["response_times"],
            "last_question_time": session["last_question_time"]
        })

        # Check for test timeout (3 minutes = 180 seconds)
        if time.time() - session["start_time"] > 180 and not session["paused"]:
            session_ref.update({"paused": True})
            return {"test_paused": True, "message": "Time is up! Continue or get your results?"}

        next_question = generate_next_question(response.session_id)
        if not next_question:
            return finalize_test(response.session_id)

        return {"next_question": next_question}
    except Exception as e:
        logging.error(f"Error in submit_response: {str(e)}")
        return {"error": "Internal server error while processing your response."}


def generate_next_question(session_id):
    """
    Generate the next question using GPT-4o.
    The question is concise, personalized, and targeted by trait, without embedding options in the text.
    The output must be strictly valid JSON (without markdown formatting or extra commentary).
    Freeform questions occur rarely (10% probability) and when used, must be simple and clear.
    """
    try:
        session_doc = db.collection("sessions").document(session_id)
        session = session_doc.get().to_dict()
        if not session:
            logging.error("Session not found during question generation.")
            return {"error": "Invalid session data"}

        question_count = len(session.get("responses", {}))
        if question_count >= 10:
            logging.info("Maximum question count reached. Finalizing test.")
            return finalize_test(session_id)

        trait_counts = session.get(
            "trait_counts", {t: 0 for t in knowledge_base["traits"]})
        target_trait = None
        for trait, count in trait_counts.items():
            if count < 2:
                target_trait = trait
                break
        if not target_trait:
            target_trait = min(trait_counts, key=trait_counts.get)

        # Limit freeform text questions to 10% probability.
        question_type = "multiple-choice" if random.random() < 0.9 else "optional-freeform"

        extra_context = ""
        if random.random() < 0.5:
            extra_context = f"Also, refer to this knowledge base info: {json.dumps(knowledge_base)}"

        # Define JSON schema instructions.
        if question_type == "multiple-choice":
            prompt_schema = f"""
            {{
              "next_question": {{
                "id": "generated_question_{session_id}_{question_count}",
                "trait": "{target_trait}",
                "type": "multiple-choice",
                "text": "<A concise question that does NOT include any option letters or texts>",
                "options": {{
                  "a": {{"text": "<Option A text>", "score": <score_value>}},
                  "b": {{"text": "<Option B text>", "score": <score_value>}},
                  "c": {{"text": "<Option C text>", "score": <score_value>}}
                }}
              }}
            }}
            """
        else:
            prompt_schema = f"""
            {{
              "next_question": {{
                "id": "optional_freeform_{session_id}_{question_count}",
                "trait": "{target_trait}",
                "type": "optional-freeform",
                "text": "<A clear and simple freeform question that is easy to answer and does NOT include any options>"
              }}
            }}
            """

        system_prompt = f"""
        You are a creative, witty AI specialized in personality tests using the Big Five framework.
        The user has answered {question_count} out of 10 questions.
        Current trait counts: {json.dumps(trait_counts)}
        Target Trait: {target_trait}
        User Interests: {json.dumps(session['interests'])}
        Previous Responses: {json.dumps(session['responses'])}
        {extra_context}
        Generate one unique, concise, and personalized question for Question {question_count + 1} of 10.
        For a multiple-choice question, ensure that the question text does not include any of the option letters or texts.
        Output must be strictly valid JSON exactly matching the following schema and nothing else (no markdown formatting or commentary):
        {prompt_schema}
        """
        # IMPORTANT: Instruct GPT to output ONLY JSON.
        logging.info("Sending prompt to GPT-4o for question generation.")
        response = client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(
                    content="Return only the JSON object as specified.")
            ],
            max_tokens=500,
            temperature=0.8,
            top_p=1.0,
            model=AZURE_OPENAI_MODEL_NAME
        )

        raw_content = response.choices[0].message.content.strip()
        logging.debug(f"Raw GPT Response: {raw_content}")

        # Remove potential markdown formatting (e.g., triple backticks).
        cleaned_json = raw_content.replace(
            "```json", "").replace("```", "").strip()

        try:
            response_content = json.loads(cleaned_json)
            next_question = response_content.get("next_question", {})
            if not next_question:
                logging.error("GPT response JSON missing 'next_question' key.")
                return {"error": "Invalid AI response format"}
            session_doc.update({"current_question": next_question})
            return next_question
        except json.JSONDecodeError as json_err:
            logging.error(
                f"JSON parsing error: {str(json_err)}. Response content: {cleaned_json}")
            return {"error": "Failed to parse AI response JSON"}
    except Exception as e:
        logging.error(
            f"Azure OpenAI API error in generate_next_question: {str(e)}")
        return {"error": "AI generation failed. Please try again."}


def finalize_test(session_id):
    """
    Finalize the personality test by generating a personalized archetype summary using GPT-4o.
    If the GPT response cannot be parsed as valid JSON, fall back to a default profile in the same format.
    """
    try:
        session = db.collection("sessions").document(
            session_id).get().to_dict()
        if not session:
            logging.error("Session not found during test finalization.")
            return {"error": "Invalid session ID"}

        scores = session.get("scores", {})
        archetype = determine_archetype(scores)

        system_prompt = f"""
        You are a creative and witty personality archetype expert.
        Given these Big Five scores:
        {json.dumps(scores, indent=2)}
        And the archetype description: "{knowledge_base["archetypes"][archetype]["description"]}",
        generate an engaging, personalized profile with three sections:
        1. Overview (a fun and concise summary with emojis)
        2. Team Work Style (how you function in a team)
        3. Ideal Team Situation (the environment where you excel)

        Return ONLY a valid JSON object EXACTLY in the following format, with no additional text, explanation, or markdown:
        {{
          "overview": "<Overview summary>",
          "team_work_style": "<Team work style description>",
          "ideal_team_situation": "<Ideal team situation description>"
        }}

        Make sure your output starts with '{{' and ends with '}}'.
        """
        logging.info("Sending prompt to GPT-4o for finalizing test results.")
        response = client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(
                    content="Return only the JSON object as specified.")
            ],
            max_tokens=200,
            temperature=0.9,
            top_p=1.0,
            model=AZURE_OPENAI_MODEL_NAME
        )

        raw_content = response.choices[0].message.content.strip()
        logging.debug(f"Raw GPT finalization response: {raw_content}")

        try:
            if not raw_content:
                raise ValueError("Empty finalization response")
            response_json = json.loads(raw_content)
            required_keys = ["overview",
                             "team_work_style", "ideal_team_situation"]
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
                f"Error in finalizing test: {str(json_err)}. Falling back to default profile.")
            # Fallback: return a JSON object with the same keys.
            fallback_profile = {
                "overview": knowledge_base["archetypes"][archetype]["description"],
                "team_work_style": "You work best in balanced teams, contributing your unique ideas while valuing collaboration.",
                "ideal_team_situation": "You excel in environments that are dynamic, creative, and supportive."
            }
            return {
                "test_complete": True,
                "final_scores": scores,
                "suggested_archetype": archetype,
                "archetype_description": fallback_profile
            }
    except Exception as e:
        logging.error(f"Error finalizing test: {str(e)}")
        return {"error": "Test finalization failed. Please try again."}


def determine_archetype(scores):
    """
    Determine the user's archetype based on their scores.
    The archetype with the closest matching scores to its criteria is selected.
    """
    best_match = None
    highest_match_score = -1

    # Assign numerical values to criteria levels for easier comparison
    level_thresholds = {"high": 4, "medium": 2}

    for archetype, data in knowledge_base["archetypes"].items():
        criteria = data["criteria"]
        match_score = 0

        for trait, required_level in criteria.items():
            user_score = scores.get(trait, 0)
            required_score = level_thresholds.get(required_level, 2)

            # Calculate how closely user matches the required level
            if user_score >= required_score:
                match_score += (user_score - required_score) + \
                    1  # Reward matches & higher scores
            else:
                # Penalize mismatches gently
                match_score -= (required_score - user_score)

        if match_score > highest_match_score:
            highest_match_score = match_score
            best_match = archetype

    # If no good match, default to "Explorer"
    if highest_match_score <= 0:
        return "Explorer"

    return best_match


def continue_test(session_id: str):
    session_ref = db.collection("sessions").document(session_id)
    session = session_ref.get().to_dict()
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    if not session["paused"]:
        raise HTTPException(status_code=400, detail="Test is not paused")
    session_ref.update({"paused": False})
    next_question = generate_next_question(session_id)
    if not next_question:
        return finalize_test(session_id)
    return {"next_question": next_question}


def get_results(session_id: str):
    return finalize_test(session_id)
