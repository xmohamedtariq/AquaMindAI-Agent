<div align="center">

# 🌊 AquaMindAI-Agent

### Autonomous AI Agent for Desalination Operations Intelligence

**Monitor · Investigate · Diagnose · Verify**

[![Live](https://img.shields.io/badge/Live_Demo-Open-000000?style=for-the-badge&logo=vercel)](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-42%2F42_Passed-16A34A?style=for-the-badge)](./tests)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-22C55E?style=for-the-badge)](./tests)

**Evidence-grounded · Safety-constrained · Traceable**

[🚀 Live App](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[📋 Specification](./SPEC.md) ·
[💻 Source](./src) ·
[🧪 Tests](./tests) ·
[💰 Cost](./COST.md) ·
[🎬 Demo](./DEMO.md)

</div>

---

## Overview

**AquaMindAI-Agent** supports reverse-osmosis desalination operations by combining plant data, engineering knowledge, incident memory, and autonomous AI reasoning.

Unlike a conventional chatbot, AquaMind follows a structured investigation loop:

> **Plan → Act → Observe → Reflect → Decide**

---

## Architecture

```mermaid
flowchart TD
    U["👤 Operator<br/>Plant Data / Question"]
    P["🧠 Planner<br/>Build Investigation Plan"]

    T["🛠️ Tools"]
    K["📊 KPI Analysis"]
    A["🚨 Anomaly Detection"]
    B["📚 Knowledge Base"]
    M["🗂️ Incident Memory"]

    O["👁️ Observe<br/>Collect Evidence"]
    R["🔄 Reflect<br/>Evaluate Hypotheses"]
    D{"Enough Evidence?"}
    S["🛡️ Safety Validation"]
    F["📑 Final Report"]
    L["🧾 Audit Trail"]

    U --> P --> T

    T --> K
    T --> A
    T --> B
    T --> M

    K --> O
    A --> O
    B --> O
    M --> O

    O --> R --> D
    D -- No --> P
    D -- Yes --> S --> F

    P -.-> L
    O -.-> L
    R -.-> L
    F -.-> L
```

[📋 Architecture & Agent Specification](./SPEC.md) ·
[💻 Inspect Implementation](./src) ·
[🧾 Execution Traces](./traces)

---

## Core Capabilities

| Capability | Explore |
|---|---|
| 🔎 Autonomous RO investigations | [Source](./src) |
| 📊 KPI & trend analysis | [Source](./src) |
| 🚨 Anomaly detection | [Source](./src) |
| 🧠 Evidence-based diagnostic reasoning | [Specification](./SPEC.md) |
| 📚 Engineering knowledge retrieval | [Source](./src) |
| 🗂️ Incident memory | [Source](./src) |
| 🔄 Reflection loop | [Source](./src) |
| 🛡️ Safety-aware recommendations | [Specification](./SPEC.md) |
| 🧾 Traceable audit trail | [Traces](./traces) |
| 💰 Cost tracking | [COST.md](./COST.md) |

---

## Example Investigation

```text
↓ Permeate Flow
↑ Differential Pressure
⚠ Abnormal RO Performance
```

AquaMind:

```text
Analyze KPIs
    ↓
Detect Anomalies
    ↓
Retrieve Engineering Knowledge
    ↓
Generate Hypotheses
    ↓
Reflect on Evidence
    ↓
Safety Check
    ↓
Recommended Action
```

Possible causes may include membrane fouling, scaling, hydraulic restrictions, feed-water changes, or pretreatment degradation.

[🚀 Try the Guided Demo](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[🎬 Demo Guide](./DEMO.md)

---

## Quality & Verification

| Check | Status |
|---|---:|
| Automated Tests | ✅ 42 / 42 |
| Test Coverage | ✅ 100% |
| Agent Loop | ✅ Implemented |
| Reflection | ✅ Implemented |
| Safety Controls | ✅ Implemented |
| Cost Tracking | ✅ Documented |
| Public Deployment | ✅ Live |

[🧪 View Tests](./tests) ·
[💰 Cost Tracking](./COST.md) ·
[🌐 Open Production App](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)

---

## Repository

```text
AquaMindAI-Agent/
├── src/              # Agent logic
├── tests/            # Automated tests
├── traces/           # Execution traces
├── web_app.py        # Web application
├── SPEC.md           # Agent specification
├── COST.md           # Cost tracking
├── DEMO.md           # Demo guide
├── requirements.txt
└── .env.example
```

[💻 `src/`](./src) ·
[🧪 `tests/`](./tests) ·
[🧾 `traces/`](./traces) ·
[🌐 `web_app.py`](./web_app.py) ·
[⚙️ `.env.example`](./.env.example)

---

## Run Locally

```bash
git clone https://github.com/xmohamedtariq/AquaMindAI-Agent.git
cd AquaMindAI-Agent

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python web_app.py
```

Run tests:

```bash
pytest --cov=src --cov-report=term-missing
```

Expected:

```text
42 / 42 tests passed
Coverage: 100%
```

---

## Safety

AquaMind is designed for **engineering decision support**.

It prioritizes:

**Evidence · Traceability · Safety · Engineering Context · Human Oversight**

It does not autonomously control physical desalination equipment.

---

## Documentation

| Resource | Purpose |
|---|---|
| [📋 SPEC.md](./SPEC.md) | Agent design and constraints |
| [💻 src/](./src) | Core implementation |
| [🧪 tests/](./tests) | Verification |
| [🧾 traces/](./traces) | Execution evidence |
| [💰 COST.md](./COST.md) | Cost tracking |
| [🎬 DEMO.md](./DEMO.md) | Demo workflow |
| [🚀 Live App](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) | Production deployment |

---

<div align="center">

### Mohammed Tariq Al-Sakkaf

**Mechatronics Engineer · Artificial Intelligence · Intelligent Automation · Water Technology**

[![GitHub](https://img.shields.io/badge/GitHub-xmohamedtariq-181717?style=for-the-badge&logo=github)](https://github.com/xmohamedtariq)

<br>

### 🌊 Intelligence for Smarter Desalination Operations

</div>
