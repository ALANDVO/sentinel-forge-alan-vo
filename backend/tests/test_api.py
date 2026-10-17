"""Integration tests for the API layer (real HTTP boundary via TestClient)."""
from __future__ import annotations

import pytest
from fastapi import status

from backend.tests.samples import SAFE_MOD, UNSAFE_MOD


@pytest.mark.usefixtures("demo_settings")
class TestAnalyzeEndpoint:
    def test_analyze_returns_200(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": "const cp = require('child_process');"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["critical"] >= 1

    def test_analyze_safe_code(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": SAFE_MOD})
        assert resp.status_code == 200
        assert resp.json()["summary"]["total"] == 0

    def test_analyze_empty_code_rejected(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": ""})
        assert resp.status_code == 422

    def test_analyze_code_too_long_rejected(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": "x" * 100_001})
        assert resp.status_code == 422

    def test_analyze_default_language(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": SAFE_MOD})
        assert resp.json()["language"] == "typescript"

    def test_analyze_with_mod_name(self, client) -> None:
        resp = client.post(
            "/api/v1/analyze",
            json={"code": SAFE_MOD, "mod_name": "my-mod", "language": "javascript"},
        )
        assert resp.json()["mod_name"] == "my-mod"
        assert resp.json()["language"] == "javascript"

    def test_analyze_findings_have_required_fields(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD})
        data = resp.json()
        for f in data["findings"]:
            assert "rule_id" in f
            assert "rule_name" in f
            assert "severity" in f
            assert "line" in f
            assert "column" in f
            assert "message" in f
            assert "suggestion" in f
            assert "code_snippet" in f

    def test_analyze_multiple_findings(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD})
        findings = resp.json()["findings"]
        assert len(findings) >= 4  # RL-001, RL-002, RL-003, RL-006

    def test_analyze_uses_correct_endpoint(self, client) -> None:
        resp = client.get("/api/v1/analyze")
        assert resp.status_code == 405  # GET not allowed on POST-only route


class TestRulesEndpoint:
    def test_list_rules_returns_200(self, client) -> None:
        resp = client.get("/api/v1/rules")
        assert resp.status_code == 200

    def test_list_rules_returns_six(self, client) -> None:
        resp = client.get("/api/v1/rules")
        assert len(resp.json()) == 6

    def test_list_rules_have_ids(self, client) -> None:
        resp = client.get("/api/v1/rules")
        ids = [r["id"] for r in resp.json()]
        assert "RL-001" in ids
        assert "RL-004" in ids  # flickering / accessibility

    def test_list_rules_have_severities(self, client) -> None:
        resp = client.get("/api/v1/rules")
        for rule in resp.json():
            assert rule["severity"] in ("critical", "warning", "info")


@pytest.mark.usefixtures("demo_settings")
class TestSavedAnalysesDemo:
    def test_save_analysis_succeeds(self, client) -> None:
        # Analyze first
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD, "mod_name": "test-mod"})
        analysis = resp.json()

        # Save it
        save_req = {
            "analysis_id": analysis["analysis_id"],
            "code": analysis["code"],
            "language": analysis["language"],
            "mod_name": analysis["mod_name"],
            "findings": analysis["findings"],
            "summary": analysis["summary"],
            "duration_ms": analysis["duration_ms"],
        }
        resp = client.post("/api/v1/analyses", json=save_req)
        assert resp.status_code == 201
        saved = resp.json()
        assert saved["mod_name"] == "test-mod"
        assert saved["total_findings"] == analysis["summary"]["total"]

    def test_list_analyses_returns_saved(self, client) -> None:
        # Save one
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD, "mod_name": "list-test"})
        analysis = resp.json()
        save_req = {
            "analysis_id": analysis["analysis_id"],
            "code": analysis["code"],
            "language": analysis["language"],
            "mod_name": analysis["mod_name"],
            "findings": analysis["findings"],
            "summary": analysis["summary"],
            "duration_ms": analysis["duration_ms"],
        }
        client.post("/api/v1/analyses", json=save_req)

        # List
        resp = client.get("/api/v1/analyses")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_list_analyses_pagination(self, client) -> None:
        resp = client.get("/api/v1/analyses?page=1&per_page=5")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 5
        assert data["page"] == 1
        assert data["per_page"] == 5

    def test_list_analyses_severity_filter(self, client) -> None:
        resp = client.get("/api/v1/analyses?severity=critical")
        assert resp.status_code == 200

    def test_get_analysis_detail(self, client) -> None:
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD, "mod_name": "detail-test"})
        analysis = resp.json()
        save_req = {
            "analysis_id": analysis["analysis_id"],
            "code": analysis["code"],
            "language": analysis["language"],
            "mod_name": analysis["mod_name"],
            "findings": analysis["findings"],
            "summary": analysis["summary"],
            "duration_ms": analysis["duration_ms"],
        }
        client.post("/api/v1/analyses", json=save_req)

        resp = client.get(f"/api/v1/analyses/{analysis['analysis_id']}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == analysis["analysis_id"]
        assert len(detail["findings"]) > 0

    def test_get_analysis_not_found(self, client) -> None:
        resp = client.get("/api/v1/analyses/nonexistent-id-12345")
        assert resp.status_code == 404


class TestAuthRejection:
    """Tests that unauthenticated requests are rejected when demo mode is off."""

    def test_analyze_works_without_auth(self, client, no_demo_settings) -> None:
        """The analyze endpoint is public by design."""
        resp = client.post("/api/v1/analyze", json={"code": UNSAFE_MOD})
        assert resp.status_code == 200

    def test_save_without_auth_rejected(self, client, no_demo_settings) -> None:
        resp = client.post("/api/v1/analyses", json={
            "analysis_id": "test",
            "code": "x",
            "language": "typescript",
            "mod_name": None,
            "findings": [],
            "summary": {"total": 0, "critical": 0, "warning": 0, "info": 0},
            "duration_ms": 1.0,
        })
        assert resp.status_code == 401

    def test_list_without_auth_rejected(self, client, no_demo_settings) -> None:
        resp = client.get("/api/v1/analyses")
        assert resp.status_code == 401

    def test_get_without_auth_rejected(self, client, no_demo_settings) -> None:
        resp = client.get("/api/v1/analyses/some-id")
        assert resp.status_code == 401

    def test_save_with_api_key_succeeds(self, client, no_demo_settings) -> None:
        resp = client.post(
            "/api/v1/analyses",
            json={
                "analysis_id": "test-key-auth",
                "code": "x",
                "language": "typescript",
                "mod_name": None,
                "findings": [],
                "summary": {"total": 0, "critical": 0, "warning": 0, "info": 0},
                "duration_ms": 1.0,
            },
            headers={"X-API-Key": "test-api-key-1234567890"},
        )
        assert resp.status_code == 201

    def test_verify_unauthenticated(self, client, no_demo_settings) -> None:
        resp = client.get("/auth/verify")
        assert resp.status_code == 200
        assert resp.json()["authenticated"] is False


class TestHealthEndpoint:
    def test_health(self, client) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_health_service_name(self, client) -> None:
        resp = client.get("/health")
        assert resp.json()["service"] == "sentinel-forge"