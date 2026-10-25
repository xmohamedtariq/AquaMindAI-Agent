# AquaMind AI — Authoritative Sources

## Purpose

This document is the human-readable bibliography for AquaMind AI's source-grounded desalination O&M knowledge base.

AquaMind does **not** claim to be trained on real plant telemetry unless such data is explicitly provided and documented. The production reasoning layer is grounded in a curated, traceable knowledge base, and the scenario bank uses reproducible **synthetic** telemetry.

Every supported diagnostic pattern should be traceable through:

**Authoritative source → knowledge rule → scenario → agent decision → test → trace**

## Source quality policy

- **Tier A** — official manufacturer manuals/bulletins, consensus standards, international public-health guidance, or government guidance.
- **Tier B** — official cross-check/draft sources that strengthen coverage but should not override applicable final standards or plant-specific documentation.
- Prefer the latest official English version where a manufacturer states that the current English version is authoritative.
- Manufacturer operating limits are product-specific and are never generalized to every membrane.
- ASTM/AWWA paid material is referenced by title, edition, DOI/catalog metadata, scope, and legitimately accessed notes. AquaMind does not redistribute copyrighted standards.
- No source in this bibliography authorizes AquaMind to actuate pumps, valves, cleaning cycles, PLCs, or SCADA.

## 1. Core RO/NF engineering — DuPont FilmTec

### DUPONT_RO_MANUAL_V20_2026 — Tier A
**FilmTec Reverse Osmosis Membranes Technical Manual — Version 20, August 2026**  
Official DuPont Water Solutions manual covering RO/NF fundamentals, feedwater analysis, pretreatment, system design, startup/shutdown, operating data, normalization, cleaning and troubleshooting.  
https://www.dupont.com/content/dam/water/amer/us/en/water/public/documents/en/RO-NF-FilmTec-Manual-45-D01504-en.pdf

### DUPONT_TROUBLESHOOTING_GRID_2022 — Tier A
**FilmTec RO/NF Troubleshooting Grid — Rev. 10, February 2022**  
Core qualitative source for symptom patterns involving permeate flow, salt passage and differential pressure and their association with scaling, colloidal fouling, biofouling, organic fouling, oxidation damage, membrane/O-ring/product-tube leaks and compaction.  
https://www.dupont.com/content/dam/dupont/amer/us/en/water-solutions/public/documents/en/RO-NF-FilmTec-Troubleshooting-Grid-Manual-Exc-45-D01653-en.pdf

### DUPONT_CLEANING_2022 — Tier A
**FilmTec Cleaning Procedures — Rev. 12, June 2022**  
Grounding for normalized-performance cleaning indicators and the requirement to consider pretreatment/operating changes before concluding that membranes require cleaning.  
https://www.dupont.com/content/dam/dupont/amer/us/en/water-solutions/public/documents/en/RO-NF-FilmTec-Cleaning-Procedures-Manual-Exc-45-D01696-en.pdf

### DUPONT_CHLORINATION_2026 — Tier A
**Water Chemistry and Pretreatment — Chlorination/Dechlorination**  
Grounding for oxidation risk, chlorine removal and biological-fouling prevention.  
https://www.dupont.com/content/dam/water/amer/us/en/water/public/documents/en/RO-NF-FilmTec-Chlorination-Dechlorination-Manual-Exc-45-D01569-en.pdf

### DUPONT_FTNORM_PRO_2026 — Tier A
**FT-Norm PRO Technical Manual — Version 1, September 2026**  
Primary reference for future formal RO/NF normalization. It explicitly explains why temperature, feedwater quality, flux and recovery changes can mask or imitate membrane performance changes.  
https://www.dupont.com/content/dam/water/amer/us/en/water/public/documents/en/RO-FT-Norm-Pro-Manual-45-D03917-en.pdf

### DUPONT_OPERATION_LIMITS_2026 — Tier A
**FilmTec RO/NF Elements Operation Excellence and Limiting Conditions**  
Product/manufacturer-specific operating protection reference.  
https://www.dupont.com/content/dam/water/amer/us/en/water/public/documents/en/RO-NF-FilmTec-Operation-Excellence-Limiting-Conditions-TechFact-45-D04388-en.pdf

## 2. Independent membrane-manufacturer cross-checks

### HYDRANAUTICS_TSB107_2026 — Tier A
**Hydranautics/Nitto TSB107.30 — Foulants and Cleaning Procedures, April 2026**  
Covers carbonate/sulfate scale, metal oxides, silica, colloids, natural/man-made organics and biological fouling and stresses normalization when operating conditions vary.  
https://membranes.com/wp-content/uploads/Documents/TSB/TSB107.pdf

### HYDRANAUTICS_TSB113 — Tier A
**Hydranautics/Nitto TSB113.04 — Procedure for Measuring SDI**  
Official manufacturer guidance for SDI/feedwater-quality testing; use together with ASTM D4189.  
https://membranes.com/wp-content/uploads/2014/12/TSB113.pdf

### HYDRANAUTICS_TSB118 — Tier A
**Hydranautics/Nitto TSB118.16 — Startup, Shutdown and Preservative Flushing**  
Grounding for safe startup/shutdown reasoning, air purging, controlled pressurization and water-hammer prevention.  
https://membranes.com/wp-content/uploads/Documents/TSB/TSB118.pdf

### LG_TSB109_FLUSHING — Tier B
**LG Water Solutions TSB 109 — Membrane Element Flushing**  
Independent manufacturer cross-check for startup/shutdown flushing and controlled pressurization.  
https://www.lgwatersolutions.com/wp-content/uploads/2025/07/109.-Membrane-Element-Flushing.pdf

## 3. AWWA professional manuals and standards

AWWA states that its manuals are developed and reviewed by water-industry committees and experts.

### AWWA_M46 — Tier A
**M46 Reverse Osmosis and Nanofiltration** — selection, installation, operation and maintenance.  
https://www.awwa.org/resource/membrane-processes/

### AWWA_M61 — Tier A
**M61 Desalination of Seawater** — technical/planning guidance for seawater desalination facilities.  
https://www.awwa.org/resource/membrane-processes/

### AWWA_M69 — Tier A
**M69 Inland Desalination and Concentrate Management**.  
https://www.awwa.org/manuals/manuals-list/

### AWWA_B114_22 — Tier A
**ANSI/AWWA B114-22 Reverse Osmosis and Nanofiltration Systems for Water Treatment** — minimum requirements for RO/NF systems.  
https://www.awwa.org/standards/standards-list

**Copyright note:** AWWA manuals/standards may require purchase. AquaMind stores bibliographic/provenance metadata and only knowledge that is lawfully available to the project.

## 4. WHO public-health and desalinated-water safety

### WHO_GDWQ_2026 — Tier A
**WHO Guidelines for drinking-water quality: fourth edition incorporating the first, second and third addenda — 17 June 2026**  
Primary health-risk/water-safety framework.  
https://www.who.int/publications/i/item/9789240121225

### WHO_DESALINATION_2011 — Tier A
**Safe drinking-water from desalination — WHO, 2011**  
Desalination-specific risk-assessment and risk-management guidance.  
https://www.who.int/publications/i/item/WHO-HSE-WSH-11.03

## 5. ASTM RO/NF standards

### ASTM_D4194_23 — Tier A
**ASTM D4194-23 — Operating Characteristics of RO/NF Devices**  
https://store.astm.org/d4194-23.html

### ASTM_D3923_23 — Tier A
**ASTM D3923-23 — Detecting Leaks in RO/NF Devices**  
https://store.astm.org/d3923-23.html

### ASTM_D4195_23 — Tier A
**ASTM D4195-23 — Water Analysis for RO/NF Application**  
https://store.astm.org/d4195-23.html

### ASTM_D4189_23 — Tier A
**ASTM D4189-23 — Silt Density Index (SDI) of Water**  
https://store.astm.org/d4189-23.html

### ASTM_D4472_23 — Tier A
**ASTM D4472-23 — Recordkeeping for RO/NF Systems**  
https://store.astm.org/d4472-23.html

### ASTM_D4516_19A — Tier A
**ASTM D4516-19a — Standardizing Reverse Osmosis Performance Data**  
Especially important for avoiding false fault conclusions when pressure, temperature, conversion/recovery or feed concentration changes.  
https://store.astm.org/standards/d4516

### ASTM_D4582_23 — Tier A
**ASTM D4582-23 — Stiff and Davis Stability Index for Reverse Osmosis**  
Applicable within its stated high-TDS concentrate scope.  
https://store.astm.org/d4582-23.html

### ASTM_D6908_25 — Tier A
**ASTM D6908-25 — Integrity Testing of Water Filtration Membrane Systems**  
Includes RO/NF/UF membrane classes.  
https://store.astm.org/standards/d6908

**Copyright note:** The registry does not redistribute ASTM standard text.

## 6. Government desalination research

### USBR_DWPR — Tier A
**U.S. Bureau of Reclamation — Desalination and Water Purification Research Program**  
Government research program focused on desalination/water-treatment innovation, cost, energy and barriers to deployment.  
https://www.usbr.gov/research/dwpr/index.html

## 7. OT / water-sector cybersecurity

### NIST_SP800_82_R3 — Tier A
**NIST SP 800-82 Rev. 3 — Guide to Operational Technology (OT) Security — Final, September 2023**  
Primary final OT-security reference for SCADA/ICS/PLC risk, architectures and controls.  
https://csrc.nist.gov/pubs/sp/800/82/r3/final

### NIST_SP800_82_R4_IPD_2026 — Tier B / Draft
**NIST SP 800-82 Rev. 4 — Initial Public Draft, September 2026**  
Useful future-looking source with expanded water/IIoT/CSF 2.0 coverage. It must not be represented as final.  
https://csrc.nist.gov/pubs/sp/800/82/r4/ipd

### NIST_SP1800_45_2026 — Tier A
**NIST SP 1800-45 — Cybersecurity for the Water and Wastewater Sector: OT Remote Access — Final, June 2026**  
Sector-specific reference for secure remote access architectures.  
https://csrc.nist.gov/pubs/sp/1800/45/final

### CISA_EPA_FBI_WATER_CYBER_2024 — Tier A
**CISA/EPA/FBI — Top Cyber Actions for Securing Water Systems**  
https://www.cisa.gov/news-events/alerts/2024/02/21/cisa-epa-and-fbi-release-top-cyber-actions-securing-water-systems

### EPA_WATER_CYBER_ASSESSMENTS — Tier A
**U.S. EPA — Cybersecurity Assessments for Water Systems**  
https://www.epa.gov/cyberwater/cybersecurity-assessments

## 8. AI-agent governance and prompt-injection defense

### NIST_AI_RMF_1_0 — Tier A
**NIST Artificial Intelligence Risk Management Framework 1.0**  
https://www.nist.gov/itl/ai-risk-management-framework

### NIST_AI_600_1 — Tier A
**NIST AI 600-1 — Generative AI Profile**  
https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence

### OWASP_LLM_PROMPT_INJECTION — Tier A
**OWASP LLM Prompt Injection Prevention Cheat Sheet**  
Supports defense-in-depth, least privilege, tool-call validation, action-specific approval and monitoring.  
https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

## Source-governance rule

AquaMind should never assert:

- that a diagnostic hypothesis is a confirmed root cause solely from telemetry;
- that a manufacturer-specific threshold is universal;
- that an ASTM/AWWA requirement was checked unless the project has legitimate access to the relevant text;
- that a draft publication is final;
- that synthetic scenarios are real plant incidents;
- that a recommendation authorizes autonomous physical plant action.

When evidence is ambiguous, the correct behavior is to report **insufficient evidence** or an **unclassified abnormal pattern** and recommend verification.
