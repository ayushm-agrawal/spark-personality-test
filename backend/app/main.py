from fastapi import FastAPI
from backend.app.api import router

app = FastAPI(title="Personality Test API")

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
