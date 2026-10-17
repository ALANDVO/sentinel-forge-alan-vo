"""Deterministic static analysis engine for Claude Code mods.

The analyzer scans source code line-by-line, applying compiled rule patterns.
For context-aware rules (e.g. missing error handler), it inspects surrounding
lines before emitting a finding.

No LLM or network access is required. The core is fully offline and deterministic.
"""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


from app.core.rules import (
    get_compiled,
    get_rule,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single finding emitted by the analyzer."""

    rule_id: str
    rule_name: str
    severity: str
    line: int
    column: int
    message: str
    suggestion: str
    code_snippet: str


@dataclass
class AnalysisSummary:
    """Aggregate counts of findings by severity."""

    total: int
    critical: int
    warning: int
    info: int


@dataclass
class AnalysisResult:
    """Complete result of analyzing a single source file."""

    analysis_id: str
    code: str
    language: str
    mod_name: str | None
    findings: list[Finding]
    summary: AnalysisSummary
    created_at: datetime
    duration_ms: float


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# How many lines to look ahead/behind for context-aware rules
_LOOKAHEAD = 3


def _line_col_to_snippet(source: str, lineno: int, max_len: int = 200) -> str:
    """Extract the source line at *lineno* (1-based)."""
    lines = source.splitlines()
    if 1 <= lineno <= len(lines):
        raw = lines[lineno - 1]
        return raw[:max_len] if len(raw) <= max_len else raw[:max_len] + "…"
    return ""


def _has_error_handler(lines: list[str], start: int, end: int) -> bool:
    """Check whether *lines* in [start, end) contain a .catch() or try/catch."""
    for i in range(start, min(end, len(lines))):
        line = lines[i]
        if re.search(r"\.catch\s*\(", line) or "try" in line or "catch" in line:
            return True
    return False


def _check_rl006(source: str, lines: list[str]) -> list[Finding]:
    """Context-aware check: fetch() without .catch() nearby."""
    findings: list[Finding] = []
    fetch_re = re.compile(r"\bfetch\s*\(")
    catch_re = re.compile(r"\.catch\s*\(")

    for i, line in enumerate(lines):
        for m in fetch_re.finditer(line):
            # Check the remainder of this line and the next _LOOKAHEAD lines
            # for a .catch() or try/catch.
            snippet_start = m.start()
            remainder = line[snippet_start:]
            window = "".join(lines[i : min(i + _LOOKAHEAD + 1, len(lines))])
            if catch_re.search(remainder) or "try" in remainder or _has_error_handler(
                lines, i, min(i + _LOOKAHEAD + 1, len(lines))
            ):
                continue
            full_window_snippet = _line_col_to_snippet(
                "\n".join(window), 1
            ) if window else line.strip()
            rule = get_rule("RL-006")
            findings.append(
                Finding(
                    rule_id="RL-006",
                    rule_name=rule.name if rule else "Missing Error Handler",
                    severity="warning",
                    line=i + 1,
                    column=m.start() + 1,
                    message=rule.message if rule else "Network call may lack error handling.",
                    suggestion=rule.suggestion if rule else "Add .catch() to all fetch promises.",
                    code_snippet=line.strip()[:200],
                )
            )
    return findings


# Rules that require context-aware checking (skip simple line matching)
_CONTEXT_RULES = {"RL-006"}


def analyze(
    code: str,
    language: str = "typescript",
    mod_name: str | None = None,
) -> AnalysisResult:
    """Analyze *code* and return a full :class:`AnalysisResult`.

    This function is deterministic: identical input always yields identical
    findings (timestamps and analysis_id excluded from that guarantee).
    """
    start = time.perf_counter()
    lines = code.splitlines()
    findings: list[Finding] = []

    compiled = get_compiled()

    for rule, pattern in compiled:
        if rule.id in _CONTEXT_RULES:
            continue  # handled separately
        for i, line in enumerate(lines):
            for m in pattern.finditer(line):
                findings.append(
                    Finding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity.value,
                        line=i + 1,
                        column=m.start() + 1,
                        message=rule.message,
                        suggestion=rule.suggestion,
                        code_snippet=line.strip()[:200],
                    )
                )

    # Context-aware rules
    findings.extend(_check_rl006(code, lines))

    # Sort by line then severity (critical first)
    _SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: (f.line, _SEVERITY_ORDER.get(f.severity, 99)))

    summary = AnalysisSummary(
        total=len(findings),
        critical=sum(1 for f in findings if f.severity == "critical"),
        warning=sum(1 for f in findings if f.severity == "warning"),
        info=sum(1 for f in findings if f.severity == "info"),
    )

    duration_ms = (time.perf_counter() - start) * 1000.0

    return AnalysisResult(
        analysis_id=str(uuid.uuid4()),
        code=code,
        language=language,
        mod_name=mod_name,
        findings=findings,
        summary=summary,
        created_at=datetime.now(timezone.utc),
        duration_ms=round(duration_ms, 3),
    )