import os
import time
import streamlit as st
from api import start_test, submit_response, select_interests, continue_test, get_results
from PIL import Image

im = Image.open("favicon.ico")
logo = Image.open("ception-logo.png")
# Set the page configuration with local favicon
st.set_page_config(
    page_title="Ception: Discover Your Team Archetype",
    page_icon=im,
    layout="centered",
    menu_items={"Report a Bug": "mailto:ayush@ception.one"}
)
st.logo(logo, size="large", link="https://personna-v01.ception.one")

# Inject custom CSS for a Typeform-inspired dark theme and layout improvements.
st.markdown(
    """
    <style>
    /* Dark background and light text */
    .reportview-container {
        background: #1e1e1e;
        color: #f5f5f5;
    }
    .sidebar .sidebar-content {
        background: #2c2c2c;
    }
    /* Custom font and spacing for titles and headers */
    h1, h2, h3, h4 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Center content in main container */
    .main .block-container {
        margin-left: auto;
        margin-right: auto;
    }
    /* Logo in top left corner */
    .logo {
        position: fixed;
        top: 10px;
        left: 10px;
        width: 120px;
        z-index: 1000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Set up session state if not already set.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = None
if "step" not in st.session_state:
    st.session_state["step"] = "welcome"
if "test_start_time" not in st.session_state:
    st.session_state["test_start_time"] = None
if "responses" not in st.session_state:
    st.session_state["responses"] = []


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


# 1️⃣ Welcome Screen
if st.session_state["step"] == "welcome":
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 2rem; color: #f5f5f5;">
          <h1 style="font-size: 3.5em; font-weight: bold; margin-bottom: 0.5em;">
            🎭 Welcome to Ception
          </h1>
          <p style="font-size: 1.4em; margin-bottom: 2em;">
            Uncover your unique team archetype and discover where you truly shine!
            Our fun, interactive personality test is designed to ignite your creative spark and reveal your ideal role in any team.
          </p>

        </div>
        """,
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Start Test", key="start-test", help="Click to start your test"):
            session = start_test()
            st.session_state["session_id"] = session["session_id"]
            st.session_state["step"] = "interests"
            st.rerun()

# 2️⃣ Interest Selection
elif st.session_state["step"] == "interests":
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem;">
          <h2>🔍 Select Your Interests</h2>
          <p style="font-size:1.1em;">We’ll use this to personalize your test. Choose from the list or add your own!</p>
        </div>
        """,
        unsafe_allow_html=True
    )
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
        "Pick your top interests:", default_interests, help="These are high level areas. You can select or add detailed low level interest below!")
    custom_interest = st.text_input(
        "Or add a custom interest:", help="You can be descriptive", placeholder="I love coding")

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
        st.session_state["test_start_time"] = time.time()  # record timer start
        st.session_state["step"] = "questions"
        st.rerun()

# 3️⃣ Questions
elif st.session_state["step"] == "questions":
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem;">
          <h2 style="color: #FFCC00; font-weight: bold;">Time to shine!</h2>
          <h3 style="color: #f5f5f5;">Answer the question below:</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    responses_count = len(st.session_state.get("responses", []))
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
    answer_display = ""

    if not question.get("type"):
        st.session_state["step"] = "results"
        st.rerun()

    if question.get("type") == "multiple-choice":
        options = question.get("options", {})
        if not isinstance(options, dict):
            st.error(
                "❌ Error: Options are not in the expected format. Please restart the test.")
            st.stop()
        option_mapping = {}
        radio_options = []
        for key, option in options.items():
            display_text = option["text"]
            option_mapping[display_text] = key
            radio_options.append(display_text)

        st.subheader(question.get("text", ""))
        answer_display = st.radio(
            "Select your answer:", radio_options, index=None, key=f"q_{question['id']}")
    elif question.get("type") == "optional-freeform":
        st.subheader(question.get("text", ""))
        answer_display = st.text_input(
            "Your answer:", key=f"q_{question['id']}")

    if st.button("Submit Answer"):
        submit_answer(question, answer_display, option_mapping if question.get(
            "type") == "multiple-choice" else None)

# 4️⃣ Pause Screen
elif st.session_state["step"] == "paused":
    st.markdown(
        """
        <div style="text-align: center; margin-top: 2rem;">
          <h2>⏳ Time's Up!</h2>
          <p>Your test was paused after 3 minutes.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
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
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 2rem;">
          <h1 style="font-size: 2.5em; margin-bottom: 0.1em;">🎭 Your Personality Archetype</h1>
          <h3 style="font-weight: normal; color: #4CAF50;">{archetype}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)
    st.balloons()
    if isinstance(description, dict):
        st.markdown("#### ✨ Overview")
        st.write(description.get("overview", "No overview available."))
        st.markdown("#### 🤝 How You Work in a Team")
        st.write(description.get("team_work_style",
                 "No team work style available."))
        st.markdown("#### 🚀 Where You Excel")
        st.write(description.get("ideal_team_situation",
                 "No ideal team situation available."))
        st.markdown("#### Your Compatible Archetypes")
        st.write(description.get("compatible_archetypes"))
    else:
        st.write(description)
