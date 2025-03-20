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
from firebase import db
from models import UserResponse, InterestSelection

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

with open("system_prompt.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()


response = client.complete(
    messages=[SystemMessage(content=system_prompt)],
    max_tokens=500,
    temperature=0.8,
    top_p=1.0,
    model=AZURE_OPENAI_MODEL_NAME
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
        "optional_responses": {},
        "response_times": {},
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
        trait = current_question.get("trait") if current_question else None

        if current_question:
            selected_key = response.answer.strip().lower()

            if current_question["type"] == "multiple-choice":
                option = current_question["options"].get(selected_key)
                if option:
                    session["scores"][trait] += option["score"]

            elif current_question["type"] == "optional-freeform":
                # Evaluate freeform response via GPT-4o dynamically
                eval_prompt = f"""
                You are evaluating a freeform personality test answer based on the Big Five trait: '{trait}'.

                User's Answer: "{response.answer}"

                Briefly analyze this answer, considering tone, sentiment, and keywords to assign a numeric score (0 to 5):
                    - 0: Not indicative
                    - 5: Highly indicative

                Output STRICTLY in this JSON format (no markdown, no commentary):
                {{"score": <number>, "reason": "<brief explanation>"}}
                """

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
                session["optional_responses"][response.question_id] = eval_json["reason"]

            # Update trait counts
            session["trait_counts"][trait] += 1

            # Track response time
            current_time = time.time()
            last_time = session.get(
                "last_question_time", session["start_time"])
            response_time = current_time - last_time
            session["last_question_time"] = current_time

            session_ref.update(session)

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

        trait_counts = session.get("trait_counts", {})
        trait_needs = {trait: 2 - count for trait,
                       count in trait_counts.items()}
        target_trait = max(trait_needs, key=trait_needs.get)

        # Limit freeform text questions to 10% probability.
        question_type = "multiple-choice" if random.random() < 0.9 else "optional-freeform"

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

        user_interests = json.dumps(session["interests"]),
        previous_responses = json.dumps(session["responses"]),
        current_trait_scores = json.dumps(session["scores"]),
        questions_answered_count = question_count,
        trait_counts = json.dumps(trait_counts)

        system_prompt = f"""
        **User Profile (Always Reference Clearly):**
        # array of strings provided by the user at the start.
        - **User Interests**: {user_interests}
        - **Previous User Responses**: {previous_responses}
        - **Current Trait Scores**: {current_trait_scores}
        - **Target Trait**: {target_trait}
        - **Questions Answered**: {questions_answered_count} of 10
        - **Trait Counts So Far**: {trait_counts}

        ## 🚨 **STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):**
        {prompt_schema}

        **Important Constraints (ALWAYS FOLLOW THESE):**
        - NEVER include markdown formatting or commentary in your response.
        - NEVER repeat previously asked questions or similar variations.
        - NEVER embed answer options or letters within question texts.
        - ALWAYS output strictly valid JSON exactly as defined by {prompt_schema}.
        - ALWAYS clearly personalize each question around user interests provided.

        You must adhere exactly to these instructions to ensure a scientifically robust, engaging, adaptive, and fully personalized personality assessment.
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
            # top_p=1.0,
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
        generate an engaging, personalized profile with three sections:
        1. Overview(a fun and long summary with emojis and examples)
        2. Team Work Style(how you function in a team)
        3. Ideal Team Situation(the environment where you excel)
        4. Best Archetypes to work with (Who do you work best with)

        # 🚨 **STRICT JSON RESPONSE FORMAT (MUST MATCH EXACTLY):**
        {output_schema}

         **Important Constraints(ALWAYS FOLLOW THESE): **
        - NEVER include markdown formatting or commentary in your response.
        - ALWAYS output strictly valid JSON exactly as defined by {output_schema}.
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
        print(f"Raw Content: {raw_content}")
        logging.debug('Raw GPT finalization response: %s' % raw_content)

        try:
            if not raw_content:
                raise ValueError("Empty finalization response")
            cleaned_json = raw_content.replace(
                "```json", "").replace("```", "").strip()
            print(f"Cleaned JSON: {cleaned_json}")
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
                f"Error in finalizing test: {str(json_err)}. Falling back to default profile.")
            fallback_profile = {
                "overview": f"Oops.. seems like there was some parsing error. \
                    While we fix this, let me tell you something I tell everyone.\n\n \
                        {knowledge_base['archetypes'][archetype]['description']}",
                "team_work_style": "You bring creativity and flexibility, thriving in environments that allow exploration and experimentation. You excel at uncovering novel solutions and pushing the boundaries of what's possible.",
                "ideal_team_situation": "Your talents shine brightest in projects that are innovative, dynamic, and offer opportunities to challenge conventional thinking and explore new ideas.",
                "compatible_archetypes": "Visionary (shares creativity and openness to new ideas, sparking innovation together), Pragmatist (balances your adventurous spirit with practical planning), Catalyst (energizes collaboration, complementing your adaptability and openness)."
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
    session_ref.update({"paused": False, "start_time": time.time()})
    next_question = generate_next_question(session_id)
    if not next_question:
        return finalize_test(session_id)
    return {"next_question": next_question}


def get_results(session_id: str):
    return finalize_test(session_id)
