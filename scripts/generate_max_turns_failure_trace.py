from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.agent.runtime import AquaMindRuntime, RuntimeConfig
from src.agent.state import AgentStatus, TerminationReason
from src.tracing.jsonl import build_trace_records, write_trace_jsonl


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
KNOWLEDGE = ROOT / "knowledge"
TRACES = ROOT / "traces"
EVIDENCE = ROOT / "evidence"

RUNTIME_DIR = TRACES / ".runtime" / "max-turns-failure"
MEMORY_DB = RUNTIME_DIR / "memory.db"
AUDIT_LOG = RUNTIME_DIR / "audit.jsonl"

TRACE_PATH = TRACES / "max_turns_failure.jsonl"
EVIDENCE_PATH = EVIDENCE / "max_turns_failure_generation.txt"
AUDIT_EVIDENCE_PATH = EVIDENCE / "max_turns_failure_audit.jsonl"

TASK_ID = "validation-live-max-turns-failure"
DATASET = "scaling_colloidal_fouling.csv"

EXPECTED_TURNS = 2
EXPECTED_TOOL_CALLS = 2
EXPECTED_LLM_CALLS = 2


def _remove_previous_runtime_artifacts() -> None:
    """
    Start the evidence run from a clean runtime state.

    This prevents previous audit or memory records from being mixed
    with the current MAX_TURNS failure demonstration.
    """

    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    TRACES.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    for path in (
        MEMORY_DB,
        AUDIT_LOG,
        TRACE_PATH,
        EVIDENCE_PATH,
    ):
        if path.exists():
            path.unlink()


def _read_audit_events() -> list[dict]:
    """Read the generated append-only audit events."""

    if not AUDIT_LOG.exists():
        raise RuntimeError(
            f"Expected audit log was not created: {AUDIT_LOG}"
        )

    events: list[dict] = []

    with AUDIT_LOG.open(
        "r",
        encoding="utf-8-sig",
    ) as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()

            if not stripped:
                continue

            try:
                event = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    "Audit log contains invalid JSON at "
                    f"line {line_number}."
                ) from exc

            if not isinstance(event, dict):
                raise RuntimeError(
                    "Audit log contains a non-object JSON record at "
                    f"line {line_number}."
                )

            events.append(event)

    return events


def _assert_no_llm_fallback(
    audit_events: list[dict],
) -> None:
    """
    Reject the evidence run if Gemini failed and the hybrid planner
    silently fell back to deterministic reasoning.
    """

    fallback_events = [
        event
        for event in audit_events
        if event.get("event_type") == "llm_reasoning"
        and event.get("action")
        == "fallback_to_deterministic_planner"
        and event.get("status") == "fallback"
    ]

    if fallback_events:
        raise RuntimeError(
            "Gemini reasoning fallback was detected. "
            "This evidence run requires live Gemini reasoning on "
            "every operational turn."
        )


def _verify_live_failure(
    result: dict,
) -> tuple[object, dict, list[dict]]:
    """Verify that this is a genuine live MAX_TURNS task failure."""

    state = result["state"]
    cost_summary = result.get("cost_summary", {})
    audit_integrity = result.get("audit_integrity", {})

    if state.status != AgentStatus.FAILED:
        raise RuntimeError(
            "Expected failed agent status, "
            f"got {state.status.value}."
        )

    if (
        state.termination_reason
        != TerminationReason.MAX_TURNS_REACHED
    ):
        actual = (
            state.termination_reason.value
            if state.termination_reason is not None
            else None
        )

        raise RuntimeError(
            "Expected MAX_TURNS_REACHED, "
            f"got {actual}."
        )

    if state.turn_count != EXPECTED_TURNS:
        raise RuntimeError(
            f"Expected exactly {EXPECTED_TURNS} turns, "
            f"got {state.turn_count}."
        )

    if state.tool_call_count != EXPECTED_TOOL_CALLS:
        raise RuntimeError(
            f"Expected exactly {EXPECTED_TOOL_CALLS} tool calls, "
            f"got {state.tool_call_count}."
        )

    llm_call_count = int(
        cost_summary.get("call_count", 0)
    )

    total_input_tokens = int(
        cost_summary.get("total_input_tokens", 0)
    )

    total_output_tokens = int(
        cost_summary.get("total_output_tokens", 0)
    )

    total_cost_usd = float(
        cost_summary.get("total_cost_usd", 0.0)
    )

    if llm_call_count != EXPECTED_LLM_CALLS:
        raise RuntimeError(
            f"Expected exactly {EXPECTED_LLM_CALLS} live Gemini "
            f"reasoning calls, got {llm_call_count}."
        )

    if total_input_tokens <= 0:
        raise RuntimeError(
            "Live Gemini evidence is invalid: "
            "provider-reported input token count is zero."
        )

    if total_output_tokens <= 0:
        raise RuntimeError(
            "Live Gemini evidence is invalid: "
            "provider-reported output token count is zero."
        )

    if total_cost_usd <= 0.0:
        raise RuntimeError(
            "Live Gemini evidence is invalid: "
            "task cost is zero."
        )

    if audit_integrity.get("valid") is not True:
        raise RuntimeError(
            "Audit integrity verification failed."
        )

    audit_events = _read_audit_events()
    _assert_no_llm_fallback(audit_events)

    if not state.observations:
        raise RuntimeError(
            "Expected real operational observations before failure."
        )

    observed_tools = [
        str(item.get("source"))
        for item in state.observations
        if isinstance(item, dict)
    ]

    expected_tools = [
        "validate_sensor_data",
        "calculate_plant_kpis",
    ]

    if observed_tools[:2] != expected_tools:
        raise RuntimeError(
            "Unexpected operational tool sequence. "
            f"Expected {expected_tools}, got {observed_tools[:2]}."
        )

    return state, cost_summary, audit_events


def _write_evidence_summary(
    *,
    state: object,
    cost_summary: dict,
    audit_events: list[dict],
    audit_integrity: dict,
) -> None:
    """Write a human-readable evidence summary for assessment."""

    metadata_status = "CONSISTENT_VERIFIED"

    lines = [
        "AquaMindAI-Agent - Live MAX_TURNS Failure Evidence",
        "=" * 58,
        "",
        "Evidence classification: GENUINE TASK FAILURE",
        "Runtime mode: LIVE",
        "LLM enabled: True",
        "LLM provider: Google Gemini",
        "Usage source: provider-reported Gemini usage metadata",
        "Deterministic LLM fallback used: False",
        "",
        f"Task ID: {TASK_ID}",
        f"Dataset: {DATASET}",
        f"Status: {state.status.value}",
        (
            "Termination reason: "
            f"{state.termination_reason.value}"
        ),
        f"Turn count: {state.turn_count}",
        f"Tool call count: {state.tool_call_count}",
        (
            "Observed tools: "
            + ", ".join(
                str(item.get("source"))
                for item in state.observations
                if isinstance(item, dict)
            )
        ),
        "",
        "Live Gemini evidence",
        "-" * 58,
        (
            "LLM call count: "
            f"{cost_summary['call_count']}"
        ),
        (
            "Provider-reported input tokens: "
            f"{cost_summary['total_input_tokens']}"
        ),
        (
            "Provider-reported output tokens: "
            f"{cost_summary['total_output_tokens']}"
        ),
        (
            "Provider-reported cached input tokens: "
            f"{cost_summary['total_cached_input_tokens']}"
        ),
        (
            "Total task cost USD: "
            f"{cost_summary['total_cost_usd']:.10f}"
        ),
        (
            "Budget cap USD: "
            f"{cost_summary['budget_cap_usd']:.2f}"
        ),
        "",
        "Integrity evidence",
        "-" * 58,
        (
            "Audit integrity valid: "
            f"{audit_integrity['valid']}"
        ),
        (
            "Audit event count: "
            f"{audit_integrity['event_count']}"
        ),
        (
            "Parsed audit events: "
            f"{len(audit_events)}"
        ),
        f"Metadata status: {metadata_status}",
        "",
        "Final answer at termination:",
        repr(state.final_answer),
        "",
        "Interpretation",
        "-" * 58,
        (
            "The agent executed two real operational turns with live "
            "Gemini reasoning enabled. Gemini usage was recorded from "
            "provider-reported usage metadata and produced non-zero "
            "token usage and task cost. The agent performed "
            "validate_sensor_data and calculate_plant_kpis, then the "
            "configured max_turns=2 hard limit terminated the task "
            "with MAX_TURNS_REACHED. No Gemini reasoning fallback was "
            "detected, and the append-only audit chain passed "
            "integrity verification."
        ),
        "",
        (
            "The separate SAFETY_BLOCK trace demonstrates successful "
            "safety enforcement and is not used as the required "
            "task-failure trace."
        ),
        "",
    ]

    EVIDENCE_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    _remove_previous_runtime_artifacts()

    runtime = AquaMindRuntime(
        RuntimeConfig(
            dataset_path=DATASET,
            allowed_data_root=DATA,
            knowledge_root=KNOWLEDGE,
            memory_db_path=MEMORY_DB,
            audit_log_path=AUDIT_LOG,
            budget_cap_usd=0.10,
            max_turns=EXPECTED_TURNS,
            llm_enabled=True,
        )
    )

    result = runtime.run(
        task_id=TASK_ID,
        user_request=(
            "Investigate the RO performance decline, identify the most "
            "defensible source-grounded hypothesis, and produce safe "
            "verification recommendations."
        ),
        plant_id="aquamind-demo-plant",
    )

    state, cost_summary, audit_events = (
        _verify_live_failure(result)
    )

    records = build_trace_records(
        result,
        scenario="live_max_turns_exhaustion",
        dataset=DATASET,
    )

    destination = write_trace_jsonl(
        TRACE_PATH,
        records,
    )

    _write_evidence_summary(
        state=state,
        cost_summary=cost_summary,
        audit_events=audit_events,
        audit_integrity=result["audit_integrity"],
    )

    shutil.copy2(
        AUDIT_LOG,
        AUDIT_EVIDENCE_PATH,
    )

    if AUDIT_EVIDENCE_PATH.read_bytes() != AUDIT_LOG.read_bytes():
        raise RuntimeError(
            "Persisted audit evidence differs from verified runtime audit."
        )

    print("")
    print("=" * 64)
    print("PASS: LIVE GEMINI MAX_TURNS_REACHED")
    print("=" * 64)
    print(f"trace={destination}")
    print(f"evidence={EVIDENCE_PATH}")
    print(f"status={state.status.value}")
    print(
        "termination_reason="
        f"{state.termination_reason.value}"
    )
    print(f"turns={state.turn_count}")
    print(f"tool_calls={state.tool_call_count}")
    print(
        "llm_calls="
        f"{cost_summary['call_count']}"
    )
    print(
        "input_tokens="
        f"{cost_summary['total_input_tokens']}"
    )
    print(
        "output_tokens="
        f"{cost_summary['total_output_tokens']}"
    )
    print(
        "total_cost_usd="
        f"{cost_summary['total_cost_usd']:.10f}"
    )
    print(
        "audit_integrity="
        f"{result['audit_integrity']['valid']}"
    )
    print("llm_fallback=False")
    print("metadata_status=CONSISTENT_VERIFIED")
    print(
        "final_answer="
        f"{state.final_answer!r}"
    )
    print("=" * 64)


if __name__ == "__main__":
    main()