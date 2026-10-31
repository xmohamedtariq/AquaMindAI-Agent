<div align="center">

# 🌊 AquaMindAI-Agent

### Autonomous AI Agent for Desalination Operations Intelligence

**Monitor · Investigate · Diagnose · Verify**

[![Production UI](https://img.shields.io/badge/PRODUCTION_UI-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)
[![Interactive Demo](https://img.shields.io/badge/INTERACTIVE_DEMO-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://aquamindai-agent.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-572%2F572-16A34A?style=for-the-badge&logo=pytest&logoColor=white)](./evidence/tests_coverage.txt)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-22C55E?style=for-the-badge)](./evidence/tests_coverage.txt)

**Evidence-Grounded · MCP-Enabled · Safety-Constrained · Traceable**

[🚀 Launch Product](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[🌐 Interactive Demo](https://aquamindai-agent.onrender.com/) ·
[📋 Agent Specification](./agent_spec.md) ·
[🎬 Demo Guide](./DEMO.md)

</div>

---

## What is AquaMind?

**AquaMindAI-Agent** is an autonomous AI system designed to investigate operational problems in **reverse-osmosis desalination plants**.

Instead of acting as a general chatbot, AquaMind follows a structured engineering workflow:

> **Plan → Act → Observe → Reflect → Decide**

The agent can analyze RO plant CSV data, calculate performance indicators, detect abnormal behavior, retrieve engineering evidence, recall previous incidents, generate diagnostic hypotheses, and produce safe verification recommendations.

It is designed as an **engineering decision-support system** and does not autonomously operate physical desalination equipment.

---

## 🚀 Try AquaMind

| Experience | Best For | Launch |
|---|---|---|
| ⚡ **Production UI** | Product experience and operational workflow | [Open on Vercel →](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) |
| 🌊 **Interactive Streamlit Demo** | Direct agent investigation and evaluation | [Open on Render →](https://aquamindai-agent.onrender.com/) |

Both interfaces connect to the same AquaMind investigation architecture and safety model.

---

## 🔎 Explore the Project

Want the short version or the engineering details? Jump directly to what interests you.

| Explore | What You Will Find |
|---|---|
| 📋 [**Agent Specification**](./agent_spec.md) | Goal, tools, termination rules, permissions, success examples |
| 🧠 [**Agent Core**](./src/agent) | Planning, runtime, state, reflection, autonomous loop |
| 🔌 [**MCP Integration**](./src/mcp) | Operational knowledge server and client |
| 🗂️ [**Persistent Memory**](./src/memory) | SQLite incident memory |
| 🛡️ [**Safety Layer**](./src/safety) | Prompt-injection guard and permission enforcement |
| 💰 [**Cost Analysis**](./cost_analysis.md) | Gemini pricing, measured usage, scaling projections |
| 🧾 [**Execution Traces**](./traces) | Successful, recovery, and explicit failure runs |
| 🧪 [**Test Suite**](./tests) | 572 automated tests |
| ✅ [**Verification Evidence**](./evidence) | Reproducible MCP, memory, safety, permissions, diagnosis, and coverage evidence |
| 🎬 [**Demo Guide**](./DEMO.md) | Recommended end-to-end demonstration |

---

## 🧠 How It Works

```mermaid
flowchart LR

    U((👤 Operator))
    DATA[(📊 RO Plant Data)]

    subgraph EXPERIENCE["User Experience"]
        WEB["Production UI"]
        ST["Streamlit UI"]
    end

    subgraph SAFETY["🛡️ Safety Boundary"]
        GUARD["Injection Guard"]
        PERM["Permission Policy"]
    end

    subgraph AGENT["🧠 Autonomous Agent"]
        PLAN["Plan"]
        ACT["Act"]
        OBS["Observe"]
        REF["Reflect"]
        DEC{"Evidence sufficient?"}

        PLAN --> ACT
        ACT --> OBS
        OBS --> REF
        REF --> DEC
        DEC -- "Continue" --> PLAN
    end

    subgraph INTELLIGENCE["🔎 Operational Intelligence"]
        VAL["Data Validation"]
        KPI["KPI Analysis"]
        ANO["Anomaly Detection"]
        MCP["MCP Knowledge"]
        MEM["SQLite Memory"]
        DIA["Diagnosis"]
        REP["Incident Report"]
    end

    U --> WEB
    U --> ST
    DATA --> WEB
    DATA --> ST

    WEB --> GUARD
    ST --> GUARD

    GUARD --> PERM
    PERM --> PLAN

    ACT --> VAL
    ACT --> KPI
    ACT --> ANO
    ACT --> MCP
    ACT --> MEM
    ACT --> DIA
    ACT --> REP

    VAL --> OBS
    KPI --> OBS
    ANO --> OBS
    MCP --> OBS
    MEM --> OBS
    DIA --> OBS
    REP --> OBS

    DEC -- "Yes" --> RESULT["✅ Evidence-Grounded Recommendation"]

    AUDIT[("🧾 Audit Trail")]
    COST[("💰 Cost Tracker")]

    AGENT -.-> AUDIT
    AGENT -.-> COST
```

---

## ⚡ Agent Capabilities

| Capability | Description | Explore |
|---|---|---|
| 🔎 **Autonomous Investigation** | Executes an RO investigation end to end | [Agent Core](./src/agent) |
| 📊 **Data Validation** | Validates plant telemetry before analysis | [Tools](./src/tools) |
| 📈 **KPI Analysis** | Calculates relevant RO performance indicators | [Tools](./src/tools) |
| 🚨 **Anomaly Detection** | Identifies abnormal operating behavior | [Anomaly Detection](./src/tools/anomaly_detection.py) |
| 📚 **MCP Knowledge Retrieval** | Retrieves approved engineering evidence | [MCP](./src/mcp) |
| 🗂️ **Incident Memory** | Recalls relevant historical incidents | [Memory](./src/memory) |
| 🧠 **Diagnostic Reasoning** | Builds evidence-backed hypotheses | [Diagnosis](./src/tools/diagnosis.py) |
| 🔄 **Reflection** | Reassesses evidence before finalizing | [Agent Core](./src/agent) |
| 🛡️ **Safety Enforcement** | Blocks unsafe and injected requests | [Safety](./src/safety) |
| 🧾 **Auditability** | Records operational decisions and actions | [Audit](./src/audit) |
| 💰 **Cost Control** | Tracks model usage and task budget | [Cost Analysis](./cost_analysis.md) |

---

## 🛠️ Approved Toolset

AquaMind operates through a deliberately constrained tool registry.

| Tool | Responsibility |
|---|---|
| `validate_sensor_data` | Validate and assess incoming plant data |
| `calculate_plant_kpis` | Calculate RO performance KPIs |
| `detect_anomalies` | Detect abnormal operational patterns |
| `search_operational_knowledge` | Retrieve engineering evidence through MCP |
| `search_incident_memory` | Search persistent historical incidents |
| `diagnose_issue` | Generate evidence-grounded hypotheses |
| `generate_incident_report` | Produce the final investigation report |

No unregistered operational tool may execute.

[Explore the complete specification →](./agent_spec.md)

---

## 🔌 Model Context Protocol

AquaMind includes a custom **Model Context Protocol server** that exposes curated desalination engineering knowledge to the agent.

The agent accesses it through:

```text
search_operational_knowledge
```

Knowledge resources are exposed through `knowledge://` URIs.

A practical MCP verification returned relevant engineering knowledge matches through the actual MCP client.

[View MCP implementation →](./src/mcp)

[View MCP verification evidence →](./evidence/mcp_knowledge_search.txt)

---

## 🗂️ Persistent Incident Memory

AquaMind uses **SQLite** to retain approved historical incidents.

Persistence was tested across independent Python processes:

```text
Save incident
      ↓
Terminate runtime
      ↓
Start fresh runtime
      ↓
Query SQLite memory
      ↓
Incident recovered successfully
```

[View memory implementation →](./src/memory)

[View memory save evidence →](./evidence/memory_restart_save.txt)

[View restart verification →](./evidence/memory_restart_verify.txt)

---

## 🛡️ Safety by Design

AquaMind treats safety as part of the system architecture rather than relying only on prompt instructions.

### Permission Model

| Level | Behavior |
|---|---|
| `AUTO` | Safe analytical and read-only operations |
| `ASK_ON_WRITE` | Persistent writes require explicit human approval |
| `ALWAYS_ASK` | High-impact operations require explicit authorization |

Physical plant-control operations remain outside AquaMind's autonomous execution boundary.

[Explore the safety layer →](./src/safety)

[View permission verification →](./evidence/permission_layer.txt)

### Prompt-Injection Defense

Three independent hostile inputs were tested:

- instruction override + hidden prompt extraction,
- safety bypass + forced tool execution,
- physical-control request targeting valve and setpoint operations.

Result:

```text
HOSTILE INPUTS PASSED: 3/3
Termination: SAFETY_BLOCK
Operational tool calls: 0
```

[View hostile-input evidence →](./evidence/hostile_inputs_test.txt)

[View detailed safety-block evidence →](./evidence/prompt_injection_safety.txt)

---

## 🧾 Execution Traces

Three execution traces demonstrate different agent outcomes.

### ✅ Successful Investigation

A complete evidence-grounded investigation ending in:

`FINAL_ANSWER`

[Open success_1.jsonl →](./traces/success_1.jsonl)

### 🔄 Near-Failure Recovery

AquaMind detects recoverable data-quality degradation, applies recovery, reassesses the remaining evidence, and continues safely.

[Open near_failure_recovery.jsonl →](./traces/near_failure_recovery.jsonl)

### 🛡️ Explicit Failure

A deliberately hostile request attempts to bypass safety and trigger physical plant control.

AquaMind blocks it before operational tools execute.

```text
termination_reason = SAFETY_BLOCK
tool_call_count = 0
```

[Open explicit_failure.jsonl →](./traces/explicit_failure.jsonl)

---

## 💰 Cost Intelligence

AquaMind integrates task-level cost tracking around **Google Gemini**.

| Metric | Value |
|---|---:|
| Model | `gemini-3.5-flash-lite` |
| Maximum budget / task | `$0.10` |
| Average Free Tier benchmark | `$0.000000` |
| Average paid-reference cost / task | `$0.00062242` |
| Estimated 100 tasks | `$0.062242` |
| Estimated 1,000 tasks | `$0.622420` |
| Estimated 10,000 tasks | `$6.224200` |

Provider-reported token usage is used for completed Gemini calls instead of fabricated token estimates.

[Explore the full cost analysis →](./cost_analysis.md)

---

## ✅ Engineering Verification

| Verification | Result |
|---|---:|
| Automated Tests | **572 / 572 Passed** ✅ |
| Source Coverage | **100.00%** ✅ |
| Statements | **2,453** |
| Missing Statements | **0** |
| Hostile Inputs | **3 / 3 Blocked** ✅ |
| MCP Search | **Verified** ✅ |
| Memory After Restart | **Verified** ✅ |
| Permission Enforcement | **Verified** ✅ |

[Open full test & coverage evidence →](./evidence/tests_coverage.txt)

---

## 🎯 Diagnostic Quality Evaluation

AquaMind was evaluated using controlled synthetic RO scenarios for deterministic engineering verification.

| Metric | Result |
|---|---:|
| End-to-End Scenario Conformance | **8 / 8 — 100%** |
| Outcome-Label Conformance | **8 / 8 — 100%** |
| Supported Diagnosis Conformance | **7 / 7** |
| Safety-Boundary Conformance | **1 / 1** |
| Reference Diagnostic Profiles | **90 / 90 — 100%** |
| Synthetic Rule Variations | **720 / 720 — 100%** |
| Synthetic Normal False-Alarm Rate | **0 / 8 — 0.00%** |
| Source-Grounded Cases | **90 / 90** |
| Fully Resolvable Source IDs | **90 / 90** |
| Verified Engineering Sources | **34** |

The evaluation datasets are **controlled synthetic engineering scenarios**, not telemetry collected from a real desalination plant.

The engineering logic, evidence requirements, diagnostic patterns, and source grounding are linked to verified manufacturer and industry references.

AquaMind deliberately returns **evidence-grounded hypotheses** rather than claiming confirmed physical root causes when the available telemetry is insufficient.

For example, scaling and colloidal fouling are not artificially separated when plant telemetry alone cannot reliably distinguish them. Further evidence such as feed-water chemistry, SDI/turbidity, stage localization, deposit inspection, and normalized membrane performance may be required.

Runtime confidence values are **heuristic support scores**, not calibrated probabilities of real-world root cause.

Independent blinded comparison against diagnoses from a qualified RO specialist remains an important future validation stage before claiming field diagnostic accuracy.

[View Diagnostic Quality Evaluation →](./evidence/diagnostic_quality_evaluation.txt)

[View End-to-End Scenario Evaluation →](./evidence/diagnostic_scenario_evaluation.txt)

---

## 🧪 Sensor-Data Robustness

AquaMind does not assume that uploaded sensor data is clean.

The recovery workflow has been tested against a dataset containing:

- invalid timestamps,
- duplicate timestamps,
- missing readings,
- non-numeric sensor values,
- out-of-order records.

The agent identifies the data-quality issue, applies recoverable processing where appropriate, records the recovery, reassesses the resulting dataset, and continues only when sufficient evidence remains.

[View recovery trace →](./traces/near_failure_recovery.jsonl)

[View diagnostic quality evidence →](./evidence/diagnostic_quality_evaluation.txt)

---

## 📂 Engineering Evidence

For reviewers, developers, or anyone who wants to inspect the system in depth:

| Evidence | Direct Link |
|---|---|
| Agent behavior and constraints | [agent_spec.md](./agent_spec.md) |
| Successful execution | [success_1.jsonl](./traces/success_1.jsonl) |
| Recovery behavior | [near_failure_recovery.jsonl](./traces/near_failure_recovery.jsonl) |
| Explicit safety failure | [explicit_failure.jsonl](./traces/explicit_failure.jsonl) |
| Diagnostic quality | [diagnostic_quality_evaluation.txt](./evidence/diagnostic_quality_evaluation.txt) |
| End-to-end diagnostic scenarios | [diagnostic_scenario_evaluation.txt](./evidence/diagnostic_scenario_evaluation.txt) |
| Cost methodology | [cost_analysis.md](./cost_analysis.md) |
| 572 tests / 100% coverage | [tests_coverage.txt](./evidence/tests_coverage.txt) |
| MCP retrieval | [mcp_knowledge_search.txt](./evidence/mcp_knowledge_search.txt) |
| Memory persistence | [memory_restart_verify.txt](./evidence/memory_restart_verify.txt) |
| Permission enforcement | [permission_layer.txt](./evidence/permission_layer.txt) |
| Prompt-injection defense | [prompt_injection_safety.txt](./evidence/prompt_injection_safety.txt) |
| Three hostile inputs | [hostile_inputs_test.txt](./evidence/hostile_inputs_test.txt) |

---

## 📁 Repository Structure

```text
AquaMindAI-Agent/
├── src/
│   ├── agent/                # Autonomous agent core
│   ├── audit/                # Audit logging
│   ├── cost/                 # Budget and cost tracking
│   ├── knowledge/            # Diagnostic knowledge services
│   ├── llm/                  # Gemini integration
│   ├── mcp/                  # MCP server and client
│   ├── memory/               # Persistent SQLite memory
│   ├── safety/               # Permissions and injection protection
│   ├── tools/                # Operational tools
│   └── tracing/              # JSONL execution tracing
│
├── knowledge/                # Source-grounded engineering knowledge
├── data/                     # Controlled synthetic evaluation scenarios
├── tests/                    # 572 automated tests
├── traces/                   # Key execution traces
├── evidence/                 # Verification and diagnostic evidence
│
├── streamlit_app.py          # Interactive Streamlit interface
├── web_app.py                # Production web application
├── agent_spec.md             # Agent behavior and constraints
├── cost_analysis.md          # Cost analysis and projections
├── DEMO.md                   # Guided demonstration
├── requirements.txt
└── README.md
```

---

<details>
<summary><b>⚙️ Agent Limits & Termination Rules</b></summary>

<br>

| Control | Configuration |
|---|---|
| Maximum turns | `12` |
| Maximum task budget | `$0.10` |
| Successful termination | `FINAL_ANSWER` |
| Safety termination | `SAFETY_BLOCK` |
| Persistent write policy | `ASK_ON_WRITE` |
| High-impact permission | `ALWAYS_ASK` |

[Read the complete specification →](./agent_spec.md)

</details>

<details>
<summary><b>🧪 Reproduce the Verification Suite</b></summary>

<br>

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=100
```

Expected:

```text
572 passed
TOTAL 2453 0 100%
Required test coverage of 100% reached.
```

[View recorded verification →](./evidence/tests_coverage.txt)

</details>

<details>
<summary><b>💻 Run Locally</b></summary>

<br>

```bash
git clone https://github.com/xmohamedtariq/AquaMindAI-Agent.git
cd AquaMindAI-Agent

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

Production-oriented interface:

[web_app.py](./web_app.py)

</details>

---

## 🎬 Demo Walkthrough

A guided end-to-end demonstration is available in:

[**Open DEMO.md →**](./DEMO.md)

The workflow covers:

**Plant Data → Validation → Planning → Tool Use → MCP → Memory → Diagnosis → Reflection → Safety → Final Recommendation**

---

## 🛡️ Operational Boundary

AquaMind may:

- analyze operational data,
- calculate RO performance indicators,
- detect abnormal patterns,
- retrieve engineering references,
- search incident memory,
- generate diagnostic hypotheses,
- recommend verification actions.

AquaMind does **not** independently:

- operate valves,
- start or stop pumps,
- change plant setpoints,
- initiate cleaning cycles,
- shut down equipment.

Final physical operational decisions remain under qualified human supervision.

---

## 🔗 Quick Links

- [🚀 Production Interface](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)
- [🌊 Interactive Streamlit Demo](https://aquamindai-agent.onrender.com/)
- [📋 Agent Specification](./agent_spec.md)
- [🎬 Demo Guide](./DEMO.md)
- [💰 Cost Analysis](./cost_analysis.md)
- [🎯 Diagnostic Quality Evaluation](./evidence/diagnostic_quality_evaluation.txt)
- [🧪 Scenario Evaluation](./evidence/diagnostic_scenario_evaluation.txt)
- [✅ Test & Coverage Evidence](./evidence/tests_coverage.txt)
- [🧾 Successful Trace](./traces/success_1.jsonl)
- [🔄 Recovery Trace](./traces/near_failure_recovery.jsonl)
- [🛡️ Explicit Failure Trace](./traces/explicit_failure.jsonl)
- [💻 Source Code](./src)
- [🧪 Automated Tests](./tests)

---

<div align="center">

## 👤 Mohammed Tariq Al-Saqqaf

**Mechatronics Engineer · Artificial Intelligence · Intelligent Automation · Water Technology**

[![GitHub](https://img.shields.io/badge/GitHub-xmohamedtariq-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/xmohamedtariq)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mohammed_Tariq-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mohammed-tariq-3a1a0824a)

<br>

### Intelligence for Smarter Desalination Operations

**Built around evidence. Designed for traceability. Constrained by safety.**

</div>
