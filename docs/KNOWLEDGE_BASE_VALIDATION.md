# AquaMindAI-Agent — Knowledge Base Validation

## Scope

This package validates the knowledge layer **before runtime integration**.

- Authoritative source records: **34**
- Canonical cases: **90**
- Structured evidence terms: **102**
- Structured diagnostic/risk/guard rules: **90**
- Synthetic conformance profiles: **720**
- Real plant incidents represented by the matrix: **0**

## Required invariants

1. Every case references at least one canonical source.
2. Every case has exactly one structured rule.
3. Every evidence field used by a case/rule is declared in the vocabulary.
4. No case authorizes autonomous physical plant action.
5. Every retained source is actively referenced by at least one canonical case; unused references are removed from the active registry.
6. Source aliases exist only to document migration from earlier IDs.
7. Every conformance profile is explicitly synthetic.
8. A rule match is a hypothesis/risk/guard result, not proof of root cause.

## Runtime boundary

The 90 rules are executable against **structured evidence**, but they are not all yet connected to raw CSV/SCADA telemetry. Runtime integration will happen only after this knowledge layer passes validation.
