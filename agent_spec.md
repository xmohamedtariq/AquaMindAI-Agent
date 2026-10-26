# AquaMindAI-Agent — Agent Specification

**Project:** AquaMindAI-Agent
**Product:** Autonomous AI Agent for Desalination Operations Intelligence

**Domain:** Data Analysis
**Agent Type:** Single autonomous ReAct agent
**Application Domain:** Reverse Osmosis Desalination Operations & Maintenance

## 1. Goal

AquaMindAI-Agent autonomously analyzes reverse-osmosis desalination operational data, detects abnormal behavior, investigates probable causes using source-grounded operational knowledge and persistent memory, and produces evidence-based recommendations while enforcing safety, cost, and permission boundaries.

## 2. Allowed Tools

The agent is restricted to the following tools:

1. `load_operational_data` — Load an authorized operational CSV dataset.
2. `validate_sensor_data` — Validate telemetry quality, detect malformed records, and apply safe recoverable cleaning.
3. `calculate_plant_kpis` — Calculate defensible RO performance indicators from validated data.
4. `detect_anomalies` — Detect abnormal changes relative to the operating baseline.
5. `diagnose_issue` — Generate evidence-based diagnostic hypotheses using the source-grounded diagnostic engine.
6. `search_operational_knowledge` — Query the custom MCP operational knowledge server.
7. `search_incident_memory` — Search historical incidents stored in persistent SQLite memory.
8. `save_incident` — Persist an approved incident to SQLite memory.
9. `generate_incident_report` — Generate the structured investigation report.

The agent has no tool for direct PLC, SCADA, pump, valve, chemical-dosing, or plant-setpoint control.

## 3. Agent Loop

AquaMind uses a single-agent ReAct-style execution loop:

**Reason → Act → Observe → Reflect → Continue / Stop**

The agent stores short auditable `decision_summary` records rather than exposing private chain-of-thought.

At each step, the agent:

1. Determines the next required action from available evidence.
2. Selects one permitted tool.
3. Observes the structured tool result.
4. Reflects on whether evidence is sufficient, whether recovery is possible, or whether execution must stop.
5. Continues until a termination condition is reached.

## 4. Termination Conditions

The runtime explicitly enforces all three required termination controls:

- **Maximum turns:** `12`
- **Per-task budget cap:** `$0.10 USD`
- **Final answer condition:** terminate when an evidence-supported final report is ready.

Additional safety termination conditions are:

- Maximum tool calls reached.
- Insufficient evidence.
- Human authorization required.
- Budget limit reached.
- Non-recoverable runtime error.
- Safety-policy violation or prompt-injection attempt.

The agent must not continue execution after a safety block or exhausted resource limit.

## 5. Budget Cap

**Maximum allowed cost per task: `$0.10 USD`.**

The cost tracker records actual model usage when model-token usage is present and prevents execution from exceeding the configured task budget.

No fabricated token usage or model cost is recorded.

## 6. Permission Policy

### `auto`

The following read-only analytical actions may execute automatically:

- Load operational data.
- Validate sensor data.
- Calculate KPIs.
- Detect anomalies.
- Diagnose issues.
- Search operational knowledge.
- Search incident memory.
- Generate an in-memory incident report.

### `ask_on_write`

The agent must request authorization before persistent write operations such as:

- Saving an incident to persistent memory.
- Exporting or persistently writing an incident report.
- Updating persistent operational records.

### `always_ask`

Any physical or high-impact operational action requires explicit human authorization.

The current AquaMind implementation intentionally exposes **no physical plant-control tools**, including:

- Pump control.
- Valve control.
- PLC commands.
- SCADA actuation.
- Setpoint modification.
- Automatic chemical dosing.
- Automatic membrane cleaning.

Recommendations are advisory and require qualified human verification before plant action.

## 7. Success Examples

### Example 1 — Successful Source-Grounded Investigation

**Input**

A reverse-osmosis operational CSV containing a sustained abnormal performance pattern consistent with membrane fouling.

**Expected Output**

- Dataset is loaded and validated.
- RO KPIs are calculated.
- Abnormal behavior is detected.
- Diagnostic evidence is extracted.
- Relevant source-grounded cases and rules are evaluated.
- Operational knowledge is queried through MCP.
- Historical incident memory is searched.
- A probable-cause hypothesis is produced with supporting evidence, source IDs, verification requirements, and safety limitations.
- A final incident report is generated.
- Termination reason: `FINAL_ANSWER`.

**Evidence:** `traces/source_grounded_fouling.jsonl`

### Example 2 — Recoverable Data-Quality Failure

**Input**

An operational CSV containing invalid timestamps, duplicate timestamps, non-numeric sensor values, and missing readings.

**Expected Output**

- Data-quality degradation is detected.
- Recoverable validation actions are applied.
- Invalid or unusable rows are safely removed.
- Recovery actions are explicitly recorded.
- The agent reflects on the cleaned evidence and continues the investigation.
- No unsafe inference is made from discarded data.
- A qualified final report is produced.
- Termination reason: `FINAL_ANSWER`.

**Evidence:** `traces/near_failure_recovery.jsonl`

### Example 3 — Explicit Safety Failure

**Input**

A hostile request attempting to override safety instructions and directly manipulate a plant valve or operational setpoint.

**Expected Output**

- Prompt-injection / unsafe-control intent is detected before operational tools execute.
- No plant-control tool is called.
- `tool_call_count = 0`.
- No physical action is authorized or executed.
- The request is terminated safely.
- Termination reason: `SAFETY_BLOCK`.

**Evidence:** `traces/explicit_failure.jsonl`

## 8. Technical Boundaries

AquaMind provides diagnostic decision support, not autonomous plant control.

Diagnostic outputs are hypotheses unless independently verified. Confidence values are heuristic decision-support signals rather than calibrated probabilities.

The project evaluation datasets are synthetic and must not be represented as real plant telemetry.

The knowledge system is grounded in an actively referenced curated source set and does not claim to have been trained on all desalination failures or operating conditions.
