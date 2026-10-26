# AquaMindAI-Agent — Execution Trace Evidence

AquaMindAI-Agent exports audit-safe JSONL execution traces for reliability, safety, and operational validation.

## Core validation traces

- `traces/source_grounded_fouling.jsonl`
- `traces/near_failure_recovery.jsonl`
- `traces/explicit_failure.jsonl`

Two additional Day-2 evidence traces are generated:

- `traces/normal_operation.jsonl`
- `traces/membrane_integrity.jsonl`

## Trace contents

Each trace contains:

1. a trace header,
2. request-boundary safety assessment,
3. ReAct decision-summary events (`reason`, `act`, `observe`, `reflect`, `terminate`),
4. compact tool-observation summaries without raw telemetry rows,
5. an explicit `recovery_evidence` record when data-quality recovery actions were applied,
6. a final outcome with termination reason, tool-call count, cost summary, and audit-integrity result.

The trace intentionally records concise operational decision summaries rather than private chain-of-thought.

## Generation

Run from the repository root:

```powershell
python -m scripts.generate_validation_traces
```

The generator uses the committed synthetic scenario bank. It does not claim that the traces are real-plant incidents.

## Expected behavior

- `source_grounded_fouling.jsonl` must finish with `FINAL_ANSWER`.
- `near_failure_recovery.jsonl` must contain explicit `recovery_evidence` showing detected data-quality issues, applied recovery actions, and that downstream investigation continued.
- `explicit_failure.jsonl` must finish with `SAFETY_BLOCK` and `tool_call_count = 0`.

Do not manually edit the official traces after generation. Regenerate them from the committed code and scenario data instead.
