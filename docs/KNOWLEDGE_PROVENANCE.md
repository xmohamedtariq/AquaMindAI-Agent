# AquaMind AI — Knowledge Provenance Policy

## Objective

Every production knowledge rule and diagnostic scenario must be traceable to authoritative evidence.

## Required chain

`source_id -> knowledge_rule_id -> scenario_id -> tool observation -> diagnosis -> test -> trace`

A rule without at least one source ID is not eligible for production diagnosis.

## Evidence hierarchy

1. Plant-specific validated limits, OEM documentation, approved SOPs and site data.
2. Current official membrane-manufacturer manuals/bulletins.
3. Consensus standards and professional manuals (ASTM/AWWA).
4. International/government guidance (WHO, USBR, NIST, EPA, CISA).
5. Official manufacturer cross-checks.
6. Peer-reviewed research may be added later as supplemental evidence, but should not silently override levels 1-4.

## Diagnostic language

Use:
- `hypothesis`
- `probable cause`
- `consistent with`
- `evidence supports`
- `insufficient evidence`
- `requires verification`

Avoid:
- `confirmed root cause` unless an explicit verification result supports it.
- calibrated probability language unless confidence has actually been calibrated on representative labeled data.

## Threshold policy

AquaMind must distinguish:

- **plant-specific safety/operating limits**
- **manufacturer product limits**
- **normalization/cleaning guidance**
- **scenario sensitivity thresholds**
- **statistical anomaly thresholds**

These are not interchangeable.

No manufacturer-specific value becomes a universal threshold.

## Copyright / licensing

For paid ASTM/AWWA standards:
- store citation metadata, standard IDs, scope summaries available from official public pages, and internal notes created from lawfully accessed copies;
- do not commit full copyrighted standards to the public repository;
- do not reproduce tables or long passages.

For public manufacturer/government guidance:
- prefer linking to official current source documents;
- paraphrase in project knowledge instead of copying long passages.

## Draft sources

Draft documents are not retained in the active production registry unless they directly support an implemented case and are clearly marked `draft`. The current active registry contains no draft sources.

## Safety boundary

Knowledge retrieval never grants physical-control permission.

AquaMind may:
- read;
- calculate;
- detect;
- search;
- diagnose;
- recommend;
- generate an in-memory report.

Persistent writes require explicit approval where configured.

Physical control remains out of scope for the MVP.

## Synthetic-data disclosure

Scenario data is synthetic and reproducible. It is designed to represent documented directional patterns and failure modes. It must never be described as real plant telemetry.

## Review rule

Before adding or changing a diagnostic rule:
1. identify the source IDs;
2. state what the sources actually support;
3. state what remains inference;
4. add/modify the scenario;
5. add tests;
6. regenerate/verify traces;
7. preserve auditability in Git history.
