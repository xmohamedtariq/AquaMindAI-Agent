import json
from pathlib import Path

import pytest

from src.agent.state import AgentState, AgentStatus, TerminationReason
from src.tracing.jsonl import build_trace_records, write_trace_jsonl


def _result() -> dict:
    state = AgentState(task_id="trace-1", user_request="Investigate RO data.")
    state.add_react_event(
        phase="reason",
        decision_summary="Validate data first.",
        action="validate_sensor_data",
        status="planned",
    )
    state.add_observation(
        "validate_sensor_data",
        {
            "success": True,
            "recoverable": True,
            "row_count": 20,
            "records": [{"secret_raw_row": 1}],
            "issues": ["duplicate timestamp detected"],
            "recovery_actions": ["duplicate timestamp removed"],
            "removed_row_count": 1,
            "quality_score": 98.5,
        },
    )
    state.add_observation(
        "diagnose_issue",
        {
            "success": True,
            "diagnosis_status": "source_grounded_hypothesis",
            "primary_hypothesis": {
                "id": "fouling",
                "case_id": "RO-FOUL-001",
                "physical_action_authorized": False,
            },
            "source_grounding": {
                "grounding_status": "rule_matched",
                "fault_diagnosis_blocked": False,
                "physical_action_authorized": False,
                "source_ids": ["SRC-1", 5],
                "rule_matches": [
                    {
                        "rule_id": "DR-1",
                        "case_id": "RO-FOUL-001",
                        "outcome_type": "diagnosis",
                        "priority": 10,
                        "extra": "omit",
                    },
                    "bad",
                ],
            },
        },
    )
    state.add_observation(
        "generate_incident_report",
        {
            "success": True,
            "report": {
                "executive_summary": "Summary.",
                "overall_severity": "warning",
                "recommendations": ["Verify trend.", 9, "Inspect evidence.", "Third."],
                "source_grounding": {
                    "grounding_status": "rule_matched",
                    "source_ids": ["SRC-1"],
                },
            },
        },
    )
    state.add_observation("custom", [1, 2, 3])
    state.terminate(TerminationReason.FINAL_ANSWER, "Completed.")
    assert state.status == AgentStatus.COMPLETED
    return {
        "state": state,
        "react_trace": list(state.react_trace),
        "safety_assessment": {"unsafe": False},
        "cost_summary": {"total_cost_usd": 0.0},
        "audit_integrity": {"valid": True},
    }


def test_build_trace_records_is_compact_and_safe() -> None:
    records = build_trace_records(
        _result(), scenario="success", dataset="demo.csv"
    )
    assert records[0]["schema"] == "aquamind.execution_trace.v1"
    assert records[1]["record_type"] == "safety_assessment"
    assert any(r.get("record_type") == "react_event" for r in records)

    observations = [r for r in records if r.get("record_type") == "tool_observation"]
    validation = next(r for r in observations if r["source"] == "validate_sensor_data")
    assert validation["summary"]["recoverable"] is True
    assert validation["summary"]["issues"] == ["duplicate timestamp detected"]
    assert validation["summary"]["recovery_actions"] == [
        "duplicate timestamp removed"
    ]
    assert "records" not in validation["summary"]

    recovery = next(r for r in records if r["record_type"] == "recovery_evidence")
    assert recovery["data_quality_degradation_detected"] is True
    assert recovery["recovery_applied"] is True
    assert recovery["recovery_actions"] == ["duplicate timestamp removed"]
    assert recovery["issues_detected"] == ["duplicate timestamp detected"]
    assert recovery["removed_row_count"] == 1
    assert recovery["post_recovery_quality_score"] == 98.5
    assert recovery["validation_success_after_recovery"] is True
    assert recovery["investigation_continued"] is True

    diagnosis = next(r for r in observations if r["source"] == "diagnose_issue")
    grounding = diagnosis["summary"]["source_grounding"]
    assert grounding["source_ids"] == ["SRC-1"]
    assert grounding["rule_matches"][0]["rule_id"] == "DR-1"
    assert "extra" not in grounding["rule_matches"][0]

    report = next(r for r in observations if r["source"] == "generate_incident_report")
    assert report["summary"]["report"]["recommendations"] == [
        "Verify trend.", "Inspect evidence."
    ]

    custom = next(r for r in observations if r["source"] == "custom")
    assert custom["summary"] == {"result_type": "list"}

    assert records[-1]["termination_reason"] == "FINAL_ANSWER"


def test_build_trace_records_validates_inputs() -> None:
    with pytest.raises(TypeError):
        build_trace_records({}, scenario="x", dataset="x.csv")

    result = _result()
    with pytest.raises(ValueError):
        build_trace_records(result, scenario=" ", dataset="x.csv")
    with pytest.raises(ValueError):
        build_trace_records(result, scenario="x", dataset=" ")


def test_write_trace_jsonl(tmp_path: Path) -> None:
    records = build_trace_records(_result(), scenario="x", dataset="x.csv")
    path = write_trace_jsonl(tmp_path / "nested" / "trace.jsonl", records)
    assert path.exists()
    loaded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert loaded == records

    with pytest.raises(ValueError):
        write_trace_jsonl(tmp_path / "empty.jsonl", [])


def test_trace_helper_edge_branches() -> None:
    from src.tracing.jsonl import (
        _grounding_summary,
        _observation_summary,
        _primary_hypothesis_summary,
        _report_summary,
    )

    assert _grounding_summary({}) is None
    assert _grounding_summary({"source_grounding": []}) is None
    assert _grounding_summary({"source_grounding": {"source_ids": "bad"}}) is None
    assert _grounding_summary(
        {
            "source_grounding": {
                "source_ids": [],
                "rule_matches": [
                    {"rule_id": []},
                    {},
                ],
            }
        }
    ) == {"source_ids": []}
    assert _grounding_summary(
        {"source_grounding": {"rule_matches": "bad"}}
    ) is None

    assert _primary_hypothesis_summary({}) is None
    assert _primary_hypothesis_summary({"primary_hypothesis": []}) is None
    assert _primary_hypothesis_summary({"primary_hypothesis": {"id": []}}) is None

    assert _report_summary({}) == {}
    assert _report_summary({"recommendations": "bad"}) == {}
    assert _report_summary({"source_grounding": []}) == {}

    assert _observation_summary(
        "generate_incident_report",
        {"report": "bad", "warnings": [object()]},
    ) == {}

    from src.tracing.jsonl import _recovery_evidence

    empty_state = AgentState(task_id="empty", user_request="x")
    assert _recovery_evidence(empty_state) is None
    empty_state.observations.append("bad")  # type: ignore[arg-type]
    empty_state.add_observation("custom", {})
    empty_state.add_observation("validate_sensor_data", [])
    assert _recovery_evidence(empty_state) is None

    no_actions_state = AgentState(task_id="no-actions", user_request="x")
    no_actions_state.add_observation("validate_sensor_data", {"recovery_actions": "bad"})
    assert _recovery_evidence(no_actions_state) is None

    filtered_actions_state = AgentState(task_id="filtered-actions", user_request="x")
    filtered_actions_state.add_observation("validate_sensor_data", {"recovery_actions": [object()]})
    assert _recovery_evidence(filtered_actions_state) is None

    compact_state = AgentState(task_id="compact", user_request="x")
    compact_state.add_observation(
        "validate_sensor_data",
        {
            "recovery_actions": ["fixed", object()],
            "issues": ["issue", object()],
            "removed_row_count": [],
            "quality_score": 99.0,
            "success": True,
        },
    )
    compact = _recovery_evidence(compact_state)
    assert compact is not None
    assert compact["recovery_actions"] == ["fixed"]
    assert compact["issues_detected"] == ["issue"]
    assert "removed_row_count" not in compact
    assert compact["investigation_continued"] is False

    no_issues_state = AgentState(task_id="no-issues", user_request="x")
    no_issues_state.add_observation(
        "validate_sensor_data",
        {"recovery_actions": ["fixed"], "issues": "bad"},
    )
    no_issues = _recovery_evidence(no_issues_state)
    assert no_issues is not None
    assert no_issues["data_quality_degradation_detected"] is False
    assert "issues_detected" not in no_issues

    no_recovery_result = _result()
    validation_content = no_recovery_result["state"].observations[0]["content"]
    validation_content.pop("recovery_actions")
    records_without_recovery = build_trace_records(
        no_recovery_result, scenario="no-recovery", dataset="demo.csv"
    )
    assert not any(
        record.get("record_type") == "recovery_evidence"
        for record in records_without_recovery
    )

    result = _result()
    state = result["state"]
    state.react_trace.append("bad")  # type: ignore[arg-type]
    result["react_trace"].append("bad")  # type: ignore[arg-type]
    state.observations.append("bad")  # type: ignore[arg-type]
    records = build_trace_records(result, scenario="edge", dataset="edge.csv")
    assert records[-1]["record_type"] == "trace_outcome"
