# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

usage-pattern-tracker

## Roadmap

### mod-safety-analyzer — Mod Safety Analyzer

Status: done

Acceptance:
- User submits TypeScript/JavaScript mod source code via API or UI
- Deterministic static analysis engine scans code against rule set
- API returns findings with rule_id, severity, line, message, and suggestion
- Findings summary aggregates counts by severity
- Analysis results are persisted to SQLite with UTC timestamps
- Paginated, filterable list of saved analyses
- At least 6 concrete analysis rules covering process execution, file writes, network calls, UI flickering, unbounded loops, and missing error handling

Implementation: `backend/app/core/analyzer.py`, `backend/app/core/rules.py`, `backend/app/api/analysis.py`, `backend/app/models/schemas.py`, `backend/app/services/storage.py`, `frontend/src/api/client.ts`, `frontend/src/components/AnalysisForm.tsx`, `frontend/src/components/FindingsList.tsx`, `frontend/src/pages/AnalysisDashboard.tsx`

Tests: `backend/tests/test_analyzer.py`, `backend/tests/test_rules.py`, `backend/tests/test_api.py`, `frontend/__tests__/AnalysisForm.test.tsx`, `frontend/__tests__/FindingsList.test.tsx`

### usage-pattern-tracker — Usage Pattern Tracker

Status: in_progress

Acceptance:
- Ingest Claude Code usage data (tokens consumed, requests, time)
- Deterministic analysis predicts when subscription limits will be hit
- Historical usage trends with rate-of-change metrics
- Threshold alert configuration per subscription tier

### mod-evaluation-harness — Mod Evaluation Harness

Status: planned

Acceptance:
- Register test scenarios for simulating agent behavior
- Evaluate mod side effects across simulated agent events
- Report coverage of registered side-effect declarations
- Export evaluation report as JSON

### oidc-auth-keycloak — OIDC Authentication with Keycloak

Status: planned

Acceptance:
- Secure OIDC authorization-code login through Keycloak with state+nonce+PKCE
- Backend-managed sessions with HttpOnly SameSite cookies
- CSRF protection on cookie-authenticated writes
- viewer/operator/admin role authorization on all data endpoints
- Local-only demo mode that binds localhost
- Tests for unauthenticated rejection and role denial
- Keycloak realm import and SAML identity brokering documentation

### llm-adapter-suite — Multi-Provider LLM Adapter Suite

Status: planned

Acceptance:
- OpenAI-compatible, Anthropic messages, Gemini generateContent, Ollama adapters
- LLM_API_KEY as only secret credential variable
- Bounded timeouts and redacted error messages
- Opt-in LLM explanations for analysis findings

