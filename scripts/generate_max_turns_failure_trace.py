from pathlib import Path

from src.agent.runtime import AquaMindRuntime, RuntimeConfig
from src.agent.state import TerminationReason
from src.tracing.jsonl import build_trace_records, write_trace_jsonl


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
KNOWLEDGE = ROOT / "knowledge"
TRACES = ROOT / "traces"
RUNTIME_DIR = TRACES / ".runtime" / "max-turns-failure"


def main() -> None:
    TRACES.mkdir(parents=True, exist_ok=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    dataset = "scaling_colloidal_fouling.csv"

    runtime = AquaMindRuntime(
        RuntimeConfig(
            dataset_path=dataset,
            allowed_data_root=DATA,
            knowledge_root=KNOWLEDGE,
            memory_db_path=RUNTIME_DIR / "memory.db",
            audit_log_path=RUNTIME_DIR / "audit.jsonl",
            budget_cap_usd=0.10,
            max_turns=2,
            llm_enabled=False,
        )
    )

    result = runtime.run(
        task_id="validation-max-turns-failure",
        user_request=(
            "Investigate the RO performance decline, identify the most "
            "defensible source-grounded hypothesis, and produce safe "
            "verification recommendations."
        ),
        plant_id="aquamind-demo-plant",
    )

    state = result["state"]

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
            f"got {actual}"
        )

    if state.turn_count != 2:
        raise RuntimeError(
            f"Expected exactly 2 turns, got {state.turn_count}"
        )

    if state.tool_call_count != 2:
        raise RuntimeError(
            "Expected exactly 2 tool calls, "
            f"got {state.tool_call_count}"
        )

    if (
        result.get("audit_integrity", {}).get("valid")
        is not True
    ):
        raise RuntimeError(
            "Audit integrity verification failed."
        )

    records = build_trace_records(
        result,
        scenario="max_turns_exhaustion",
        dataset=dataset,
    )

    destination = write_trace_jsonl(
        TRACES / "max_turns_failure.jsonl",
        records,
    )

    print("PASS: MAX_TURNS_REACHED")
    print(f"trace={destination}")
    print(f"status={state.status.value}")
    print(
        "termination_reason="
        f"{state.termination_reason.value}"
    )
    print(f"turns={state.turn_count}")
    print(f"tool_calls={state.tool_call_count}")
    print(
        "audit_integrity="
        f"{result['audit_integrity']['valid']}"
    )
    print(
        "final_answer="
        f"{state.final_answer}"
    )


if __name__ == "__main__":
    main()
