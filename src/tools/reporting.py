from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from src.agent.state import AgentState


VALIDATION_SOURCE = "validate_sensor_data"
KPI_SOURCE = "calculate_plant_kpis"
ANOMALY_SOURCE = "detect_anomalies"
KNOWLEDGE_SOURCE = "search_operational_knowledge"
MEMORY_SOURCE = "search_incident_memory"
DIAGNOSIS_SOURCE = "diagnose_issue"


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _failure(
    message: str,
) -> dict[str, Any]:
    """Return a standard reporting failure."""

    return {
        "success": False,
        "recoverable": False,
        "error": message,
    }


def _latest_observation(
    state: AgentState,
    source: str,
) -> dict[str, Any] | None:
    """
    Return the latest successful dictionary observation
    produced by a specific AquaMind tool.
    """

    for observation in reversed(
        state.observations
    ):
        if (
            observation.get("source")
            != source
        ):
            continue

        content = observation.get(
            "content"
        )

        if not isinstance(
            content,
            dict,
        ):
            continue

        if (
            content.get("success")
            is not True
        ):
            continue

        return content

    return None


def _dedupe_strings(
    values: list[Any],
) -> list[str]:
    """Normalize and deduplicate non-empty strings."""

    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(
            value,
            str,
        ):
            continue

        normalized = value.strip()

        if not normalized:
            continue

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        result.append(
            normalized
        )

    return result


def _collect_recommendations(
    state: AgentState,
    diagnosis: dict[str, Any],
) -> list[str]:
    """
    Combine agent recommendations with diagnostic
    verification steps without duplication.
    """

    candidates: list[Any] = list(
        state.recommendations
    )

    primary = diagnosis.get(
        "primary_hypothesis"
    )

    if isinstance(
        primary,
        dict,
    ):
        verification_steps = (
            primary.get(
                "verification_steps"
            )
        )

        if isinstance(
            verification_steps,
            list,
        ):
            candidates.extend(
                verification_steps
            )

    return _dedupe_strings(
        candidates
    )


def build_incident_report(
    state: AgentState,
    *,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """
    Build AquaMind's structured in-memory incident report.

    Report generation itself does not perform a physical
    action and does not modify plant equipment.
    """

    diagnosis = _latest_observation(
        state,
        DIAGNOSIS_SOURCE,
    )

    if diagnosis is None:
        return _failure(
            (
                "A successful diagnosis is required "
                "before an incident report can be "
                "generated."
            )
        )

    validation = _latest_observation(
        state,
        VALIDATION_SOURCE,
    )

    kpis = _latest_observation(
        state,
        KPI_SOURCE,
    )

    anomalies = _latest_observation(
        state,
        ANOMALY_SOURCE,
    )

    knowledge = _latest_observation(
        state,
        KNOWLEDGE_SOURCE,
    )

    memory = _latest_observation(
        state,
        MEMORY_SOURCE,
    )

    recommendations = (
        _collect_recommendations(
            state,
            diagnosis,
        )
    )

    primary_hypothesis = (
        diagnosis.get(
            "primary_hypothesis"
        )
    )

    if not isinstance(
        primary_hypothesis,
        dict,
    ):
        primary_hypothesis = None

    conclusion = diagnosis.get(
        "conclusion"
    )

    if not isinstance(
        conclusion,
        str,
    ) or not conclusion.strip():
        conclusion = (
            "No diagnostic conclusion "
            "was produced."
        )

    report = {
        "report_version":
            "1.0",
        "generated_at":
            generated_at
            or _utc_now(),
        "task_id":
            state.task_id,
        "plant_id":
            state.plant_id,
        "user_request":
            state.user_request,
        "executive_summary":
            conclusion,
        "diagnosis_status":
            diagnosis.get(
                "diagnosis_status",
                "unknown",
            ),
        "primary_hypothesis":
            primary_hypothesis,
        "recommendations":
            recommendations,
        "evidence": {
            "validation":
                validation,
            "plant_kpis":
                kpis,
            "anomaly_analysis":
                anomalies,
            "operational_knowledge":
                knowledge,
            "historical_memory":
                memory,
            "diagnosis":
                diagnosis,
        },
        "execution": {
            "turn_count":
                state.turn_count,
            "tool_call_count":
                state.tool_call_count,
            "cumulative_cost_usd":
                state.cumulative_cost_usd,
            "input_tokens":
                state.input_tokens,
            "output_tokens":
                state.output_tokens,
        },
        "safety_notice": (
            "AquaMind provides analytical and "
            "diagnostic decision support only. "
            "This report does not authorize direct "
            "physical control of pumps, valves, "
            "setpoints, cleaning cycles, or plant "
            "shutdown operations."
        ),
    }

    return {
        "success": True,
        "recoverable": False,
        "report": report,
    }


def generate_incident_report_from_state(
    state: AgentState,
) -> dict[str, Any]:
    """AgentLoop-compatible incident reporting tool."""

    return build_incident_report(
        state
    )


def make_generate_incident_report() -> Callable[
    [AgentState],
    dict[str, Any],
]:
    """Create the AgentLoop-compatible report tool."""

    def tool(
        state: AgentState,
    ) -> dict[str, Any]:

        return (
            generate_incident_report_from_state(
                state
            )
        )

    return tool