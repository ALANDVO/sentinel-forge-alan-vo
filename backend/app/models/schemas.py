"""Pydantic schemas for the Sentinel Forge API."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for the analyze endpoint."""

    code: str = Field(..., min_length=1, max_length=100_000)
    language: str = Field(default="typescript", pattern=r"^(typescript|javascript)$")
    mod_name: Optional[str] = Field(default=None, max_length=200)


class FindingResponse(BaseModel):
    """A single finding from the analysis engine."""

    rule_id: str
    rule_name: str
    severity: str
    line: int
    column: int
    message: str
    suggestion: str
    code_snippet: str


class SummaryResponse(BaseModel):
    """Aggregate counts of findings by severity."""

    total: int
    critical: int
    warning: int
    info: int


class AnalysisResponse(BaseModel):
    """Full analysis result returned by the analyze endpoint."""

    analysis_id: str
    code: str
    language: str
    mod_name: Optional[str]
    findings: list[FindingResponse]
    summary: SummaryResponse
    created_at: datetime
    duration_ms: float


class RuleInfoResponse(BaseModel):
    """Public metadata for a single analysis rule."""

    id: str
    name: str
    severity: str
    description: str
    message: str
    suggestion: str


class AnalysisRecordResponse(BaseModel):
    """A lightweight analysis record for list views."""

    id: str
    mod_name: Optional[str]
    language: str
    code_length: int
    total_findings: int
    critical: int
    warning: int
    info: int
    created_at: datetime
    duration_ms: float


class AnalysisListResponse(BaseModel):
    """Paginated list of analysis records."""

    items: list[AnalysisRecordResponse]
    total: int
    page: int
    per_page: int
    pages: int


class SaveAnalysisRequest(BaseModel):
    """Request body for saving an analysis result."""

    analysis_id: str
    code: str
    language: str
    mod_name: Optional[str] = None
    findings: list[FindingResponse]
    summary: SummaryResponse
    duration_ms: float


class SavedAnalysisResponse(BaseModel):
    """Detailed analysis record with full findings."""

    id: str
    mod_name: Optional[str]
    language: str
    code: str
    findings: list[FindingResponse]
    summary: SummaryResponse
    created_at: datetime
    duration_ms: float


class AuthVerifyResponse(BaseModel):
    """Response for auth verification endpoint."""

    authenticated: bool
    user: Optional[str] = None
    role: Optional[str] = None