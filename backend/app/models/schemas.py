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


class UsagePatternRequest(BaseModel):
    """Request body for ingesting usage data."""

    subscription_tier: str = Field(..., pattern="^(free|pro|max)$")
    tokens_consumed: int = Field(..., ge=0)
    requests_made: int = Field(..., ge=0)
    duration_seconds: int = Field(..., ge=0)
    timestamp: Optional[datetime] = None


class UsagePatternResponse(BaseModel):
    """Response for a single usage pattern record."""

    id: str
    subscription_tier: str
    tokens_consumed: int
    requests_made: int
    duration_seconds: int
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class UsagePatternListResponse(BaseModel):
    """Paginated list of usage pattern records."""

    items: List[UsagePatternResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UsageTrendResponse(BaseModel):
    """Historical usage trend data point."""

    period_start: datetime
    period_end: datetime
    total_tokens: int
    total_requests: int
    avg_tokens_per_request: float
    token_rate_of_change: float
    request_rate_of_change: float


class UsagePredictionResponse(BaseModel):
    """Prediction of when subscription limits will be hit."""

    subscription_tier: str
    current_period_tokens: int
    current_period_requests: int
    tokens_limit: int
    requests_limit: int
    tokens_used_pct: float
    requests_used_pct: float
    estimated_tokens_exhaustion: Optional[datetime] = None
    estimated_requests_exhaustion: Optional[datetime] = None
    days_until_tokens_exhaustion: Optional[float] = None
    days_until_requests_exhaustion: Optional[float] = None
    tokens_trend: str  # "increasing", "decreasing", "stable"
    requests_trend: str


class AlertThresholdRequest(BaseModel):
    """Request body for setting alert thresholds."""

    subscription_tier: str = Field(..., pattern="^(free|pro|max)$")
    tokens_warning_threshold: int = Field(..., ge=0)
    tokens_critical_threshold: int = Field(..., ge=0)
    requests_warning_threshold: int = Field(..., ge=0)
    requests_critical_threshold: int = Field(..., ge=0)


class AlertThresholdResponse(BaseModel):
    """Response for alert threshold configuration."""

    id: str
    subscription_tier: str
    tokens_warning_threshold: int
    tokens_critical_threshold: int
    requests_warning_threshold: int
    requests_critical_threshold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertCheckResponse(BaseModel):
    """Response for checking current usage against alert thresholds."""

    subscription_tier: str
    current_tokens: int
    current_requests: int
    tokens_status: str  # "ok", "warning", "critical"
    requests_status: str
    tokens_warning_threshold: int
    tokens_critical_threshold: int
    requests_warning_threshold: int
    requests_critical_threshold: int
    tokens_warning_triggered: bool
    tokens_critical_triggered: bool
    requests_warning_triggered: bool
    requests_critical_triggered: bool