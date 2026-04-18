import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api import router, limiter

app = FastAPI(title="Personality Test API")

# Attach the shared rate limiter and its default exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


# Static origins: local dev + production custom domains.
default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "https://personality.ception.one",
    "https://ception.one",
]
# Extra origins (comma-separated) can be provided via env for Vercel preview URLs etc.
extra_origins = _parse_origins(os.environ.get("EXTRA_CORS_ORIGINS"))

# Optional tight regex for a specific preview-deploy pattern, e.g.
#   CORS_ORIGIN_REGEX=^https://spark-personality-test(-[a-z0-9]+)*-ayushm-agrawal\.vercel\.app$
cors_origin_regex = os.environ.get("CORS_ORIGIN_REGEX")

app.add_middleware(
    CORSMiddleware,
    allow_origins=default_origins + extra_origins,
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Ception Personality Test API", "docs": "/docs"}


@app.get("/health")
def health():
    """Health check for Azure."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
