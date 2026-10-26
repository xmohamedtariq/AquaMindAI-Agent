# AquaMindAI-Agent - Source-Grounded Diagnostic Engine

This module converts the first 16 source-grounded canonical cases into machine-readable rules. It is intentionally separate from the existing runtime during this commit.

## Executable first batch

- temperature-driven apparent performance change
- recovery-driven apparent performance change
- source-water quality change requiring normalization/context
- stuck sensor
- transient sensor spike
- unit mismatch
- conflicting redundant telemetry
- water-hammer startup risk
- permeate-backpressure risk
- chlorine/oxidant breakthrough
- oxidation-damage hypothesis
- O-ring leak hypothesis
- product-tube leak hypothesis
- elevated SDI / colloidal-fouling risk
- pretreatment upset
- mixed biological + particulate fouling

## Safety and scientific interpretation

Outcomes are `diagnosis`, `risk`, `guard`, or `data_quality`. Guards may block ordinary fault diagnosis. A diagnosis is a source-grounded hypothesis, not proof or a calibrated probability. The engine never authorizes physical plant actuation.

Every match resolves `rule_id -> case_id -> source_ids`, preserving the provenance chain already documented in the repository.

`knowledge/diagnostic_examples.json` contains deterministic synthetic evidence profiles, not real plant incidents.

Run `python -m scripts.evaluate_diagnostic_rules` to evaluate the reference profiles.

The next engineering step is mapping current AquaMind runtime observations into this evidence model and calling the engine from the runtime without changing the existing safe semantics for unclassified or insufficient-evidence cases.
