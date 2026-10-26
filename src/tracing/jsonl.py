import json
from pathlib import Path
from typing import Any

from src.agent.state import AgentState


_TRACE_SCHEMA = "aquamind.execution_trace.v1"

_SCALAR_KEYS = (
    "success",
    "recoverable",
    "error",
    "message",
    "row_count",
    "valid_row_count",
    "invalid_row_count",
    "removed_row_count",
    "duplicate_count",
    "duplicates_removed",
    "missing_value_count",
    "quality_score",
    "anomaly_detected",
    "overall_severity",
    "diagnosis_status",
    "insufficient_evidence",
    "match_count",
    "permission_level",
)


def _scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _grounding_summary(content: dict[str, Any]) -> dict[str, Any] | None:
    grounding = content.get("source_grounding")
    if not isinstance(grounding, dict):
        return None

    summary: dict[str, Any] = {}
    for key in (
        "grounding_status",
        "fault_diagnosis_blocked",
        "physical_action_authorized",
    ):
        if key in grounding and _scalar(grounding[key]):
            summary[key] = grounding[key]

    source_ids = grounding.get("source_ids")
    if isinstance(source_ids, list):
        summary["source_ids"] = [
            item for item in source_ids if isinstance(item, str)
        ]

    rule_matches = grounding.get("rule_matches")
    if isinstance(rule_matches, list):
        compact_matches = []
        for match in rule_matches:
            if not isinstance(match, dict):
                continue
            compact = {
                key: match[key]
                for key in ("rule_id", "case_id", "outcome_type", "priority")
                if key in match and _scalar(match[key])
            }
            if compact:
                compact_matches.append(compact)
        if compact_matches:
            summary["rule_matches"] = compact_matches

    return summary or None


def _primary_hypothesis_summary(content: dict[str, Any]) -> dict[str, Any] | None:
    hypothesis = content.get("primary_hypothesis")
    if not isinstance(hypothesis, dict):
        return None

    summary = {
        key: hypothesis[key]
        for key in (
            "id",
            "label",
            "rule_id",
            "case_id",
            "severity",
            "physical_action_authorized",
        )
        if key in hypothesis and _scalar(hypothesis[key])
    }
    return summary or None


def _report_summary(report: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}

    for key in (
        "executive_summary",
        "overall_severity",
        "diagnosis_status",
    ):
        if key in report and _scalar(report[key]):
            summary[key] = report[key]

    recommendations = report.get("recommendations")
    if isinstance(recommendations, list):
        summary["recommendations"] = [
            item for item in recommendations[:3] if isinstance(item, str)
        ]

    grounding = _grounding_summary(report)
    if grounding is not None:
        summary["source_grounding"] = grounding

    return summary


def _observation_summary(source: str, content: Any) -> dict[str, Any]:
    if not isinstance(content, dict):
        return {"result_type": type(content).__name__}

    summary: dict[str, Any] = {
        key: content[key]
        for key in _SCALAR_KEYS
        if key in content and _scalar(content[key])
    }

    hypothesis = _primary_hypothesis_summary(content)
    if hypothesis is not None:
        summary["primary_hypothesis"] = hypothesis

    grounding = _grounding_summary(content)
    if grounding is not None:
        summary["source_grounding"] = grounding

    if source == "generate_incident_report":
        report = content.get("report")
        if isinstance(report, dict):
            summary["report"] = _report_summary(report)

    # Preserve compact data-quality evidence without exporting raw telemetry.
    for key in (
        "issues",
        "warnings",
        "repairs",
        "recovery_actions",
    ):
        value = content.get(key)
        if isinstance(value, list):
            safe_items = [
                item for item in value if isinstance(item, (str, int, float, bool))
            ]
            if safe_items:
                summary[key] = safe_items[:20]

    return summary


def _recovery_evidence(state: AgentState) -> dict[str, Any] | None:
    """Return compact evidence that data-quality recovery occurred."""

    for index, observation in enumerate(state.observations):
        if not isinstance(observation, dict):
            continue
        if observation.get("source") != "validate_sensor_data":
            continue

        content = observation.get("content")
        if not isinstance(content, dict):
            continue

        raw_actions = content.get("recovery_actions")
        if not isinstance(raw_actions, list):
            return None

        actions = [
            item
            for item in raw_actions
            if isinstance(item, (str, int, float, bool))
        ]
        if not actions:
            return None

        raw_issues = content.get("issues")
        issues = []
        if isinstance(raw_issues, list):
            issues = [
                item
                for item in raw_issues
                if isinstance(item, (str, int, float, bool))
            ][:20]

        evidence: dict[str, Any] = {
            "record_type": "recovery_evidence",
            "source": "validate_sensor_data",
            "data_quality_degradation_detected": bool(issues),
            "recovery_applied": True,
            "recovery_actions": actions[:20],
            "investigation_continued": index < len(state.observations) - 1,
            "decision_summary": (
                "Data-quality issues were detected and recovery actions were "
                "applied before downstream analysis continued."
            ),
        }

        if issues:
            evidence["issues_detected"] = issues

        for source_key, target_key in (
            ("removed_row_count", "removed_row_count"),
            ("quality_score", "post_recovery_quality_score"),
            ("success", "validation_success_after_recovery"),
        ):
            value = content.get(source_key)
            if _scalar(value):
                evidence[target_key] = value

        return evidence

    return None


def build_trace_records(
    result: dict[str, Any],
    *,
    scenario: str,
    dataset: str,
) -> list[dict[str, Any]]:
    """Build a compact, auditable JSONL trace from one runtime result."""

    state = result.get("state")
    if not isinstance(state, AgentState):
        raise TypeError("result['state'] must be an AgentState")
    if not scenario.strip():
        raise ValueError("scenario must not be empty")
    if not dataset.strip():
        raise ValueError("dataset must not be empty")

    records: list[dict[str, Any]] = [
        {
            "record_type": "trace_header",
            "schema": _TRACE_SCHEMA,
            "scenario": scenario,
            "task_id": state.task_id,
            "dataset": dataset,
            "plant_id": state.plant_id,
            "user_request": state.user_request,
            "trace_policy": "audit_safe_decision_summaries_only",
        }
    ]

    safety = result.get("safety_assessment")
    records.append(
        {
            "record_type": "safety_assessment",
            "assessment": safety,
        }
    )

    for event in result.get("react_trace", []):
        if isinstance(event, dict):
            records.append(
                {
                    "record_type": "react_event",
                    **event,
                }
            )

    for observation in state.observations:
        if not isinstance(observation, dict):
            continue
        source = str(observation.get("source", "unknown"))
        records.append(
            {
                "record_type": "tool_observation",
                "source": source,
                "summary": _observation_summary(
                    source,
                    observation.get("content"),
                ),
            }
        )

    recovery = _recovery_evidence(state)
    if recovery is not None:
        records.append(recovery)

    termination = (
        state.termination_reason.value
        if state.termination_reason is not None
        else None
    )

    records.append(
        {
            "record_type": "trace_outcome",
            "status": state.status.value,
            "termination_reason": termination,
            "turn_count": state.turn_count,
            "tool_call_count": state.tool_call_count,
            "final_answer": state.final_answer,
            "cost_summary": result.get("cost_summary"),
            "audit_integrity": result.get("audit_integrity"),
        }
    )

    return records


def write_trace_jsonl(
    path: str | Path,
    records: list[dict[str, Any]],
) -> Path:
    """Write trace records as UTF-8 JSON Lines."""

    if not records:
        raise ValueError("records must not be empty")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            handle.write("\n")

    return destination
