from fastapi import APIRouter
from backend.app.services import start_test, submit_response, continue_test, get_results, select_interests
from backend.app.models import UserResponse, InterestSelection
from pydantic import BaseModel

router = APIRouter()


class SessionRequest(BaseModel):
    session_id: str


@router.post("/start-test/")
async def start():
    return start_test()


@router.post("/select-interests/")
async def select_interests_api(selection: InterestSelection):
    return select_interests(selection)


@router.post("/submit-response/")
async def submit(response: UserResponse):
    return submit_response(response)


@router.post("/continue-test/")
async def continue_quiz(request: SessionRequest):
    return continue_test(request.session_id)


@router.post("/get-results/")
async def results(request: SessionRequest):
    return get_results(request.session_id)
