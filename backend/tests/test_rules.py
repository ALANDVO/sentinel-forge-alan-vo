"""Tests for the rules module."""
from __future__ import annotations

import re

import pytest

from app.core.rules import (
    Rule,
    Severity,
    get_compiled,
    get_rule,
    get_rules,
    rule_to_dict,
)


class TestRuleRegistry:
    def test_get_rules_returns_six(self) -> None:
        assert len(get_rules()) == 6

    def test_get_compiled_returns_pairs(self) -> None:
        compiled = get_compiled()
        assert len(compiled) == 6
        for rule, pattern in compiled:
            assert isinstance(rule, Rule)
            assert isinstance(pattern, re.Pattern)

    def test_all_rule_ids_unique(self) -> None:
        ids = [r.id for r in get_rules()]
        assert len(ids) == len(set(ids))

    def test_all_severities_valid(self) -> None:
        for rule in get_rules():
            assert rule.severity in (
                Severity.CRITICAL,
                Severity.WARNING,
                Severity.INFO,
            )

    def test_all_rules_have_all_fields(self) -> None:
        for rule in get_rules():
            assert rule.id
            assert rule.name
            assert rule.pattern
            assert rule.message
            assert rule.suggestion
            assert rule.description


class TestRuleLookup:
    def test_get_rule_by_id(self) -> None:
        rule = get_rule("RL-001")
        assert rule is not None
        assert rule.name == "Unsafe Process Execution"
        assert rule.severity == Severity.CRITICAL

    def test_get_rule_each_id(self) -> None:
        for rule in get_rules():
            assert get_rule(rule.id) is rule

    def test_get_rule_nonexistent(self) -> None:
        assert get_rule("RL-999") is None
        assert get_rule("") is None


class TestRuleSerialization:
    def test_rule_to_dict_fields(self) -> None:
        rule = get_rule("RL-001")
        d = rule_to_dict(rule)
        assert d["id"] == "RL-001"
        assert d["name"] == "Unsafe Process Execution"
        assert d["severity"] == "critical"
        assert d["description"]
        assert d["message"]
        assert d["suggestion"]
        assert d["pattern"]

    def test_severity_enum_values(self) -> None:
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"