from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.db.init_db import init_db
from app.db.session import SessionLocal


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
    allow_origins=["http://localhost:5173"],
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