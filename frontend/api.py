import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = 60  # seconds


def start_test():
    """
    Initiates a new test session by calling the backend endpoint.

    Returns:
        dict: JSON response containing the session id and next question.

    Raises:
        HTTPError: If the response status code is not 200.
        JSONDecodeError: If the response JSON cannot be parsed.
    """
    response = requests.post(
        f"{BACKEND_URL}/start-test/", timeout=DEFAULT_TIMEOUT)

    # Debug the response before calling .json()
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        response.raise_for_status()

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Failed to decode JSON:", response.text)
        raise e


def select_interests(session_id, interests):
    """
    Sends the selected interests to the backend and retrieves the next question.

    Args:
        session_id (str): The session identifier.
        interests (list): A list of interests selected by the user.

    Returns:
        dict: JSON response containing a message and the next question.
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/select-interests/",
            json={"session_id": session_id, "interests": interests},
            timeout=DEFAULT_TIMEOUT
        )

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return {"error": f"Backend error: {response.status_code}"}

        json_response = response.json()

        if not json_response:
            print("❌ API returned empty response.")
            return {"error": "Empty response"}

        if "error" in json_response:
            return {"error": json_response["error"]}

        return json_response

    except requests.exceptions.RequestException as e:
        print(f"❌ Network/API Error: {str(e)}")
        return {"error": "Failed to connect to backend"}
    except HTTPException as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return {"error": "Unexpected error occurred"}


def submit_response(session_id, question_id=None, answer=None):
    """
    Submits a user's answer to a question and returns the backend's response.

    Args:
        session_id (str): The session identifier.
        question_id (str, optional): The question identifier.
        answer (str, optional): The user's answer.

    Returns:
        dict: JSON response from the backend.

    Raises:
        JSONDecodeError: If the backend response is not valid JSON.
    """
    resp = requests.post(
        f"{BACKEND_URL}/submit-response/",
        json={"session_id": session_id,
              "question_id": question_id, "answer": answer},
        timeout=DEFAULT_TIMEOUT
    )

    try:
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        print(
            f"Backend returned non-JSON response: {resp.status_code} - {resp.text}")
        raise


def continue_test(session_id):
    """
    Sends a request to the backend to continue a paused test session.

    Args:
        session_id (str): The session identifier.

    Returns:
        Response object from the backend (if any).
    """
    return requests.post(
        f"{BACKEND_URL}/continue-test/",
        json={"session_id": session_id},
        timeout=DEFAULT_TIMEOUT
    )


def get_results(session_id):
    """
    Retrieves the test results from the backend.

    Args:
        session_id (str): The session identifier.

    Returns:
        dict: JSON response containing the test results.
    """
    return requests.post(
        f"{BACKEND_URL}/get-results/",
        json={"session_id": session_id},
        timeout=DEFAULT_TIMEOUT
    ).json()


def collect_feedback(rating, timestamp, session_id, archetype):
    """
    Sends user feedback to the backend for storage.

    Args:
        rating (int): The star rating provided by the user.
        timestamp (float): The timestamp when the feedback was submitted.
        session_id (str): The session identifier.
        archetype (str): The determined personality archetype for the session.

    Returns:
        dict: JSON response from the backend regarding feedback submission.
    """
    return requests.post(
        f"{BACKEND_URL}/collect-feedback/",
        json={
            "rating": rating,
            "timestamp": timestamp,
            "session_id": session_id,
            "archetype": archetype
        },
        timeout=DEFAULT_TIMEOUT
    ).json()
