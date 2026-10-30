<div align="center">

# 🌊 AquaMindAI-Agent

### Autonomous AI Agent for Desalination Operations Intelligence

**Monitor · Investigate · Diagnose · Verify**

[![Live Demo](https://img.shields.io/badge/LIVE_DEMO-Launch-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-572%2F572_Passed-16A34A?style=for-the-badge&logo=pytest&logoColor=white)](./tests)
[![Coverage](https://img.shields.io/badge/Coverage-100%25-22C55E?style=for-the-badge)](./tests)

**Evidence-Grounded · Safety-Constrained · Traceable**

[🚀 Live App](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[💻 Source](./src) ·
[📋 Specification](./SPEC.md) ·
[🧪 Tests](./tests) ·
[💰 Cost](./COST.md) ·
[🎬 Demo](./DEMO.md)

</div>

---

## Overview

**AquaMindAI-Agent** is an autonomous AI agent designed to support reverse-osmosis desalination operations.

It combines **plant data, engineering knowledge, incident memory, analytical tools, reflection, and safety controls** to investigate operational problems and produce evidence-based recommendations.

> **Plan → Act → Observe → Reflect → Decide**

---

## 🧠 Architecture

```mermaid
flowchart LR

    U((👤 Operator))
    DATA[(📊 Plant Data)]

    subgraph CORE["🧠 Autonomous Agent Core"]
        P["Planner"]
        T["Tool Router"]
        O["Observe"]
        R["Reflect"]
        D{"Evidence<br/>Sufficient?"}

        P --> T
        O --> R
        R --> D
        D -- "No" --> P
    end

    subgraph INTEL["🔎 Operational Intelligence"]
        KPI["📈 KPI & Trend<br/>Analysis"]
        ANO["🚨 Anomaly<br/>Detection"]
        KB["📚 Knowledge<br/>Base"]
        MEM["🗂️ Incident<br/>Memory"]
    end

    subgraph OUTPUT["✅ Decision Layer"]
        SAFE["🛡️ Safety<br/>Validation"]
        REPORT["📑 Investigation<br/>Report"]
    end

    U --> P
    DATA --> P

    T --> KPI
    T --> ANO
    T --> KB
    T --> MEM

    KPI --> O
    ANO --> O
    KB --> O
    MEM --> O

    D -- "Yes" --> SAFE
    SAFE --> REPORT

    AUDIT[("🧾 Audit Trail")]

    P -.-> AUDIT
    O -.-> AUDIT
    R -.-> AUDIT
    REPORT -.-> AUDIT
```

<div align="center">

[📋 Agent Specification](./SPEC.md) ·
[💻 Core Implementation](./src) ·
[🧾 Execution Traces](./traces)

</div>

---

## ⚡ Capabilities

| Capability | Purpose | Explore |
|---|---|---|
| 🔎 **Autonomous Investigation** | Executes structured RO investigations | [Source](./src) |
| 📊 **KPI Analysis** | Evaluates operational performance and trends | [Source](./src) |
| 🚨 **Anomaly Detection** | Identifies abnormal plant behavior | [Source](./src) |
| 🧠 **Diagnostic Reasoning** | Forms evidence-based hypotheses | [Specification](./SPEC.md) |
| 📚 **Knowledge Retrieval** | Uses desalination engineering knowledge | [Source](./src) |
| 🗂️ **Incident Memory** | Reuses relevant historical cases | [Source](./src) |
| 🔄 **Reflection Loop** | Re-evaluates evidence before deciding | [Source](./src) |
| 🛡️ **Safety Validation** | Constrains unsupported recommendations | [Specification](./SPEC.md) |
| 🧾 **Audit Trail** | Preserves actions, evidence, and decisions | [Traces](./traces) |
| 💰 **Cost Tracking** | Tracks AI/runtime cost considerations | [COST.md](./COST.md) |

---

## 🎯 Example Investigation

```text
↓ Permeate Flow
↑ Differential Pressure
⚠ Abnormal RO Performance
        │
        ▼
KPI Analysis
        │
        ▼
Anomaly Detection
        │
        ▼
Engineering Knowledge
        │
        ▼
Diagnostic Hypotheses
        │
        ▼
Reflection + Safety Check
        │
        ▼
Recommended Action
```

Possible hypotheses include **membrane fouling, scaling, hydraulic restrictions, feed-water changes, or pretreatment degradation**.

[🚀 Try AquaMind](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[🎬 Demo Guide](./DEMO.md)

---

## ✅ Verification

| Check | Status |
|---|---:|
| Automated Tests | ✅ **572 / 572 Passed** |
| Test Coverage | ✅ **100%** |
| Autonomous Agent Loop | ✅ |
| Reflection | ✅ |
| Safety Controls | ✅ |
| Auditability | ✅ |
| Cost Tracking | ✅ |
| Production Deployment | ✅ **Live** |

---

## 📚 Explore the Project

| Resource | Description |
|---|---|
| 🚀 [**Live Application**](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) | Production deployment |
| 📋 [**SPEC.md**](./SPEC.md) | Goals, behavior, tools, and constraints |
| 💻 [**src/**](./src) | Core agent implementation |
| 🧪 [**tests/**](./tests) | Full automated test suite |
| 🧾 [**traces/**](./traces) | Agent execution and audit traces |
| 💰 [**COST.md**](./COST.md) | Cost tracking documentation |
| 🎬 [**DEMO.md**](./DEMO.md) | Guided demonstration workflow |
| 🌐 [**web_app.py**](./web_app.py) | Production web application |
| ⚙️ [**.env.example**](./.env.example) | Environment configuration |
| 📦 [**requirements.txt**](./requirements.txt) | Python dependencies |

---

## 📁 Structure

```text
AquaMindAI-Agent/
├── src/                # Agent core
├── tests/              # 572 automated tests
├── traces/             # Execution traces
├── web_app.py          # Web application
├── SPEC.md             # Agent specification
├── COST.md             # Cost tracking
├── DEMO.md             # Demo guide
├── requirements.txt
├── .env.example
└── README.md
```

---

<details>
<summary><b>🚀 Run Locally</b></summary>

<br>

```bash
git clone https://github.com/xmohamedtariq/AquaMindAI-Agent.git
cd AquaMindAI-Agent

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python web_app.py
```

Environment configuration:

```bash
copy .env.example .env
```

</details>

<details>
<summary><b>🧪 Run Tests & Coverage</b></summary>

<br>

```bash
pytest --cov=src --cov-report=term-missing
```

Expected:

```text
572 passed
Coverage: 100%
```

[View Test Suite →](./tests)

</details>

---

## 🛡️ Safety

AquaMind is an **engineering decision-support system** built around:

**Evidence · Traceability · Safety · Engineering Context · Human Oversight**

It does not autonomously control physical desalination equipment.

---

<div align="center">

## 👤 Mohammed Tariq Al-Sakkaf

**Mechatronics Engineer · Artificial Intelligence · Intelligent Automation · Water Technology**

[![GitHub](https://img.shields.io/badge/GitHub-xmohamedtariq-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/xmohamedtariq)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mohammed_Tariq-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mohammed-tariq-3a1a0824a)

<br>

### 🌊 Intelligence for Smarter Desalination Operations

**Built around evidence. Designed for traceability. Constrained by safety.**

</div>
