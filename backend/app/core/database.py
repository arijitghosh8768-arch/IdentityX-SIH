import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# We will use SQLite by default if PostgreSQL URL is not provided (easier for hackathon dev!)
# For postgres, set DATABASE_URL=postgresql://user:password@localhost/identityx in .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./identityx.db")

# SQLite needs check_same_thread=False, Postgres doesn't
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_sqlite_schema():
    """Add new SQLite columns to an existing local database without deleting data."""
    if "sqlite" not in SQLALCHEMY_DATABASE_URL:
        return

    columns = {column["name"] for column in inspect(engine).get_columns("documents")}
    if "extracted_fields" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE documents ADD COLUMN extracted_fields TEXT"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
