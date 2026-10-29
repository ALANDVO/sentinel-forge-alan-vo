"""SQLAlchemy database setup and ORM models for persistent storage."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


class AnalysisRecord(Base):
    """Persistent record of a saved analysis."""

    __tablename__ = "analysis_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mod_name = Column(String(200), nullable=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    findings_json = Column(Text, nullable=False)
    total_findings = Column(Integer, nullable=False, default=0)
    critical_count = Column(Integer, nullable=False, default=0)
    warning_count = Column(Integer, nullable=False, default=0)
    info_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class UsagePattern(Base):
    """Persistent record of a usage pattern entry."""

    __tablename__ = "usage_patterns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_tier = Column(String(50), nullable=False)
    tokens_consumed = Column(Integer, nullable=False, default=0)
    requests_made = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Integer, nullable=False, default=0)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class UsageAlertThreshold(Base):
    """Threshold configuration for usage alerts per subscription tier."""

    __tablename__ = "usage_alert_thresholds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_tier = Column(String(50), nullable=False, unique=True)
    tokens_warning_threshold = Column(Integer, nullable=False)
    tokens_critical_threshold = Column(Integer, nullable=False)
    requests_warning_threshold = Column(Integer, nullable=False)
    requests_critical_threshold = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Default alert thresholds per subscription tier
DEFAULT_THRESHOLDS = {
    "free": {
        "tokens_warning_threshold": 50000,
        "tokens_critical_threshold": 80000,
        "requests_warning_threshold": 500,
        "requests_critical_threshold": 800,
    },
    "pro": {
        "tokens_warning_threshold": 500000,
        "tokens_critical_threshold": 800000,
        "requests_warning_threshold": 5000,
        "requests_critical_threshold": 8000,
    },
    "max": {
        "tokens_warning_threshold": 2000000,
        "tokens_critical_threshold": 3200000,
        "requests_warning_threshold": 20000,
        "requests_critical_threshold": 32000,
    },
}

class AuditLog(Base):
    """Audit log for significant operations."""

    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    user = Column(String(100), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class Database:
    """Database manager with engine, session factory, and CRUD helpers."""

    def __init__(self, database_url: str):
        self._url = database_url
        if database_url.startswith("sqlite"):
            self._engine = create_engine(
                database_url, connect_args={"check_same_thread": False}
            )
        else:
            self._engine = create_engine(database_url)
        self._SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

    def create_tables(self) -> None:
        """Create all tables. Safe to call on every startup."""
        Base.metadata.create_all(self._engine)

    def dispose(self) -> None:
        """Dispose of the connection pool."""
        self._engine.dispose()

    @property
    def engine(self):
        return self._engine

    @property
    def SessionLocal(self):
        return self._SessionLocal

    def get_session(self) -> Session:
        """Return a new database session (caller manages lifecycle)."""
        db = self._SessionLocal()
        try:
            yield db
        finally:
            db.close()


_default_db: Database | None = None


def set_default_database(db: Database) -> None:
    """Set the default database instance for get_db dependency."""
    global _default_db
    _default_db = db


def get_default_database() -> Database:
    """Get the default database instance."""
    if _default_db is None:
        raise RuntimeError("Database not initialized. Call set_default_database() first.")
    return _default_db


def get_db() -> Session:
    """FastAPI dependency for getting a database session."""
    db = get_default_database()._SessionLocal()
    try:
        yield db
    finally:
        db.close()
