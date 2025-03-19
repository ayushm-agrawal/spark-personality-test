import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def start_test():
    response = requests.post(f"{BACKEND_URL}/start-test/")

    # Debug the response before calling .json()
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        response.raise_for_status()  # Raise error if response is not 200

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Failed to decode JSON:", response.text)
        raise e


def select_interests(session_id, interests):
    try:
        response = requests.post(
            f"{BACKEND_URL}/select-interests/",
            json={"session_id": session_id, "interests": interests}
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
    except Exception as e:
        print(f"❌ Unexpected Error: {str(e)}")
        return {"error": "Unexpected error occurred"}


def submit_response(session_id, question_id=None, answer=None):
    resp = requests.post(
        f"{BACKEND_URL}/submit-response/",
        json={"session_id": session_id,
              "question_id": question_id, "answer": answer}
    )

    try:
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        print(
            f"Backend returned non-JSON response: {resp.status_code} - {resp.text}")
        raise


def continue_test(session_id):
    requests.post(f"{BACKEND_URL}/continue-test/",
                  json={"session_id": session_id})


def get_results(session_id):
    return requests.post(f"{BACKEND_URL}/get-results/", json={"session_id": session_id}).json()
