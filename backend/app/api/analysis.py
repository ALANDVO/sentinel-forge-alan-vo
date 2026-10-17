"""API routes for mod analysis and saved-analysis CRUD."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_current_user, get_db, require_auth
from app.core.analyzer import AnalysisResult, AnalysisSummary, Finding, analyze
from app.core.rules import get_rules, rule_to_dict
from app.models.schemas import (
    AnalysisListResponse,
    AnalysisRecordResponse,
    AnalysisResponse,
    AnalyzeRequest,
    FindingResponse,
    RuleInfoResponse,
    SaveAnalysisRequest,
    SavedAnalysisResponse,
    SummaryResponse,
)
from app.services.storage import AnalysisStorage

router = APIRouter()


def _result_to_response(result: AnalysisResult) -> AnalysisResponse:
    """Convert an AnalysisResult to the API response schema."""
    return AnalysisResponse(
        analysis_id=result.analysis_id,
        code=result.code,
        language=result.language,
        mod_name=result.mod_name,
        findings=[FindingResponse(**asdict(f)) for f in result.findings],
        summary=SummaryResponse(**asdict(result.summary)),
        created_at=result.created_at,
        duration_ms=result.duration_ms,
    )


@router.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_code(request: AnalyzeRequest) -> AnalysisResponse:
    """Analyze TypeScript/JavaScript mod source code for safety issues.

    This endpoint does not require authentication — it is the core
    stateless analysis workflow.
    """
    result = analyze(request.code, request.language, request.mod_name)
    return _result_to_response(result)


@router.get("/api/v1/rules", response_model=list[RuleInfoResponse])
async def list_rules() -> list[RuleInfoResponse]:
    """List all available static analysis rules."""
    return [RuleInfoResponse(**rule_to_dict(r)) for r in get_rules()]


@router.post("/api/v1/analyses", response_model=AnalysisRecordResponse, status_code=status.HTTP_201_CREATED)
async def save_analysis(
    request: SaveAnalysisRequest,
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_auth),
) -> AnalysisRecordResponse:
    """Save an analysis result to persistent storage.

    Requires authentication (demo mode auto-auths localhost).
    """
    result = AnalysisResult(
        analysis_id=request.analysis_id,
        code=request.code,
        language=request.language,
        mod_name=request.mod_name,
        findings=[
            Finding(
                rule_id=f.rule_id,
                rule_name=f.rule_name,
                severity=f.severity,
                line=f.line,
                column=f.column,
                message=f.message,
                suggestion=f.suggestion,
                code_snippet=f.code_snippet,
            )
            for f in request.findings
        ],
        summary=AnalysisSummary(
            total=request.summary.total,
            critical=request.summary.critical,
            warning=request.summary.warning,
            info=request.summary.info,
        ),
        created_at=datetime.now(timezone.utc),
        duration_ms=request.duration_ms,
    )
    storage = AnalysisStorage(db)
    record = storage.save_from_result(result, user=ctx.user)
    return AnalysisRecordResponse(
        id=record.id,
        mod_name=record.mod_name,
        language=record.language,
        code_length=len(record.code) if record.code else 0,
        total_findings=record.total_findings,
        critical=record.critical_count,
        warning=record.warning_count,
        info=record.info_count,
        created_at=record.created_at,
        duration_ms=record.duration_ms,
    )


@router.get("/api/v1/analyses", response_model=AnalysisListResponse)
async def list_analyses(
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    severity: str | None = Query(None, pattern=r"^(critical|warning|info)$"),
    mod_name: str | None = Query(None, max_length=200),
    db: Session = Depends(get_db),
    ctx: AuthContext = Depends(require_auth),
) -> AnalysisListResponse:
    """List saved analyses with pagination and filtering.

    Requires authentication (demo mode auto-auths localhost).
    """
    storage = AnalysisStorage(db)
    records, total = storage.list(page, per_page, severity, mod_name)
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return AnalysisListResponse(
        items=[
            AnalysisRecordResponse(
                id=r.id,
                mod_name=r.mod_name,
                language=r.language,
                code_length=len(r.code) if r.code else 0,
                total_findings=r.total_findings,
                critical=r.critical_count,
                warning=r.warning_count,
                info=r.info_count,
                created_at=r.created_at,
                duration_ms=r.duration_ms,
            )
            for r in records
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/api/v1/analyses/{analysis_id}", response_model=SavedAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    ctx: AuthContext | None = Depends(get_current_user),
) -> SavedAnalysisResponse:
    """Retrieve a saved analysis by ID.

    Requires authentication (demo mode auto-auths localhost).
    """
    if ctx is None or not ctx.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    storage = AnalysisStorage(db)
    record = storage.get(analysis_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found.",
        )
    data = storage.record_to_dict(record)
    return SavedAnalysisResponse(
        id=data["id"],
        mod_name=data["mod_name"],
        language=data["language"],
        code=data["code"],
        findings=[FindingResponse(**f) for f in data["findings"]],
        summary=SummaryResponse(**data["summary"]),
        created_at=data["created_at"],
        duration_ms=data["duration_ms"],
    )