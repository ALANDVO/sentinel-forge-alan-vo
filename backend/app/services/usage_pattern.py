"""Usage pattern tracking service for Claude Code usage data."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.schemas import (
    AlertCheckResponse,
    AlertThresholdRequest,
    AlertThresholdResponse,
    UsagePatternRequest,
    UsagePatternResponse,
    UsagePatternListResponse,
    UsagePredictionResponse,
    UsageTrendResponse,
)
from app.services.database import UsageAlertThreshold, UsagePattern, DEFAULT_THRESHOLDS


# Subscription tier limits (monthly)
TIER_LIMITS = {
    "free": {"tokens": 100000, "requests": 1000},
    "pro": {"tokens": 1000000, "requests": 10000},
    "max": {"tokens": 4000000, "requests": 40000},
}


class UsagePatternService:
    """Service for tracking and analyzing usage patterns."""

    def __init__(self, db: Session):
        self.db = db
        self._ensure_default_thresholds()

    def _ensure_default_thresholds(self) -> None:
        """Ensure default alert thresholds exist for all tiers."""
        for tier, thresholds in DEFAULT_THRESHOLDS.items():
            existing = self.db.execute(
                select(UsageAlertThreshold).where(
                    UsageAlertThreshold.subscription_tier == tier
                )
            ).scalar_one_or_none()
            if not existing:
                threshold = UsageAlertThreshold(
                    subscription_tier=tier, **thresholds
                )
                self.db.add(threshold)
        self.db.commit()

    def ingest_usage(self, request: UsagePatternRequest) -> UsagePatternResponse:
        """Ingest a new usage data point."""
        timestamp = request.timestamp or datetime.now(timezone.utc)
        pattern = UsagePattern(
            subscription_tier=request.subscription_tier,
            tokens_consumed=request.tokens_consumed,
            requests_made=request.requests_made,
            duration_seconds=request.duration_seconds,
            timestamp=timestamp,
        )
        self.db.add(pattern)
        self.db.commit()
        self.db.refresh(pattern)
        return UsagePatternResponse.model_validate(pattern)

    def get_usage(
        self,
        subscription_tier: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> UsagePatternListResponse:
        """Get paginated usage patterns."""
        query = select(UsagePattern).order_by(UsagePattern.timestamp.desc())
        if subscription_tier:
            query = query.where(UsagePattern.subscription_tier == subscription_tier)

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        ) or 0

        records = self.db.execute(
            query.offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()

        pages = math.ceil(total / page_size) if page_size > 0 else 1

        return UsagePatternListResponse(
            items=[UsagePatternResponse.model_validate(r) for r in records],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_trends(
        self,
        subscription_tier: str,
        days: int = 30,
        bucket_hours: int = 24,
    ) -> list[UsageTrendResponse]:
        """Get historical usage trends with rate-of-change metrics."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Get raw data points
        records = self.db.execute(
            select(UsagePattern)
            .where(
                UsagePattern.subscription_tier == subscription_tier,
                UsagePattern.timestamp >= since,
            )
            .order_by(UsagePattern.timestamp.asc())
        ).scalars().all()

        if not records:
            return []

        # Bucket by time interval
        bucket_size = timedelta(hours=bucket_hours)
        buckets: dict[datetime, list[UsagePattern]] = {}
        for record in records:
            bucket_start = record.timestamp.replace(
                minute=0, second=0, microsecond=0
            )
            # Round down to bucket boundary
            hours_since_epoch = int(bucket_start.timestamp() // 3600)
            bucket_hours_aligned = hours_since_epoch // bucket_hours * bucket_hours
            bucket_key = datetime.fromtimestamp(
                bucket_hours_aligned * 3600, tz=timezone.utc
            )
            buckets.setdefault(bucket_key, []).append(record)

        # Build trend points
        sorted_buckets = sorted(buckets.keys())
        trends = []

        for i, bucket_start in enumerate(sorted_buckets):
            bucket_records = buckets[bucket_start]
            bucket_end = bucket_start + bucket_size

            total_tokens = sum(r.tokens_consumed for r in bucket_records)
            total_requests = sum(r.requests_made for r in bucket_records)
            avg_tokens_per_request = (
                total_tokens / total_requests if total_requests > 0 else 0.0
            )

            # Calculate rate of change compared to previous bucket
            if i > 0:
                prev_bucket = sorted_buckets[i - 1]
                prev_records = buckets[prev_bucket]
                prev_tokens = sum(r.tokens_consumed for r in prev_records)
                prev_requests = sum(r.requests_made for r in prev_records)

                token_rate_of_change = (
                    (total_tokens - prev_tokens) / prev_tokens * 100
                    if prev_tokens > 0
                    else 0.0
                )
                request_rate_of_change = (
                    (total_requests - prev_requests) / prev_requests * 100
                    if prev_requests > 0
                    else 0.0
                )
            else:
                token_rate_of_change = 0.0
                request_rate_of_change = 0.0

            trends.append(
                UsageTrendResponse(
                    period_start=bucket_start,
                    period_end=bucket_end,
                    total_tokens=total_tokens,
                    total_requests=total_requests,
                    avg_tokens_per_request=avg_tokens_per_request,
                    token_rate_of_change=token_rate_of_change,
                    request_rate_of_change=request_rate_of_change,
                )
            )

        return trends

    def predict_exhaustion(
        self, subscription_tier: str, lookback_days: int = 7
    ) -> UsagePredictionResponse:
        """Predict when subscription limits will be hit based on recent usage."""
        since = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        # Get current period usage (last 30 days as billing period approximation)
        period_start = datetime.now(timezone.utc) - timedelta(days=30)
        period_records = self.db.execute(
            select(UsagePattern)
            .where(
                UsagePattern.subscription_tier == subscription_tier,
                UsagePattern.timestamp >= period_start,
            )
            .order_by(UsagePattern.timestamp.asc())
        ).scalars().all()

        current_tokens = sum(r.tokens_consumed for r in period_records)
        current_requests = sum(r.requests_made for r in period_records)

        limits = TIER_LIMITS.get(subscription_tier, {"tokens": 0, "requests": 0})
        tokens_limit = limits["tokens"]
        requests_limit = limits["requests"]

        tokens_used_pct = (
            (current_tokens / tokens_limit * 100) if tokens_limit > 0 else 0.0
        )
        requests_used_pct = (
            (current_requests / requests_limit * 100) if requests_limit > 0 else 0.0
        )

        # Get recent trend for prediction
        recent_records = self.db.execute(
            select(UsagePattern)
            .where(
                UsagePattern.subscription_tier == subscription_tier,
                UsagePattern.timestamp >= since,
            )
            .order_by(UsagePattern.timestamp.asc())
        ).scalars().all()

        if len(recent_records) < 2:
            return UsagePredictionResponse(
                subscription_tier=subscription_tier,
                current_period_tokens=current_tokens,
                current_period_requests=current_requests,
                tokens_limit=tokens_limit,
                requests_limit=requests_limit,
                tokens_used_pct=tokens_used_pct,
                requests_used_pct=requests_used_pct,
                tokens_trend="stable",
                requests_trend="stable",
            )

        # Calculate daily average rates
        days_span = max(
            1,
            (recent_records[-1].timestamp - recent_records[0].timestamp).days,
        )
        daily_tokens = sum(r.tokens_consumed for r in recent_records) / days_span
        daily_requests = sum(r.requests_made for r in recent_records) / days_span

        # Determine trend direction
        if len(recent_records) >= 3:
            first_half = recent_records[: len(recent_records) // 2]
            second_half = recent_records[len(recent_records) // 2 :]
            first_tokens = sum(r.tokens_consumed for r in first_half)
            second_tokens = sum(r.tokens_consumed for r in second_half)
            first_requests = sum(r.requests_made for r in first_half)
            second_requests = sum(r.requests_made for r in second_half)

            tokens_trend = (
                "increasing"
                if second_tokens > first_tokens * 1.1
                else "decreasing" if second_tokens < first_tokens * 0.9 else "stable"
            )
            requests_trend = (
                "increasing"
                if second_requests > first_requests * 1.1
                else "decreasing" if second_requests < first_requests * 0.9 else "stable"
            )
        else:
            tokens_trend = "stable"
            requests_trend = "stable"

        # Predict exhaustion
        remaining_tokens = tokens_limit - current_tokens
        remaining_requests = requests_limit - current_requests

        estimated_tokens_exhaustion = None
        estimated_requests_exhaustion = None
        days_until_tokens_exhaustion = None
        days_until_requests_exhaustion = None

        if daily_tokens > 0 and remaining_tokens > 0:
            days_until_tokens_exhaustion = remaining_tokens / daily_tokens
            estimated_tokens_exhaustion = datetime.now(
                timezone.utc
            ) + timedelta(days=days_until_tokens_exhaustion)

        if daily_requests > 0 and remaining_requests > 0:
            days_until_requests_exhaustion = remaining_requests / daily_requests
            estimated_requests_exhaustion = datetime.now(
                timezone.utc
            ) + timedelta(days=days_until_requests_exhaustion)

        return UsagePredictionResponse(
            subscription_tier=subscription_tier,
            current_period_tokens=current_tokens,
            current_period_requests=current_requests,
            tokens_limit=tokens_limit,
            requests_limit=requests_limit,
            tokens_used_pct=tokens_used_pct,
            requests_used_pct=requests_used_pct,
            estimated_tokens_exhaustion=estimated_tokens_exhaustion,
            estimated_requests_exhaustion=estimated_requests_exhaustion,
            days_until_tokens_exhaustion=days_until_tokens_exhaustion,
            days_until_requests_exhaustion=days_until_requests_exhaustion,
            tokens_trend=tokens_trend,
            requests_trend=requests_trend,
        )

    def get_threshold(
        self, subscription_tier: str
    ) -> Optional[AlertThresholdResponse]:
        """Get alert threshold configuration for a tier."""
        threshold = self.db.execute(
            select(UsageAlertThreshold).where(
                UsageAlertThreshold.subscription_tier == subscription_tier
            )
        ).scalar_one_or_none()

        if not threshold:
            return None

        return AlertThresholdResponse.model_validate(threshold)

    def set_threshold(
        self, request: AlertThresholdRequest
    ) -> AlertThresholdResponse:
        """Set or update alert threshold configuration for a tier."""
        threshold = self.db.execute(
            select(UsageAlertThreshold).where(
                UsageAlertThreshold.subscription_tier == request.subscription_tier
            )
        ).scalar_one_or_none()

        if threshold:
            threshold.tokens_warning_threshold = request.tokens_warning_threshold
            threshold.tokens_critical_threshold = request.tokens_critical_threshold
            threshold.requests_warning_threshold = request.requests_warning_threshold
            threshold.requests_critical_threshold = request.requests_critical_threshold
        else:
            threshold = UsageAlertThreshold(**request.model_dump())
            self.db.add(threshold)

        self.db.commit()
        self.db.refresh(threshold)
        return AlertThresholdResponse.model_validate(threshold)

    def check_alerts(
        self, subscription_tier: str
    ) -> Optional[AlertCheckResponse]:
        """Check current usage against alert thresholds."""
        threshold = self.db.execute(
            select(UsageAlertThreshold).where(
                UsageAlertThreshold.subscription_tier == subscription_tier
            )
        ).scalar_one_or_none()

        if not threshold:
            return None

        # Get current period usage
        period_start = datetime.now(timezone.utc) - timedelta(days=30)
        period_records = self.db.execute(
            select(UsagePattern)
            .where(
                UsagePattern.subscription_tier == subscription_tier,
                UsagePattern.timestamp >= period_start,
            )
        ).scalars().all()

        current_tokens = sum(r.tokens_consumed for r in period_records)
        current_requests = sum(r.requests_made for r in period_records)

        tokens_warning_triggered = (
            current_tokens >= threshold.tokens_warning_threshold
        )
        tokens_critical_triggered = (
            current_tokens >= threshold.tokens_critical_threshold
        )
        requests_warning_triggered = (
            current_requests >= threshold.requests_warning_threshold
        )
        requests_critical_triggered = (
            current_requests >= threshold.requests_critical_threshold
        )

        tokens_status = "ok"
        if tokens_critical_triggered:
            tokens_status = "critical"
        elif tokens_warning_triggered:
            tokens_status = "warning"

        requests_status = "ok"
        if requests_critical_triggered:
            requests_status = "critical"
        elif requests_warning_triggered:
            requests_status = "warning"

        return AlertCheckResponse(
            subscription_tier=subscription_tier,
            current_tokens=current_tokens,
            current_requests=current_requests,
            tokens_status=tokens_status,
            requests_status=requests_status,
            tokens_warning_threshold=threshold.tokens_warning_threshold,
            tokens_critical_threshold=threshold.tokens_critical_threshold,
            requests_warning_threshold=threshold.requests_warning_threshold,
            requests_critical_threshold=threshold.requests_critical_threshold,
            tokens_warning_triggered=tokens_warning_triggered,
            tokens_critical_triggered=tokens_critical_triggered,
            requests_warning_triggered=requests_warning_triggered,
            requests_critical_triggered=requests_critical_triggered,
        )
