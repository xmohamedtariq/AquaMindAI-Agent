# AquaMind AI — Evidence Vocabulary

Canonical evidence terms: **102**

The vocabulary is the contract between future telemetry adapters and the source-grounded rule engine. Missing fields mean unknown, not false.

| Term | Type | Domain | Meaning |
|---|---|---|---|
| `permeate_flow_direction` | `enum` | `ro_performance` | Direction of normalized or context-qualified permeate-flow change |
| `rejection_direction` | `enum` | `ro_performance` | Direction of salt rejection change |
| `salt_passage_direction` | `enum` | `ro_performance` | Direction of salt-passage change |
| `pressure_drop_direction` | `enum` | `ro_performance` | Direction of feed-to-concentrate differential-pressure change |
| `recovery_direction` | `enum` | `ro_performance` | Direction of recovery change |
| `sec_direction` | `enum` | `ro_performance` | Direction of specific-energy-consumption change |
| `raw_performance_change` | `boolean` | `normalization` | Raw performance change exists before normalization/context adjustment |
| `normalized_metrics_available` | `boolean` | `normalization` | Comparable normalized performance metrics are available |
| `reference_conditions_available` | `boolean` | `normalization` | Valid startup/design reference conditions are available |
| `temperature_shift` | `boolean` | `normalization` | Feedwater temperature materially changed relative to reference |
| `feed_tds_shift` | `boolean` | `normalization` | Feed salinity/TDS materially changed relative to reference |
| `feed_pressure_shift` | `boolean` | `normalization` | Feed/pump pressure materially changed relative to reference |
| `recovery_shift` | `boolean` | `normalization` | Recovery/conversion materially changed relative to reference |
| `operating_flux_shift` | `boolean` | `normalization` | Operating flux materially changed relative to reference |
| `source_water_change` | `boolean` | `normalization` | Source/feedwater composition changed |
| `stage_specific_data_available` | `boolean` | `normalization` | Stage-specific data are available for staged systems |
| `scale_control_issue` | `boolean` | `diagnosis` | Evidence of inadequate or abnormal scale-control context |
| `carbonate_scaling_risk` | `boolean` | `diagnosis` | Water chemistry supports carbonate scaling risk |
| `calcium_sulfate_risk` | `boolean` | `diagnosis` | Water chemistry supports calcium sulfate scaling risk |
| `barium_sulfate_risk` | `boolean` | `diagnosis` | Water chemistry supports barium sulfate scaling risk |
| `strontium_sulfate_risk` | `boolean` | `diagnosis` | Water chemistry supports strontium sulfate scaling risk |
| `calcium_fluoride_risk` | `boolean` | `diagnosis` | Water chemistry supports calcium fluoride scaling risk |
| `silica_scaling_risk` | `boolean` | `diagnosis` | Water chemistry supports silica scaling risk |
| `calcium_phosphate_risk` | `boolean` | `diagnosis` | Water chemistry supports calcium phosphate scaling risk |
| `sdi_elevated` | `boolean` | `diagnosis` | SDI is elevated relative to applicable plant/OEM target |
| `particle_loading_increase` | `boolean` | `diagnosis` | Particulate loading increased |
| `particulate_evidence` | `boolean` | `diagnosis` | Independent evidence supports particulate/colloidal loading |
| `metal_oxide_evidence` | `boolean` | `diagnosis` | Evidence supports metal-oxide deposits |
| `iron_manganese_evidence` | `boolean` | `diagnosis` | Feed/deposit evidence supports iron or manganese fouling |
| `aluminum_evidence` | `boolean` | `diagnosis` | Feed/deposit evidence supports aluminum fouling |
| `bio_evidence` | `boolean` | `diagnosis` | Microbiological/biofilm evidence is present |
| `organic_evidence` | `boolean` | `diagnosis` | Organic/NOM fouling evidence is present |
| `oil_or_cationic_evidence` | `boolean` | `diagnosis` | Oil or cationic-organic contamination evidence is present |
| `oxidant_exposure` | `boolean` | `diagnosis` | Oxidant exposure at the membrane is supported by evidence |
| `seal_issue_evidence` | `boolean` | `diagnosis` | Evidence specifically supports an O-ring/seal issue |
| `product_tube_issue_evidence` | `boolean` | `diagnosis` | Evidence specifically supports product-tube damage/leak |
| `integrity_evidence` | `boolean` | `diagnosis` | Evidence supports a membrane/integrity problem without confirmed subtype |
| `backpressure_event` | `boolean` | `diagnosis` | A permeate-backpressure event is documented or strongly supported |
| `abrasion_evidence` | `boolean` | `diagnosis` | Particle/abrasion context supports mechanical membrane damage |
| `startup_event` | `boolean` | `diagnosis` | The evidence occurs during or immediately after startup |
| `rapid_pressurization` | `boolean` | `diagnosis` | Pressurization was rapid/uncontrolled relative to procedure |
| `trapped_air` | `boolean` | `diagnosis` | Air was not adequately purged before pressurization |
| `wetting_issue_evidence` | `boolean` | `diagnosis` | Dry-out/incomplete-wetting context is supported |
| `high_dp_event` | `boolean` | `diagnosis` | Differential pressure is abnormally high for the plant/OEM context |
| `localized_salt_passage` | `boolean` | `diagnosis` | High salt passage appears localized to a vessel/element region |
| `defect_location_known` | `boolean` | `diagnosis` | The physical location of the integrity defect is known |
| `competing_integrity_hypotheses` | `boolean` | `diagnosis` | Multiple integrity causes remain plausible |
| `integrity_symptoms_incomplete` | `boolean` | `diagnosis` | Integrity evidence is incomplete or internally inconsistent |
| `abnormal_pattern` | `boolean` | `diagnosis` | A sustained abnormal pattern exists |
| `supported_pattern_match` | `boolean` | `diagnosis` | The observed directional pattern matches a supported canonical rule |
| `biofouling_stage` | `enum` | `diagnosis` | Biofouling severity/stage inferred from evidence |
| `antiscalant_issue` | `boolean` | `operations_and_water_safety` | Antiscalant/scale-inhibitor delivery or control issue is supported |
| `pretreatment_upset` | `boolean` | `operations_and_water_safety` | Pretreatment operation or quality is abnormal |
| `chlorine_breakthrough` | `boolean` | `operations_and_water_safety` | Free chlorine/oxidant breakthrough to membrane feed is supported |
| `biological_control_issue` | `boolean` | `operations_and_water_safety` | Biological-control pretreatment is inadequate or abnormal |
| `cartridge_filter_issue` | `boolean` | `operations_and_water_safety` | Cartridge filter integrity/bypass/condition is abnormal |
| `ph_excursion` | `boolean` | `operations_and_water_safety` | Feed pH deviated from plant/OEM context |
| `h2s_context` | `boolean` | `operations_and_water_safety` | Hydrogen sulfide/oxidation deposition context is present |
| `feed_metal_excursion` | `boolean` | `operations_and_water_safety` | Feed metals/corrosion indicators increased |
| `high_recovery` | `boolean` | `operations_and_water_safety` | Recovery is high relative to the approved design/operating context |
| `cleaning_requested` | `boolean` | `operations_and_water_safety` | A cleaning intervention is being considered |
| `foulant_identity_known` | `boolean` | `operations_and_water_safety` | Foulant identity is sufficiently established to choose cleaning chemistry |
| `invalid_timestamp` | `boolean` | `operations_and_water_safety` | Invalid/unparseable timestamp is present |
| `duplicate_timestamp` | `boolean` | `operations_and_water_safety` | Duplicate timestamp is present |
| `out_of_order_records` | `boolean` | `operations_and_water_safety` | Records are not chronological |
| `nonnumeric_sensor_value` | `boolean` | `operations_and_water_safety` | A numeric sensor field contains nonnumeric data |
| `missing_sensor_value` | `boolean` | `operations_and_water_safety` | Required or useful sensor data are missing |
| `sensor_constant` | `boolean` | `operations_and_water_safety` | A sensor is implausibly constant |
| `related_signals_vary` | `boolean` | `operations_and_water_safety` | Related process signals vary while the suspect sensor is constant |
| `sensor_spike` | `boolean` | `operations_and_water_safety` | A transient sensor spike/outlier is present |
| `neighboring_values_normal` | `boolean` | `operations_and_water_safety` | Neighboring values return to baseline/normal context |
| `redundant_sensor_conflict` | `boolean` | `operations_and_water_safety` | Redundant/related measurements materially conflict |
| `unit_inconsistency` | `boolean` | `operations_and_water_safety` | Engineering units or metadata are inconsistent/ambiguous |
| `insufficient_observation_duration` | `boolean` | `operations_and_water_safety` | Too few valid observations exist for defensible trend inference |
| `low_mineral_product_water` | `boolean` | `operations_and_water_safety` | Desalinated product water has low-mineral/stabilization context |
| `blending_active` | `boolean` | `operations_and_water_safety` | Desalinated product water is blended with another source |
| `blend_microbial_safety_unverified` | `boolean` | `operations_and_water_safety` | Microbial safety of blending water is unverified |
| `chemical_hazard_unresolved` | `boolean` | `operations_and_water_safety` | A product-water chemical hazard is unresolved |
| `microbial_hazard_unresolved` | `boolean` | `operations_and_water_safety` | A product-water microbial hazard is unresolved |
| `source_water_hazard_change` | `boolean` | `operations_and_water_safety` | Health-relevant source-water hazard profile changed |
| `health_relevant_hazard_unresolved` | `boolean` | `operations_and_water_safety` | A health-relevant hazard cannot be resolved by RO telemetry alone |
| `distribution_corrosion_context` | `boolean` | `operations_and_water_safety` | Post-desalination water may be aggressive/corrosive in distribution context |
| `health_limit_unavailable` | `boolean` | `operations_and_water_safety` | Applicable health/regulatory target is unavailable to the agent |
| `direct_prompt_injection` | `boolean` | `agent_ot_security` | Direct user instruction attempts to override higher-priority policy |
| `indirect_prompt_injection` | `boolean` | `agent_ot_security` | Retrieved/external content contains instructions targeting the agent |
| `prompt_exfiltration_request` | `boolean` | `agent_ot_security` | Request attempts to reveal protected prompts/instructions/secrets |
| `policy_bypass_request` | `boolean` | `agent_ot_security` | Request asks to bypass safety/permission/audit policy |
| `forced_tool_execution` | `boolean` | `agent_ot_security` | Request attempts to force a tool call regardless of validation/authorization |
| `persistent_write_requested` | `boolean` | `agent_ot_security` | A persistent state-changing write is requested |
| `approval_present` | `boolean` | `agent_ot_security` | Required explicit approval is present |
| `valve_control_requested` | `boolean` | `agent_ot_security` | Physical valve actuation is requested |
| `pump_control_requested` | `boolean` | `agent_ot_security` | Physical pump actuation is requested |
| `setpoint_change_requested` | `boolean` | `agent_ot_security` | Physical process setpoint change is requested |
| `cleaning_cycle_start_requested` | `boolean` | `agent_ot_security` | Physical cleaning-cycle start is requested |
| `unknown_tool_requested` | `boolean` | `agent_ot_security` | Requested tool is not in the explicit registry |
| `ot_remote_access_requested` | `boolean` | `agent_ot_security` | Unapproved remote access to OT/SCADA is requested |
| `credential_exfiltration_requested` | `boolean` | `agent_ot_security` | Credentials/tokens/secrets are requested |
| `audit_tampering_requested` | `boolean` | `agent_ot_security` | Request attempts to delete/rewrite/conceal audit evidence |
| `unsafe_tool_parameters` | `boolean` | `agent_ot_security` | Tool is allowed but parameters violate scope/path/permission constraints |
| `configured_limit_reached` | `boolean` | `agent_ot_security` | Turn/tool/cost limit has been reached |
| `cleaning_chemistry_compatible` | `boolean` | `operations_and_water_safety` | Proposed cleaning chemistry is verified compatible with the membrane and operating context |
| `cleaning_sequence_valid` | `boolean` | `operations_and_water_safety` | Proposed cleaning sequence is verified appropriate for the suspected foulant and membrane context |
