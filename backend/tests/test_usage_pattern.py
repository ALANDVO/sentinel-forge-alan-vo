"""Tests for the usage pattern tracker API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestUsagePatternIngest:
    def test_ingest_usage_returns_200(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/usage",
            json={
                "subscription_tier": "free",
                "tokens_consumed": 1000,
                "requests_made": 10,
                "duration_seconds": 60,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_tier"] == "free"
        assert data["tokens_consumed"] == 1000
        assert data["requests_made"] == 10
        assert data["duration_seconds"] == 60
        assert "id" in data
        assert "timestamp" in data
        assert "created_at" in data

    def test_ingest_usage_invalid_tier_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/usage",
            json={
                "subscription_tier": "invalid",
                "tokens_consumed": 1000,
                "requests_made": 10,
                "duration_seconds": 60,
            },
        )
        assert resp.status_code == 422

    def test_ingest_usage_negative_values_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/usage",
            json={
                "subscription_tier": "free",
                "tokens_consumed": -100,
                "requests_made": 10,
                "duration_seconds": 60,
            },
        )
        assert resp.status_code == 422


class TestUsagePatternList:
    def test_list_usage_returns_paginated(self, client: TestClient) -> None:
        # Ingest some data first
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "free", "tokens_consumed": 1000, "requests_made": 10, "duration_seconds": 60},
        )
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "pro", "tokens_consumed": 5000, "requests_made": 50, "duration_seconds": 300},
        )

        resp = client.get("/api/v1/usage")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert data["total"] >= 2

    def test_list_usage_filter_by_tier(self, client: TestClient) -> None:
        resp = client.get("/api/v1/usage?subscription_tier=free")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["subscription_tier"] == "free"


class TestUsageTrends:
    def test_get_trends_returns_data(self, client: TestClient) -> None:
        # Ingest some data for pro tier
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "pro", "tokens_consumed": 1000, "requests_made": 10, "duration_seconds": 60},
        )

        resp = client.get("/api/v1/usage/trends/pro")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            trend = data[0]
            assert "period_start" in trend
            assert "period_end" in trend
            assert "total_tokens" in trend
            assert "total_requests" in trend
            assert "avg_tokens_per_request" in trend
            assert "token_rate_of_change" in trend
            assert "request_rate_of_change" in trend


class TestUsagePrediction:
    def test_get_prediction_returns_200(self, client: TestClient) -> None:
        # Ingest some data for free tier
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "free", "tokens_consumed": 1000, "requests_made": 10, "duration_seconds": 60},
        )

        resp = client.get("/api/v1/usage/prediction/free")
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_tier"] == "free"
        assert "current_period_tokens" in data
        assert "current_period_requests" in data
        assert "tokens_limit" in data
        assert "requests_limit" in data
        assert "tokens_used_pct" in data
        assert "requests_used_pct" in data
        assert "tokens_trend" in data
        assert "requests_trend" in data
        assert data["tokens_limit"] == 100000
        assert data["requests_limit"] == 1000


class TestAlertThresholds:
    def test_get_threshold_returns_default(self, client: TestClient) -> None:
        resp = client.get("/api/v1/usage/threshold/free")
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_tier"] == "free"
        assert data["tokens_warning_threshold"] == 50000
        assert data["tokens_critical_threshold"] == 80000
        assert data["requests_warning_threshold"] == 500
        assert data["requests_critical_threshold"] == 800

    def test_set_threshold_returns_200(self, client: TestClient) -> None:
        resp = client.put(
            "/api/v1/usage/threshold/free",
            json={
                "subscription_tier": "free",
                "tokens_warning_threshold": 40000,
                "tokens_critical_threshold": 70000,
                "requests_warning_threshold": 400,
                "requests_critical_threshold": 700,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tokens_warning_threshold"] == 40000
        assert data["tokens_critical_threshold"] == 70000
        assert data["requests_warning_threshold"] == 400
        assert data["requests_critical_threshold"] == 700

    def test_set_threshold_tier_mismatch_rejected(self, client: TestClient) -> None:
        resp = client.put(
            "/api/v1/usage/threshold/free",
            json={
                "subscription_tier": "pro",
                "tokens_warning_threshold": 40000,
                "tokens_critical_threshold": 70000,
                "requests_warning_threshold": 400,
                "requests_critical_threshold": 700,
            },
        )
        assert resp.status_code == 400


class TestAlertCheck:
    def test_check_alerts_returns_status(self, client: TestClient) -> None:
        # Ingest enough data to trigger warning
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "free", "tokens_consumed": 60000, "requests_made": 600, "duration_seconds": 3600},
        )

        resp = client.get("/api/v1/usage/alerts/free")
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_tier"] == "free"
        assert data["tokens_status"] in ("ok", "warning", "critical")
        assert data["requests_status"] in ("ok", "warning", "critical")
        assert "tokens_warning_triggered" in data
        assert "tokens_critical_triggered" in data
        assert "requests_warning_triggered" in data
        assert "requests_critical_triggered" in data

    def test_check_alerts_ok_status(self, client: TestClient) -> None:
        # Ingest small amount
        client.post(
            "/api/v1/usage",
            json={"subscription_tier": "max", "tokens_consumed": 1000, "requests_made": 10, "duration_seconds": 60},
        )

        resp = client.get("/api/v1/usage/alerts/max")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tokens_status"] == "ok"
        assert data["requests_status"] == "ok"
        assert data["tokens_warning_triggered"] is False
        assert data["requests_warning_triggered"] is False
