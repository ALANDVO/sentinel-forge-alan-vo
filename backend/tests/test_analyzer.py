"""Tests for the static analysis engine."""
from __future__ import annotations

import uuid

import pytest

from app.core.analyzer import AnalysisResult, analyze, AnalysisSummary, Finding
from app.core.rules import get_rule

from backend.tests.samples import (
    SAFE_MOD,
    UNSAFE_MOD,
    FLICKERING_MOD,
    UNBOUNDED_MOD,
    FETCH_WITH_CATCH,
    MINIMAL_CODE,
    LONG_CODE,
)


class TestAnalyzeSafeCode:
    def test_safe_code_no_findings(self) -> None:
        result = analyze(SAFE_MOD)
        assert result.summary.total == 0
        assert result.summary.critical == 0
        assert result.summary.warning == 0
        assert result.summary.info == 0

    def test_minimal_code_no_findings(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert result.summary.total == 0

    def test_returns_analysis_result(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert isinstance(result, AnalysisResult)

    def test_analysis_id_is_uuid(self) -> None:
        result = analyze(MINIMAL_CODE)
        # UUID v4 format
        parts = result.analysis_id.split("-")
        assert len(parts) == 5
        assert len(result.analysis_id) == 36


class TestAnalyzeUnsafeCode:
    def test_unsafe_mod_detects_critical(self) -> None:
        result = analyze(UNSAFE_MOD)
        assert result.summary.critical >= 1
        assert any(f.rule_id == "RL-001" for f in result.findings)

    def test_unsafe_mod_detects_file_write(self) -> None:
        result = analyze(UNSAFE_MOD)
        assert any(f.rule_id == "RL-002" for f in result.findings)

    def test_unsafe_mod_detects_network_call(self) -> None:
        result = analyze(UNSAFE_MOD)
        assert any(f.rule_id == "RL-003" for f in result.findings)

    def test_unsafe_mod_detects_missing_error_handler(self) -> None:
        result = analyze(UNSAFE_MOD)
        assert any(f.rule_id == "RL-006" for f in result.findings)


class TestRuleRL004Flickering:
    def test_flickering_detected(self) -> None:
        result = analyze(FLICKERING_MOD)
        assert result.summary.info >= 1
        assert any(f.rule_id == "RL-004" for f in result.findings)

    def test_flickering_severity_is_info(self) -> None:
        result = analyze(FLICKERING_MOD)
        flickering = [f for f in result.findings if f.rule_id == "RL-004"]
        assert flickering[0].severity == "info"


class TestRuleRL005Unbounded:
    def test_while_true_detected(self) -> None:
        result = analyze(UNBOUNDED_MOD)
        assert any(f.rule_id == "RL-005" for f in result.findings)

    def test_set_interval_detected(self) -> None:
        result = analyze("setInterval(() => { console.log('tick'); }, 1000);")
        assert any(f.rule_id == "RL-005" for f in result.findings)


class TestRuleRL006ErrorHandling:
    def test_fetch_with_catch_not_flagged(self) -> None:
        result = analyze(FETCH_WITH_CATCH)
        assert not any(f.rule_id == "RL-006" for f in result.findings)

    def test_fetch_without_catch_flagged(self) -> None:
        result = analyze("const r = await fetch('https://example.com');")
        assert any(f.rule_id == "RL-006" for f in result.findings)

    def test_fetch_with_catch_still_flags_network(self) -> None:
        result = analyze(FETCH_WITH_CATCH)
        assert any(f.rule_id == "RL-003" for f in result.findings)


class TestFindingProperties:
    def test_findings_have_code_snippet(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            assert f.code_snippet
            assert f.code_snippet.strip()

    def test_findings_have_line_numbers(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            assert f.line > 0

    def test_findings_have_column(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            assert f.column > 0

    def test_findings_have_suggestion(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            assert f.suggestion

    def test_findings_have_message(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            assert f.message

    def test_finding_severity_matches_rule(self) -> None:
        result = analyze(UNSAFE_MOD)
        for f in result.findings:
            rule = get_rule(f.rule_id)
            assert f.severity == rule.severity.value


class TestAnalysisOrdering:
    def test_findings_sorted_by_line(self) -> None:
        result = analyze(UNSAFE_MOD)
        lines = [f.line for f in result.findings]
        assert lines == sorted(lines)

    def test_findings_sorted_by_line_then_severity(self) -> None:
        code = "const cp = require('child_process'); fetch('https://x.com');"
        result = analyze(code)
        for i in range(len(result.findings) - 1):
            f1, f2 = result.findings[i], result.findings[i + 1]
            if f1.line == f2.line:
                sev_order = {"critical": 0, "warning": 1, "info": 2}
                assert sev_order[f1.severity] <= sev_order[f2.severity]


class TestAnalysisMetadata:
    def test_mod_name_preserved(self) -> None:
        result = analyze(SAFE_MOD, mod_name="my-test-mod")
        assert result.mod_name == "my-test-mod"

    def test_mod_name_defaults_none(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert result.mod_name is None

    def test_language_default(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert result.language == "typescript"

    def test_language_javascript(self) -> None:
        result = analyze(MINIMAL_CODE, language="javascript")
        assert result.language == "javascript"

    def test_created_at_is_utc(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert result.created_at.tzinfo is not None

    def test_duration_ms_nonnegative(self) -> None:
        result = analyze(MINIMAL_CODE)
        assert result.duration_ms >= 0.0

    def test_summary_counts_consistent(self) -> None:
        result = analyze(UNSAFE_MOD)
        assert result.summary.total == len(result.findings)
        assert result.summary.critical == sum(
            1 for f in result.findings if f.severity == "critical"
        )
        assert result.summary.warning == sum(
            1 for f in result.findings if f.severity == "warning"
        )
        assert result.summary.info == sum(
            1 for f in result.findings if f.severity == "info"
        )


class TestAnalyzeDeterminism:
    def test_same_input_same_findings(self) -> None:
        r1 = analyze(UNSAFE_MOD)
        r2 = analyze(UNSAFE_MOD)
        # Findings should be identical (ignoring analysis_id and timestamps)
        assert len(r1.findings) == len(r2.findings)
        for f1, f2 in zip(r1.findings, r2.findings):
            assert f1.rule_id == f2.rule_id
            assert f1.line == f2.line
            assert f1.column == f2.column
            assert f1.message == f2.message

    def test_deterministic_findings_count(self) -> None:
        results = [analyze(UNSAFE_MOD) for _ in range(5)]
        counts = [len(r.findings) for r in results]
        assert all(c == counts[0] for c in counts)