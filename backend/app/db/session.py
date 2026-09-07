import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def get_database_url() -> str | URL:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        if database_url.startswith("postgresql://"):
            return database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1,
            )

        return database_url

    database_host = os.getenv("PGHOST")

    if database_host:
        return URL.create(
            drivername="postgresql+psycopg",
            username=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            host=database_host,
            port=int(os.getenv("PGPORT", "5432")),
            database=os.getenv("PGDATABASE", "supportops"),
        )

    return (
        "postgresql+psycopg://supportops:"
        "supportops_dev_password@localhost:5432/supportops"
    )


engine = create_engine(get_database_url())

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
