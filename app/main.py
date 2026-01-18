"""
main.py

FastAPI application entrypoint.
"""

from fastapi import FastAPI

from app.api.jobs import router as jobs_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Content Analysis Service",
        version="1.0.0",
        description="Async AI-powered content moderation backend",
    )

    app.include_router(jobs_router)

    return app


app = create_app()
