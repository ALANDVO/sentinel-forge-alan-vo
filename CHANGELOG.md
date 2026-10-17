# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-17

### Added

- **Mod Safety Analyzer** — Deterministic static analysis engine for Claude Code mods (function hooks). Scans TypeScript/JavaScript source code against 6 rules (RL-001 through RL-006) covering unsafe process execution, file system writes, network calls, UI flickering accessibility, unbounded loops, and missing error handlers.
- **FastAPI backend** with SQLAlchemy + SQLite persistent storage, pagination, filtering, UTC timestamps, audit logging, and transactional mutations.
- **React + TypeScript + Vite frontend** with AnalysisForm, FindingsList, FindingCard, AnalysisDashboard, and SavedAnalyses pages.
- **Typed API client** derived from backend route schemas using native fetch.
- **Three complete workflows**: Analyze (create), Save & Browse (list with pagination/filtering), Detail & Export (per-record view with JSON export).
- **Basic authentication**: demo mode (localhost-only auto-auth) and API key auth (X-API-Key header). Full OIDC/Keycloak SSO is a planned future milestone.
- **Docker support**: multi-stage Dockerfiles with nonroot users, healthchecks, and .dockerignore files.
- **compose.yaml** with backend, frontend, and Keycloak (behind `auth` Docker profile).
- **CI workflow** on `ubuntu-latest`: backend pytest, frontend TypeScript build + vitest, Docker builds with buildx.
- **69 backend tests** covering domain logic, boundary/malformed inputs, persistence, auth rejection, and API integration.
- **16 frontend tests** covering form submission, findings display, filtering, and API client behavior.

### Security

- Demo mode binds to 127.0.0.1 only and refuses to activate in production.
- API key auth for persistence endpoints in non-demo mode.
- No real credentials committed; `.env.example` provided with blank templates.

### Known Limitations

- Auth is demo/API-key only; full OIDC/Keycloak with SAML identity brokering is planned.
- LLM adapter suite (opt-in advisory explanations) is not yet implemented.
- Static analysis uses regex pattern matching, not full AST parsing; false positives in comments/strings and false negatives in multi-line chains are documented.