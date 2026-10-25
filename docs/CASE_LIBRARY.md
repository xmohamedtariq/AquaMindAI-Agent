# AquaMind AI — Canonical Case Library

Canonical cases: **90**
Structured rules: **90**
Synthetic rule-conformance scenarios: **720**

The library contains no duplicate canonical semantics for the two cases identified in the October 2026 audit. Deprecated IDs are retained only as migration aliases.

## Domains
- `agent_ot_security`: 16
- `data_quality`: 10
- `drinking_water`: 8
- `membrane_condition`: 19
- `membrane_integrity`: 13
- `pretreatment`: 14
- `ro_performance`: 10

| Case | Domain | Label | Runtime status | Rule status | Sources |
|---|---|---|---|---|---|
| `RO-NORMAL-001` | `ro_performance` | `normal_operation` | `runtime_supported` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A`, `TORAY_TRAK`, `AWWA_M46_3E`, `ASTM_D4194_23`, `DUPONT_FTNORM_TOOL_CURRENT` |
| `RO-NORM-001` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A`, `TORAY_TRAK`, `DUPONT_FTNORM_TOOL_CURRENT` |
| `RO-NORM-002` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A`, `ASTM_D4195_23`, `DUPONT_FTNORM_TOOL_CURRENT` |
| `RO-NORM-003` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A`, `DUPONT_FTNORM_TOOL_CURRENT` |
| `RO-NORM-004` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022` |
| `RO-NORM-005` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4516_19A`, `TORAY_RO_HANDLING_MANUAL_2025` |
| `RO-NORM-006` | `ro_performance` | `stage_specific_normalization` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4516_19A`, `DUPONT_FTNORM_PRO_R0_2022` |
| `RO-NORM-007` | `ro_performance` | `insufficient_reference_data` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A` |
| `RO-NORM-008` | `ro_performance` | `operating_condition_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4516_19A`, `TORAY_TRAK` |
| `RO-NORM-009` | `ro_performance` | `normalized_pressure_drop_context` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022` |
| `RO-SCALE-001` | `membrane_condition` | `scaling_or_colloidal_fouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TSB107_28_2025`, `DUPONT_OPERATION_LIMITS_R1_2025` |
| `RO-SCALE-002` | `membrane_condition` | `carbonate_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `ASTM_D4195_23`, `HYDRANAUTICS_TAB111_2022` |
| `RO-SCALE-003` | `membrane_condition` | `calcium_sulfate_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `ASTM_D4195_23`, `HYDRANAUTICS_TAB111_2022` |
| `RO-SCALE-004` | `membrane_condition` | `barium_sulfate_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-SCALE-005` | `membrane_condition` | `strontium_sulfate_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-SCALE-006` | `membrane_condition` | `calcium_fluoride_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-SCALE-007` | `membrane_condition` | `silica_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `ASTM_D4195_23` |
| `RO-SCALE-008` | `membrane_condition` | `calcium_phosphate_scaling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-FOUL-001` | `membrane_condition` | `scaling_or_colloidal_fouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TSB107_28_2025`, `ASTM_D4189_23` |
| `RO-FOUL-002` | `membrane_condition` | `particulate_fouling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `TORAY_RO_HANDLING_MANUAL_2025`, `HYDRANAUTICS_TAB116_2022` |
| `RO-FOUL-003` | `pretreatment` | `elevated_colloidal_fouling_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB113_04_2016`, `ASTM_D4189_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `DUPONT_OPERATION_LIMITS_R1_2025` |
| `RO-FOUL-004` | `membrane_condition` | `metal_oxide_fouling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `ASTM_D4195_23` |
| `RO-FOUL-005` | `membrane_condition` | `iron_manganese_fouling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-FOUL-006` | `membrane_condition` | `aluminum_fouling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-FOUL-007` | `membrane_condition` | `biofouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TSB107_28_2025`, `TORAY_MBFR` |
| `RO-FOUL-008` | `membrane_condition` | `biofouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `TORAY_MBFR` |
| `RO-FOUL-009` | `membrane_condition` | `organic_fouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TSB107_28_2025` |
| `RO-FOUL-010` | `membrane_condition` | `organic_fouling` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TSB107_28_2025` |
| `RO-FOUL-011` | `membrane_condition` | `mixed_fouling` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `TORAY_MBFR` |
| `RO-FOUL-012` | `membrane_condition` | `unclassified_pattern` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `NIST_AI_RMF_1_0` |
| `RO-INT-001` | `membrane_integrity` | `membrane_integrity_or_seal_issue` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `ASTM_D3923_23`, `ASTM_D6908_25` |
| `RO-INT-002` | `membrane_integrity` | `o_ring_leak` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `ASTM_D3923_23` |
| `RO-INT-003` | `membrane_integrity` | `product_tube_leak` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `ASTM_D3923_23` |
| `RO-INT-004` | `membrane_integrity` | `oxidation_damage` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `DUPONT_CHLORINATION_R11_2026` |
| `RO-INT-005` | `membrane_integrity` | `permeate_backpressure_damage` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D3923_23`, `ASTM_D6908_25` |
| `RO-INT-006` | `membrane_integrity` | `abrasion_damage` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `ASTM_D3923_23`, `HYDRANAUTICS_TAB116_2022` |
| `RO-INT-007` | `membrane_integrity` | `water_hammer_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB118_16_2019`, `TORAY_RO_HANDLING_MANUAL_2025`, `LG_TSB109_FLUSHING_V2_4_1` |
| `RO-INT-008` | `membrane_integrity` | `compaction_or_mechanical_change` | `runtime_supported` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022` |
| `RO-INT-009` | `membrane_integrity` | `incomplete_wetting` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026` |
| `RO-INT-011` | `membrane_integrity` | `high_differential_pressure` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `TORAY_RO_HANDLING_MANUAL_2025` |
| `RO-INT-012` | `membrane_integrity` | `localization_required` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D3923_23`, `ASTM_D6908_25` |
| `RO-INT-013` | `membrane_integrity` | `integrity_verification_required` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D3923_23`, `ASTM_D6908_25` |
| `RO-INT-014` | `membrane_integrity` | `insufficient_evidence` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D3923_23`, `NIST_AI_RMF_1_0` |
| `RO-PRE-001` | `pretreatment` | `scale_control_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `DUPONT_TROUBLESHOOTING_GRID_R10_2022`, `HYDRANAUTICS_TAB111_2022` |
| `RO-PRE-002` | `pretreatment` | `pretreatment_upset` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB113_04_2016`, `ASTM_D4189_23`, `TORAY_RO_HANDLING_MANUAL_2025` |
| `RO-PRE-003` | `pretreatment` | `oxidant_breakthrough_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_CHLORINATION_R11_2026`, `DUPONT_RO_MANUAL_R19_2026`, `TORAY_RO_HANDLING_MANUAL_2025`, `HYDRANAUTICS_TAB110` |
| `RO-PRE-004` | `pretreatment` | `biofouling_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `HYDRANAUTICS_TSB107_28_2025`, `TORAY_MBFR` |
| `RO-PRE-005` | `pretreatment` | `particle_release_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `TORAY_RO_HANDLING_MANUAL_2025`, `HYDRANAUTICS_TAB116_2022` |
| `RO-PRE-006` | `pretreatment` | `ph_excursion` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23`, `TORAY_RO_HANDLING_MANUAL_2025` |
| `RO-PRE-007` | `pretreatment` | `h2s_deposition_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-PRE-008` | `pretreatment` | `metal_fouling_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4195_23` |
| `RO-PRE-009` | `pretreatment` | `source_water_change` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_FTNORM_PRO_R0_2022`, `ASTM_D4195_23`, `WHO_DESALINATION_2011` |
| `RO-PRE-010` | `pretreatment` | `concentration_risk` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_RO_MANUAL_R19_2026`, `ASTM_D4516_19A`, `ASTM_D4195_23`, `HYDRANAUTICS_TAB111_2022` |
| `RO-PRE-011` | `pretreatment` | `cleaning_requires_verification` | `knowledge_grounded` | `executable_structured_rule` | `HYDRANAUTICS_TSB107_28_2025`, `DUPONT_CLEANING_R13_2026` |
| `RO-DATA-001` | `data_quality` | `recoverable_data_quality_issue` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-002` | `data_quality` | `recoverable_data_quality_issue` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-003` | `data_quality` | `recoverable_data_quality_issue` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-004` | `data_quality` | `recoverable_data_quality_issue` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-005` | `data_quality` | `recoverable_data_quality_issue` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-006` | `data_quality` | `sensor_stuck_suspected` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-007` | `data_quality` | `sensor_spike_suspected` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-008` | `data_quality` | `insufficient_evidence` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-009` | `data_quality` | `unit_mismatch` | `knowledge_grounded` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-DATA-010` | `data_quality` | `insufficient_evidence` | `runtime_supported` | `executable_structured_rule` | `ASTM_D4472_23`, `TORAY_RO_HANDLING_MANUAL_2025`, `NIST_AI_RMF_1_0` |
| `RO-WQ-001` | `drinking_water` | `stabilization_required_context` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `WHO_DESALINATION_2011` |
| `RO-WQ-002` | `drinking_water` | `blending_microbiological_risk` | `knowledge_grounded` | `executable_structured_rule` | `WHO_DESALINATION_2011`, `WHO_GDWQ_2026` |
| `RO-WQ-003` | `drinking_water` | `chemical_risk_assessment_required` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `WHO_DESALINATION_2011` |
| `RO-WQ-004` | `drinking_water` | `microbial_risk_assessment_required` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `WHO_DESALINATION_2011` |
| `RO-WQ-005` | `drinking_water` | `source_water_risk_change` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `WHO_DESALINATION_2011` |
| `RO-WQ-006` | `drinking_water` | `water_safety_plan_escalation` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `WHO_DESALINATION_2011` |
| `RO-WQ-007` | `drinking_water` | `stabilization_required_context` | `knowledge_grounded` | `executable_structured_rule` | `WHO_DESALINATION_2011`, `WHO_GDWQ_2026` |
| `RO-WQ-008` | `drinking_water` | `insufficient_evidence` | `knowledge_grounded` | `executable_structured_rule` | `WHO_GDWQ_2026`, `NIST_AI_RMF_1_0` |
| `AI-SEC-001` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_SP800_82_R3`, `NIST_AI_RMF_1_0`, `NIST_AI_600_1` |
| `AI-SEC-002` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_600_1` |
| `AI-SEC-003` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_600_1` |
| `AI-SEC-004` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_SP800_82_R3`, `NIST_AI_RMF_1_0`, `NIST_AI_600_1` |
| `AI-SEC-005` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_RMF_1_0` |
| `AI-SEC-006` | `agent_ot_security` | `human_authorization_required` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_RMF_1_0` |
| `AI-SEC-007` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `NIST_SP800_82_R3`, `NIST_SP1800_45_2026`, `OWASP_LLM_PROMPT_INJECTION` |
| `AI-SEC-008` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `NIST_SP800_82_R3`, `NIST_SP1800_45_2026`, `OWASP_LLM_PROMPT_INJECTION` |
| `AI-SEC-009` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `NIST_SP800_82_R3`, `NIST_SP1800_45_2026`, `OWASP_LLM_PROMPT_INJECTION` |
| `AI-SEC-010` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `NIST_SP800_82_R3`, `OWASP_LLM_PROMPT_INJECTION`, `HYDRANAUTICS_TSB107_28_2025` |
| `AI-SEC-011` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_SP800_82_R3` |
| `AI-SEC-012` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `NIST_SP1800_45_2026`, `NIST_SP800_82_R3`, `CISA_EPA_FBI_WATER_CYBER_2024`, `EPA_WATER_CYBER_ASSESSMENTS` |
| `AI-SEC-013` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_SP800_82_R3`, `NIST_SP1800_45_2026` |
| `AI-SEC-014` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_RMF_1_0`, `NIST_SP800_82_R3` |
| `AI-SEC-015` | `agent_ot_security` | `safety_block` | `safety_policy` | `executable_structured_rule` | `OWASP_LLM_PROMPT_INJECTION`, `NIST_AI_RMF_1_0` |
| `AI-SEC-016` | `agent_ot_security` | `budget_or_limit_termination` | `safety_policy` | `executable_structured_rule` | `NIST_AI_RMF_1_0`, `NIST_AI_600_1` |
| `RO-CLEAN-001` | `pretreatment` | `cleaning_chemistry_verification_required` | `knowledge_grounded` | `executable_structured_rule` | `DUPONT_CLEANING_R13_2026`, `HYDRANAUTICS_TSB107_28_2025`, `HYDRANAUTICS_TAB111_2022` |
| `RO-CLEAN-002` | `pretreatment` | `cleaning_sequence_verification_required` | `knowledge_grounded` | `executable_structured_rule` | `HYDRANAUTICS_TSB107_28_2025`, `DUPONT_CLEANING_R13_2026` |
