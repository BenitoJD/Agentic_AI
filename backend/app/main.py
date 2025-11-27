"""FastAPI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import agents, chat, files, kpi


def create_app() -> FastAPI:
    app = FastAPI(title="Multi-Agent Hackathon Backend")
    app.include_router(chat.router)
    app.include_router(files.router)
    app.include_router(agents.router)
    app.include_router(kpi.router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    async def healthcheck():
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()

