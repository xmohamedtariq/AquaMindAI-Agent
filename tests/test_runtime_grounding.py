from pathlib import Path

import pytest

from src.agent.state import AgentState
from src.knowledge.diagnostic_engine import SourceGroundedDiagnosticEngine
from src.knowledge.runtime_grounding import (
    _canonical_support,
    _collect_source_ids,
    _deterministic_label,
    _grounding_status,
    _serialize_case,
    _serialize_match,
    _source_grounded_hypothesis,
    apply_source_grounding,
    make_source_grounded_diagnosis,
)


KNOWLEDGE = Path("knowledge")
VOCAB = KNOWLEDGE / "evidence_vocabulary.json"


def _engine() -> SourceGroundedDiagnosticEngine:
    return SourceGroundedDiagnosticEngine.from_files(
        rules_path=KNOWLEDGE / "diagnostic_rules.json",
        library_path=KNOWLEDGE / "case_library.json",
        registry_path=KNOWLEDGE / "source_registry.json",
    )


def _anomaly_state(
    *,
    context=None,
    anomaly_detected=True,
) -> AgentState:
    state = AgentState(
        task_id="grounding",
        user_request="Investigate RO performance.",
        diagnostic_context=context or {},
    )
    state.add_observation(
        "detect_anomalies",
        {
            "success": True,
            "method": "baseline_relative_change",
            "anomaly_detected": anomaly_detected,
            "overall_severity": "warning",
            "warning_threshold_pct": 5.0,
            "comparisons": {
                "permeate_flow": {"change_pct": -7.0},
                "tds_salt_rejection_pct": {"change_pct": -7.0},
                "pressure_drop": {"change_pct": 8.0},
            },
        },
    )
    return state


def _broad_result(label="scaling_or_colloidal_fouling"):
    return {
        "success": True,
        "recoverable": False,
        "insufficient_evidence": False,
        "diagnosis_status": "hypothesis_generated",
        "hypotheses": [{"id": label}],
        "primary_hypothesis": {"id": label},
        "conclusion": "Broad hypothesis.",
        "notes": [],
    }


def test_serializers_and_helpers() -> None:
    engine = _engine()
    case = engine.case_library.get("RO-SCALE-001")
    assert case is not None
    serialized_case = _serialize_case(case)
    assert serialized_case["case_id"] == "RO-SCALE-001"
    assert serialized_case["physical_action_authorized"] is False

    decision = engine.decide(
        {
            "raw_performance_change": True,
            "temperature_shift": True,
            "normalized_metrics_available": False,
        }
    )
    assert decision.primary is not None
    serialized_match = _serialize_match(decision.primary)
    assert serialized_match["blocks_fault_diagnosis"] is True

    hypothesis = _source_grounded_hypothesis(
        decision.primary,
        severity="warning",
    )
    assert hypothesis["physical_action_authorized"] is False

    assert _deterministic_label(_broad_result()) == (
        "scaling_or_colloidal_fouling"
    )
    assert _deterministic_label({"primary_hypothesis": None}) is None
    assert _deterministic_label({"primary_hypothesis": {"id": ""}}) is None

    canonical = _canonical_support(
        engine,
        "scaling_or_colloidal_fouling",
    )
    assert canonical
    assert _canonical_support(engine, None) == ()

    sources = _collect_source_ids(decision, canonical)
    assert sources == sorted(set(sources))

    assert _grounding_status(decision, canonical) == "blocked_by_guard"


def test_canonical_support_only_for_broad_raw_hypothesis() -> None:
    engine = _engine()
    state = _anomaly_state()

    result = apply_source_grounding(
        state=state,
        diagnosis_result=_broad_result(),
        engine=engine,
        vocabulary_path=VOCAB,
        top_k=5,
    )

    grounding = result["source_grounding"]
    assert grounding["grounding_status"] == "canonical_support_only"
    assert grounding["rule_matches"] == []
    assert grounding["canonical_support"]
    assert grounding["source_ids"]
    assert grounding["physical_action_authorized"] is False
    assert result["primary_hypothesis"]["id"] == (
        "scaling_or_colloidal_fouling"
    )


def test_guard_blocks_diagnosis() -> None:
    engine = _engine()
    state = _anomaly_state(
        context={
            "temperature_shift": True,
            "normalized_metrics_available": False,
        }
    )

    result = apply_source_grounding(
        state=state,
        diagnosis_result=_broad_result(),
        engine=engine,
        vocabulary_path=VOCAB,
    )

    assert result["insufficient_evidence"] is True
    assert result["diagnosis_status"] == (
        "blocked_by_source_grounded_guard"
    )
    assert result["primary_hypothesis"] is None
    assert result["source_grounding"]["fault_diagnosis_blocked"] is True
    assert "Blocking rule:" in result["notes"][-2]


def test_direct_rule_can_promote_unclassified_result() -> None:
    engine = _engine()
    state = _anomaly_state(
        context={
            "permeate_flow_direction": "down",
            "metal_oxide_evidence": True,
        }
    )

    base = {
        "success": True,
        "recoverable": False,
        "insufficient_evidence": True,
        "diagnosis_status": "unclassified_pattern",
        "hypotheses": [],
        "primary_hypothesis": None,
        "conclusion": "Unclassified.",
        "notes": [],
    }

    result = apply_source_grounding(
        state=state,
        diagnosis_result=base,
        engine=engine,
        vocabulary_path=VOCAB,
    )

    assert result["insufficient_evidence"] is False
    assert result["diagnosis_status"] == "source_grounded_hypothesis"
    assert result["primary_hypothesis"]["rule_id"] == "DR-FOUL-004"
    assert result["primary_hypothesis"]["physical_action_authorized"] is False
    assert result["source_grounding"]["grounding_status"] == "rule_matched"


def test_normal_rule_does_not_turn_normal_into_fault_hypothesis() -> None:
    engine = _engine()
    state = _anomaly_state(
        context={"normalized_metrics_available": True},
        anomaly_detected=False,
    )
    base = {
        "success": True,
        "recoverable": False,
        "insufficient_evidence": False,
        "diagnosis_status": "no_actionable_anomaly",
        "hypotheses": [],
        "primary_hypothesis": None,
        "conclusion": "No actionable anomaly.",
    }

    result = apply_source_grounding(
        state=state,
        diagnosis_result=base,
        engine=engine,
        vocabulary_path=VOCAB,
    )

    assert result["diagnosis_status"] == "no_actionable_anomaly"
    assert result["primary_hypothesis"] is None
    assert result["source_grounding"]["grounding_status"] == "rule_matched"


def test_non_diagnostic_rule_match_does_not_promote() -> None:
    engine = _engine()
    state = _anomaly_state(
        context={"scale_control_issue": True},
    )
    base = {
        "success": True,
        "recoverable": False,
        "insufficient_evidence": True,
        "diagnosis_status": "unclassified_pattern",
        "hypotheses": [],
        "primary_hypothesis": None,
        "conclusion": "Unclassified.",
    }

    result = apply_source_grounding(
        state=state,
        diagnosis_result=base,
        engine=engine,
        vocabulary_path=VOCAB,
    )

    # The PRE rule is a risk, not a fault diagnosis.
    assert result["primary_hypothesis"] is None


def test_apply_source_grounding_validation_and_passthrough() -> None:
    engine = _engine()
    state = _anomaly_state()

    with pytest.raises(TypeError):
        apply_source_grounding(
            state=state,
            diagnosis_result="bad",  # type: ignore[arg-type]
            engine=engine,
            vocabulary_path=VOCAB,
        )

    with pytest.raises(ValueError):
        apply_source_grounding(
            state=state,
            diagnosis_result=_broad_result(),
            engine=engine,
            vocabulary_path=VOCAB,
            top_k=0,
        )

    failed = {"success": False, "error": "base failure"}
    assert apply_source_grounding(
        state=state,
        diagnosis_result=failed,
        engine=engine,
        vocabulary_path=VOCAB,
    ) is failed


def test_wrapper_handles_invalid_context_and_base_failure() -> None:
    engine = _engine()

    def base_tool(state):
        return _broad_result()

    tool = make_source_grounded_diagnosis(
        base_tool=base_tool,
        engine=engine,
        vocabulary_path=VOCAB,
    )

    state = _anomaly_state(
        context={"temperature_shift": "invalid"}
    )
    result = tool(state)
    assert result["success"] is False
    assert result["diagnosis_status"] == "invalid_diagnostic_context"

    expected = {"success": False, "error": "base failed"}

    def failing_base(state):
        return expected

    passthrough = make_source_grounded_diagnosis(
        base_tool=failing_base,
        engine=engine,
        vocabulary_path=VOCAB,
    )
    assert passthrough(_anomaly_state()) is expected


def test_helper_edge_branches() -> None:
    from src.knowledge.diagnostic_engine import DiagnosticDecision
    from src.knowledge.runtime_grounding import _apply_guard, _promote_direct_rule_match

    engine = _engine()
    empty = DiagnosticDecision(
        status="no_supported_match",
        primary=None,
        matches=(),
        fault_diagnosis_blocked=False,
    )
    assert _grounding_status(empty, ()) == "no_supported_match"
    original = _broad_result()
    assert _apply_guard(original, empty) is original

    matched = engine.decide(
        {
            "permeate_flow_direction": "down",
            "metal_oxide_evidence": True,
        }
    )
    assert matched.primary is not None

    # Existing deterministic hypotheses are never overwritten.
    assert _promote_direct_rule_match(original, matched) is original

    # Explicit severity is preserved when a direct rule is promoted.
    no_primary = {
        "success": True,
        "primary_hypothesis": None,
        "overall_severity": "critical",
    }
    promoted = _promote_direct_rule_match(no_primary, matched)
    assert promoted["primary_hypothesis"]["severity"] == "critical"
