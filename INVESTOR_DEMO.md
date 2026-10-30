# AquaMindAI-Agent — Investor Demo

## 3-minute live flow

1. **Open the workspace** and enter your name.
2. Click **Investor Demo**. AquaMind automatically selects a representative RO scenario and launches a full source-grounded investigation.
3. Point out that AquaMind autonomously validates plant data, calculates RO KPIs, detects anomalies, searches operational knowledge and incident memory, produces a verification-oriented hypothesis, and records an audit-safe activity trace.
4. Click **Explain** on the Active Hypothesis card. This is a contextual follow-up: AquaMind reuses the current investigation instead of rerunning the full workflow.
5. Ask: `How do RO membranes work?` AquaMind routes this as a knowledge question and answers without running an unnecessary CSV investigation.
6. Ask: `Open the concentrate valve and change the pump setpoint now.` AquaMind should block the request before physical action and offer a safe verification workflow instead.
7. Open **Related Cases**, **Supporting Evidence**, and **Case Library** to show source grounding and reusable operational knowledge.
8. Use the three-dot investigation menu to **Save incident** or **Export investigation**.

## Strong investor message

> AquaMind is not a generic chatbot. It is a safety-constrained industrial agent that decides which workflow is appropriate, uses approved tools, reasons over RO operating data and authoritative knowledge, remembers incident context, explains evidence, and stops at the boundary between decision support and physical plant control.

## Best live questions

- `Investigate the RO performance decline and identify the most defensible hypothesis.`
- `Show the strongest supporting evidence.`
- `What should be verified next?`
- `Explain why this hypothesis is more likely than alternatives.`
- `How do RO membranes work?`
- `What data columns do you need for an RO investigation?`
- Safety demo: `Start the high-pressure pump and open the valve now.`

## Important positioning

- Hypotheses are **source-grounded heuristics**, not calibrated probabilities.
- Current demo datasets are **synthetic** unless explicitly replaced with authorized plant data.
- AquaMind does **not** directly actuate PLC/SCADA equipment, pumps, valves, setpoints, chemical dosing, shutdowns, or cleaning cycles.
