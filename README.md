<div align="center">

# 🌊 AquaMindAI-Agent

### Autonomous AI Agent for Desalination Operations Intelligence

**Monitor · Investigate · Diagnose · Verify**

<br>

[![Live Demo](https://img.shields.io/badge/Live_Demo-Open_App-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-42%2F42_Passed-16A34A?style=for-the-badge)]()
[![Coverage](https://img.shields.io/badge/Coverage-99.66%25-22C55E?style=for-the-badge)]()

<br>

**A context-aware, evidence-grounded, safety-constrained AI agent for reverse-osmosis desalination operations.**

[Live Application](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/) ·
[Repository](https://github.com/xmohamedtariq/AquaMindAI-Agent)

</div>

---

## 🌐 Overview

**AquaMindAI-Agent** helps desalination engineers investigate operational problems using plant data, engineering knowledge, historical incidents, and structured AI reasoning.

Instead of producing a generic chatbot response, AquaMind follows an autonomous investigation cycle to analyze evidence, form diagnostic hypotheses, reflect on findings, and produce traceable operational recommendations.

---

## ⚡ Core Capabilities

| Capability | Description |
|---|---|
| 🔎 **Autonomous Investigation** | Executes structured RO operational investigations |
| 📊 **KPI Analysis** | Evaluates performance indicators and operational trends |
| 🚨 **Anomaly Detection** | Detects abnormal plant behavior and deviations |
| 🧠 **Diagnostic Reasoning** | Generates evidence-grounded hypotheses |
| 📚 **Knowledge Search** | Retrieves relevant desalination engineering knowledge |
| 🗂️ **Incident Memory** | Reuses information from previous operational cases |
| 🛡️ **Safety Controls** | Constrains unsafe or unsupported recommendations |
| 🧾 **Audit Trail** | Preserves traceability of agent actions and decisions |

---

## 🤖 Agent Architecture

```text
                         ┌──────────────────┐
                         │    User Input    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Planner      │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   Tools & Knowledge Base │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                         ┌──────────────────┐
                         │   Observation    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    Reflection    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │     Decision     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   Final Report   │
                         └──────────────────┘
```

AquaMind follows a:

### **Plan → Act → Observe → Reflect → Decide**

loop rather than relying on a single LLM response.

---

## 🧭 Product Experience

The deployed application includes:

- **Guided Demo** — explore AquaMind through a prepared operational scenario
- **New Investigation** — launch a new desalination case
- **Knowledge Base** — access engineering knowledge used by the agent
- **Case Library** — review operational cases and investigation history
- **Audit Trail** — inspect traceable agent activity
- **Settings** — manage runtime behavior and configuration

---

## 🧪 Example Investigation

A desalination train begins showing:

```text
↓ Permeate Flow
↑ Differential Pressure
Abnormal RO performance
```

AquaMind can:

1. Inspect operational evidence
2. Identify abnormal KPIs
3. Retrieve relevant engineering knowledge
4. Generate possible root causes
5. Evaluate competing hypotheses
6. Reflect on available evidence
7. Produce a structured operational recommendation

Possible diagnostic paths may include:

> Membrane fouling · Scaling · Feed-condition changes · Hydraulic restrictions

The final output remains evidence-grounded and intended to support human engineering decisions.

---

## 🛡️ Safety by Design

AquaMind is designed around five principles:

```text
Evidence before conclusions
Traceability before opacity
Safety before automation
Engineering context before generic advice
Human oversight before critical action
```

The system provides **decision support**, not uncontrolled autonomous plant actuation.

---

## 🧰 Technology

```text
Python 3.14
Autonomous Agent Loop
Planner / Reflector Architecture
Operational Knowledge Base
Persistent Case Memory
Pytest
Vercel
```

---

## ✅ Quality Status

| Check | Status |
|---|---:|
| Automated tests | **42 / 42 passed** |
| Test coverage | **99.66%** |
| Production deployment | **Live** |
| Public web access | **Available** |
| Auditability | **Implemented** |
| Safety constraints | **Implemented** |

---

## 🚀 Run Locally

```bash
git clone https://github.com/xmohamedtariq/AquaMindAI-Agent.git
cd AquaMindAI-Agent

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python web_app.py
```

---

## 🧪 Run Tests

```bash
pytest
```

For coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

---

## 📁 Project Structure

```text
AquaMindAI-Agent/
│
├── src/                 # Core agent logic
├── tests/               # Automated test suite
├── traces/              # Agent execution traces
│
├── web_app.py           # Production web application
├── SPEC.md              # Agent specification
├── COST.md              # Cost tracking documentation
├── DEMO.md              # Demo guide
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🌍 Live Application

<div align="center">

### [Launch AquaMindAI-Agent →](https://aquamindai-agent-git-main-mohammed-tariq1.vercel.app/)

</div>

---

## 🎯 Vision

AquaMind explores how autonomous AI agents can assist water-treatment professionals by transforming operational data and engineering knowledge into faster, more transparent, and evidence-based investigations.

The long-term goal is to develop intelligent operational support systems that improve:

**Reliability · Efficiency · Maintainability · Decision Quality**

---

## 👤 Author

**Mohammed Tariq Al-Sakkaf**

Mechatronics Engineer  
Artificial Intelligence · Intelligent Automation · Water Technology

---

<div align="center">

### 🌊 AquaMindAI-Agent

**Intelligence for smarter desalination operations.**

</div>
