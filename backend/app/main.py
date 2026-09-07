import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.api.security import router as security_router
from app.db.init_db import init_db
from app.db.session import SessionLocal


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [
        origin.strip()
        for origin in configured_origins.split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SupportOps AI Agent API",
    description="Backend API for the SupportOps AI Agent project.",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "supportops-ai-agent-backend",
    }


@app.get("/db/health")
def database_health_check():
    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "postgresql",
        }
    finally:
        db.close()


app.include_router(chat_router)
app.include_router(security_router)
