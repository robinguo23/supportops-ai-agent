from sqlalchemy import text

from app.db.models import Base
from app.db.session import engine


def init_db() -> None:
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()

    Base.metadata.create_all(bind=engine)