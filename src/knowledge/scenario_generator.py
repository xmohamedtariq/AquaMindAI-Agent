from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.knowledge.diagnostic_engine import DiagnosticRule, EvidenceCondition


@dataclass(frozen=True)
class GeneratedScenario:
    scenario_id: str
    case_id: str
    expected_primary_case_id: str
    variation: int
    evidence: dict[str, Any]
    synthetic: bool = True


def _materialize(condition: EvidenceCondition) -> Any:
    if condition.op == "eq":
        return condition.value
    if condition.op == "in":
        return condition.value[0]
    if condition.op == "neq":
        return "__different__"
    if condition.op == "not_in":
        return "__outside__"
    if condition.op == "gte" or condition.op == "lte":
        return condition.value
    if condition.op == "exists":
        return "present" if condition.value else None
    raise ValueError(f"Unsupported condition operator: {condition.op}")


def materialize_rule(rule: DiagnosticRule, *, any_choice: int = 0, include_support: bool = False) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for condition in rule.required_all:
        evidence[condition.field] = _materialize(condition)
    for group in rule.required_any_groups:
        condition = group[min(any_choice, len(group) - 1)]
        evidence[condition.field] = _materialize(condition)
    if include_support:
        for condition in rule.supporting:
            evidence[condition.field] = _materialize(condition)
    return evidence


def generate_rule_scenarios(rule: DiagnosticRule, *, variations: int = 8) -> tuple[GeneratedScenario, ...]:
    if isinstance(variations, bool) or not isinstance(variations, int) or variations <= 0:
        raise ValueError("variations must be a positive integer")
    noise = [
        {}, {"evaluation_noise_tag": "A"}, {"evaluation_noise_tag": "B", "unrelated_boolean": False},
        {"evaluation_noise_tag": "C", "unrelated_numeric": 123.456},
        {"evaluation_noise_tag": "D", "unrelated_text": "synthetic"},
        {"evaluation_noise_tag": "E", "unused_direction": "stable"},
        {"evaluation_noise_tag": "F", "unrelated_boolean": True, "unrelated_numeric": 0},
        {"evaluation_noise_tag": "G", "unrelated_text": "control-profile"},
    ]
    items: list[GeneratedScenario] = []
    for index in range(variations):
        evidence = materialize_rule(rule, any_choice=index, include_support=(index % 2 == 1))
        evidence.update(noise[index % len(noise)])
        items.append(GeneratedScenario(
            scenario_id=f"{rule.case_id}-V{index + 1:02d}", case_id=rule.case_id,
            expected_primary_case_id=rule.case_id, variation=index + 1, evidence=evidence,
        ))
    return tuple(items)
