# AquaMind ReAct Runtime

## Purpose

AquaMind remains a **single autonomous agent**. Its execution loop is expressed as:

`REASON -> ACT -> OBSERVE -> REFLECT -> repeat or terminate`

AquaMindAI-Agent uses a production-oriented Plan/Act/Observe/Reflect execution loop. The runtime records concise `decision_summary` events for auditability. It does **not** store or expose private chain-of-thought reasoning.

## Source-grounded diagnosis

`diagnose_issue` remains one allowed tool. Internally it now combines:

1. the existing deterministic RO troubleshooting classifier;
2. an evidence adapter;
3. the 90-rule source-grounded diagnostic engine;
4. the 90-case canonical case library;
5. source IDs and verification requirements.

This preserves a focused single-agent architecture with deterministic safety boundaries.

## Evidence policy

Raw baseline-relative telemetry trends are **not** silently promoted to normalized diagnostic-rule directions. The rule engine receives:

- structured evidence fields declared in `knowledge/evidence_vocabulary.json`;
- `raw_performance_change` derived from the anomaly detector;
- explicit structured diagnostic context when available.

Raw percentage changes remain visible in `raw_trend_summary` for transparency.

This avoids claiming formal ASTM/OEM normalization where AquaMind has not actually performed it.

## Guard behavior

If a source-grounded guard matches, AquaMind withholds fault diagnosis and terminates safely with `INSUFFICIENT_EVIDENCE`. Examples include unresolved normalization confounders, data-quality blockers, unsafe plant-control requests, and other guard conditions encoded in the knowledge base.

## Safety boundary

Source grounding never authorizes physical plant action. Every grounding block contains:

`physical_action_authorized: false`

AquaMind remains analytical decision support only.

## ReAct trace

`AgentState.react_trace` contains events such as:

- `reason` - concise decision summary and planned action;
- `act` - approved tool execution;
- `observe` - audit-safe result summary;
- `reflect` - continue/retry/stop/approval decision;
- `terminate` - final termination reason.

The runtime result exposes this list as `react_trace`, which will later be serialized into the core JSONL validation traces.
