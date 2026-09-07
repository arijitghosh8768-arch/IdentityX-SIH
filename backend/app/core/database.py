import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

settings = get_settings()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQLite needs check_same_thread=False, Postgres doesn't
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Modern declarative base for all ORM models."""
    pass


def ensure_sqlite_schema():
    """Add new SQLite columns to an existing local database without deleting data."""
    if "sqlite" not in SQLALCHEMY_DATABASE_URL:
        return

    inspector = inspect(engine)

    # Documents table migrations
    if inspector.has_table("documents"):
        columns = {column["name"] for column in inspector.get_columns("documents")}
        migrations = {
            "extracted_fields": "ALTER TABLE documents ADD COLUMN extracted_fields TEXT",
            "created_at": "ALTER TABLE documents ADD COLUMN created_at TIMESTAMP",
        }
        with engine.begin() as connection:
            for col_name, sql in migrations.items():
                if col_name not in columns:
                    connection.execute(text(sql))

    # Verification reports table migrations
    if inspector.has_table("verification_reports"):
        columns = {column["name"] for column in inspector.get_columns("verification_reports")}
        migrations = {
            "updated_at": "ALTER TABLE verification_reports ADD COLUMN updated_at TIMESTAMP",
            "notes": "ALTER TABLE verification_reports ADD COLUMN notes TEXT",
            "risk_level": "ALTER TABLE verification_reports ADD COLUMN risk_level TEXT DEFAULT 'UNKNOWN'",
        }
        with engine.begin() as connection:
            for col_name, sql in migrations.items():
                if col_name not in columns:
                    connection.execute(text(sql))


def get_db():
    """FastAPI dependency: yields a database session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
