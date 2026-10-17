"""Static analysis rules for Claude Code mods (function hooks).

Each rule is a deterministic pattern matcher operating on source code lines.
Rules are designed to detect safety, accessibility, and correctness issues in
TypeScript/JavaScript mod plugins before they are deployed into agentic coding
sessions.

Issue references:
  - #769  UI flickering / full-buffer redraw accessibility
  - #91870 Function hooks / Mods extensibility system
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class Rule:
    """A single static analysis rule."""

    id: str
    name: str
    severity: Severity
    pattern: str
    message: str
    suggestion: str
    description: str = ""


def _compile(rule: Rule) -> re.Pattern[str]:
    return re.compile(rule.pattern)


RULES: list[Rule] = [
    Rule(
        id="RL-001",
        name="Unsafe Process Execution",
        severity=Severity.CRITICAL,
        description="Detects direct process execution without side-effect tracking or sandboxing.",
        pattern=r"require\s*\(\s*['\"]child_process['\"]\s*\)|child_process\.(exec|execSync|spawn|spawnSync)\s*\(",
        message="Process execution detected without side-effect tracking or user confirmation.",
        suggestion="Register this side effect in the mod's side_effects declaration and guard with explicit user approval.",
    ),
    Rule(
        id="RL-002",
        name="Unsafe File System Write",
        severity=Severity.WARNING,
        description="Detects file system mutations that may not be wrapped in error handling.",
        pattern=r"fs\.(writeFile|writeFileSync|unlink|unlinkSync|rmSync|rmdirSync|mkdirSync|chmodSync)\s*\(",
        message="File system mutation detected; verify error handling and side-effect declaration.",
        suggestion="Wrap fs operations in try/catch and declare them in the mod's side_effects metadata.",
    ),
    Rule(
        id="RL-003",
        name="Unsafe Network Call",
        severity=Severity.WARNING,
        description="Detects network calls without timeout, error handling, or side-effect declaration.",
        pattern=r"\bfetch\s*\(|http\.(request|get)\s*\(|https\.(request|get)\s*\(",
        message="Network call detected; verify timeout, error handling, and side-effect declaration.",
        suggestion="Add a timeout, .catch() handler, and declare the network call in side_effects.",
    ),
    Rule(
        id="RL-004",
        name="UI Flickering Pattern",
        severity=Severity.INFO,
        description="Detects full-screen terminal redraws that can cause accessibility issues (issue #769).",
        pattern=r"console\.clear\s*\(\)|process\.stdout\.cursorTo\s*\(\s*0|process\.stdout\.clearScreen|process\.stdout\.moveCursor\s*\(\s*-?\d+\s*,\s*-?\d+",
        message="Full-screen terminal redraw detected; can cause screen flickering for accessibility-sensitive users (issue #769).",
        suggestion="Use line-specific terminal control sequences instead of full-buffer redraws.",
    ),
    Rule(
        id="RL-005",
        name="Unbounded Loop",
        severity=Severity.WARNING,
        description="Detects loops and intervals without visible exit conditions.",
        pattern=r"while\s*\(\s*true\s*\)|while\s*\(\s*1\s*\)|setInterval\s*\(",
        message="Potentially unbounded loop or interval without a clear exit condition.",
        suggestion="Add a bounded iteration count or a clear exit condition for long-running operations.",
    ),
    Rule(
        id="RL-006",
        name="Missing Error Handler",
        severity=Severity.WARNING,
        description="Detects async network calls that may lack .catch() on the same or adjacent lines.",
        pattern=r"\bfetch\s*\(",
        message="Network call may lack a .catch() handler or try/catch on the following lines.",
        suggestion="Add .catch() to all fetch promises or wrap in try/catch.",
    ),
]


# Pre-compile for performance
_COMPILED: list[tuple[Rule, re.Pattern[str]]] = [
    (r, _compile(r)) for r in RULES
]


def get_rules() -> list[Rule]:
    """Return a copy of the rule list."""
    return list(RULES)


def get_rule(rule_id: str) -> Rule | None:
    """Look up a rule by ID."""
    for r in RULES:
        if r.id == rule_id:
            return r
    return None


def get_compiled() -> list[tuple[Rule, re.Pattern[str]]]:
    """Return pre-compiled rule/pattern pairs for the analyzer."""
    return list(_COMPILED)


def rule_to_dict(rule: Rule) -> dict:
    """Serialize a rule to a dict for API responses."""
    return {
        "id": rule.id,
        "name": rule.name,
        "severity": rule.severity.value,
        "description": rule.description,
        "message": rule.message,
        "suggestion": rule.suggestion,
        "pattern": rule.pattern,
    }