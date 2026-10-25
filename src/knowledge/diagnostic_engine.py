from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.knowledge.case_library import CaseLibrary, KnowledgeCase, load_case_library


class DiagnosticRuleError(ValueError):
    """Raised when source-grounded diagnostic rules are invalid."""


_ALLOWED_OPERATORS = frozenset({"eq", "neq", "in", "not_in", "gte", "lte", "exists"})
_ALLOWED_OUTCOMES = frozenset({"diagnosis", "risk", "guard", "data_quality"})


@dataclass(frozen=True)
class EvidenceCondition:
    field: str
    op: str
    value: Any


@dataclass(frozen=True)
class DiagnosticRule:
    rule_id: str
    case_id: str
    outcome_type: str
    priority: int
    blocks_fault_diagnosis: bool
    required_all: tuple[EvidenceCondition, ...]
    required_any_groups: tuple[tuple[EvidenceCondition, ...], ...]
    supporting: tuple[EvidenceCondition, ...]


@dataclass(frozen=True)
class DiagnosticMatch:
    rule_id: str
    case_id: str
    title: str
    expected_label: str
    outcome_type: str
    priority: int
    blocks_fault_diagnosis: bool
    matched_fields: tuple[str, ...]
    supporting_fields: tuple[str, ...]
    source_ids: tuple[str, ...]
    verification_required: bool
    reasoning_basis: tuple[str, ...]
    inference_note: str


@dataclass(frozen=True)
class DiagnosticDecision:
    status: str
    primary: DiagnosticMatch | None
    matches: tuple[DiagnosticMatch, ...]
    fault_diagnosis_blocked: bool

    @property
    def source_ids(self) -> tuple[str, ...]:
        values = {source_id for item in self.matches for source_id in item.source_ids}
        return tuple(sorted(values))


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise DiagnosticRuleError(f"JSON file does not exist: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DiagnosticRuleError(f"Unable to read valid JSON from {path}") from exc
    if not isinstance(value, dict):
        raise DiagnosticRuleError(f"JSON root must be an object: {path}")
    return value


def _nonempty_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DiagnosticRuleError(f"{field} must be a non-empty string")
    return value.strip()


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DiagnosticRuleError(f"{field} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise DiagnosticRuleError(f"{field} must be a finite number")
    return number


def _parse_condition(raw: Any, field: str) -> EvidenceCondition:
    if not isinstance(raw, dict):
        raise DiagnosticRuleError(f"{field} must be an object")
    name = _nonempty_text(raw.get("field"), f"{field}.field")
    op = _nonempty_text(raw.get("op"), f"{field}.op")
    if op not in _ALLOWED_OPERATORS:
        raise DiagnosticRuleError(f"{field}.op is not supported: {op}")
    value = raw.get("value")
    if op in {"in", "not_in"}:
        if not isinstance(value, list) or not value:
            raise DiagnosticRuleError(f"{field}.value must be a non-empty list")
        value = tuple(value)
    elif op in {"gte", "lte"}:
        value = _finite_number(value, f"{field}.value")
    elif op == "exists" and not isinstance(value, bool):
        raise DiagnosticRuleError(f"{field}.value must be boolean")
    return EvidenceCondition(field=name, op=op, value=value)


def _parse_condition_list(raw: Any, field: str, *, allow_empty: bool) -> tuple[EvidenceCondition, ...]:
    if not isinstance(raw, list):
        raise DiagnosticRuleError(f"{field} must be a list")
    if not allow_empty and not raw:
        raise DiagnosticRuleError(f"{field} must not be empty")
    return tuple(_parse_condition(value, f"{field}[{index}]") for index, value in enumerate(raw))


def _parse_any_groups(raw: Any, field: str) -> tuple[tuple[EvidenceCondition, ...], ...]:
    if not isinstance(raw, list):
        raise DiagnosticRuleError(f"{field} must be a list")
    return tuple(_parse_condition_list(group, f"{field}[{index}]", allow_empty=False) for index, group in enumerate(raw))


def _parse_rule(raw: Any) -> DiagnosticRule:
    if not isinstance(raw, dict):
        raise DiagnosticRuleError("each diagnostic rule must be an object")
    rule_id = _nonempty_text(raw.get("rule_id"), "rule_id")
    case_id = _nonempty_text(raw.get("case_id"), f"{rule_id}.case_id")
    outcome_type = _nonempty_text(raw.get("outcome_type"), f"{rule_id}.outcome_type")
    if outcome_type not in _ALLOWED_OUTCOMES:
        raise DiagnosticRuleError(f"{rule_id} has invalid outcome_type")
    priority = raw.get("priority")
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise DiagnosticRuleError(f"{rule_id}.priority must be an integer")
    blocked = raw.get("blocks_fault_diagnosis")
    if not isinstance(blocked, bool):
        raise DiagnosticRuleError(f"{rule_id}.blocks_fault_diagnosis must be boolean")
    return DiagnosticRule(
        rule_id=rule_id,
        case_id=case_id,
        outcome_type=outcome_type,
        priority=priority,
        blocks_fault_diagnosis=blocked,
        required_all=_parse_condition_list(raw.get("required_all"), f"{rule_id}.required_all", allow_empty=False),
        required_any_groups=_parse_any_groups(raw.get("required_any_groups"), f"{rule_id}.required_any_groups"),
        supporting=_parse_condition_list(raw.get("supporting"), f"{rule_id}.supporting", allow_empty=True),
    )


def load_diagnostic_rules(path: str | Path) -> tuple[DiagnosticRule, ...]:
    data = _read_json_object(Path(path))
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list) or not raw_rules:
        raise DiagnosticRuleError("diagnostic rules must contain a non-empty rules list")
    parsed: list[DiagnosticRule] = []
    seen: set[str] = set()
    for raw in raw_rules:
        rule = _parse_rule(raw)
        if rule.rule_id in seen:
            raise DiagnosticRuleError(f"duplicate rule id: {rule.rule_id}")
        seen.add(rule.rule_id)
        parsed.append(rule)
    return tuple(parsed)


def _condition_matches(evidence: dict[str, Any], condition: EvidenceCondition) -> bool:
    exists = condition.field in evidence and evidence[condition.field] is not None
    if condition.op == "exists":
        return exists == condition.value
    if not exists:
        return False
    actual = evidence[condition.field]
    if condition.op == "eq":
        return actual == condition.value
    if condition.op == "neq":
        return actual != condition.value
    if condition.op == "in":
        return actual in condition.value
    if condition.op == "not_in":
        return actual not in condition.value
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        return False
    actual_number = float(actual)
    if not math.isfinite(actual_number):
        return False
    if condition.op == "gte":
        return actual_number >= condition.value
    return actual_number <= condition.value


def _rule_matches(evidence: dict[str, Any], rule: DiagnosticRule) -> tuple[bool, tuple[str, ...], tuple[str, ...]]:
    required_fields: list[str] = []
    for condition in rule.required_all:
        if not _condition_matches(evidence, condition):
            return False, (), ()
        required_fields.append(condition.field)
    for group in rule.required_any_groups:
        matched = [condition for condition in group if _condition_matches(evidence, condition)]
        if not matched:
            return False, (), ()
        required_fields.extend(condition.field for condition in matched)
    supporting_fields = tuple(condition.field for condition in rule.supporting if _condition_matches(evidence, condition))
    return True, tuple(dict.fromkeys(required_fields)), tuple(dict.fromkeys(supporting_fields))


class SourceGroundedDiagnosticEngine:
    """Return source-linked hypotheses and guards without authorizing physical actuation."""

    def __init__(self, *, case_library: CaseLibrary, rules: tuple[DiagnosticRule, ...]) -> None:
        self.case_library = case_library
        self.rules = rules
        case_map = {item.case_id: item for item in case_library.cases}
        for rule in rules:
            if rule.case_id not in case_map:
                raise DiagnosticRuleError(f"{rule.rule_id} references unknown case id: {rule.case_id}")
            if case_map[rule.case_id].physical_action_authorized:
                raise DiagnosticRuleError(f"{rule.case_id} cannot authorize physical plant action")
        self._case_map = case_map

    @classmethod
    def from_files(cls, *, rules_path: str | Path, library_path: str | Path, registry_path: str | Path) -> "SourceGroundedDiagnosticEngine":
        return cls(case_library=load_case_library(library_path, registry_path), rules=load_diagnostic_rules(rules_path))

    @property
    def rule_count(self) -> int:
        return len(self.rules)

    def _build_match(self, rule: DiagnosticRule, required_fields: tuple[str, ...], supporting_fields: tuple[str, ...]) -> DiagnosticMatch:
        item: KnowledgeCase = self._case_map[rule.case_id]
        return DiagnosticMatch(
            rule_id=rule.rule_id,
            case_id=item.case_id,
            title=item.title,
            expected_label=item.expected_label,
            outcome_type=rule.outcome_type,
            priority=rule.priority,
            blocks_fault_diagnosis=rule.blocks_fault_diagnosis,
            matched_fields=required_fields,
            supporting_fields=supporting_fields,
            source_ids=item.source_ids,
            verification_required=item.verification_required,
            reasoning_basis=item.reasoning_basis,
            inference_note=item.inference_note,
        )

    def match(self, evidence: dict[str, Any], *, top_k: int | None = None) -> tuple[DiagnosticMatch, ...]:
        if not isinstance(evidence, dict):
            raise DiagnosticRuleError("evidence must be a dictionary")
        if top_k is not None and (isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0):
            raise DiagnosticRuleError("top_k must be a positive integer")
        matches: list[DiagnosticMatch] = []
        for rule in self.rules:
            matched, required_fields, supporting_fields = _rule_matches(evidence, rule)
            if matched:
                matches.append(self._build_match(rule, required_fields, supporting_fields))
        matches.sort(key=lambda item: (-int(item.blocks_fault_diagnosis), -item.priority, -len(item.matched_fields), -len(item.supporting_fields), item.case_id))
        if top_k is not None:
            matches = matches[:top_k]
        return tuple(matches)

    def decide(self, evidence: dict[str, Any]) -> DiagnosticDecision:
        matches = self.match(evidence)
        if not matches:
            return DiagnosticDecision(status="no_supported_match", primary=None, matches=(), fault_diagnosis_blocked=False)
        blockers = tuple(item for item in matches if item.blocks_fault_diagnosis)
        if blockers:
            return DiagnosticDecision(status="blocked_by_guard", primary=blockers[0], matches=matches, fault_diagnosis_blocked=True)
        return DiagnosticDecision(status="matched", primary=matches[0], matches=matches, fault_diagnosis_blocked=False)
