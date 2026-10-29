"""Usage pattern tracking API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.schemas import (
    AlertCheckResponse,
    AlertThresholdRequest,
    AlertThresholdResponse,
    UsagePatternListResponse,
    UsagePatternRequest,
    UsagePatternResponse,
    UsagePredictionResponse,
    UsageTrendResponse,
)
from app.services.database import get_db
from app.services.usage_pattern import UsagePatternService

router = APIRouter()


@router.post("/api/v1/usage", response_model=UsagePatternResponse)
def ingest_usage(
    request: UsagePatternRequest,
    db: Session = Depends(get_db),
) -> UsagePatternResponse:
    """Ingest a new usage data point."""
    service = UsagePatternService(db)
    return service.ingest_usage(request)


@router.get("/api/v1/usage", response_model=UsagePatternListResponse)
def list_usage(
    subscription_tier: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
) -> UsagePatternListResponse:
    """Get paginated usage patterns."""
    service = UsagePatternService(db)
    return service.get_usage(subscription_tier, page, page_size)


@router.get("/api/v1/usage/trends/{subscription_tier}", response_model=list[UsageTrendResponse])
def get_trends(
    subscription_tier: str,
    days: int = 30,
    bucket_hours: int = 24,
    db: Session = Depends(get_db),
) -> list[UsageTrendResponse]:
    """Get historical usage trends with rate-of-change metrics."""
    service = UsagePatternService(db)
    return service.get_trends(subscription_tier, days, bucket_hours)


@router.get("/api/v1/usage/prediction/{subscription_tier}", response_model=UsagePredictionResponse)
def get_prediction(
    subscription_tier: str,
    lookback_days: int = 7,
    db: Session = Depends(get_db),
) -> UsagePredictionResponse:
    """Predict when subscription limits will be hit based on recent usage."""
    service = UsagePatternService(db)
    return service.predict_exhaustion(subscription_tier, lookback_days)


@router.get("/api/v1/usage/threshold/{subscription_tier}", response_model=AlertThresholdResponse)
def get_threshold(
    subscription_tier: str,
    db: Session = Depends(get_db),
) -> AlertThresholdResponse:
    """Get alert threshold configuration for a tier."""
    service = UsagePatternService(db)
    result = service.get_threshold(subscription_tier)
    if not result:
        raise HTTPException(status_code=404, detail="Threshold not found")
    return result


@router.put("/api/v1/usage/threshold/{subscription_tier}", response_model=AlertThresholdResponse)
def set_threshold(
    subscription_tier: str,
    request: AlertThresholdRequest,
    db: Session = Depends(get_db),
) -> AlertThresholdResponse:
    """Set or update alert threshold configuration for a tier."""
    if subscription_tier != request.subscription_tier:
        raise HTTPException(
            status_code=400, detail="Subscription tier mismatch"
        )
    service = UsagePatternService(db)
    return service.set_threshold(request)


@router.get("/api/v1/usage/alerts/{subscription_tier}", response_model=AlertCheckResponse)
def check_alerts(
    subscription_tier: str,
    db: Session = Depends(get_db),
) -> AlertCheckResponse:
    """Check current usage against alert thresholds."""
    service = UsagePatternService(db)
    result = service.check_alerts(subscription_tier)
    if not result:
        raise HTTPException(status_code=404, detail="Threshold not found")
    return result
