# Architecture

## Overview

Sentinel Forge is a developer toolkit for evaluating the safety of Claude Code
mods (function hooks). The backend performs deterministic static analysis on
TypeScript/JavaScript source code, while the frontend provides an interactive
dashboard for submitting code, viewing findings, and saving results.

## Components

### Backend (FastAPI + Python 3.12)

| Module | Responsibility |
|--------|---------------|
| `app/main.py` | Application factory; includes CORS, health endpoint, lifespan management |
| `app/core/config.py` | Pydantic-settings based configuration (demo mode, DB URL, CORS) |
| `app/core/analyzer.py` | Static analysis engine: tokenizes lines, applies rules, collects findings |
| `app/core/rules.py` | Rule definitions (6 rules with compiled regex patterns) |
| `app/models/schemas.py` | Pydantic request/response schemas |
| `app/api/analysis.py` | REST routes: `/analyze`, `/rules`, `/analyses/{id}`, `/analyses` |
| `app/api/auth.py` | Auth endpoints: `/verify`, `/logout` |
| `app/api/deps.py` | FastAPI dependencies: DB session, auth context, auth enforcement |
| `app/services/database.py` | SQLAlchemy setup, ORM models, session factory |
| `app/services/storage.py` | CRUD service for analysis records and audit logs |

### Frontend (React + TypeScript + Vite)

| Module | Responsibility |
|--------|---------------|
| `src/main.tsx` | React entry point |
| `src/App.tsx` | Navigation between Analyze and Saved Analyses tabs |
| `src/api/client.ts` | Typed API client using native fetch |
| `src/types/index.ts` | TypeScript interfaces mirroring backend schemas |
| `src/components/AnalysisForm.tsx` | Code input form with language/mod-name selectors |
| `src/components/FindingsList.tsx` | Findings display with severity filtering |
| `src/components/FindingCard.tsx` | Individual finding card with severity badge |
| `src/pages/AnalysisDashboard.tsx` | Analyze workflow: form → results → save/export |
| `src/pages/SavedAnalyses.tsx` | Saved analyses list with pagination and detail view |

## Data Flow

```
1. User pastes mod code in AnalysisForm
2. Frontend calls POST /api/v1/analyze
3. Backend analyzer scans code against 6 rules
4. Findings returned to frontend
5. FindingsList renders results with severity badges
6. User saves → POST /api/v1/analyses → SQLite
7. User exports → JSON download
```

## Storage

SQLite persistent storage with two tables:

- **analysis_records**: saved analysis results (code, findings JSON, summary counts, timestamps)
- **audit_log**: audit trail of save operations

All mutations are transactional with rollback on failure.