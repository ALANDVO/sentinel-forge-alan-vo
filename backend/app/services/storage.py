"""Storage service: CRUD operations for analysis records and audit log."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.analyzer import AnalysisResult
from app.services.database import AnalysisRecord, AuditLog


class AnalysisStorage:
    """Storage service for saved analysis results."""

    def __init__(self, db: Session):
        self.db = db

    def save_from_result(self, result: AnalysisResult, user: str | None = None) -> AnalysisRecord:
        """Persist an :class:`AnalysisResult` to the database.

        Transactional: if the insert fails, the session is rolled back.
        """
        findings_data = [
            {
                "rule_id": f.rule_id,
                "rule_name": f.rule_name,
                "severity": f.severity,
                "line": f.line,
                "column": f.column,
                "message": f.message,
                "suggestion": f.suggestion,
                "code_snippet": f.code_snippet,
            }
            for f in result.findings
        ]
        record = AnalysisRecord(
            id=result.analysis_id,
            mod_name=result.mod_name,
            language=result.language,
            code=result.code,
            findings_json=json.dumps(findings_data),
            total_findings=result.summary.total,
            critical_count=result.summary.critical,
            warning_count=result.summary.warning,
            info_count=result.summary.info,
            duration_ms=result.duration_ms,
            created_at=result.created_at,
            updated_at=result.created_at,
        )
        self.db.add(record)
        self.db.add(
            AuditLog(action="analysis_save", resource_id=record.id, user=user)
        )
        try:
            self.db.commit()
            self.db.refresh(record)
        except Exception:
            self.db.rollback()
            raise
        return record

    def get(self, analysis_id: str) -> AnalysisRecord | None:
        """Retrieve a single record by ID."""
        return self.db.get(AnalysisRecord, analysis_id)

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        severity: str | None = None,
        mod_name: str | None = None,
    ) -> tuple[list[AnalysisRecord], int]:
        """Return paginated, optionally filtered records and total count."""
        stmt = select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc())

        if severity:
            severity_map = {"critical": "critical_count", "warning": "warning_count", "info": "info_count"}
            col_name = severity_map.get(severity)
            if col_name:
                col = getattr(AnalysisRecord, col_name)
                stmt = stmt.where(col > 0)

        if mod_name:
            stmt = stmt.where(
                AnalysisRecord.mod_name.like(f"%{mod_name}%",)
            )

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(total_stmt).scalar() or 0

        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        records = self.db.execute(stmt).scalars().all()
        return records, total

    def record_to_dict(self, record: AnalysisRecord) -> dict[str, Any]:
        """Serialize an AnalysisRecord to a dict suitable for API response."""
        findings = json.loads(record.findings_json) if record.findings_json else []
        return {
            "id": record.id,
            "mod_name": record.mod_name,
            "language": record.language,
            "code": record.code,
            "findings": findings,
            "summary": {
                "total": record.total_findings,
                "critical": record.critical_count,
                "warning": record.warning_count,
                "info": record.info_count,
            },
            "created_at": record.created_at,
            "duration_ms": record.duration_ms,
        }

    def record_to_summary(self, record: AnalysisRecord) -> dict[str, Any]:
        """Serialize an AnalysisRecord to a lightweight list-view dict."""
        return {
            "id": record.id,
            "mod_name": record.mod_name,
            "language": record.language,
            "code_length": len(record.code) if record.code else 0,
            "total_findings": record.total_findings,
            "critical": record.critical_count,
            "warning": record.warning_count,
            "info": record.info_count,
            "created_at": record.created_at,
            "duration_ms": record.duration_ms,
        }