import streamlit as st
import requests
import os
import json
import time
from api import start_test, submit_response, select_interests, continue_test, get_results

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="Personality Test", layout="centered")

if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "step" not in st.session_state:
    st.session_state["step"] = "welcome"
if "test_start_time" not in st.session_state:
    st.session_state["test_start_time"] = None
if "responses" not in st.session_state:
    st.session_state["responses"] = []

# --- Callback function for submitting an answer ---


def submit_answer(question, answer, option_mapping=None):
    if not question.get("id") or not answer:
        st.error("❌ Error: Missing question ID or answer.")
        return

    # Determine answer_key based on question type.
    if question.get("type") == "multiple-choice":
        answer_key = option_mapping.get(answer)
    else:
        answer_key = answer.strip()

    # Submit answer to backend.
    resp = submit_response(
        st.session_state["session_id"],
        question["id"],
        answer_key
    )

    # Update responses.
    st.session_state["responses"].append({question["id"]: answer_key})

    # Process backend response.
    if "test_paused" in resp and resp["test_paused"]:
        st.session_state["step"] = "paused"
    elif "error" in resp:
        st.error(f"❌ API Error: {resp['error']}")
        return
    elif "next_question" not in resp or not resp["next_question"]:
        st.error("❌ Error: No next question received. Please check the backend.")
        st.write("🛠️ API Response:", resp)
        return
    else:
        st.session_state["next_question"] = resp["next_question"]
        st.session_state["step"] = "questions"

    st.rerun()  # Force immediate re-run after state update

# --- UI Code ---


# 1️⃣ Welcome Screen
if st.session_state["step"] == "welcome":
    st.title("🎭 Welcome to the Personality Test!")
    st.write("Discover your personality archetype in just a few minutes.")
    if st.button("Start Test"):
        session = start_test()
        st.session_state["session_id"] = session["session_id"]
        st.session_state["test_start_time"] = time.time()  # record timer start
        st.session_state["step"] = "interests"
        st.rerun()

# 2️⃣ Interest Selection
elif st.session_state["step"] == "interests":
    st.title("🔍 Select Your Interests")
    default_interests = [
        "Fantasy (Magical Quests)",
        "Science Fiction (Futuristic Worlds)",
        "Adventure (Travel & Exploration)",
        "Business & Entrepreneurship",
        "Art & Creativity",
        "Gaming & Esports",
        "Pop Culture (Movies, TV, Anime)",
        "Technology & Innovation",
        "Music & Performing Arts",
        "Sports & Fitness",
        "Other"
    ]
    selected_interests = st.multiselect(
        "Pick your top interests:", default_interests)
    custom_interest = st.text_input("Or add a custom interest:")

    interests = selected_interests.copy()
    if custom_interest.strip():
        interests.append(custom_interest.strip())

    if st.button("Continue"):
        response = select_interests(st.session_state["session_id"], interests)
        if not response or "error" in response:
            st.error(f"❌ API Error: {response.get('error', 'Unknown error')}")
            st.stop()
        if "next_question" not in response or not response["next_question"]:
            st.error(
                "❌ Error: No next question received. Please check the backend.")
            st.write("🛠️ API Response:", response)
            st.stop()
        st.session_state["next_question"] = response["next_question"]
        st.session_state["step"] = "questions"
        st.rerun()

# 3️⃣ Questions
elif st.session_state["step"] == "questions":
    st.title("🧠 Answer the Questions")

    responses_count = len(st.session_state.get("responses", []))
    # If we've reached 10 responses, skip to results.
    if responses_count >= 10:
        st.session_state["step"] = "results"
        st.rerun()

    question_number = responses_count + 1
    progress_value = responses_count / 10.0  # progress value between 0 and 1
    st.progress(progress_value)
    st.markdown(f"**Question {question_number} of 10**")

    if st.session_state.get("test_start_time"):
        elapsed = time.time() - st.session_state["test_start_time"]
        remaining = max(0, 180 - int(elapsed))
        minutes, seconds = divmod(remaining, 60)
        st.markdown(f"**Time Remaining:** {minutes:02d}:{seconds:02d}")

    if "next_question" not in st.session_state or not st.session_state["next_question"]:
        st.error("❌ No next question found. Please restart the test.")
        st.stop()

    question = st.session_state["next_question"]

    # If the returned question has no type, assume the test is complete.
    if not question.get("type"):
        st.session_state["step"] = "results"
        st.rerun()

    # Display based on question type.
    if question.get("type") == "multiple-choice":
        options = question.get("options", {})
        if not isinstance(options, dict):
            st.error(
                "❌ Error: Options are not in the expected format. Please restart the test.")
            st.stop()

        # Do not pre-select any option (no default value)
        option_mapping = {}
        radio_options = []
        for key, option in options.items():
            display_text = option["text"]
            option_mapping[display_text] = key
            radio_options.append(display_text)

        st.subheader(question.get("text", ""))
        answer_display = st.radio(
            "Select your answer:", radio_options, key=f"q_{question['id']}")

    elif question.get("type") == "optional-freeform":
        st.subheader(question.get("text", ""))
        answer_display = st.text_input(
            "Your answer:", key=f"q_{question['id']}")

    if st.button("Submit Answer"):
        submit_answer(question, answer_display, option_mapping if question.get(
            "type") == "multiple-choice" else None)

# 4️⃣ Pause Screen
elif st.session_state["step"] == "paused":
    st.title("⏳ Time's Up!")
    st.write(
        "Your test was paused after 3 minutes. Would you like to continue or get your results now?")
    if st.button("Continue Test"):
        continue_test(st.session_state["session_id"])
        st.session_state["step"] = "questions"
        st.rerun()
    if st.button("Get Results"):
        st.session_state["step"] = "results"
        st.rerun()

# 5️⃣ Results
elif st.session_state["step"] == "results":
    result = get_results(st.session_state["session_id"])
    archetype = result.get("suggested_archetype", "Unknown")
    description = result.get("archetype_description",
                             "No description available.")

    st.title(f"🎭 Your Personality Archetype \n\n")
    st.markdown(f"### {archetype}")
    st.markdown("---")

    if isinstance(description, dict):
        st.markdown("#### ✨ Overview")
        st.write(description.get("overview", "No overview available."))
        st.markdown("#### 🤝 How You Work in a Team")
        st.write(description.get("team_work_style",
                 "No team work style available."))
        st.markdown("#### 🚀 Where You Excel")
        st.write(description.get("ideal_team_situation",
                 "No ideal team situation available."))
    else:
        # Fallback for a plain text description.
        st.write(description)
