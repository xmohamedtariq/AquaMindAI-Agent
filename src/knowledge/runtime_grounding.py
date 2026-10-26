from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.agent.state import AgentState
from src.knowledge.case_library import KnowledgeCase
from src.knowledge.diagnostic_engine import (
    DiagnosticDecision,
    DiagnosticMatch,
    SourceGroundedDiagnosticEngine,
)
from src.knowledge.evidence_adapter import (
    EvidenceAdapterError,
    build_runtime_evidence_bundle,
)


DiagnosticTool = Callable[
    [AgentState],
    dict[str, Any],
]


def _serialize_match(
    match: DiagnosticMatch,
) -> dict[str, Any]:
    """Convert a source-grounded match into JSON-safe data."""

    return {
        "rule_id": match.rule_id,
        "case_id": match.case_id,
        "title": match.title,
        "expected_label": match.expected_label,
        "outcome_type": match.outcome_type,
        "priority": match.priority,
        "blocks_fault_diagnosis": (
            match.blocks_fault_diagnosis
        ),
        "matched_fields": list(
            match.matched_fields
        ),
        "supporting_fields": list(
            match.supporting_fields
        ),
        "source_ids": list(
            match.source_ids
        ),
        "verification_required": (
            match.verification_required
        ),
        "reasoning_basis": list(
            match.reasoning_basis
        ),
        "inference_note": (
            match.inference_note
        ),
        "physical_action_authorized": False,
    }


def _serialize_case(
    item: KnowledgeCase,
) -> dict[str, Any]:
    """Serialize a broad canonical case alignment."""

    return {
        "case_id": item.case_id,
        "title": item.title,
        "expected_label": item.expected_label,
        "source_ids": list(
            item.source_ids
        ),
        "support_level": item.support_level,
        "confidence_type": (
            item.confidence_type
        ),
        "verification_required": (
            item.verification_required
        ),
        "reasoning_basis": list(
            item.reasoning_basis
        ),
        "inference_note": item.inference_note,
        "physical_action_authorized": False,
        "support_type": (
            "canonical_case_alignment"
        ),
    }


def _deterministic_label(
    result: dict[str, Any],
) -> str | None:
    """Return the broad label produced by the deterministic classifier."""

    primary = result.get(
        "primary_hypothesis"
    )

    if not isinstance(primary, dict):
        return None

    value = primary.get("id")

    if not isinstance(value, str) or not value.strip():
        return None

    return value.strip()


def _canonical_support(
    engine: SourceGroundedDiagnosticEngine,
    label: str | None,
) -> tuple[KnowledgeCase, ...]:
    """Return runtime-supported canonical cases aligned to a broad label."""

    if label is None:
        return ()

    return engine.case_library.find(
        expected_label=label,
        implementation_status=(
            "runtime_supported"
        ),
    )


def _collect_source_ids(
    decision: DiagnosticDecision,
    canonical: tuple[KnowledgeCase, ...],
) -> list[str]:
    """Deduplicate source IDs from rule matches and case alignment."""

    values = set(
        decision.source_ids
    )

    for item in canonical:
        values.update(
            item.source_ids
        )

    return sorted(values)


def _grounding_status(
    decision: DiagnosticDecision,
    canonical: tuple[KnowledgeCase, ...],
) -> str:
    """Describe the strongest available grounding level."""

    if decision.fault_diagnosis_blocked:
        return "blocked_by_guard"

    if decision.primary is not None:
        return "rule_matched"

    if canonical:
        return "canonical_support_only"

    return "no_supported_match"


def _source_grounded_hypothesis(
    match: DiagnosticMatch,
    *,
    severity: str,
) -> dict[str, Any]:
    """Build a hypothesis from an executable source-grounded rule match."""

    return {
        "id": match.expected_label,
        "label": match.title,
        "case_id": match.case_id,
        "rule_id": match.rule_id,
        "confidence": None,
        "confidence_type": "source_grounded_rule_match",
        "severity": severity,
        "interpretation": (
            "Structured evidence matched an executable source-grounded "
            "diagnostic rule. The result remains a hypothesis and "
            "requires the documented verification evidence before any "
            "operational intervention."
        ),
        "evidence": [
            {
                "field": field,
                "role": "required_match",
            }
            for field in match.matched_fields
        ],
        "verification_steps": list(
            match.reasoning_basis
        ),
        "source_ids": list(
            match.source_ids
        ),
        "verification_required": (
            match.verification_required
        ),
        "physical_action_authorized": False,
    }


def _build_grounding(
    *,
    decision: DiagnosticDecision,
    canonical: tuple[KnowledgeCase, ...],
    evidence_bundle: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:
    """Build the public source-grounding block attached to diagnosis."""

    matches = decision.matches[
        :top_k
    ]

    return {
        "grounding_status": (
            _grounding_status(
                decision,
                canonical,
            )
        ),
        "fault_diagnosis_blocked": (
            decision.fault_diagnosis_blocked
        ),
        "rule_evidence": (
            evidence_bundle[
                "rule_evidence"
            ]
        ),
        "evidence_provenance": (
            evidence_bundle[
                "evidence_provenance"
            ]
        ),
        "raw_trend_summary": (
            evidence_bundle[
                "raw_trend_summary"
            ]
        ),
        "supplemental_context": (
            evidence_bundle[
                "supplemental_context"
            ]
        ),
        "rule_matches": [
            _serialize_match(item)
            for item in matches
        ],
        "canonical_support": [
            _serialize_case(item)
            for item in canonical
        ],
        "source_ids": (
            _collect_source_ids(
                decision,
                canonical,
            )
        ),
        "verification_required": bool(
            decision.primary
            or canonical
        ),
        "physical_action_authorized": False,
        "policy_note": (
            evidence_bundle[
                "policy_note"
            ]
        ),
    }


def _apply_guard(
    result: dict[str, Any],
    decision: DiagnosticDecision,
) -> dict[str, Any]:
    """Withhold fault diagnosis when an executable guard blocks it."""

    primary = decision.primary

    if primary is None:
        return result

    updated = dict(result)
    updated["insufficient_evidence"] = True
    updated["diagnosis_status"] = (
        "blocked_by_source_grounded_guard"
    )
    updated["hypotheses"] = []
    updated["primary_hypothesis"] = None
    updated["conclusion"] = (
        "A source-grounded diagnostic guard matched the available "
        "structured evidence. AquaMind withheld a fault diagnosis "
        "until the guard condition is resolved or independently "
        "verified."
    )

    notes = list(
        updated.get("notes")
        if isinstance(
            updated.get("notes"),
            list,
        )
        else []
    )

    notes.append(
        f"Blocking rule: {primary.rule_id} / case {primary.case_id}."
    )
    notes.append(
        "No physical action is authorized by this guard result."
    )

    updated["notes"] = notes

    return updated


def _promote_direct_rule_match(
    result: dict[str, Any],
    decision: DiagnosticDecision,
) -> dict[str, Any]:
    """
    Promote a direct diagnostic rule only when the deterministic layer
    did not already produce a supported hypothesis.
    """

    primary = decision.primary

    if (
        primary is None
        or primary.outcome_type
        != "diagnosis"
        or primary.expected_label
        == "normal_operation"
    ):
        return result

    current = result.get(
        "primary_hypothesis"
    )

    if isinstance(current, dict):
        return result

    severity = "warning"

    raw = result.get(
        "overall_severity"
    )

    if isinstance(raw, str) and raw.strip():
        severity = raw

    hypothesis = (
        _source_grounded_hypothesis(
            primary,
            severity=severity,
        )
    )

    updated = dict(result)
    updated["insufficient_evidence"] = False
    updated["diagnosis_status"] = (
        "source_grounded_hypothesis"
    )
    updated["hypotheses"] = [
        hypothesis
    ]
    updated["primary_hypothesis"] = (
        hypothesis
    )
    updated["conclusion"] = (
        "Structured evidence matched a supported source-grounded "
        "diagnostic rule. The result is a hypothesis and requires "
        "verification before operational intervention."
    )

    return updated


def apply_source_grounding(
    *,
    state: AgentState,
    diagnosis_result: dict[str, Any],
    engine: SourceGroundedDiagnosticEngine,
    vocabulary_path: str | Path,
    top_k: int = 5,
) -> dict[str, Any]:
    """Attach source-grounded rule and case evidence to one diagnosis."""

    if not isinstance(
        diagnosis_result,
        dict,
    ):
        raise TypeError(
            "diagnosis_result must be a dictionary"
        )

    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, int)
        or top_k <= 0
    ):
        raise ValueError(
            "top_k must be a positive integer"
        )

    if (
        diagnosis_result.get("success")
        is not True
    ):
        return diagnosis_result

    evidence_bundle = (
        build_runtime_evidence_bundle(
            state,
            vocabulary_path=(
                vocabulary_path
            ),
        )
    )

    decision = engine.decide(
        evidence_bundle[
            "rule_evidence"
        ]
    )

    label = _deterministic_label(
        diagnosis_result
    )

    canonical = _canonical_support(
        engine,
        label,
    )

    updated = dict(
        diagnosis_result
    )

    if decision.fault_diagnosis_blocked:
        updated = _apply_guard(
            updated,
            decision,
        )

    else:
        updated = (
            _promote_direct_rule_match(
                updated,
                decision,
            )
        )

    updated["source_grounding"] = (
        _build_grounding(
            decision=decision,
            canonical=canonical,
            evidence_bundle=evidence_bundle,
            top_k=top_k,
        )
    )

    return updated


def make_source_grounded_diagnosis(
    *,
    base_tool: DiagnosticTool,
    engine: SourceGroundedDiagnosticEngine,
    vocabulary_path: str | Path,
    top_k: int = 5,
) -> DiagnosticTool:
    """Wrap the existing diagnosis tool with source-grounded evidence."""

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:
        result = base_tool(
            state
        )

        try:
            return apply_source_grounding(
                state=state,
                diagnosis_result=result,
                engine=engine,
                vocabulary_path=(
                    vocabulary_path
                ),
                top_k=top_k,
            )

        except EvidenceAdapterError as exc:
            return {
                "success": False,
                "recoverable": False,
                "error": str(exc),
                "diagnosis_status": (
                    "invalid_diagnostic_context"
                ),
            }

    return tool
