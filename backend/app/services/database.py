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
