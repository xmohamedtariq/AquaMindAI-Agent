from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class KnowledgeAuditError(ValueError):
    """Raised when the authoritative knowledge registry is internally inconsistent."""


@dataclass(frozen=True)
class AuditSummary:
    source_count: int
    case_count: int
    rule_count: int
    vocabulary_count: int
    scenario_count: int
    draft_source_ids: tuple[str, ...]
    unused_source_ids: tuple[str, ...]


def _read(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise KnowledgeAuditError(f"Missing knowledge file: {p}")
    try:
        value = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KnowledgeAuditError(f"Invalid JSON knowledge file: {p}") from exc
    if not isinstance(value, dict):
        raise KnowledgeAuditError(f"JSON root must be an object: {p}")
    return value


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KnowledgeAuditError(f"{field} must be a non-empty string")
    return value.strip()


def audit_knowledge_base(
    *, registry_path: str | Path, case_library_path: str | Path,
    rules_path: str | Path, vocabulary_path: str | Path,
    scenario_matrix_path: str | Path,
) -> AuditSummary:
    registry = _read(registry_path)
    cases_doc = _read(case_library_path)
    rules_doc = _read(rules_path)
    vocab_doc = _read(vocabulary_path)
    scenario_doc = _read(scenario_matrix_path)

    raw_sources = registry.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise KnowledgeAuditError("source registry must contain a non-empty sources list")
    source_ids: set[str] = set()
    draft_ids: list[str] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            raise KnowledgeAuditError("each source must be an object")
        source_id = _nonempty(source.get("id"), "source.id")
        if source_id in source_ids:
            raise KnowledgeAuditError(f"duplicate source id: {source_id}")
        source_ids.add(source_id)
        url = _nonempty(source.get("url"), f"{source_id}.url")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            raise KnowledgeAuditError(f"{source_id} must use a valid https URL")
        status = _nonempty(source.get("publication_status"), f"{source_id}.publication_status")
        if status == "draft":
            draft_ids.append(source_id)

    aliases = registry.get("aliases", {})
    if not isinstance(aliases, dict):
        raise KnowledgeAuditError("aliases must be an object")
    for old, new in aliases.items():
        _nonempty(old, "alias.old")
        if new not in source_ids:
            raise KnowledgeAuditError(f"alias target is not a canonical source: {new}")

    cases = cases_doc.get("cases")
    if not isinstance(cases, list) or not cases:
        raise KnowledgeAuditError("case library must contain cases")
    case_ids: set[str] = set()
    used_sources: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise KnowledgeAuditError("each case must be an object")
        case_id = _nonempty(case.get("case_id"), "case_id")
        if case_id in case_ids:
            raise KnowledgeAuditError(f"duplicate case id: {case_id}")
        case_ids.add(case_id)
        ids = case.get("source_ids")
        if not isinstance(ids, list) or not ids:
            raise KnowledgeAuditError(f"{case_id} must reference at least one source")
        unknown = set(ids) - source_ids
        if unknown:
            raise KnowledgeAuditError(f"{case_id} references unknown sources: {sorted(unknown)}")
        used_sources.update(ids)
        if case.get("physical_action_authorized") is not False:
            raise KnowledgeAuditError(f"{case_id} cannot authorize physical action")
        if case.get("rule_status") != "executable_structured_rule":
            raise KnowledgeAuditError(f"{case_id} must have an executable structured rule")

    rules = rules_doc.get("rules")
    if not isinstance(rules, list) or not rules:
        raise KnowledgeAuditError("diagnostic rules must be non-empty")
    rule_case_ids: set[str] = set()
    rule_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise KnowledgeAuditError("each diagnostic rule must be an object")
        rule_id = _nonempty(rule.get("rule_id"), "rule_id")
        if rule_id in rule_ids:
            raise KnowledgeAuditError(f"duplicate rule id: {rule_id}")
        rule_ids.add(rule_id)
        case_id = _nonempty(rule.get("case_id"), f"{rule_id}.case_id")
        if case_id not in case_ids:
            raise KnowledgeAuditError(f"{rule_id} references unknown case: {case_id}")
        if case_id in rule_case_ids:
            raise KnowledgeAuditError(f"multiple primary rules map to case: {case_id}")
        rule_case_ids.add(case_id)
    if rule_case_ids != case_ids:
        raise KnowledgeAuditError("every canonical case must have exactly one structured rule")

    terms = vocab_doc.get("terms")
    if not isinstance(terms, list) or not terms:
        raise KnowledgeAuditError("evidence vocabulary must be non-empty")
    term_names: set[str] = set()
    for term in terms:
        if not isinstance(term, dict):
            raise KnowledgeAuditError("each vocabulary term must be an object")
        name = _nonempty(term.get("name"), "term.name")
        if name in term_names:
            raise KnowledgeAuditError(f"duplicate evidence term: {name}")
        term_names.add(name)
    for case in cases:
        unknown = set(case.get("evidence_terms", [])) - term_names
        if unknown:
            raise KnowledgeAuditError(f"{case['case_id']} uses undeclared evidence terms: {sorted(unknown)}")
    for rule in rules:
        conds = list(rule.get("required_all", [])) + list(rule.get("supporting", []))
        for group in rule.get("required_any_groups", []):
            conds.extend(group)
        for condition in conds:
            field = condition.get("field")
            if field not in term_names:
                raise KnowledgeAuditError(f"{rule['rule_id']} uses undeclared evidence field: {field}")

    scenarios = scenario_doc.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise KnowledgeAuditError("scenario matrix must be non-empty")
    if scenario_doc.get("scenario_count") != len(scenarios):
        raise KnowledgeAuditError("scenario_count does not match scenario matrix")
    for scenario in scenarios:
        if scenario.get("synthetic") is not True:
            raise KnowledgeAuditError("every matrix scenario must be explicitly synthetic")
        if scenario.get("case_id") not in case_ids:
            raise KnowledgeAuditError("scenario references unknown case")

    return AuditSummary(
        source_count=len(source_ids), case_count=len(case_ids), rule_count=len(rule_ids),
        vocabulary_count=len(term_names), scenario_count=len(scenarios),
        draft_source_ids=tuple(sorted(draft_ids)),
        unused_source_ids=tuple(sorted(source_ids - used_sources)),
    )
